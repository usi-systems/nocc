import argparse
import socket
import struct
from threading import Thread
from common import *


class IncClient(Thread, StoreClient):
    def __init__(self, count, store_addr):
        StoreClient.__init__(self, store_addr=store_addr)
        self.count = count
        Thread.__init__(self)

    def run(self):
        # Initialize key/value if it's not already there
        resp = self.req(r_key=1)
        if resp.status == STATUS_NOTFOUND:
            resp = self.req(w_key=1, w_value='0')
            assert(resp.status == STATUS_OK)
        for i in range(self.count):
            while True:
                resp1 = self.req(r_key=1)
                old_val = int(resp1.value.rstrip('\0'))
                resp2 = self.req(r_key=1, r_version=resp1.version, w_key=1, w_value=str(old_val +1))
                if resp2.status == STATUS_OK: break
                #else: print resp2
            if i+1 == self.count:
                print "client", self.cl_name, "(%11d)"%self.cl_id, "incremented it to", resp2.value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num_clients", "-n", type=int, help="number of parallel clients", default=2)
    parser.add_argument("--count", "-c", type=int, help="number of +1 increments to perform", default=1000)
    args = parser.parse_args()

    store_addr = (args.host, args.port)

    clients = [IncClient(args.count, store_addr) for _ in range(args.num_clients)]
    for cl in clients: cl.start()
    for cl in clients: cl.join()
