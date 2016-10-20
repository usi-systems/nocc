#!/usr/bin/env python
import subprocess
import shutil
from os import path
import time
import json
import itertools

BINDIR='/home/pacheco/workspace/gotthard/pygotthard/'
LOGDIR='/home/pacheco/workspace/gotthard/ec2/3S_LOGS/'
STORE_PORT=9994
SWITCH1_PORT=9995
SWITCH2_PORT=9996
SWITCH0_PORT=9997

# COMBINATIONS=[
#     {
#         'rw': [0.05, 0.1, 0.2],
#         'ctotal': [4],
#         'clocal': [4, 3, 2],
#         'mode': ['forward', 'read_cache', 'optimistic_abort'],
#     },
#     {
#         'rw': [0.05, 0.1, 0.2],
#         'ctotal': [8],
#         'clocal': [8, 6, 4],
#         'mode': ['forward', 'read_cache', 'optimistic_abort'],
#     },
#     {
#         'rw': [0.05, 0.1, 0.2],
#         'ctotal': [16],
#         'clocal': [16, 12, 8],
#         'mode': ['forward', 'read_cache', 'optimistic_abort'],
#     },
# ]


COMBINATIONS=[
    {
        'rw': [0.05, 0.1, 0.2],
        'ctotal': [8],
        'clocal': [7, 5],
        'mode': ['forward', 'read_cache', 'optimistic_abort'],
    },
    {
        'rw': [0.05, 0.1, 0.2],
        'ctotal': [16],
        'clocal': [15,14,10],
        'mode': ['forward', 'read_cache', 'optimistic_abort'],
    },
]


PARAMS={
    'transactions': 'A(%(key)s,%(key)s) W(%(key)s,%(key)s+1) | R(%(key)s)',
    'think': 0.005,
    'think_var': 0.1,
    'duration': 30,
    'delta': 0.2,
    'latency': 0.05,
}


def exps_from_combinations():
    exps = set()
    for c in COMBINATIONS:
        for rw in c['rw']:
            for ctotal in c['ctotal']:
                for clocal in c['clocal']:
                    for mode in c['mode']:
                        exps.add((rw,ctotal,clocal,mode))
    return [{'rw': exp[0], 'ctotal': exp[1], 'clocal': exp[2], 'mode': exp[3]} for exp in exps]


def run_switch(port, store_host, store_port, mode, client_delta=None, server_delta=None):
    cmd = [BINDIR + 'software_switch.py']
    if client_delta:
        cmd += ['--client-delta', str(client_delta)]
    if server_delta:
        cmd += ['--server-delta', str(server_delta)]
    cmd += ['-p', str(port)]
    cmd += ['--mode', mode]
    cmd += [store_host, str(store_port)]
    print cmd
    return subprocess.Popen(cmd)


def run_store(port):
    cmd = [
        BINDIR + 'store.py',
        '-p %d' % (STORE_PORT),
        '-l' + LOGDIR + 'store.log',
        #'-v2',
    ]
    print cmd
    return subprocess.Popen(cmd)


if __name__ == '__main__':
    subprocess.call(['mkdir', '-p', LOGDIR])
    print PARAMS
    with open(LOGDIR + 'params.json', 'w') as f:
        json.dump(PARAMS, f)
    count = 0
    exps = exps_from_combinations()
    for exp in exps:
        print "-------------------------------- "
        print "DONE %s/%s" % (count, len(exps))
        print "Around %s secs to finish..." % ((len(exps) - count) * PARAMS['duration'])
        print "-------------------------------- "
        count+=1
        print exp
        allprocs = []
        locality = exp['clocal'] / float(exp['ctotal'])
        allprocs.append(run_store(STORE_PORT))

        allprocs.append(run_switch(SWITCH0_PORT,
                                   '127.0.0.1', STORE_PORT,
                                   exp['mode'],
                                   server_delta=0.001))

        allprocs.append(run_switch(SWITCH1_PORT,
                                   '127.0.0.1', SWITCH0_PORT,
                                   exp['mode'],
                                   server_delta=PARAMS['latency'] * (1-PARAMS['delta']),
                                   client_delta=PARAMS['latency'] * PARAMS['delta']))

        allprocs.append(run_switch(SWITCH2_PORT,
                                   '127.0.0.1', SWITCH0_PORT,
                                   exp['mode'],
                                   server_delta=PARAMS['latency'] * (1-PARAMS['delta']),
                                   client_delta=PARAMS['latency'] * PARAMS['delta']))

        time.sleep(1)
        try:
            CLIENT_LOG=LOGDIR + '%.3frw_%sctotal_%.3fl_%s' % (exp['rw'], exp['ctotal'], locality, exp['mode'])
            CLIENT_LOG+='_sw%s_%s.raw'
            # client 1 ----------------------------------------
            client_cmd = [
                BINDIR + 'load_generator.py',
                '-n', str(exp['clocal']),
                '-d', str(PARAMS['duration']),
                '--transactions', PARAMS['transactions'] % {'key':'x'},
                '-p', str(exp['rw']),
                '--id', '0',
                '-r', '0.5',
                '--think', str(PARAMS['think']),
                '--think-var', str(PARAMS['think_var']),
                '--log', CLIENT_LOG % (1, 'loc'),
                '127.0.0.1', str(SWITCH1_PORT),
            ]
            print client_cmd
            client1_local = subprocess.Popen(client_cmd)
            allprocs.append(client1_local)
            client_cmd = [
                BINDIR + 'load_generator.py',
                '-n', str(exp['ctotal'] - exp['clocal']),
                '-d', str(PARAMS['duration']),
                '--transactions', PARAMS['transactions'] % {'key':'y'},
                '-p', str(exp['rw']),
                '--id', '100',
                '-r', '0.5',
                '--think', str(PARAMS['think']),
                '--think-var', str(PARAMS['think_var']),
                '--log', CLIENT_LOG % (1, 'rem'),
                '127.0.0.1', str(SWITCH1_PORT),
            ]
            print client_cmd
            client1_remote = subprocess.Popen(client_cmd)
            allprocs.append(client1_remote)
            # client 2 ----------------------------------------
            client_cmd = [
                BINDIR + 'load_generator.py',
                '-n', str(exp['clocal']),
                '-d', str(PARAMS['duration']),
                '--transactions', PARAMS['transactions'] % {'key':'y'},
                '-p', str(exp['rw']),
                '--id', '200',
                '-r', '0.5',
                '--think', str(PARAMS['think']),
                '--think-var', str(PARAMS['think_var']),
                '--log', CLIENT_LOG % (2, 'loc'),
                '127.0.0.1', str(SWITCH2_PORT),
            ]
            print client_cmd
            client2_local = subprocess.Popen(client_cmd)
            allprocs.append(client2_local)
            client_cmd = [
                BINDIR + 'load_generator.py',
                '-n', str(exp['ctotal'] - exp['clocal']),
                '-d', str(PARAMS['duration']),
                '--transactions', PARAMS['transactions'] % {'key':'x'},
                '-p', str(exp['rw']),
                '--id', '300',
                '-r', '0.5',
                '--think', str(PARAMS['think']),
                '--think-var', str(PARAMS['think_var']),
                '--log', CLIENT_LOG % (2, 'rem'),
                '127.0.0.1', str(SWITCH2_PORT),
            ]
            print client_cmd
            client2_remote = subprocess.Popen(client_cmd)
            allprocs.append(client2_remote)

            client1_local.wait()
            client1_remote.wait()
            client2_local.wait()
            client2_remote.wait()
            allprocs.remove(client1_local)
            allprocs.remove(client1_remote)
            allprocs.remove(client2_local)
            allprocs.remove(client2_remote)
        finally:
            for proc in allprocs:
                proc.kill()
