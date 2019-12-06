#! /usr/bin/python3
from interval_metric import  Interval_Metric
import matplotlib.pyplot as plt
import json
import pprint
from collections import namedtuple
import numpy as np
import sys

pp = pprint.PrettyPrinter(indent=4)

BYTES_PER_MBYTE = 1024*1024


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
g_plot_nrows = 1 # Don't change this
g_plot_ncols = 2 # Don't change this

# where plot_targets is a list of Plot_Target
# Only builds them, does not execute plt.show(), so that addtional config may be done
def build_plot(target):
    plt.subplot(g_plot_nrows, g_plot_ncols, g_plot_index) # Plot indices begin at 1
    plt.plot(target.x_values, target.y_values)
    plt.xlabel(target.x_axis_label)
    plt.ylabel(target.y_axis_label)
    plt.title(target.title)

def get_single_metric_average(field, metrics):
    return sum(get_single_metric(field, metrics)) / len(get_single_metric(field, metrics))

#             Summary Table
# Will make a new window with just this table. Be sure to display all the other built graphs before this
# (Since this function is going to override the subplot indices, the other graphs would be lost)
#
# Since the math behind client and server summary is different, I'm going to split them apart, and keep the
# common fields in build_summary_table_common
# # 
# Common:
#   Protocol
#   If server or client
#   Avg CPU usage
#   Avg Context switches per sec
#   Avg interrupts per sec
#   Avg soft interrupts per sec
# Specific to role:
#   RTT (If Client)
#   Overhead Percentage
#   Avg Bytes sent per sec (System or iperf, depending on which role this is)
#   Avg Bytes received per sec (System or iperf, depending on which role this is)


# Returns (Row labels, Row Data)
# Doesn't do any matplotlib interaction
def build_summary_table_common_data(metrics_dict, metrics):
    rowLabels = [
        "Protocol",
        "Role",
        "Avg CPU usage",
        "Avg context switches/second",
        "Avg interrupts/second",
        "Avg soft interrupts/second",
        "Avg MB Sent/sec (System)",
        "Avg MB Received/sec (System)",
        "Target Hostname",
    ]

    rowData = [
        metrics_dict["protocol"],
        metrics_dict["role"],
        (int(get_single_metric_average("avg_cpu_utilization", metrics))),
        int(get_single_metric_average("context_switches_per_sec", metrics)),
        int(get_single_metric_average("interrupts_per_sec", metrics)),
        int(get_single_metric_average("soft_interrupts_per_sec", metrics)),
        "{0:.2f} MB/sec".format(get_single_metric_average("bytes_sent_per_sec", metrics) / BYTES_PER_MBYTE),
        "{0:.2f} MB/sec".format(get_single_metric_average("bytes_received_per_sec", metrics) / BYTES_PER_MBYTE),
        metrics_dict["target_hostname"],
    ]

    return (rowLabels, rowData)

# returns [row labels], [row data]
def build_client_summary_data(metrics_dict, metrics):
    common_row_labels, common_row_data  = build_summary_table_common_data(metrics_dict, metrics)

    client_row_labels = [
        "Avg RTT milliseconds",
        "Send Overhead %",
        "Avg MB Sent/sec (Effective)",
    ]


    iperf_avg_sent_bytes_per_sec  = metrics_dict["client"]["bytes_per_second"]
    system_avg_sent_bytes_per_sec = get_single_metric_average("bytes_sent_per_sec", metrics)

    send_overhead_percent = ((system_avg_sent_bytes_per_sec - iperf_avg_sent_bytes_per_sec) / iperf_avg_sent_bytes_per_sec) * 100.0

    # Due to inherent uncertainty in tracking number of bytes handled by the OS, this can be negative for extremely small values
    # so just 0 it so we don't have tiny negative percentages
    send_overhead_percent = send_overhead_percent if send_overhead_percent > 0.0 else 0.0

    client_row_data = [
        round(metrics_dict["client"]["avg_rtt_ms"], 2),
        round(send_overhead_percent, 2),
        round(metrics_dict["client"]["bytes_per_second"] / BYTES_PER_MBYTE, 2),
    ]

    return (common_row_labels+client_row_labels, common_row_data+client_row_data)

def build_client_summary_table(metrics_dict, metrics):
    labels, data = build_client_summary_data(metrics_dict, metrics)

    build_summary_table(labels, data)

def build_server_summary_data(metrics_dict, metrics):
    common_row_labels, common_row_data = build_summary_table_common_data(metrics_dict, metrics)

    server_row_labels = [
        "Receive Overhead %",
        "Avg MB Received/sec (Effective)",
    ]

    iperf_avg_bytes_rcv_per_second = metrics_dict["server"]["bytes_per_second"]
    system_avg_bytes_rcv_per_second = get_single_metric_average("bytes_received_per_sec", metrics)

    # Due to inherent uncertainty in tracking number of bytes handled by the OS, this can be negative for extremely small values
    # so just 0 it so we don't have tiny negative percentages
    received_overhead_percent = ((system_avg_bytes_rcv_per_second - iperf_avg_bytes_rcv_per_second) / iperf_avg_bytes_rcv_per_second) * 100.0
    received_overhead_percent = received_overhead_percent if received_overhead_percent > 0.0 else 0.00

    server_row_data = [
        round(received_overhead_percent, 2),
        round(iperf_avg_bytes_rcv_per_second / BYTES_PER_MBYTE, 2),
    ]

    return (common_row_labels+server_row_labels, common_row_data+server_row_data)

def build_server_summary_table(metrics_dict, metrics):
    labels, data = build_server_summary_data(metrics_dict, metrics)

    build_summary_table(labels, data)


# Generic call used by either client or server
def build_summary_table(rowLabels, rowData):
    axs = plt.subplot(1,1,1) 

    # Table data needs to be a 2d list of strings
    data = [[str(d)] for d in rowData]

    axs.axis('tight')
    axs.axis('off')
    axs.table(cellText=data, rowLabels=rowLabels, loc='center')

    plt.show()

# Intended for use by other scripts
# returns {}
def get_summary(file_path):
    metrics_dict = parse_json_to_dict(file_path)

    is_client = metrics_dict["role"] == "client"
    metrics = parse_interval_metrics(metrics_dict)

    labels = None
    data = None

    if is_client:
        labels, data = build_client_summary_data(metrics_dict, metrics)
    else:
        labels, data = build_server_summary_data(metrics_dict, metrics)

    return dict(zip(labels, data))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: <json file to parse>")

    file_path = sys.argv[1]

    metrics_dict = parse_json_to_dict(file_path)

    is_client = metrics_dict["role"] == "client"
    protocol = metrics_dict["protocol"]

    metrics = parse_interval_metrics(metrics_dict)

    # pp.pprint(metrics)
    interval_index = get_single_metric("interval_index", metrics)

    #######################
    # Build the plots 
    #######################
    plt.figure().canvas.set_window_title('General '+file_path)

    # Plot_Target(title="timestamp", y_values=get_single_metric("timestamp", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="THE_Y"))
    build_plot(Plot_Target(title="per_cpu_utilization", y_values=get_single_metric("per_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    g_plot_index += 1
    build_plot(Plot_Target(title="avg_cpu_utilization", y_values=get_single_metric("avg_cpu_utilization", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Utilization %"))
    g_plot_index += 1
    # build_plot(Plot_Target(title="context_switches_per_sec", y_values=get_single_metric("context_switches_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Context Switches/sec"))
    # g_plot_index += 1
    # build_plot(Plot_Target(title="interrupts_per_sec", y_values=get_single_metric("interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Interrupts/sec"))
    # g_plot_index += 1
    # build_plot(Plot_Target(title="soft_interrupts_per_sec", y_values=get_single_metric("soft_interrupts_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="Soft Interrupts/sec"))
    # g_plot_index += 1

    ################## 
    # Special Cases
    ##################

    # For either client or server, we will plot the relevant iperf metrics on top of the system wide.
    # For these next two, the orange is the avg reported by iperf, and the green is the average of the system wide collection
    # In theory, they should be pretty damn close, with only overhead being the discrepancy
    # build_plot(Plot_Target(title="bytes_sent_per_sec", y_values=get_single_metric("bytes_sent_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    # if is_client:
    #     x_values = interval_index

    #     # Iperf avg
    #     y_values = [metrics_dict["client"]["bytes_per_second"]] * len(interval_index)
    #     plt.subplot(g_plot_nrows, g_plot_ncols, g_plot_index) # Plot indices begin at 1
    #     plt.plot(x_values, y_values)

    #     # System avg
    #     y_values = [sum(get_single_metric("bytes_sent_per_sec", metrics)) / len(get_single_metric("bytes_sent_per_sec", metrics))]*len(interval_index)
    #     plt.subplot(g_plot_nrows, g_plot_ncols, g_plot_index) # Plot indices begin at 1
    #     plt.plot(x_values, y_values)


    # g_plot_index += 1

    # build_plot(Plot_Target(title="bytes_received_per_sec", y_values=get_single_metric("bytes_received_per_sec", metrics), x_values=interval_index, x_axis_label="Interval Index", y_axis_label="bytes/sec"))
    # if not is_client:
    #     x_values = interval_index

    #     # Iperf avg
    #     y_values = [metrics_dict["server"]["bytes_per_second"]] * len(interval_index)
    #     plt.subplot(g_plot_nrows, g_plot_ncols, g_plot_index) # Plot indices begin at 1
    #     plt.plot(x_values, y_values)

    #     # System avg
    #     y_values = [sum(get_single_metric("bytes_received_per_sec", metrics)) / len(interval_index)] * len(interval_index)
    #     plt.subplot(g_plot_nrows, g_plot_ncols, g_plot_index) # Plot indices begin at 1
    #     plt.plot(x_values, y_values)
    # g_plot_index += 1

    plt.show()


    # plt.figure().canvas.set_window_title('Summary '+file_path)
    # if is_client:
    #     build_client_summary_table(metrics_dict, metrics)
    # else:
    #     build_server_summary_table(metrics_dict, metrics)