#! /usr/bin/bash

./results_processor.py ../../results/server/vm_one_core_openvpn_tcp_server.json
mv per_cpu_utilization.png openvpn_one_core_per_cpu.png

./results_processor.py ../../results/server/vm_one_core_wireguard_tcp_server.json
mv per_cpu_utilization.png wireguard_one_core_per_cpu.png

./results_processor.py ../../results/server/vm_two_core_openvpn_tcp_server.json
mv per_cpu_utilization.png openvpn_two_core_per_cpu.png

./results_processor.py ../../results/server/vm_two_core_wireguard_tcp_server.json
mv per_cpu_utilization.png wireguard_two_core_per_cpu.png

