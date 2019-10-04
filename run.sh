#!/bin/bash

# Disable host key checking
export ANSIBLE_HOST_KEY_CHECKING=false

# Call the WireGuard Ansible playbook and inventory file
# with the become option and ask for pass
#ansible-playbook -i inventory wireguard.yml -b -K --user=root --ask-pass

# Call the WireGuard Ansible playbook and inventory file
# with the become option, this will assume a key is used, and sudo don't require pass
ansible-playbook -i inventory wireguard.yml -b --user=root