#! /usr/bin/python3

# Needs to be installed with pip
import psutil as ps

import time
import subprocess
from threading import Thread
import pprint
import json
import sys

from interval_metric import  Interval_Metric

COLLECTOR_PADDING_SECS = 2

pp = pprint.PrettyPrinter(indent=4)

class Benchmark_Server:
    def __init__(self, bind_address, bind_port, protocol):
        #--server --port 9001 --bind 127.0.0.1 --interval 1 -J --one-off
        self.iperf_args = None

        if protocol == "tcp":
            self.iperf_args = ["iperf3", "--server", "--port", str(bind_port), "--bind", bind_address, "--interval", "0", "-J", "--one-off"]
        elif protocol == "udp":
            self.iperf_args = ["iperf3", "--server", "--port", str(bind_port), "--bind", bind_address, "--interval", "0", "-J", "--one-off"]

    def start(self):
        print("Starting iperf server")
        self.sub_process = subprocess.Popen(self.iperf_args, stdout=subprocess.PIPE)
        print("iperf server started")

    def wait_until_done(self):
        self.sub_process.wait()

    def get_metrics(self):
        stdout, _ = self.sub_process.communicate()
        metrics  = json.loads(stdout)

        ret_dict = {}
        ret_dict["bytes_per_second"] = float(metrics["intervals"][0]["streams"][0]["bits_per_second"]) / 8.0

        return ret_dict

class Benchmark_Client:
    def __init__(self, target_hostname, target_port, duration, protocol):
        self.iperf_args = None
        self.sub_process = None
        self.protocol = protocol

        #iperf3 --client 127.0.0.1 --port 9001 --bandwidth 0 --format m --interval 5 --time 10 -J
        if protocol == "tcp":
            self.iperf_args = ["iperf3", "--client", target_hostname, "--port", str(target_port), "--bandwidth", "0", "--format", "m", "--interval", "0", "--time", str(duration), "-J"]
        else:
            self.iperf_args = ["iperf3", "--client", target_hostname, "--port", str(target_port), "--bandwidth", "0", "--format", "m", "--interval", "0", "--time", str(duration), "-J", "--udp"]

    def start(self):
        print("Starting iperf client")
        self.sub_process = subprocess.Popen(self.iperf_args, stdout=subprocess.PIPE)
        print("iperf client started")

    def wait_until_done(self):
        self.sub_process.wait()

    def get_metrics(self):
        stdout, _ = self.sub_process.communicate()
        metrics  = json.loads(stdout)

        ret_dict = {}
        ret_dict["bytes_per_second"] = float(metrics["intervals"][0]["streams"][0]["bits_per_second"]) / 8.0

        if self.protocol == "udp":
            ret_dict["lost_udp_packets_percent"] = metrics["end"]["sum"]["lost_percent"]

        return ret_dict


class RTT_Client:
    def __init__(self, target_hostname):
        self.target_hostname = target_hostname

    # returns the average RTT to the target, in ms
    def run(self):
        print("Running RTT test")
        self.sub_process = subprocess.Popen(["ping", "-q", "-c10", self.target_hostname], stdout=subprocess.PIPE)
        self.sub_process.wait()

        stdout, _ = self.sub_process.communicate()
        stdout = str(stdout)

        # Output is in the form of 
        #   rtt min/avg/max/mdev = 14.239/44.202/85.424/22.772 ms

        equal_index = stdout.find("=")
        substr = stdout[equal_index:-3] # Strip of trailing newline and a "'"

        units = substr[-2:] # Get the units of the output

        substr = substr[2:-3]
        
        rtt_avg = substr.split("/")[1]
        rtt_avg = float(rtt_avg)

        if units != "ms":
            print("Units are jacked up on the ping command!")
            sys.exit(1)
        
        print("RTT test done")
        
        return rtt_avg
        

        

class Benchmark_Collector:
    def __init__(self):
        self.callbacks = []

    # Begin Collection    
    def start(self, duration_secs, interval_secs):
        self.duration_secs = duration_secs
        self.interval_secs = interval_secs

        print("Running for {} seconds, collecting metrics every {} seconds".format(self.duration_secs, self.interval_secs))
        self.thread = Thread(target=self._main_loop, args=())
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
            network_interval = ps.net_io_counters(pernic=True)["eth0"]

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
        
        # OK, kinda shitty, we have to convert all those named tuples to dicts in order to json them
        self.metrics = [m._asdict() for m in metrics]

    def get_metrics(self):
        return self.metrics




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

    client = None
    server = None
    rtt_client = None

    bench = Benchmark_Collector()
    bench.register_callback(metric_cb)
    

    if is_client:
        client = Benchmark_Client(hostname, port, duration_secs, protocol)
        client.start()
    else:
        server = Benchmark_Server(hostname, port, protocol)
        server.start()


    time.sleep(COLLECTOR_PADDING_SECS)
    print("Starting benchmark collector")
    bench.start(duration_secs - COLLECTOR_PADDING_SECS, interval_secs)
    print("Benchmark collector started")


    if is_client:
        print("Waiting until client is done")
        client.wait_until_done()
        print("Client is done")
    else:
        print("Waiting until server is done")
        server.wait_until_done()
        print("Server is done")

    print("Waiting until benchmark collector is done")
    bench.wait_until_done()

    avg_rtt_ms = None
    if is_client:
        rtt_client = RTT_Client(hostname)
        avg_rtt_ms = rtt_client.run()

    print("All done")


    print("Collating results")
    all_metrics = {}
    baseline_metrics = bench.get_metrics()
    

    all_metrics["baseline"] = baseline_metrics
    all_metrics["protocol"] = protocol
    all_metrics["target_hostname"] = hostname

    if is_client:
        client_metrics = client.get_metrics()
        client_metrics["avg_rtt_ms"] = avg_rtt_ms
        all_metrics["client"] = client_metrics
        all_metrics["role"] = "client"
    else:
        server_metrics = server.get_metrics()
        all_metrics["server"] = server_metrics
        all_metrics["role"] = "server"
        
    with open(results_path, "w") as f:
        f.write(json.dumps(all_metrics, indent=4, sort_keys=True)) 
 
