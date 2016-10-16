#!/usr/bin/env python
import subprocess
import shutil
from os import path
import time
import json

BINDIR='/home/pacheco/workspace/gotthard/pygotthard/'
LOGDIR='/home/pacheco/workspace/gotthard/ec2/RW_LOGS/'
STORE_PORT=9992
SWITCH_PORT=9993

# # second plot
DELTA=[0.2]
RW_VALUES=[0, 0.1, 0.2, 0.4, 0.6, 0.8]
CLIENT_VALUES=[8]

MODES=['forward', 'read_cache', 'early_abort', 'optimistic_abort']

PARAMS={
    # 'client_delta': 0.04,
    # 'server_delta': 0.01,
    'transactions': 'A(X,X) W(X,X+1) | R(X)',
    # 'think': 0.001,
    # 'think_var': 0.05,
    'duration': 30,
    # 'mode': 'forward', # 'forward', 'read_cache', 'early_abort', 'optimistic_abort'
}

if __name__ == '__main__':
    for delta in DELTA:
        for mode in MODES:
            store_cmd = [
                BINDIR + 'store.py',
                '-p %d' % (STORE_PORT),
                '-l' + LOGDIR + 'store.log',
                #'-v2',
            ]
            switch_cmd = [
                BINDIR + 'software_switch.py',
                '--server-delta', str(0.05 * (1-delta)),
                '--client-delta', str(0.05 * delta),
                '-p', str(SWITCH_PORT),
                '--mode', mode,
                '-v2',
                '127.0.0.1',
                str(STORE_PORT),
            ]

            allprocs = []
            try:
                store = subprocess.Popen(store_cmd)
                allprocs.append(store)
                print switch_cmd
                switch = subprocess.Popen(switch_cmd)
                allprocs.append(switch)

                with open(LOGDIR + 'params.json', 'w') as f:
                    json.dump(PARAMS, f)

                time.sleep(1)

                for rw in RW_VALUES:
                    for clients in CLIENT_VALUES:
                        client_cmd = [
                            BINDIR + 'load_generator.py',
                            '-n', str(clients),
                            '-d', str(PARAMS['duration']),
                            '--transactions', PARAMS['transactions'],
                            '-p', str(rw),
                            '--id', '0',
                            # '--think', str(PARAMS['think']),
                            # '--think-var', str(PARAMS['think_var']),
                            '--log', LOGDIR + 'client-n%s-p%s.log' % (clients, rw),
                            '127.0.0.1', str(SWITCH_PORT),
                        ]
                        print client_cmd
                        client = subprocess.Popen(client_cmd)
                        allprocs.append(client)
                        client.wait()
                        allprocs.remove(client)
            finally:
                for proc in allprocs:
                    proc.kill()
            run_dir = mode + '_' + str(delta) + 'delta'
            subprocess.call(['mkdir', LOGDIR + run_dir])
            subprocess.call(" ".join(['mv',
                                      LOGDIR + '*.log', LOGDIR + '*.json',
                                      LOGDIR + run_dir]),
                            shell=True)

