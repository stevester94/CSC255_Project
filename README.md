# Private server to server tunnel with Ansible, WireGuard, and OpenVPN

Installs [WireGuard](https://wireguard.com) on Ubuntu, creates a mesh between all servers by adding them all as peers and configures the wg-quick systemd service.

## Requirements

Install Ansible

```bash
sudo apt install python3 python3-pip
sudo pip3 install ansible
```

## Configure

### WireGuard Specific

Edit `roles/wireguard_tunnel/defaults/main.yml` to adjust some WireGuard specific options.
Make sure you open the specified port (default is UDP 443) in your Firewall.

### Servers

The Ansible inventory file contains the hosts and their desired VPN IPs.

```yaml
# inventory host file

wireguard:
  hosts:
    ec2_1:
      ansible_host: 1.2.3.4
      ansible_port: 22
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ssh_keys/ec2_1.pem
      vpn_ip: 10.9.0.1/32
    ec2_2:
      ansible_host: 1.2.3.5
      ansible_port: 22
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ssh_keys/ec2_2.pem
      vpn_ip: 10.9.0.2/32

openvpn_servers:
  hosts:
    ec2_1:
      ansible_host: 1.2.3.4
      ansible_port: 22
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ssh_keys/ec2_1.pem

openvpn_clients:
  hosts:
    ec2_2:
      ansible_host: 1.2.3.5
      ansible_port: 22
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ssh_keys/ec2_2.pem
```

## Run

Run the Ansible playbook for WireGuard:

```bash
sh run.sh wireguard
```

Run the Ansible playbook for OpenVPN:

```bash
sh run.sh openvpn
```

## Find IPs - OpenVPN

Servers will have an interface called tun1. To find the server IP run:

```bash
ifconfig tun1 | grep 'inet' | cut -d: -f2 | awk '{print $2}'
```

Clients will have an interface called tun2. To find the client IP run:
```bash
ifconfig tun2 | grep 'inet' | cut -d: -f2 | awk '{print $2}'
```

## TODO

Create task to chmod 600 files in ssh_keys

## Benchmarking
### Generate Metrics (Server-Side)
Requires python3 and psutil
```bash
sudo apt-get install python3-pip
sudo pip3 install psutil
```
To run:
```bash
./metrics.py <duration> <interval for metrics>
```
Will generate a file named results.json (This results file path is hardcoded for now)

### Generate Graphs (Desktop/Laptop)
Requires matplotlib (assuming you have python3 and pip3)
```bash
sudo pip3 install matplotlib
```
parse results.json
```bash
./results_processor.py
```
### Benchmarking TODO
Add pip3 and psutil to ansible playbook
Optional path to results.json
Better graph layout



