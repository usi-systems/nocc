#!/usr/bin/env python
from subprocess import Popen
import time
import json

BINDIR='/home/pacheco/workspace/gotthard/pygotthard/'
LOGDIR='/home/pacheco/workspace/gotthard/LOGS/'
STORE_PORT=9990
SWITCH_PORT=9991

RW_VALUES=[1, 0.99, 0.9, 0.8, 0.5, 0.2]
CLIENT_VALUES=[1, 2, 4, 8, 16, 32, 64]

PARAMS={
    'client_delta': 0.01,
    'server_delta': 0.04,
    'transactions': 'R(X) | A(X,X) W(X,X+1)',
    'think': 0.001,
    'think_var': 0.05,
    'duration': 20,
    'mode': 'forward', # 'forward', 'read_cache', 'early_abort', 'optimistic_abort'
}

if __name__ == '__main__':
    store_cmd = [
        BINDIR + 'store.py',
        '-p %d' % (STORE_PORT),
        '-l' + LOGDIR + 'store.log',
        #'-v2',
    ]
    switch_cmd = [
        BINDIR + 'software_switch.py',
        '--server-delta', str(PARAMS['server_delta']),
        '--client-delta', str(PARAMS['client_delta']),
        '-p', str(SWITCH_PORT),
        '--mode', PARAMS['mode'],
        '-v2',
        '127.0.0.1',
        str(STORE_PORT),
    ]

    allprocs = []
    try:
        store = Popen(store_cmd)
        allprocs.append(store)
        print switch_cmd
        switch = Popen(switch_cmd)
        allprocs.append(switch)

        with open(LOGDIR + 'params.json', 'w') as f:
            json.dump(PARAMS, f)

        for rw in RW_VALUES:
            for clients in CLIENT_VALUES:
                client_cmd = [
                    BINDIR + 'load_generator.py',
                    '-n', str(clients),
                    '-d', str(PARAMS['duration']),
                    '--transactions', PARAMS['transactions'],
                    '-p', str(rw),
                    '--id', '0',
                    '--think', str(PARAMS['think']),
                    '--think-var', str(PARAMS['think_var']),
                    '--log', LOGDIR + 'client-n%s-p%s.log' % (clients, rw),
                    '127.0.0.1', str(SWITCH_PORT),
                ]
                print client_cmd
                client = Popen(client_cmd)
                allprocs.append(client)
                client.wait()
                allprocs.remove(client)
    finally:
        for proc in allprocs:
            proc.kill()

