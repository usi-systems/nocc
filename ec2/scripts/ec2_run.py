#!/usr/bin/env python
import subprocess
import shutil
from os import path
import time
import json
from common import *

STORE_HOST='ec2-52-91-143-132.compute-1.amazonaws.com'
STORE_IP='52.91.143.132'
SWITCH_HOST='ec2-54-183-78-222.us-west-1.compute.amazonaws.com'
SWITCH_IP='54.183.78.222'

RW_VALUES=[0.5]
CLIENT_VALUES=[1, 2, 4, 6, 8, 10, 12, 16]

MODES=['forward', 'read_cache', 'early_abort', 'optimistic_abort']


PARAMS={
    # 'server_delta': 0.01,
    'transactions': 'A(X,X) W(X,X+1) | R(X)',
    # 'think': 0.001,
    # 'think_var': 0.05,
    'duration': 30,
    # 'mode': 'forward', # 'forward', 'read_cache', 'early_abort', 'optimistic_abort'
}

if __name__ == '__main__':
    for mode in MODES:
        for mode in MODES:
            Popen(['ssh', SWITCH_HOST, 'pkill -f gotthard']).wait()
            Popen(['ssh', STORE_HOST, 'pkill -f gotthard']).wait()
            store_cmd = [
                'ssh',
                STORE_HOST,
                BINDIR + 'store.py',
                '-p %d' % (STORE_PORT),
                '-l' + LOGDIR + 'store.log',
                #'-v2',
            ]
            switch_cmd = [
                'ssh',
                SWITCH_HOST,
                BINDIR + 'software_switch.py',
                '-p', str(SWITCH_PORT),
                '--mode', mode,
                STORE_HOST,
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
                            '-r', '0.5',
                            '--log', LOGDIR + 'client-n%s-p%s.log' % (clients, rw),
                            SWITCH_HOST, str(SWITCH_PORT),
                        ]
                        print client_cmd
                        client = subprocess.Popen(client_cmd)
                        allprocs.append(client)
                        client.wait()
                        allprocs.remove(client)
            finally:
                for proc in allprocs:
                    proc.kill()
                Popen(['ssh', SWITCH_HOST, 'pkill -f gotthard'])
                Popen(['ssh', STORE_HOST, 'pkill -f gotthard'])
            run_dir = mode
            subprocess.call(['mkdir', LOGDIR + run_dir])
            subprocess.call(" ".join(['mv',
                                      LOGDIR + '*.log', LOGDIR + '*.json',
                                      LOGDIR + run_dir]),
                            shell=True)
