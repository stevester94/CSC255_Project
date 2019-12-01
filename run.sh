#!/bin/bash

# Disable host key checking
export ANSIBLE_HOST_KEY_CHECKING=false

# Call the Ansible playbook and inventory file
# with the become option and ask for pass
#ansible-playbook -i inventory vpn.yml -b -K --user=root --ask-pass

# Call the Ansible playbook and inventory file
# with the become option, this will assume a key is used, and sudo don't require pass

if [ -z "$1" ]
  then
    echo "No argument supplied. Please pick between wireguard and openvpn"
  else
    ansible-playbook -i inventory vpn.yml -b --user=root --tags "$1"
fi