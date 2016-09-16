#!/usr/bin/env python
import argparse
import socket
import asyncore
import signal
import sys
from Queue import Queue
import threading
from time import sleep
from common import *

class SwitchCache:
    def __init__(self):
        self.keys = []
        self.values = {}
        self.versions = {}

    def insert(self, key=None, version=None, value=None):
        if version == 0: # a rm operation
            del self.versions[key]
            del self.values[key]
            self.keys.remove(key)
        else:
            self.versions[key] = version
            self.values[key] = value
            if not key in self.keys: self.keys.append(key)

    def hit(self, key):
        return key in self.keys

    def sameVersion(self, key, version):
        assert(self.hit(key))
        return version == self.versions[key]

class ClientPort(asyncore.dispatcher):

    def __init__(self, bind_addr=None, req_queue=None):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(bind_addr)
        self.client_map = {}
        self.req_queue = req_queue

    def writable(self):
        return False

    def handle_read(self):
        data, cl_addr = self.recvfrom(REQMSG_SIZE)
        req = ReqMsg(binstr=data)
        self.client_map[req.cl_id] = cl_addr
        self.req_queue.put(req)

    def sendRes(self, res):
        assert(res.cl_id in self.client_map.keys())
        self.sendto(res.pack(), self.client_map[res.cl_id])



class StorePort(asyncore.dispatcher):

    def __init__(self, store_addr=None, res_queue=None):
        asyncore.dispatcher.__init__(self)
        self.store_addr = store_addr
        self.res_queue = res_queue
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(('', 0))

    def writable(self):
        return False

    def handle_read(self):
        data, fromaddr = self.recvfrom(RESPMSG_SIZE)
        assert(fromaddr == self.store_addr)
        res = RespMsg(binstr=data)
        self.res_queue.put(res)

    def sendReq(self, req):
        self.sendto(req.pack(), self.store_addr)

class SoftwareSwitch:

    def __init__(self, store_addr=None, bind_addr=None,
            store_threads=4, client_threads=4, store_delay=None, client_delay=None):
        self.store_delay = store_delay
        self.client_delay = client_delay

        self.cache = SwitchCache()

        self.res_queue = Queue()
        self.req_queue = Queue()

        self.client_handlers = [threading.Thread(target=self._clientHandler) for _ in xrange(client_threads)]
        self.store_handlers = [threading.Thread(target=self._storeHandler) for _ in xrange(store_threads)]
        for t in self.client_handlers: t.start()
        for t in self.store_handlers: t.start()

        self.store_port = StorePort(store_addr=store_addr, res_queue=self.res_queue)
        self.client_port = ClientPort(bind_addr=bind_addr, req_queue=self.req_queue)

    def loop(self):
        asyncore.loop()

    def stop(self):
        self.client_port.close()
        self.store_port.close()
        for _ in xrange(len(self.client_handlers)): self.req_queue.put(False)
        for _ in xrange(len(self.store_handlers)): self.res_queue.put(False)

    def _clientHandler(self):
        while True:
            req = self.req_queue.get()
            if req == False: break # it's time to stop

            if self.client_delay: sleep(self.client_delay)

            if req.r_key != 0 and req.w_key != 0: # RW operation
                if self.cache.hit(req.r_key) and not self.cache.sameVersion(req.r_key, req.r_version):
                    # Do an early reject:
                    reject_msg = RespMsg(cl_id=req.cl_id, req_id=req.req_id, status=STATUS_REJECT, from_switch=1,
                            key=req.r_key, value=self.cache.values[req.r_key], version=self.cache.versions[req.r_key])
                    self.client_port.sendRes(reject_msg)
                    continue
            elif req.r_key != 0:                  # R operation
                if self.cache.hit(req.r_key):
                    resp = RespMsg(cl_id=req.cl_id, req_id=req.req_id, status=STATUS_OK, from_switch=1,
                            key=req.r_key, value=self.cache.values[req.r_key], version=self.cache.versions[req.r_key])
                    self.client_port.sendRes(resp)
                    continue

            # Otherwise, just forward packet:
            if self.store_delay: sleep(self.store_delay)
            self.store_port.sendReq(req)

    def _storeHandler(self):
        while True:
            res = self.res_queue.get()
            if res == False: break # it's time to stop

            if self.store_delay: sleep(self.store_delay)

            # Update our cache, if necessary:
            if res.status == STATUS_OK and res.key != 0:
                self.cache.insert(key=res.key, version=res.version, value=res.value)

            if self.client_delay: sleep(self.client_delay)
            self.client_port.sendRes(res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
    parser.add_argument("--server-delta", "-D", help="delay (s) sending/receiving with server",
                        type=float, required=False, default=None)
    parser.add_argument("--client-delta", "-d", help="delay (s)  sending/receiving with client",
                        type=float, required=False, default=None)
    parser.add_argument("store_host", type=str, help="store hostname")
    parser.add_argument("store_port", type=int, help="store port")
    args = parser.parse_args()

    store_addr = (args.store_host, args.store_port)
    sw = SoftwareSwitch(store_addr=store_addr,
                        bind_addr=('', args.port),
                        store_delay=args.server_delta,
                        client_delay=args.client_delta)

    def signal_handler(signal, frame):
        sw.stop()
    signal.signal(signal.SIGINT, signal_handler)

    sw.loop()
