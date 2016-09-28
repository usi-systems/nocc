#!/usr/bin/env python
import argparse
import socket
import asyncore
import signal
import sys
from Queue import Queue
import threading
from time import sleep
from gotthard import *

class SwitchCache:
    def __init__(self):
        self.values = {}
        self.optimistic_values = {}

    # only a response from the store should update the cache
    def insert(self, key=None, value=None, o=None):
        if o:
            key, value = o.key, o.value
        if key in self.optimistic_values: del self.optimistic_values[key]
        self.values[key] = value

    def optimisticInsert(self, key=None, value=None, o=None):
        self.optimistic_values[o.key if o else key] = o.value if o else value

    def optiValue(self, o=None, key=None):
        key = o.key if o else key
        if key in self.optimistic_values: return self.optimistic_values[key]
        elif key in self.values: return self.values[key]
        else: return '' # by default, a missing object has value ''

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
        data, cl_addr = self.recvfrom(MAX_TXNMSG_SIZE)
        req = TxnMsg(binstr=data)
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
        data, fromaddr = self.recvfrom(MAX_TXNMSG_SIZE)
        assert(fromaddr == self.store_addr)
        res = TxnMsg(binstr=data)
        self.res_queue.put(res)

    def sendReq(self, req):
        self.sendto(req.pack(), self.store_addr)

class SoftwareSwitch:

    def __init__(self, store_addr=None, bind_addr=None, mode='early_abort',
            store_threads=4, client_threads=4, store_delay=None, client_delay=None):
        self.mode = mode
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

    def _sendToStore(self, req):
        if self.store_delay: sleep(self.store_delay)
        self.store_port.sendReq(req)

    def _sendToClient(self, res):
        if self.client_delay: sleep(self.client_delay)
        self.client_port.sendRes(res)

    def _op(self, k=None, o=None, t=TXN_VALUE, opti=False):
        assert(k or (o and o.key))
        k = o.key if o else k
        return TxnOp(t=t, key=k,
                value=self.cache.optiValue(key=k) if opti else self.cache.values[k])

    def _clientHandler(self):
        while True:
            req = self.req_queue.get()
            if req == False: break # it's time to stop

            if self.client_delay: sleep(self.client_delay)

            if self.mode == 'forward':
                self._sendToStore(req)
                continue

            if len(req.ops) < 1:
                self._sendToClient(TxnMsg(replyto=req, status=STATUS_BADREQ, from_switch=1))
                continue

            rb_ops = [o for o in req.ops if o.type == TXN_VALUE] # read before
            r_ops = [o for o in req.ops if o.type == TXN_READ]
            w_ops = [o for o in req.ops if o.type == TXN_WRITE]

            # Check all the read-befores
            was_optimistic = False
            bad_reads = []
            for rb in rb_ops:
                if self.mode == 'optimistic_abort' and rb.key in self.cache.optimistic_values:
                    if rb.value != self.cache.optimistic_values[rb.key]:
                        was_optimistic = True
                        bad_reads.append(self._op(o=rb, opti=True))
                elif rb.key in self.cache.values and rb.value != self.cache.values[rb.key]:
                    bad_reads.append(self._op(o=rb, opti=True))

            if len(bad_reads) > 0:
                self._sendToClient(TxnMsg(replyto=req, ops=bad_reads, from_switch=1,
                    status=STATUS_OPTIMISTIC_ABORT if was_optimistic else STATUS_ABORT))
                continue

            # Update the optimistic cache with write values
            if len(w_ops) > 0:
                if self.mode == 'optimistic_abort':
                    for o in w_ops: self.cache.optimisticInsert(o=o)
            # If only one R, satisfy it if possible
            elif len(r_ops) == 1 and r_ops[0].key in self.cache.values:
                self._sendToClient(TxnMsg(replyto=req, status=STATUS_OK, from_switch=1,
                    ops=[self._op(o=r_ops[0])]))
                continue

            self._sendToStore(req) # forward the packet

    def _storeHandler(self):
        while True:
            res = self.res_queue.get()
            if res == False: break # it's time to stop

            if self.store_delay: sleep(self.store_delay)

            if self.mode == 'forward':
                self._sendToClient(res)
                continue

            # Update our cache, if necessary:
            if res.status == STATUS_OK and len(res.ops) > 0:
                updates = [o for o in res.ops if o.type == TXN_UPDATED]
                for o in updates:
                    self.cache.insert(o=o)

            self._sendToClient(res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
    parser.add_argument("--server-delta", "-D", help="delay (s) sending/receiving with server",
                        type=float, required=False, default=None)
    parser.add_argument("--client-delta", "-d", help="delay (s)  sending/receiving with client",
                        type=float, required=False, default=None)
    parser.add_argument("--mode", "-m", choices=['forward', 'early_abort', 'optimistic_abort'], type=str, default="early_abort")
    parser.add_argument("store_host", type=str, help="store hostname")
    parser.add_argument("store_port", type=int, help="store port")
    args = parser.parse_args()

    store_addr = (args.store_host, args.store_port)
    sw = SoftwareSwitch(store_addr=store_addr,
                        bind_addr=('', args.port),
                        store_delay=args.server_delta,
                        client_delay=args.client_delta,
                        mode=args.mode)

    def signal_handler(signal, frame):
        sw.stop()
    signal.signal(signal.SIGINT, signal_handler)

    sw.loop()
