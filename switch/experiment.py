#!/usr/bin/env python2

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import subprocess
import signal
import os
import sys
from sourcer import sourceFile

env_vars = sourceFile('./env.sh')
sys.path.append(os.path.join(env_vars['BMV2_PATH'], 'mininet'))

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from p4_mininet import P4Switch, P4Host

import argparse
from time import sleep

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", default=9090)
parser.add_argument('--num-clients', help='Number of hosts to connect to switch',
                    type=int, action="store", default=2)
parser.add_argument('--mode', choices=['l2', 'l3'], type=str, default='l3')
parser.add_argument('--cli', help="start the mininet cli",
                    action="store_true", required=False, default=False)
parser.add_argument('--disable-cache', help="disable the switch cach",
                    action="store_true", required=False, default=False)
parser.add_argument('--json', help='Path to JSON config file',
                    type=str, action="store", required=True)
parser.add_argument('--pcap-dump', help='Dump packets on interfaces to pcap files',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--store-delay', help='Delay (ms) between switch and store',
                    type=int, action="store", required=False, default=0)
parser.add_argument('--client-delay', help='Delay (ms) between switch and client',
                    type=int, action="store", required=False, default=0)
parser.add_argument('--client-cmd', help='Command to execute on clients',
                    type=str, action="store", required=True, default=False)
parser.add_argument('--store-cmd', help='Command to start store',
                    type=str, action="store", required=True, default=False)

args = parser.parse_args()


class SingleSwitchTopo(Topo):
    "Single switch connected to n (< 256) hosts."
    def __init__(self, sw_path, json_path, thrift_port, pcap_dump, n, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        switch = self.addSwitch('s1',
                                sw_path = sw_path,
                                json_path = json_path,
                                thrift_port = thrift_port,
                                pcap_dump = pcap_dump)

        for h in xrange(n):
            host = self.addHost('h%d' % (h + 1),
                                ip = "10.0.%d.10/24" % h,
                                mac = '00:04:00:00:00:%02x' %h)
            delay = args.store_delay if n==0 else args.client_delay
            self.addLink(host, switch, delay="%dms"%delay)

def main():
    num_hosts = args.num_clients + 1
    mode = args.mode

    topo = SingleSwitchTopo(args.behavioral_exe,
                            args.json,
                            args.thrift_port,
                            args.pcap_dump,
                            num_hosts)
    net = Mininet(topo = topo,
                  link = TCLink,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None)
    net.start()


    sw_mac = ["00:aa:bb:00:00:%02x" % n for n in xrange(num_hosts)]

    sw_addr = ["10.0.%d.1" % n for n in xrange(num_hosts)]

    store_addr, store_port = "10.0.0.10", "9999"

    for n in xrange(num_hosts):
        h = net.get('h%d' % (n + 1))
        if mode == "l2":
            h.setDefaultRoute("dev eth0")
        else:
            h.setARP(sw_addr[n], sw_mac[n])
            h.setDefaultRoute("dev eth0 via %s" % sw_addr[n])

    for n in xrange(num_hosts):
        h = net.get('h%d' % (n + 1))
        h.describe()


    sleep(1)

    with open('./commands.txt', 'r') as f:
        p4_commands = f.read()
    if p4_commands[-1] != "\n": p4_commands += "\n"
    for n in xrange(num_hosts + 1):
        p4_commands += "table_add send_frame rewrite_mac %d => 00:aa:bb:00:00:%02x\n" % (n+1, n)
        p4_commands += "table_add forward set_dmac 10.0.%d.10 => 00:04:00:00:00:%02x\n" % (n, n)
        p4_commands += "table_add ipv4_lpm set_nhop 10.0.%d.10/32 => 10.0.%d.10 %d\n" % (n, n, n+1)
    if args.disable_cache:
        p4_commands += "table_set_default gotthard_cache_table _no_op\n"
    p = subprocess.Popen(['./add_entries_stdin.sh'], stdin=subprocess.PIPE)
    p.communicate(input=p4_commands)

    store = net.get('h1')
    store_proc = store.popen(args.store_cmd.replace('%p', store_port))
    sleep(0.5)

    client_procs = []
    for n in xrange(1, num_hosts):
        h = net.get('h%d' % (n + 1))
        command = args.client_cmd.replace('%h', store_addr).replace('%p', store_port)
        print h.name, command
        p = h.popen(command)
        client_procs.append(p)

    if args.cli:
        CLI( net )

    for p in client_procs:
        print p.communicate()
        if p.returncode is None:
            p.wait()
            print p.communicate()
    if store_proc.returncode is None:
        store_proc.send_signal(signal.SIGINT)
        sleep(0.2)
        if store_proc.returncode is None:
            store_proc.kill()

    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
