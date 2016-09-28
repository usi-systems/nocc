#!/usr/bin/env python
import argparse
from threading import Thread
from gotthard import *
from random import gauss
from time import sleep


class IncClient(Thread, GotthardClient):
    def __init__(self, count, log, store_addr, think, think_var):
        GotthardClient.__init__(self, store_addr=store_addr, logger=log)
        Thread.__init__(self)
        self.count = count
        self.think = think
        self.think_var = think_var

    def run(self):
        with self:
            # Initialize key/value if it's not already there
            resp = self.req(r_key=1, r_value='', w_key=1, w_value=str(0))
            if self.think and self.think_var: think_sigma = self.think * self.think_var
            for i in range(self.count):
                while True:
                    cached_value = int(resp.value.rstrip('\0'))
                    resp = self.req(r_key=1, r_value=str(cached_value), w_key=1, w_value=str(cached_value+1))
                    if resp.status == STATUS_OK: break
                if self.think:
                    sleep(abs(gauss(self.think, think_sigma)) if self.think_var else self.think)

            print "client", self.cl_name, "(%11d)"%self.cl_id, "incremented it to", resp.value.rstrip('\0')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=1)
    parser.add_argument("--count", "-c", type=int, help="number of +1 increments to perform", default=1000)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    parser.add_argument("--id", "-i", type=int, help="assign cl_id starting from this value", default=None)
    parser.add_argument("--think", "-t", type=float, help="think time (s) between increments", default=None)
    parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=None)
    args = parser.parse_args()

    store_addr = (args.host, args.port)

    logger = GotthardLogger(args.log) if args.log else None
    clients = []
    for n in xrange(args.num_clients):
        cl = IncClient(args.count, logger, store_addr, args.think, args.think_var)
        if not args.id is None: cl.cl_id = args.id + n
        clients.append(cl)

    for cl in clients: cl.start()
    for cl in clients: cl.join()
    if logger: logger.close()
