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
import json
import time
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
                    action="store_true", required=False, default=False)
parser.add_argument('--server-delay', help='Delay (ms) between switch and server',
                    type=int, action="store", required=False, default=0)
parser.add_argument('--client-delay', help='Delay (ms) between switch and client',
                    type=int, action="store", required=False, default=0)
parser.add_argument('--client-cmd', help='Command to execute on clients',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--server-cmd', help='Command to start server',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--config', help='JSON client config file',
                    type=str, action="store", required=False, default=False)
parser.add_argument('--entries', help='default table entries (commands.txt) to add to the switch',
                    type=str, action="store", required=False, default='default_commands.txt')

args = parser.parse_args()


class SingleSwitchTopo(Topo):
    "Single switch connected to n (< 256) hosts."
    def __init__(self, sw_path, json_path, thrift_port, pcap_dump, hosts, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        switch = self.addSwitch('s1',
                                sw_path = sw_path,
                                json_path = json_path,
                                thrift_port = thrift_port,
                                pcap_dump = pcap_dump)

        for h in hosts:
            host = self.addHost(h['name'], ip=h['ip']+'/24', mac=h['mac'])
            self.addLink(host, switch, delay="%dms"%h['delay'])


def main():
    if args.config:
        with open(args.config, 'r') as f:
            conf = json.load(f)
        assert('server' in conf and type(conf['server']) is dict)
        assert('cmd' in conf['server'])
        assert('clients' in conf and type(conf['clients']) is list)
    else:
        conf = dict(server=dict(cmd=args.server_cmd),
                    clients=[dict(cmd=args.client_cmd) for _ in xrange(args.num_clients)])

    if not 'switch' in conf: conf['switch'] = dict(disable_cache=args.disable_cache)

    conf['dir'] = os.path.dirname(os.path.abspath(args.config if args.config else './'))
    conf['log_dir'] = os.path.join(conf['dir'], 'logs')
    if not os.path.isdir(conf['log_dir']):
        if os.path.exists(conf['log_dir']): raise Exception('Log dir exists and is not a dir')
        os.mkdir(conf['log_dir'])

    hosts = []
    srv = conf['server']
    server_addr = srv['addr'] if 'addr' in srv else "10.0.0.10"
    server_port = srv['port'] if 'port' in srv else "9999"

    default_think_s = conf['think_s'] if 'think_s' in conf else 0
    default_think_v = conf['think_v'] if 'think_v' in conf else 0
    default_req_count = conf['req_count'] if 'req_count' in conf else 1

    server_log = os.path.join(conf['log_dir'], 'server.log')
    if os.path.exists(server_log): os.remove(server_log)
    hosts.append(dict(
            name = srv['name'] if 'name' in srv else 'h1',
            ip = srv['ip'] if 'ip' in srv else "10.0.0.10",
            sw_addr = srv['sw_addr'] if 'sw_addr' in srv else "10.0.0.1",
            mac = srv['mac'] if 'mac' in srv else '00:04:00:00:00:00',
            sw_mac = srv['sw_mac'] if 'sw_mac' in srv else "00:aa:bb:00:00:00",
            delay = srv['delay'] if 'delay' in srv else args.server_delay,
            cmd = srv['cmd'].replace('%h', server_addr).replace('%p', server_port).replace('%l', server_log)
            ))
    for n, cl in enumerate(conf['clients']):
        assert(type(cl) is dict and 'cmd' in cl)
        h = n + 1
        think_s = cl['think_s'] if 'think_s' in cl else default_think_s
        think_v = cl['think_v'] if 'think_v' in cl else default_think_v
        req_count = cl['req_count'] if 'req_count' in cl else default_req_count
        host = dict(
                name = cl['name'] if 'name' in cl else 'h%d' % (h + 1),
                ip = cl['ip'] if 'ip' in cl else "10.0.%d.10" % h,
                sw_addr = cl['sw_addr'] if 'sw_addr' in cl else "10.0.%d.1" % h,
                mac = cl['mac'] if 'mac' in cl else '00:04:00:00:00:%02x' % h,
                sw_mac = cl['sw_mac'] if 'sw_mac' in cl else "00:aa:bb:00:00:%02x" % h,
                delay = cl['delay'] if 'delay' in cl else args.client_delay)
        host['log'] = os.path.join(conf['log_dir'], '%s.log' % host['name'])
        if os.path.exists(host['log']): os.remove(host['log'])
        host['cmd'] = cl['cmd'].replace('%h', server_addr).replace('%p', server_port).replace('%t', str(think_s)).replace('%v', str(think_v)).replace('%c', str(req_count)).replace('%l', host['log'])
        hosts.append(host)

    topo = SingleSwitchTopo(args.behavioral_exe,
                            args.json,
                            args.thrift_port,
                            args.pcap_dump,
                            hosts)
    net = Mininet(topo = topo,
                  link = TCLink,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None)
    net.start()



    for n, host in enumerate(hosts):
        h = net.get(host['name'])
        if args.mode == "l2":
            h.setDefaultRoute("dev eth0")
        else:
            h.setARP(host['sw_addr'], host['sw_mac'])
            h.setDefaultRoute("dev eth0 via %s" % host['sw_addr'])

    for host in hosts:
        h = net.get(host['name'])
        h.describe()


    sleep(1)

    with open(args.entries, 'r') as f:
        p4_t_entries = f.read()
    if p4_t_entries[-1] != "\n": p4_t_entries += "\n"
    for n, host in enumerate(hosts):
        p4_t_entries += "table_add send_frame rewrite_mac %d => %s\n" % (n+1, host['mac'])
        p4_t_entries += "table_add forward set_dmac %s => %s\n" % (host['ip'], host['mac'])
        p4_t_entries += "table_add ipv4_lpm set_nhop %s/32 => %s %d\n" % (host['ip'], host['ip'], n+1)
    if conf['switch']['disable_cache']:
        p4_t_entries += "table_set_default gotthard_cache_table _no_op\n"
        p4_t_entries += "table_set_default gotthard_res_table _no_op\n"
    print p4_t_entries
    p = subprocess.Popen(['./add_entries_stdin.sh', args.json], stdin=subprocess.PIPE)
    p.communicate(input=p4_t_entries)

    with os.fdopen(os.open(os.path.join(conf['log_dir'], 'summary.txt'), os.O_CREAT | os.O_WRONLY, 0666), 'w') as f:
        cmd_line = ' '.join(['"%s"'%a if ' ' in a else a for a in sys.argv])
        git_rev = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE).communicate()[0].strip()
        f.write("time: %s\n"%time.strftime("%a, %d %b %Y %H:%M:%S %z"))
        f.write("command: %s\n"%cmd_line)
        f.write("git revision: %s\n"%git_rev)
        f.close()

    devnull = open('/dev/null', 'w')

    server = net.get(hosts[0]['name'])
    server_proc = server.popen(hosts[0]['cmd'], stdout=devnull)
    sleep(0.5)

    client_procs = []
    for host in hosts[1:]:
        h = net.get(host['name'])
        print h.name, host['cmd']
        p = h.popen(host['cmd'], stdout=devnull)
        client_procs.append(p)

    if args.cli:
        CLI( net )

    for p in client_procs:
        print p.communicate()
        if p.returncode is None:
            p.wait()
            print p.communicate()
    if server_proc.returncode is None:
        server_proc.send_signal(signal.SIGINT)
        sleep(0.2)
        if server_proc.returncode is None:
            server_proc.kill()

    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
