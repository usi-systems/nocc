from subprocess import Popen
import os
import time

BINDIR=os.path.expanduser("~/workspace/gotthard/pygotthard/")
LOGDIR=os.path.expanduser("~/workspace/gotthard/ec2/LOGS/")

STORE_PORT=9990
SWITCH_PORT=9991

def kill_processes(host):
    Popen(['ssh', host, 'pkill -f gotthard'])

def run_store(host,
              port=STORE_PORT,
              log=LOGDIR + 'store.log'):
    store_cmd = ' '.join([
        BINDIR + 'store.py',
        '-p', str(port),
        '-l', log,
        #'-v2',
    ])
    print store_cmd
    return Popen(['ssh', host, store_cmd])

def run_switch(host,
               store_host,
               mode,
               port=SWITCH_PORT,
               store_port=STORE_PORT,
               server_delta=None,
               client_delta=None):
    switch_cmd = ' '.join([
        BINDIR + 'software_switch.py',
        '--server-delta ' + str(server_delta) if server_delta else "",
        '--client-delta ' + str(client_delta) if client_delta else "",
        '-p', str(port),
        '--mode', mode,
        '127.0.0.1',
        str(store_port),
    ])
    print switch_cmd
    return Popen(['ssh', host, switch_cmd])

def run_client(host,
               switch_host,
               switch_port=SWITCH_PORT,
               log=LOGDIR + 'clients.log',
               clients=1,
               duration=60,
               transactions='R(X) | A(X,X) W(X,X+1)',
               t_ratios='0.8',
               think=1,
               think_var=0.05,
               cid=0):
    client_cmd = ' '.join([
        BINDIR + 'load_generator.py',
        '-n', str(clients),
        '-d', str(duration),
        '--transactions', '"%s"' % (transactions),
        '-p', '"%s"' % (t_ratios),
        '--id', str(cid),
        '--think', str(think),
        '--think-var', str(think_var),
        '--log', log,
        switch_host,
        str(switch_port),
    ])
    print client_cmd


if __name__ == '__main__':
    run_client('localhost', 'localhost')
    # store = run_store('localhost')
    # switch = run_switch('localhost', 'localhost', 'forward')
    # time.sleep(1)
    # assert(switch.poll() is None)
    # assert(store.poll() is None)
    # kill_processes('localhost')
