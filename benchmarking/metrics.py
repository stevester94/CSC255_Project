#! /usr/bin/python3

# Needs to be installed with pip
import psutil as ps
import iperf3

import time
from multiprocessing import Process, Manager
import pprint
import json
import sys

from interval_metric import  Interval_Metric

COLLECTOR_PADDING_SECS = 2

pp = pprint.PrettyPrinter(indent=4)

class Benchmark_Server:
    # What a pain in the ass. Have to pass a dict from multiprocessing.Manager, so that the results
    # can actually be passed back to the originating process. Fuck
    def __init__(self, bind_address, bind_port, duration, protocol, managed_metrics_dict):
        self.server = iperf3.Server()
        
        # Configure server
        self.server.protocol = protocol
        # self.server.duration = duration
        self.server.bind_address = bind_address
        self.server.port = bind_port
        self.metrics = managed_metrics_dict

    def _start(self):
        self.metrics = self.server.run()

    def start(self):
        self.thread = Process(target=self._start, args=())
        print("Starting Server")
        self.thread.start()
        print("Server started")

    def wait_until_done(self):
        self.thread.join()


class Benchmark_Client:
    def __init__(self, target_hostname, target_port, duration, protocol, managed_metrics_dict):
        self.client =  iperf3.Client()
        self.metrics = managed_metrics_dict
        # Configure Client
        self.client.server_hostname = target_hostname
        self.client.port = target_port
        self.client.duration = duration
        self.client.protocol = protocol

    def start(self):
        print("Starting client")
        self.thread = Process(target=self._start, args=())
        self.thread.start()
        print("Client started")

    def _start(self):
        self.results = self.client.run()

    def wait_until_done(self):
        self.thread.join()

    def get_results(self):
        return self.results


class Benchmark_Collector:
    # NB!: this accepts a list, not a dict like the client/server benchmark
    def __init__(self, managed_metrics_list):
        self.metrics = managed_metrics_list
        self.callbacks = []

    # Begin Collection    
    def start(self, duration_secs, interval_secs):
        self.duration_secs = duration_secs
        self.interval_secs = interval_secs

        print("Running for {} seconds, collecting metrics every {} seconds".format(self.duration_secs, self.interval_secs))
        self.thread = Process(target=self._main_loop, args=())

        # print("Warning, not doing shit!")
        self.thread.start()
        

    
    # Block until we are done with the collection
    def wait_until_done(self):
        self.thread.join()

    # Optional. Register callbacks to be called on every metric
    # callback takes a single arg of Interval_Metric
    # Multiple callbacks can be registered
    def register_callback(self, cb):
        self.callbacks.append(cb)

    def clear_callbacks(self):
        self.callbacks = []

    # Collect for duration_secs, write out results to metrics_path when done
    def _main_loop(self):
        self.start_time = time.time()

        metrics = []
        interval_index = 0

        # https://psutil.readthedocs.io/en/latest/ : cpu_percent()
        #   compares system CPU times elapsed since last call or module import, returning immediately.
        # This entails we must prime the pump...
        ps.cpu_percent(percpu=True)
        ps.cpu_times_percent(percpu=False) # Same for this guy

        # This returns number of bytes sent/received since system start, so we are guaranteed to be monotonically increasing
        # Also entails we need a reference point for when we start collecting metrics, hence we need this initial
        network_initial = ps.net_io_counters()
        cpu_stats_intial = ps.cpu_stats()

        while(time.time() - self.start_time  < self.duration_secs):
            time.sleep(self.interval_secs)

            interval_metric = {}
            interval_metric["timestamp"] = time.time()
            interval_metric["interval_index"] = interval_index
            interval_index += 1

            ###################
            # CPU UTILIZATION #
            ###################

            # Get per CPU utilization since last call
            interval_metric["per_cpu_utilization"] = ps.cpu_percent(percpu=True)
            interval_metric["cpu_times_percent"] = ps.cpu_times_percent(percpu=False)

            # Average the CPU utilization
            total = 0
            for util in interval_metric["per_cpu_utilization"]:
                total += util
            
            interval_metric["avg_cpu_utilization"] = total / len(interval_metric["per_cpu_utilization"])

            cpu_stats = ps.cpu_stats()
            # Totals
            interval_metric["context_switches_since_system_start"] = cpu_stats.ctx_switches
            interval_metric["interrupts_since_system_start"] = cpu_stats.interrupts
            interval_metric["soft_interrupts_since_system_start"] = cpu_stats.soft_interrupts

            # if first interval, use the cpu_stats_initial that we took before starting
            if(len(metrics) == 0):
                interval_metric["context_switches_per_sec"] = (interval_metric["context_switches_since_system_start"] -  cpu_stats_intial.ctx_switches) / self.interval_secs
                interval_metric["interrupts_per_sec"] = (interval_metric["interrupts_since_system_start"] - cpu_stats_intial.interrupts) / self.interval_secs
                interval_metric["soft_interrupts_per_sec"] = (interval_metric["soft_interrupts_since_system_start"] - cpu_stats_intial.soft_interrupts) / self.interval_secs

                # Rates
            else:
                interval_metric["context_switches_per_sec"] = (interval_metric["context_switches_since_system_start"] - metrics[-1].context_switches_since_system_start) / self.interval_secs
                interval_metric["interrupts_per_sec"] = (interval_metric["interrupts_since_system_start"] - metrics[-1].interrupts_since_system_start) / self.interval_secs
                interval_metric["soft_interrupts_per_sec"] = (interval_metric["soft_interrupts_since_system_start"] - metrics[-1].soft_interrupts_since_system_start) / self.interval_secs
            
            #######################
            # NETWORK UTILIZATION #
            #######################

            # Calculate number of bytes sent in this interval.
            # This gives number of bytes sent/received since system start, so we are guaranteed to be monotonically increasing
            network_interval = ps.net_io_counters()

            # if first interval, use the network_initial we took before starting
            if(len(metrics) == 0):
                # Totals for the interval
                interval_metric["bytes_sent_since_system_start"] = network_interval.bytes_sent
                interval_metric["bytes_received_since_system_start"] = network_interval.bytes_recv

                # Rate for the interval
                interval_metric["bytes_sent_per_sec"] = (network_interval.bytes_sent - network_initial.bytes_sent) / self.interval_secs
                interval_metric["bytes_received_per_sec"] = (network_interval.bytes_recv - network_initial.bytes_recv) / self.interval_secs
            else:
                # Totals for the interval, use the previous metric interval for this calculation
                interval_metric["bytes_sent_since_system_start"] = network_interval.bytes_sent
                interval_metric["bytes_received_since_system_start"] = network_interval.bytes_recv

                # Rate for the interval, use the previous interval metric for this calculation
                interval_metric["bytes_sent_per_sec"] = (network_interval.bytes_sent - metrics[-1].bytes_sent_since_system_start) / self.interval_secs
                interval_metric["bytes_received_per_sec"] = (network_interval.bytes_recv - metrics[-1].bytes_received_since_system_start) / self.interval_secs

            # Pack it into our named tuple before appending to list
            i = Interval_Metric(**interval_metric)

            for cb in self.callbacks:
                cb(i)

            metrics.append(i)
        
        print("Collecting done, setting metrics")
        self.metrics = [m._asdict() for m in self.metrics]
        print("Metrics set")




def metric_cb(metric):
    print("Finished with metric: {}".format(metric.interval_index))

if __name__ == "__main__":
    if(len(sys.argv) != 8):
        print("Usage is <client|server> <tcp|udp> <hostname> <port> <duration secs> <metric interval secs> <results out path>")
        print("Note, metric interval seconds can be fractional, duration must be whole seconds")
        print("Note, the general metrics (interrupts, cpu usage, etc) start {} seconds after iperf, and end {} seconds before iperf".format(COLLECTOR_PADDING_SECS,COLLECTOR_PADDING_SECS))
        print("    This is so that we only collect metrics while the test is running")
        sys.exit(1)

    print("Note, the general metrics (interrupts, cpu usage, etc) start {} seconds after iperf, and end {} seconds before iperf".format(COLLECTOR_PADDING_SECS,COLLECTOR_PADDING_SECS))
    print("    This is so that we only collect metrics while the test is running")

    is_client = "client" == sys.argv[1]
    protocol  = sys.argv[2]
    hostname = sys.argv[3]
    port     = sys.argv[4]
    duration_secs = int(sys.argv[5])
    interval_secs = float(sys.argv[6])
    results_path = sys.argv[7]

    with Manager() as manager:
        client = None
        server = None
        client_metrics = None
        server_metrics = None
        baseline_metrics = manager.list()
        
        bench = Benchmark_Collector(baseline_metrics)
        bench.register_callback(metric_cb)
        

        if is_client:
            client_metrics = manager.dict()
            client = Benchmark_Client(hostname, port, duration_secs, protocol, client_metrics)
            client.start()
        else:
            server_metrics = manager.dict()
            server = Benchmark_Server(hostname, port, duration_secs, protocol, server_metrics) # Still need to decide if duration is necessary for the server
            server.start()


        time.sleep(COLLECTOR_PADDING_SECS)
        print("Starting benchmark collector")
        bench.start(duration_secs - COLLECTOR_PADDING_SECS, interval_secs)
        print("Benchmark collector started")


        if is_client:
            print("Waiting until client is done")
            client.wait_until_done()
        else:
            print("Waiting until server is done")
            server.wait_until_done()

        print("Waiting until benchmark collector is done")
        bench.wait_until_done()
        print("All done")


        print("Collating results")
        all_metrics = {}
        
        print(baseline_metrics)

        all_metrics["baseline"] = baseline_metrics

        if is_client:
            all_metrics["client"] = client_metrics
        else:
            all_metrics["server"] = server_metrics
            
        with open(results_path, "w") as f:
            f.write(json.dumps(all_metrics, indent=4, sort_keys=True)) 
