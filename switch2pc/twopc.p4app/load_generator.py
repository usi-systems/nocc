#!/usr/bin/env python
import argparse
import signal
import sys
import threading
import random
import time

from minitxn import *
from client import Client
from logger import Logger

def parseAddr(s):
    h, p = s.split(':')
    return (h, int(p))

class LoadClient(Client, threading.Thread):

    def __init__(self, server_addr=None, cl_id=None, txn_cnt=1000, duration=None, logger=None):
        threading.Thread.__init__(self)
        Client.__init__(self, server_addr=server_addr, cl_id=cl_id, logger=logger)
        self.txn_cnt = txn_cnt
        self.duration = duration
        self.error = False


    def run(self):
        try:
            self._run()
        except:
            self.error = True
            raise

    def _run(self):
        keys = range(1, 1001)
        max_keys = 10
        if max_keys > len(keys): max_keys = len(keys)
        R, W, C, Txn = self.R, self.W, self.C, self.Txn
        self.abort_cnt = 0
        start_ts = time.time()
        end_ts = start_ts + self.duration if self.duration is not None else None
        n = 0
        while True:
            x = random.randint(0, 2)
            x=3
            num_keys = random.randint(1, max_keys)
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

            n += 1
            if n == self.txn_cnt: break
            if end_ts is not None and time.time() >= end_ts: break

        print "abort_cnt:", self.abort_cnt

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--num-clients", type=int, help="number of clients", default=1)
    parser.add_argument("-n", "--num-txns", type=int, help="number of transactions", default=None)
    parser.add_argument("--duration", "-d", type=float, help="Maximum duration of experiment", default=None)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    parser.add_argument("--verbosity", "-v", type=int, help="set verbosity level", default=0, required=False)
    parser.add_argument("server_addr", type=parseAddr, help="Address of coordinator")
    args = parser.parse_args()

    if args.num_txns is None and args.duration is None:
        parser.error("Either --num-txns or --duration is required")

    logger = Logger(args.log) if args.log else None

    clients = [LoadClient(server_addr=args.server_addr, txn_cnt=args.num_txns, duration=args.duration, cl_id=n+1, logger=logger) for n in xrange(args.num_clients)]
    if args.num_clients == 1:
        clients[0].run()
    else:
        for c in clients: c.start()
        for c in clients: c.join()

    if logger: logger.close()

    errors = [1 for c in clients if c.error]
    rc = len(errors)
    sys.exit(rc)
