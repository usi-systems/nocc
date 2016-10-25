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
import argparse
from sourcer import sourceFile

env_vars = sourceFile('./env.sh')
sys.path.append(os.path.join(env_vars['BMV2_PATH'], 'mininet'))

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI

from p4_mininet import P4Switch, P4Host

sys.path.append('..')
from pygotthard import GOTTHARD_MAX_OP
from time import sleep
from util import waitForTcpPort

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument('--behavioral-exe', help='Path to behavioral executable',
                    type=str, action="store", required=True)
parser.add_argument('--thrift-port', help='Thrift server port for table updates',
                    type=int, action="store", default=9090)
parser.add_argument('--num-clients', help='Number of hosts to connect to switch',
                    type=int, action="store", default=2)
parser.add_argument('--lmode', choices=['l2', 'l3'], type=str, default='l3')
parser.add_argument('--cli', help="start the mininet cli",
                    action="store_true", required=False, default=False)
parser.add_argument("--mode", "-m", choices=['forward', 'early_abort', 'optimistic_abort'], type=str, default="early_abort")
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


class MultiSwitchTopo(Topo):
    "Single switch connected to n (< 256) hosts."
    def __init__(self, sw_path, json_path, thrift_port, pcap_dump, switches, clients, store, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)


        switch_a = self.addSwitch('s1',
                                sw_path = sw_path,
                                json_path = json_path,
                                thrift_port = thrift_port,
                                pcap_dump = pcap_dump)

        store_host = self.addHost(store['name'])#, ip=store['addr']+'/24', mac=store['mac'])
        self.addLink(store_host, switch_a, delay='1ms', addr1=store['mac'], intfName1='eth0')

        sw_objects = {}
        sorted_switches = sorted(switches.items(), key=lambda t: t[1]['sw_a_port'])
        for sw_name, switch_conf in sorted_switches:
            sw_objects[sw_name] = self.addSwitch(sw_name,
                                sw_path = sw_path,
                                json_path = json_path,
                                thrift_port = thrift_port+switch_conf['port_offset'],
                                pcap_dump = pcap_dump)
            self.addLink(sw_objects[sw_name], switch_a, delay="%dms"%store['delay'])

        for cl in clients:
            host = self.addHost(cl['name'])#, ip=cl['links'][0]['cl_addr'], mac=cl['links'][0]['cl_mac'])
            for l in cl['links']:
                b_switch = sw_objects[l['sw_name']]
                self.addLink(host, b_switch, delay="%dms"%l['delay'],
                        addr1=l['cl_mac'], addr2=l['sw_mac'],
                        intfName1='eth%d'%l['iface'])


def fmtStr(tmpl, params):
    return reduce(lambda s, p: s.replace('%'+p[0]+'%', str(p[1])), params.items(), tmpl)

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

    if not 'switch' in conf: conf['switch'] = dict(mode=args.mode)
    if not 'sequential_clients' in conf: conf['sequential_clients'] = False

    conf['dir'] = os.path.dirname(os.path.abspath(args.config if args.config else './'))
    conf['log_dir'] = os.path.join(conf['dir'], 'logs')
    if not os.path.isdir(conf['log_dir']):
        if os.path.exists(conf['log_dir']): raise Exception('Log dir exists and is not a dir')
        os.mkdir(conf['log_dir'])

    hosts = []
    srv = conf['server']

    params = dict(conf['parameters'].items() if 'parameters' in conf else [])

    server_addr = srv['addr'] if 'addr' in srv else "10.0.0.10"
    server_port = srv['port'] if 'port' in srv else "9999"


    server_log = os.path.join(conf['log_dir'], 'server.log')
    if os.path.exists(server_log): os.remove(server_log)
    store = dict(
            name = 'store',
            addr = "10.0.0.10",
            sw_addr = "10.0.0.1",
            mac = '00:dd:aa:00:00:01',
            sw_mac = "00:aa:dd:00:00:01",
            delay = srv['delay'] if 'delay' in srv else args.server_delay,
            cmd = fmtStr(srv['cmd'].replace('%h', server_addr).replace('%p', server_port).replace('%l', server_log), params)
            )
    hosts.append(store)

    switches = {}
    clients = []
    for n, cl in enumerate(conf['clients']):
        assert(type(cl) is dict and 'cmd' in cl)
        h = n + 1
        host = dict(
                name = cl['name'] if 'name' in cl else 'h%d' % (h + 1),
                links = []
                )
        if 'stdout_log' in cl and cl['stdout_log']:
            host['stdout_log'] = os.path.join(conf['log_dir'], '%s.stdout.log' % host['name'])
        host['log'] = os.path.join(conf['log_dir'], '%s.log' % host['name'])
        if os.path.exists(host['log']): os.remove(host['log'])
        host['cmd'] = cl['cmd'].replace('%h', server_addr).replace('%p', server_port).replace('%e', conf['dir']).replace('%l', host['log'])
        host['cmd'] = fmtStr(host['cmd'], params)

        if 'switch' in cl:
            cl_switch_names = cl['switch'] if type(cl['switch']) is list else [cl['switch']]
        else: cl_switch_names = ['s2']

        for i, sw_name in enumerate(cl_switch_names):
            if sw_name not in switches:
                switches[sw_name] = dict(subnet=len(switches)+1,
                                         mac="00:bb:aa:00:00:%02x" % (len(switches)+1),
                                         t_entries=[],
                                         sw_a_port=len(switches)+2,
                                         port_offset=len(switches)+1,
                                         links=[],
                                         clients=[])
            switch = switches[sw_name]
            switch_link = dict(
                iface=i,
                sw_name = sw_name,
                cl_addr = cl['addr'] if 'addr' in cl else "10.%d.%d.10" % (switch['subnet'], h),
                cl_mac = cl['mac'] if 'mac' in cl else '00:cc:bb:00:%02x:%02x' % (switch['subnet'], h),
                sw_port = len(switch['clients'])+2,
                sw_addr = "10.%d.%d.1" % (switch['subnet'], h),
                sw_mac = "00:bb:cc:00:%02x:%02x" % (switch['subnet'], h),
                store_addr = "10.0.0.%d" % (10 + i),
                delay = cl['delay'] if 'delay' in cl else args.client_delay,
                )
            switch['links'].append(switch_link)
            host['links'].append(switch_link)
            switch['clients'].append(host)

        hosts.append(host)
        clients.append(host)

    topo = MultiSwitchTopo(args.behavioral_exe,
                            args.json,
                            args.thrift_port,
                            args.pcap_dump,
                            switches,
                            clients,
                            store)
    net = Mininet(topo = topo,
                  link = TCLink,
                  host = P4Host,
                  switch = P4Switch,
                  controller = None)
    net.start()

    store_obj = net.get(store['name'])
    store_obj.setARP(store['sw_addr'], store['sw_mac'])

    store_addresses = set([l['store_addr'] for cl in clients for l in cl['links']])
    for i, addr in enumerate(store_addresses):
        store_obj.cmd('ip address add %s/24 dev eth0' % (addr))

    for n, host in enumerate(clients):
        h = net.get(host['name'])
        if args.lmode == "l2":
            h.setDefaultRoute("dev eth0")
        else:
            for link in host['links']:
                h.setIP(link['cl_addr'], intf='eth%d'%link['iface'])
                store_obj.cmd('ip route add %s via %s dev eth0 src %s' % (link['cl_addr'], store['sw_addr'], link['store_addr']))
                h.cmd('ip route add %s via %s dev eth%d src %s' % (link['store_addr'], link['sw_addr'], link['iface'], link['cl_addr']))
                h.cmd('ip route add %s via %s' % (link['store_addr'], link['sw_addr']))
                h.cmd('ip route add %s dev eth%d src %s' % (link['sw_addr'], link['iface'], link['cl_addr']))
                # to fix checksum bug: https://github.com/mininet/mininet/issues/653
                h.cmd('ethtool -K eth%d tx off' % link['iface'])
                h.setARP(link['sw_addr'], link['sw_mac'])

    for host in hosts:
        h = net.get(host['name'])
        h.describe()


    for p in xrange(args.thrift_port, args.thrift_port+len(switches)+1):
        waitForTcpPort(p, timeout=120) # wait for P4 switch to start thrift server
    sleep(0.3)

    def add_entries(entries, port):
        print '\n'.join(entries)
        p = subprocess.Popen(['./add_entries_stdin.sh', args.json, str(port)], stdin=subprocess.PIPE)
        p.communicate(input='\n'.join(entries))

    with open(args.entries, 'r') as f:
        all_t_entries = [l.rstrip() for l in f.readlines() if l != '\n']

    max_op_cnt = GOTTHARD_MAX_OP
    if conf['switch']['mode'] != 'forward': # i.e. both early/opti abort
        read_cache_enabled = 1 if conf['switch']['mode'] == 'read_cache' else 0
        opti_enabled = 1 if conf['switch']['mode'] == 'optimistic_abort' else 0
        for i in xrange(max_op_cnt):
            all_t_entries.append("table_add t_store_update do_store_update%d %d => %d"%(i,i+1,opti_enabled))
            all_t_entries.append("table_add t_req_pass1 do_check_op%d %d => %d"%(i,i+1,read_cache_enabled))
            all_t_entries.append("table_add t_req_fix do_req_fix%d %d =>"%(i,i+1))

    if conf['switch']['mode'] == 'optimistic_abort':
        for i in xrange(max_op_cnt):
            all_t_entries.append("table_add t_opti_update do_opti_update%d %d =>"%(i,i+1))

    switch_a_entries = [e for e in all_t_entries]
    switch_a_entries.append("table_add send_frame rewrite_mac 1 => %s" % store['sw_mac'])
    def insert(entries, entry):
        if entry not in entries: entries.append(entry)

    n = 0
    for switch_name, switch in switches.items():
        n += 1
        switch_entries = [e for e in all_t_entries]
        insert(switch_entries, "table_add send_frame rewrite_mac 1 => %s" % switch['mac'])
        insert(switch_a_entries, "table_add send_frame rewrite_mac %d => aa:bb:00:00:00:01" % switch['sw_a_port'])
        for link in switch['links']:
            # cl -> (switchB) -> switchA -> st
            insert(switch_entries, "table_add ipv4_lpm set_nhop %s/32 => %s 1" % (link['store_addr'], link['store_addr']))
            insert(switch_entries, "table_add forward set_dmac %s => %s" % (link['store_addr'], store['mac']))

            # cl -> switchB -> (switchA) -> st
            insert(switch_a_entries, "table_add ipv4_lpm set_nhop %s/32 => %s 1" % (link['store_addr'], link['store_addr']))
            insert(switch_a_entries, "table_add forward set_dmac %s => %s" % (link['store_addr'], store['mac']))

            # cl <- switchB <- (switchA) <- st
            insert(switch_a_entries, "table_add ipv4_lpm set_nhop %s/32 => %s %d" % (link['cl_addr'], link['cl_addr'], switch['sw_a_port']))
            insert(switch_a_entries, "table_add forward set_dmac %s => %s" % (link['cl_addr'], link['cl_mac']))

            # cl <- (switchB) <- switchA <- st
            insert(switch_entries, "table_add ipv4_lpm set_nhop %s/32 => %s %d" % (link['cl_addr'], link['cl_addr'], link['sw_port']))
            insert(switch_entries, "table_add forward set_dmac %s => %s" % (link['cl_addr'], link['cl_mac']))
            insert(switch_entries, "table_add send_frame rewrite_mac %d => %s" % (link['sw_port'], link['sw_mac']))

        add_entries(switch_entries, args.thrift_port+switch['port_offset'])

    add_entries(switch_a_entries, args.thrift_port)


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


    return_codes = []
    def _wait_for_client(p, host):
        print p.communicate()
        if p.returncode is None:
            p.wait()
            print p.communicate()
        return_codes.append(p.returncode)
        if 'stdoutfile' in host:
            host['stdoutfile'].flush()
            host['stdoutfile'].close()

    if args.cli:
        CLI( net )

    client_procs = []
    for host in hosts[1:]:
        h = net.get(host['name'])
        print h.name, host['cmd']
        pipe_stdout_to = devnull
        if 'stdout_log' in host:
            host['stdoutfile'] = open(host['stdout_log'], 'w')
            pipe_stdout_to = host['stdoutfile']
        p = h.popen(host['cmd'], stdout=pipe_stdout_to)
        if conf['sequential_clients']: _wait_for_client(p, host)
        client_procs.append((p, host))

    if args.cli:
        CLI( net )

    if not conf['sequential_clients']:
        for p, host in client_procs: _wait_for_client(p, host)

    if server_proc.returncode is None:
        server_proc.send_signal(signal.SIGINT)
        sleep(0.2)
        if server_proc.returncode is None:
            server_proc.kill()
        print server_proc.communicate()
        return_codes.append(server_proc.returncode)

    net.stop()

    bad_codes = [rc for rc in return_codes if rc != 0]
    with os.fdopen(os.open(os.path.join(conf['log_dir'], 'done.txt'), os.O_CREAT | os.O_WRONLY, 0666), 'w') as f:
        cmd_line = ' '.join(['"%s"'%a if ' ' in a else a for a in sys.argv])
        f.write("time: %s\n\n"%time.strftime("%a, %d %b %Y %H:%M:%S %z"))
        f.write("Error: %s\n"% ('true' if len(bad_codes) else 'false'))
        f.close()
    if len(bad_codes) > 0: sys.exit(1)

if __name__ == '__main__':
    setLogLevel( 'info' )
    main()
