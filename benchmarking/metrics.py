#! /usr/bin/python3

# Needs to be installed with pip
import psutil as ps

import time
import threading
import pprint
import json
import sys

from interval_metric import  Interval_Metric

pp = pprint.PrettyPrinter(indent=4)




class Benchmark_Collector:
    def __init__(self, metrics_path):
        self.metrics_path = metrics_path
        self.callbacks = []

    # Begin Collection    
    def start(self, duration_secs, interval_secs):
        self.duration_secs = duration_secs
        self.interval_secs = interval_secs

        print("Running for {} seconds, collecting metrics every {} seconds".format(self.duration_secs, self.interval_secs))
        self.thread = threading.Thread(target=self._main_loop, args=())
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
            
        self._write_metrics_to_file(metrics)

    def _write_metrics_to_file(self, metrics):
        # Kinda sucks, serializing namedtuples with json.dumps does not maintain the field names
        metrics_as_dicts = [m._asdict() for m in metrics]
        
        with open(self.metrics_path, "w") as f:
            f.write(json.dumps(metrics_as_dicts, indent=4, sort_keys=True))




def metric_cb(metric):
    print("Finished with metric: {}".format(metric.interval_index))

if __name__ == "__main__":
    if(len(sys.argv) != 4):
        print("Usage is <duration secs> <metric interval secs> <results out path>")
        print("Note, seconds can be fractional")
        sys.exit(1)

    bench = Benchmark_Collector(sys.argv[3])
    bench.register_callback(metric_cb)

    bench.start(float(sys.argv[1]), float(sys.argv[2]))
    print("Constructed")
    bench.wait_until_done()
    print("Done")
