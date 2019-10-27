# Used as a supporting module for the rest of the benchmarks, so we don't have to screw around with keys in dicts

from collections import namedtuple


interval_metric_fields = [
    "timestamp", # Unix epoch
    "interval_index", # The numerical index of this metric
    "per_cpu_utilization", # list, each item representing a cpu core
    "avg_cpu_utilization", # Average across all cores
    "bytes_sent_since_system_start", 
    "bytes_received_since_system_start",
    "bytes_sent_per_sec", # Bytes sent in this interval
    "bytes_received_per_sec", # Bytes received in this interval
    "cpu_times_percent", # Named tuple, consisting of (user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice) for this interval
    "context_switches_since_system_start",
    "interrupts_since_system_start",
    "soft_interrupts_since_system_start",
    "context_switches_per_sec",
    "interrupts_per_sec",
    "soft_interrupts_per_sec",
]

Interval_Metric = namedtuple("Interval_Metric", interval_metric_fields)