#! /usr/bin/python3
from interval_metric import  Interval_Metric
import matplotlib.pyplot as plt
import json
import pprint
from collections import namedtuple

pp = pprint.PrettyPrinter(indent=4)


# Unused metrics, we'll keep these around if we want them later
    # Plot_Target(title="bytes_sent_since_system_start", y_values=get_single_metric("bytes_sent_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes"))
    # Plot_Target(title="bytes_received_since_system_start", y_values=get_single_metric("bytes_received_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes"))
    # Plot_Target(title="context_switches_since_system_start", y_values=get_single_metric("context_switches_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Context Switches"))
    # Plot_Target(title="interrupts_since_system_start", y_values=get_single_metric("interrupts_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Interrupts"))
    # Plot_Target(title="soft_interrupts_since_system_start", y_values=get_single_metric("soft_interrupts_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Soft Interrupts"))
    # Plot_Target(title="per_cpu_utilization", y_values=get_single_metric("per_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    # Plot_Target(title="cpu_times_percent", y_values=get_single_metric("cpu_times_percent", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Time %"))

def parse_interval_metrics(d):
    metrics = []


    for metric in d["baseline"]:
        m = Interval_Metric(**metric)
        metrics.append(m)
    
    return metrics

def parse_json_to_dict(path):
    with open(path, "r") as f:
        j = json.load(f)
        return j

def get_single_metric(field, metrics):
    return [getattr(m, field) for m in metrics]


plot_target_fields = [
    "title",
    "x_values",
    "y_values",
    "x_axis_label",
    "y_axis_label"
]
Plot_Target = namedtuple("Plot_Target", plot_target_fields)

# Global plot index, set back to 1 if you're making a new window
g_plot_index = 1
g_plot_nrows = 3 # Don't change this
g_plot_ncols = 2 # Don't change this

# where plot_targets is a list of Plot_Target
# Only builds them, does not execute plt.show(), so that addtional config may be done
def build_plot(target):
    plt.subplot(3,2, g_plot_index) # Plot indices begin at 1
    plt.plot(target.x_values, target.y_values)
    plt.xlabel(target.x_axis_label)
    plt.ylabel(target.y_axis_label)
    plt.title(target.title)
    
import sys
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: <json file to parse>")

    metrics_dict = parse_json_to_dict(sys.argv[1])

    is_client = metrics_dict["role"] == "client"

    metrics = parse_interval_metrics(metrics_dict)

    # pp.pprint(metrics)
    interval_index = get_single_metric("interval_index", metrics)

    #######################
    # Build the plots 
    #######################
    plt.figure().canvas.set_window_title('General')

    # Plot_Target(title="timestamp", y_values=get_single_metric("timestamp", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="THE_Y"))
    build_plot(Plot_Target(title="avg_cpu_utilization", y_values=get_single_metric("avg_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    g_plot_index += 1
    build_plot(Plot_Target(title="context_switches_per_sec", y_values=get_single_metric("context_switches_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Context Switches/sec"))
    g_plot_index += 1
    build_plot(Plot_Target(title="interrupts_per_sec", y_values=get_single_metric("interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Interrupts/sec"))
    g_plot_index += 1
    build_plot(Plot_Target(title="soft_interrupts_per_sec", y_values=get_single_metric("soft_interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Soft Interrupts/sec"))
    g_plot_index += 1

    # These guys are special, need some extra sauce
    build_plot(Plot_Target(title="bytes_sent_per_sec", y_values=get_single_metric("bytes_sent_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    if is_client:
        x_values = interval_index
        y_values = [metrics_dict["client"]["bytes_per_second"]] * len(interval_index)
        plt.subplot(3,2, g_plot_index) # Plot indices begin at 1
        plt.plot(x_values, y_values)

    g_plot_index += 1

    build_plot(Plot_Target(title="bytes_received_per_sec", y_values=get_single_metric("bytes_received_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    if not is_client:
        x_values = interval_index
        y_values = [metrics_dict["server"]["bytes_per_second"]] * len(interval_index)
        plt.subplot(3,2, g_plot_index) # Plot indices begin at 1
        plt.plot(x_values, y_values)
    g_plot_index += 1

    plt.show()
