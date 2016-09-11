import argparse
import socket
import asyncore
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("store_host", type=str, help="store hostname")
parser.add_argument("store_port", type=int, help="store port")
args = parser.parse_args()

store_addr = (args.store_host, args.store_port)

class SwitchCache:
    def __init__(self):
        self.keys = []
        self.values = {}
        self.versions = {}

    def insert(self, key=None, version=None, value=None):
        if not key in self.keys: self.keys.append(key)
        self.versions[key] = version
        self.values[key] = value

    def hit(self, key):
        return key in self.keys

    def sameVersion(self, key, version):
        assert(self.hit(key))
        return version == self.versions[key]

class ClientSock(asyncore.dispatcher):

    def __init__(self, bind_addr=None, switch=None):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(bind_addr)
        self.client_map = {}
        self.switch = switch
        self.cache = switch.cache

    def writable(self):
        return False

    def handle_read(self):
        data, cl_addr = self.recvfrom(REQMSG_SIZE)
        req = ReqMsg(binstr=data)

        if not req.cl_id in self.client_map.keys():
            self.client_map[req.cl_id] = cl_addr

        if req.r_key != 0 and req.w_key != 0: # RW operation
            if self.cache.hit(req.r_key) and not self.cache.sameVersion(req.r_key, req.r_version):
                # Do an early reject:
                reject_msg = RespMsg(cl_id=req.cl_id, req_id=req.req_id, status=STATUS_REJECT)
                self.sendto(reject_msg.pack(), cl_addr)
                return
        elif req.r_key != 0:                  # R operation
            if self.cache.hit(req.r_key):
                resp = RespMsg(cl_id=req.cl_id, req_id=req.req_id, status=STATUS_OK,
                        key=req.r_key, value=self.cache.values[req.r_key], version=self.cache.versions[req.r_key])
                self.sendto(resp.pack(), cl_addr)
                return

        # Otherwise, just forward packet:
        self.switch.sendto_store(data=data)

    def sendto_client(self, cl_id=None, data=None):
        assert(cl_id in self.client_map.keys())
        self.sendto(data, self.client_map[cl_id])


class SoftwareSwitch(asyncore.dispatcher):

    def __init__(self, store_addr=None, bind_addr=None):
        asyncore.dispatcher.__init__(self)
        self.store_addr = store_addr
        self.cache = SwitchCache()

        # Listen for clients:
        self.client_sock = ClientSock(bind_addr=bind_addr, switch=self)

        # Connect to store:
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(('', 0))

    def run(self):
        asyncore.loop()

    def writable(self):
        return False

    def handle_read(self):
        data, fromaddr = self.recvfrom(RESPMSG_SIZE)
        assert(fromaddr == self.store_addr)
        resp = RespMsg(binstr=data)

        # Update our cache, if necessary:
        if resp.status == STATUS_OK and resp.key != 0:
            self.cache.insert(key=resp.key, version=resp.version, value=resp.value)

        # Finally, forward the response:
        self.client_sock.sendto_client(data=data, cl_id=resp.cl_id)

    def sendto_store(self, data=None):
        self.sendto(data, self.store_addr)

if __name__ == '__main__':
    sw = SoftwareSwitch(store_addr=store_addr, bind_addr=('', args.port))
    sw.run()
