#!/usr/bin/env python
import argparse
from threading import Thread
from common import *


class IncClient(Thread, StoreClient):
    def __init__(self, count, log, store_addr):
        StoreClient.__init__(self, store_addr=store_addr, log_filename=log)
        self.count = count
        Thread.__init__(self)

    def run(self):
        # Initialize key/value if it's not already there
        resp = self.req(r_key=1, r_version=0, w_key=1, w_value=str(0))
        cached_version, cached_value = resp.version, int(resp.value.rstrip('\0'))
        for i in range(self.count):
            while True:
                cached_value += 1
                resp = self.req(r_key=1, r_version=cached_version, w_key=1, w_value=str(cached_value))
                cached_version, cached_value = resp.version, int(resp.value.rstrip('\0'))
                if resp.status == STATUS_OK: break

        print "client", self.cl_name, "(%11d)"%self.cl_id, "incremented it to", resp.value.rstrip('\0')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=2)
    parser.add_argument("--count", "-c", type=int, help="number of +1 increments to perform", default=1000)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    parser.add_argument("--id", "-i", type=int, help="assign cl_id starting from this value", default=None)
    args = parser.parse_args()

    store_addr = (args.host, args.port)

    clients = []
    for n in xrange(args.num_clients):
        cl = IncClient(args.count, args.log, store_addr)
        if not args.id is None: cl.cl_id = args.id + n
        clients.append(cl)

    for cl in clients: cl.start()
    for cl in clients: cl.join()
