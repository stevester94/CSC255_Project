#! /usr/bin/python3


import psutil as ps
import time
import threading
import pprint
from collections import namedtuple

pp = pprint.PrettyPrinter(indent=4)

class Benchmark_Collector:
    def __init__(self, metrics_path):
        self.metrics_path = metrics_path

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

    # Collect for duration_secs, write out results to metrics_path when done
    def _main_loop(self):
        self.start_time = time.time()

        metrics = []
        interval_index = 0

        # https://psutil.readthedocs.io/en/latest/ : cpu_percent()
        #   compares system CPU times elapsed since last call or module import, returning immediately.
        # This entails we must prime the pump...
        ps.cpu_percent(percpu=True)

        # This returns number of bytes sent/received since system start, so we are guaranteed to be monotonically increasing
        # Also entails we need a reference point for when we start collecting metrics, hence we need this initial
        network_initial = ps.net_io_counters()

        while(time.time() - self.start_time  < self.duration_secs):
            time.sleep(self.interval_secs)

            interval_metric = {}
            interval_metric["timestamp"] = time.time()
            interval_metric["interval_index"] = interval_index
            print("Begin interval {}".format(interval_index))
            interval_index += 1

            # Get per CPU utilization since last call
            interval_metric["per_cpu_utilization"] = ps.cpu_percent(percpu=True)

            # Average the CPU utilization
            total = 0
            for util in interval_metric["per_cpu_utilization"]:
                total += util
            
            interval_metric["avg_cpu_utilization"] = total / len(interval_metric["per_cpu_utilization"])
            
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
                interval_metric["bytes_sent_per_sec"] = (network_interval.bytes_sent - metrics[-1]["bytes_sent_since_system_start"]) / self.interval_secs
                interval_metric["bytes_received_per_sec"] = (network_interval.bytes_recv - metrics[-1]["bytes_received_since_system_start"]) / self.interval_secs





            metrics.append(interval_metric)
            

        # pp.pprint(metrics)


def test_cpu_times():
    first = ps.cpu_times(percpu=False)
    first = first.user + first.system + first.idle

    time.sleep(1)

    second = ps.cpu_times(percpu=False)
    second = second.user + second.system + second.idle

    print("second - first: {}".format(second- first))


if __name__ == "__main__":
    bench = Benchmark_Collector("results.json")

    test_cpu_times()

    # bench.start(60, 0.1)
    # print("Constructed")
    # bench.wait_until_done()
    # print("Done")