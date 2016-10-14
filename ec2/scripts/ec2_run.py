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
#CLIENT_VALUES=[1, 2, 4, 6, 8, 10, 12, 16, 32, 64]
CLIENT_VALUES=[2]

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
        print 'killing processes...'
        kill_processes(STORE_HOST)
        kill_processes(SWITCH_HOST)
        print 'starting store...'
        store = run_store(STORE_HOST)
        print 'starting switch...'
        switch = run_switch(SWITCH_HOST, STORE_HOST, mode)
        time.sleep(1)
        assert(store.poll() is None)
        assert(switch.poll() is None)

        try:
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
                        # '--think', str(PARAMS['think']),
                        # '--think-var', str(PARAMS['think_var']),
                        '--log', LOGDIR + 'client-n%s-p%s.log' % (clients, rw),
                        SWITCH_HOST, str(SWITCH_PORT),
                    ]
                    print client_cmd
                    client = subprocess.Popen(client_cmd)
                    client.wait()
        finally:
            kill_processes(STORE_HOST)
            kill_processes(SWITCH_HOST)
            kill_processes('localhost')
            for proc in allprocs:
                proc.kill()
        run_dir = mode + '_' + str(delta) + 'delta'
        subprocess.call(['mkdir', LOGDIR + run_dir])
        subprocess.call(" ".join(['mv',
                                  LOGDIR + '*.log', LOGDIR + '*.json',
                                  LOGDIR + run_dir]),
                        shell=True)
