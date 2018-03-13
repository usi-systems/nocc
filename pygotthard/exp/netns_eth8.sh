#!/bin/bash
sudo ip netns delete ns_eth8
sudo ip netns add ns_eth8
sudo ip link set eth8 netns ns_eth8
sudo ip netns exec ns_eth8 ip addr add dev eth8 192.168.1.13/24
sudo ip netns exec ns_eth8 ip link set dev eth8 up

# node95 eth0
sudo ip netns exec ns_eth8 arp -s 192.168.1.11 0c:c4:7a:ba:c6:c6
# node95 eth1
sudo ip netns exec ns_eth8 arp -s 192.168.1.12 0c:c4:7a:ba:c6:c7
# node96 eth9
sudo ip netns exec ns_eth8 arp -s 192.168.1.14 0c:c4:7a:a3:25:c8
