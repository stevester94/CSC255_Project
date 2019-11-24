#! /usr/bin/python3

import copy
import paramiko
import pprint
import time
import socket

pp = pprint.PrettyPrinter()


TEST_PORT = 9001
TEST_DURATION_SECS = 10
METRICS_INTERVAL_SECS = 1

PROTOCOLS = ["tcp", "udp"]

WIREGUARD_SERVER_IP = "10.9.0.1"
OPENVPN_SERVER_IP   = "10.8.0.1"

REMOTE_RESULTS_BASE_PATH = "/tmp/"

METRICS_BIN_NAME = "metrics.py"
AWS_METRIC_BIN_PATH =  "/home/ubuntu/CSC255_Project/benchmarking/" + METRICS_BIN_NAME
VM_METRIC_BIN_PATH =  "/home/steven/CSC255_Project/benchmarking/" + METRICS_BIN_NAME
LOCAL_METRIC_BIN_PATH =  "/home/steven/School/CSC255/CSC255_Project/benchmarking/" + METRICS_BIN_NAME



CASES = None
ONE_OFF = True


if not ONE_OFF:
    CASES = [
    ################
    # Local Cases
    ################
    {
        "SERVER_SSH_USERNAME" : "steven",
        "CLIENT_SSH_USERNAME" : "steven",
        "SERVER_SSH_IP" : "127.0.0.1",
        "SERVER_TEST_IP" : "127.0.0.1",
        "CLIENT_SSH_IP" : "127.0.0.1",
        "RESULTS_FILE_PREFIX" : "local_regular",
        "NIC_NAME" : "lo",
        "METRICS_BIN_PATH" : LOCAL_METRIC_BIN_PATH,
    },

    ################
    # AWS Cases
    ################
    {
        "SERVER_SSH_USERNAME" : "ubuntu",
        "CLIENT_SSH_USERNAME" : "ubuntu",
        "SERVER_SSH_IP" : "aws_singapore.ssmackey.com",
        "SERVER_TEST_IP" : WIREGUARD_SERVER_IP,
        "CLIENT_SSH_IP" : "aws_oregon.ssmackey.com",
        "RESULTS_FILE_PREFIX" : "aws_wireguard",
        "NIC_NAME" : "eth0",
        "METRICS_BIN_PATH" : AWS_METRIC_BIN_PATH,
    },
    {
        "SERVER_SSH_USERNAME" : "ubuntu",
        "CLIENT_SSH_USERNAME" : "ubuntu",
        "SERVER_SSH_IP" : "aws_singapore.ssmackey.com",
        "SERVER_TEST_IP" : "aws_singapore.ssmackey.com",
        "CLIENT_SSH_IP" : "aws_oregon.ssmackey.com",
        "RESULTS_FILE_PREFIX" : "aws_regular",
        "NIC_NAME" : "eth0",
        "METRICS_BIN_PATH" : AWS_METRIC_BIN_PATH,
    },
    {
        "SERVER_SSH_USERNAME" : "ubuntu",
        "CLIENT_SSH_USERNAME" : "ubuntu",
        "SERVER_SSH_IP" : "aws_singapore.ssmackey.com",
        "SERVER_TEST_IP" : OPENVPN_SERVER_IP,
        "CLIENT_SSH_IP" : "aws_oregon.ssmackey.com",
        "RESULTS_FILE_PREFIX" : "aws_openvpn",
        "NIC_NAME" : "eth0",
        "METRICS_BIN_PATH" : AWS_METRIC_BIN_PATH,
    },

    ################
    # VM Cases
    ################
    {
        "SERVER_SSH_USERNAME" : "steven",
        "CLIENT_SSH_USERNAME" : "steven",
        "SERVER_SSH_IP" : "192.168.86.100",
        "SERVER_TEST_IP" : WIREGUARD_SERVER_IP,
        "CLIENT_SSH_IP" : "192.168.86.200",
        "RESULTS_FILE_PREFIX" : "vm_wireguard",
        "NIC_NAME" : "ens34",
        "METRICS_BIN_PATH" : VM_METRIC_BIN_PATH,
    },
    {
        "SERVER_SSH_USERNAME" : "steven",
        "CLIENT_SSH_USERNAME" : "steven",
        "SERVER_SSH_IP" : "192.168.86.100",
        "SERVER_TEST_IP" : "192.168.86.100",
        "CLIENT_SSH_IP" : "192.168.86.200",
        "RESULTS_FILE_PREFIX" : "vm_regular",
        "NIC_NAME" : "ens34",
        "METRICS_BIN_PATH" : VM_METRIC_BIN_PATH,
    },
    {
        "SERVER_SSH_USERNAME" : "steven",
        "CLIENT_SSH_USERNAME" : "steven",
        "SERVER_SSH_IP" : "192.168.86.100",
        "SERVER_TEST_IP" : OPENVPN_SERVER_IP,
        "CLIENT_SSH_IP" : "192.168.86.200",
        "RESULTS_FILE_PREFIX" : "vm_openvpn",
        "NIC_NAME" : "ens34",
        "METRICS_BIN_PATH" : VM_METRIC_BIN_PATH,
    },
    ]
else:
    TEST_DURATION_SECS = 10
    PROTOCOLS = ["tcp"]
    CASES = [
    {
        "SERVER_SSH_USERNAME" : "ubuntu",
        "CLIENT_SSH_USERNAME" : "ubuntu",
        "SERVER_SSH_IP" : "aws_singapore.ssmackey.com",
        "SERVER_TEST_IP" : "aws_singapore.ssmackey.com",
        "CLIENT_SSH_IP" : "aws_oregon.ssmackey.com",
        "RESULTS_FILE_PREFIX" : "aws_regular",
        "NIC_NAME" : "eth0",
        "METRICS_BIN_PATH" : AWS_METRIC_BIN_PATH,
    },
    ]

def check_command_done(client):
  # use the code below if is_active() returns True
  try:
      transport = client.get_transport()
      transport.send_ignore()
      return False
  except EOFError as e:
      return True

def synch_ssh_command(client, command, silent=True):
    stdin, stdout, stderr = client.exec_command(command)

    # if(not silent):
    #     lines = stdout.readlines()
    #     for line in lines:
    #         print(line)

    return stdout.channel.recv_exit_status()


def asynch_ssh_command(client, command):
    transport = client.get_transport()
    channel = transport.open_session()
    channel.exec_command(command)
    channel.setblocking(0)

    return channel

# Return false if the channel is closed, true if still open
def poll_channel(channel, silent=False):
    recv = None

    try:
        recv = channel.recv(80)
    except socket.timeout as e: return True

    if len(recv) == 0:
        return False
    else:
        if not silent: print(str(recv))
        return True

    


# Add common values to all cases
FINAL_CASES = []
for c in CASES:
    for p in PROTOCOLS:
        new_c = copy.copy(c)
        new_c["PROTOCOL"] = p
        new_c["TEST_PORT"] = TEST_PORT
        new_c["TEST_DURATION_SECS"] = TEST_DURATION_SECS
        new_c["METRICS_INTERVAL_SECS"] = METRICS_INTERVAL_SECS

        new_c["CLIENT_RESULTS_NAME"] = c["RESULTS_FILE_PREFIX"] + "_" + new_c["PROTOCOL"] + "_client.json"
        new_c["SERVER_RESULTS_NAME"] = c["RESULTS_FILE_PREFIX"] + "_" + new_c["PROTOCOL"] + "_server.json"

        new_c["CLIENT_RESULTS_PATH"] = REMOTE_RESULTS_BASE_PATH + new_c["CLIENT_RESULTS_NAME"]
        new_c["SERVER_RESULTS_PATH"] = REMOTE_RESULTS_BASE_PATH + new_c["SERVER_RESULTS_NAME"]

        FINAL_CASES.append(new_c)


print("Have {} cases".format(len(FINAL_CASES)))
for case in FINAL_CASES:
    pp.pprint(case)

    

    server_client = paramiko.SSHClient()
    server_client.load_system_host_keys()
    server_client.connect(case["SERVER_SSH_IP"], username=case["SERVER_SSH_USERNAME"], timeout=5)

    client_client = paramiko.SSHClient()
    client_client.load_system_host_keys()
    client_client.connect(case["CLIENT_SSH_IP"], username=case["CLIENT_SSH_USERNAME"], timeout=5)

    # remove any pre-exisitng results
    rm_ret = synch_ssh_command(server_client, "rm {}".format(case["SERVER_RESULTS_PATH"]))
    if rm_ret != 0:
        print("Server failed to remove previous results, this is fine")
    else:
        print("Removed previous results")
    rm_ret = synch_ssh_command(client_client, "rm {}".format(case["CLIENT_RESULTS_PATH"]))
    if rm_ret != 0:
        print("Client failed to remove previous results, this is fine")
    else:
        print("Removed previous results")
    

    print("All ready, executing tests...")
    server_command = "{METRICS_BIN_PATH} server {PROTOCOL} {SERVER_TEST_IP} {TEST_PORT} {TEST_DURATION_SECS} {METRICS_INTERVAL_SECS} {SERVER_RESULTS_PATH} {NIC_NAME}".format(**case)
    print("Server is executing: " + server_command)
    server_channel = asynch_ssh_command(server_client, server_command)
        

    # We wait just a smidgen for the server to come alive
    time.sleep(1)
    client_command = "{METRICS_BIN_PATH} client {PROTOCOL} {SERVER_TEST_IP} {TEST_PORT} {TEST_DURATION_SECS} {METRICS_INTERVAL_SECS} {CLIENT_RESULTS_PATH} {NIC_NAME}".format(**case)
    print("Client is executing: " + client_command)
    client_channel = asynch_ssh_command(client_client, client_command)
        
    
    test_done = False
    while not test_done:
        # time.sleep(1)
        server_still_working = poll_channel(server_channel)
        # if not server_still_working: print("Server is done")

        client_still_working = poll_channel(client_channel)
        # if not client_still_working: print("Client is done")

        test_done = (not server_still_working) and (not client_still_working)


    print("Fetching client results")
    client_client_sftp=client_client.open_sftp()
    client_client_sftp.get(case["CLIENT_RESULTS_PATH"], case["CLIENT_RESULTS_NAME"])

    print("Fetching server results")
    server_client_sftp=server_client.open_sftp()
    server_client_sftp.get(case["SERVER_RESULTS_PATH"], case["SERVER_RESULTS_NAME"])

    print("Done with case")
    server_client.close()
    client_client.close()

print("All done")
print("Completed {} cases, should have {} results files", len(FINAL_CASES), len(FINAL_CASES)*2)

# SERVER_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME server $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $SERVER_RESULTS_OUT_PATH $NIC_NAME"
# CLIENT_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME client $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $CLIENT_RESULTS_OUT_PATH $NIC_NAME"

# SERVER_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME server $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $SERVER_RESULTS_OUT_PATH $NIC_NAME"
# CLIENT_COMMAND="$BENCHMARK_ROOT_DIR$BINARY_NAME client $PROTOCOL $SERVER_TEST_IP $PORT $DURATION $INTERVAL $CLIENT_RESULTS_OUT_PATH $NIC_NAME"

