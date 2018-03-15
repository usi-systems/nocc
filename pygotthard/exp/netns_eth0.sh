#!/bin/bash
sudo ip netns delete ns_eth0
sudo ip netns add ns_eth0
sudo ip link set eth0 netns ns_eth0
sudo ip netns exec ns_eth0 ip addr add dev eth0 192.168.1.11/24
sudo ip netns exec ns_eth0 ip link set dev eth0 up

#sudo ip netns exec ns_eth0 arp -s 192.168.1.11 0c:c4:7a:ba:c6:c6
sudo ip netns exec ns_eth0 arp -s 192.168.1.12 0c:c4:7a:ba:c6:c7
sudo ip netns exec ns_eth0 arp -s 192.168.1.13 0c:c4:7a:a3:25:c9
sudo ip netns exec ns_eth0 arp -s 192.168.1.14 0c:c4:7a:a3:25:c8
