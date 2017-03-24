#!/usr/bin/env python
import argparse
import signal
import sys
import threading
import random

from minitxn import *
from client import Client

def parseAddr(s):
    h, p = s.split(':')
    return (h, int(p))

class StressClient(Client, threading.Thread):

    def __init__(self, server_addr=None, cl_id=None, txn_cnt=1000):
        threading.Thread.__init__(self)
        Client.__init__(self, server_addr=server_addr, cl_id=cl_id)
        self.txn_cnt = txn_cnt


    def run(self):
        keys = range(1, 10001)
        R, W, C, Txn = self.R, self.W, self.C, self.Txn
        self.abort_cnt = 0
        for n in xrange(self.txn_cnt):
            x = random.randint(0, 2)
            num_keys = random.randint(1, 10)
            txn_keys = random.sample(keys, num_keys)
            if x < 1:
                t = Txn(*[R(k) for k in txn_keys])
            elif x < 2:
                v = str(random.random())
                t = Txn(*[W(k, v) for k in txn_keys])
            else:
                v = str(random.random())
                num_c = num_keys/2
                num_w = num_keys - num_c
                #num_c = 0
                cmps = [C(k) for k in txn_keys[:num_c]]
                writes = [W(k, v) for k in txn_keys[num_c:num_w]]
                t = Txn(*(cmps+writes))

            res = self.issue(t)
            if res['status'] == STATUS_ABORT:
                self.abort_cnt += 1

        print "abort_cnt:", self.abort_cnt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--num-clients", type=int, help="number of clients", default=1)
    parser.add_argument("-n", "--num-txns", type=int, help="number of transactions", default=1000)
    parser.add_argument("--verbosity", "-v", type=int, help="set verbosity level", default=0, required=False)
    parser.add_argument("server_addr", type=parseAddr, help="Address of coordinator")
    args = parser.parse_args()

    clients = [StressClient(server_addr=args.server_addr, txn_cnt=args.num_txns, cl_id=n+1) for n in xrange(args.num_clients)]
    if args.num_clients == 1:
        clients[0].run()
    else:
        for c in clients: c.start()
        for c in clients: c.join()
