#! /usr/bin/python3
from interval_metric import  Interval_Metric
import matplotlib.pyplot as plt
import json
import pprint
from collections import namedtuple

pp = pprint.PrettyPrinter(indent=4)


def parse_json_to_interval_metrics(path):
    metrics = []
    with open(path, "r") as f:
        j = json.load(f)

        for metric in j:
            m = Interval_Metric(**metric)
            metrics.append(m)
    
    return metrics

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

# where plot_targets is a list of Plot_Target
# Only builds them, does not execute plt.show(), so that addtional config may be done
def build_plots(plot_targets):
    for index, target in enumerate(plot_targets):
        plt.subplot(3,2, index+1) # Plot indices begin at 1
        plt.plot(target.x_values, target.y_values)
        plt.xlabel(target.x_axis_label)
        plt.ylabel(target.y_axis_label)
        plt.title(target.title)
    

if __name__ == "__main__":
    metrics = parse_json_to_interval_metrics("results.json")

    # pp.pprint(metrics)
    interval_index = get_single_metric("interval_index", metrics)

    targets = []
    # targets.append(Plot_Target(title="timestamp", y_values=get_single_metric("timestamp", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="THE_Y"))
    targets.append(Plot_Target(title="avg_cpu_utilization", y_values=get_single_metric("avg_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    # targets.append(Plot_Target(title="bytes_sent_since_system_start", y_values=get_single_metric("bytes_sent_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes"))
    # targets.append(Plot_Target(title="bytes_received_since_system_start", y_values=get_single_metric("bytes_received_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes"))
    targets.append(Plot_Target(title="bytes_sent_per_sec", y_values=get_single_metric("bytes_sent_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    targets.append(Plot_Target(title="bytes_received_per_sec", y_values=get_single_metric("bytes_received_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    # targets.append(Plot_Target(title="context_switches_since_system_start", y_values=get_single_metric("context_switches_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Context Switches"))
    # targets.append(Plot_Target(title="interrupts_since_system_start", y_values=get_single_metric("interrupts_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Interrupts"))
    # targets.append(Plot_Target(title="soft_interrupts_since_system_start", y_values=get_single_metric("soft_interrupts_since_system_start", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Soft Interrupts"))
    targets.append(Plot_Target(title="context_switches_per_sec", y_values=get_single_metric("context_switches_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Context Switches/sec"))
    targets.append(Plot_Target(title="interrupts_per_sec", y_values=get_single_metric("interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Interrupts/sec"))
    targets.append(Plot_Target(title="soft_interrupts_per_sec", y_values=get_single_metric("soft_interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Soft Interrupts/sec"))

    plt.figure().canvas.set_window_title('General') # These get their own window
    build_plots(targets)

    # These guys are special, need some extra sauce
    # plt.figure().canvas.set_window_title('Special')

    # targets = []
    # targets.append(Plot_Target(title="per_cpu_utilization", y_values=get_single_metric("per_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    # targets.append(Plot_Target(title="cpu_times_percent", y_values=get_single_metric("cpu_times_percent", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Time %"))
    # build_plots(targets)

    
    plt.show()


    # plt.plot(interval_index, avg_cpu_utilization)
    # plt.show()


# plt.subplot(2, 2, 1)
# plt.plot(range(0,10), range(0,10))
# plt.subplot(2, 2, 2)
# plt.plot(range(0,20), range(0,20))

# plt.show()
