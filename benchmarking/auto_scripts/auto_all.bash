./auto_aws_regular.bash
sleep 5

./auto_aws_wireguard.bash
sleep 5

./auto_local_regular.bash
sleep 5

./auto_vm_regular.bash
sleep 5

./auto_vm_wireguard.bash
sleep 5

./run_benchmark.bash
sleep 5

