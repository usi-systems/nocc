import argparse
import socket
import struct
from threading import Thread
from common import *


class IncClient(Thread):
    req_id_seq = 0

    def __init__(self, client_id, count):
        self.client_id = client_id
        self.count = count
        Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))

    def sendreq(self, req_id=None, r_key=0, r_version=0, w_key=0, w_value=''):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq
        req = ReqMsg(req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value)
        self.sock.sendto(req.pack(), (args.host, args.port))
        data, fromaddr = self.sock.recvfrom(RESPMSG_SIZE)
        return RespMsg(binstr=data)

    def run(self):
        # Initialize key/value if it's not already there
        resp = self.sendreq(r_key=1)
        if resp.status == STATUS_NOTFOUND:
            resp = self.sendreq(w_key=1, w_value='0')
            assert(resp.status == STATUS_OK)
        for i in range(self.count):
            while True:
                resp1 = self.sendreq(r_key=1)
                old_val = int(resp1.value.rstrip('\0'))
                resp2 = self.sendreq(r_key=1, r_version=resp1.version, w_key=1, w_value=str(old_val +1))
                if resp2.status == STATUS_OK: break
                #else: print resp2
            if i+1 == self.count:
                print "client", self.client_id, "incremented it to", resp2.value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num_clients", "-n", type=int, help="number of parallel clients", default=2)
    parser.add_argument("--count", "-c", type=int, help="number of +1 increments to perform", default=1000)
    args = parser.parse_args()

    clients = [IncClient(i, args.count) for i in range(args.num_clients)]
    for cl in clients: cl.start()
    for cl in clients: cl.join()
