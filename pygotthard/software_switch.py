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

    def clear(self):
        self.values, self.optimistic_values = {}, {}

    # only a response from the store should update the cache
    def insert(self, key=None, value=None, o=None):
        if o:
            key, value = o.key, o.value
        if key in self.optimistic_values: self.optimistic_values[key] = None
        self.values[key] = value

    def optimisticInsert(self, key=None, value=None, o=None):
        self.optimistic_values[o.key if o else key] = o.value if o else value

    def optiValue(self, o=None, key=None):
        key = o.key if o else key
        opti_val = self.optimistic_values.get(key)
        if opti_val is not None: return opti_val
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
        # assert(fromaddr == self.store_addr)
        res = TxnMsg(binstr=data)
        self.res_queue.put(res)

    def sendReq(self, req):
        self.sendto(req.pack(), self.store_addr)

class SoftwareSwitch:

    def __init__(self, store_addr=None, bind_addr=None, mode='optimistic_abort', verbosity=0,
                 store_threads=128, client_threads=128, store_delay=None, client_delay=None):
        self.mode = mode
        self.verbosity = verbosity
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
            self._handleClientReq(req)

    def _handleClientReq(self, req):
        if self.client_delay: sleep(self.client_delay)

        if self.mode == 'forward':
            return self._sendToStore(req)

        if req.frag_cnt > 1: # we can't do anything with only part of the TXN
            return self._sendToStore(req)

        if req.flags.reset:
            if self.verbosity > 0: print "Resetting cache"
            self.cache.clear()

        rb_ops = [o for o in req.ops if o.type == TXN_VALUE] # read before
        r_ops = [o for o in req.ops if o.type == TXN_READ]
        w_ops = [o for o in req.ops if o.type == TXN_WRITE]

        if self.mode == 'read_cache':
            cache_hits = [self._op(o=o) for o in r_ops if o.key in self.cache.values]
            # All the ops are reads satisfied by the cache:
            if len(req.ops) and len(cache_hits) == len(req.ops):
                return self._sendToClient(TxnMsg(replyto=req, from_switch=1,
                                                ops=cache_hits, status=STATUS_OK))
            else:
                return self._sendToStore(req)

        if len(r_ops) > 0: # Switch cannot satisfy R operations
            return self._sendToStore(req)

        # Check all the read-befores
        was_optimistic = False
        bad_reads = []
        for rb in rb_ops:
            opti_val = self.cache.optimistic_values.get(rb.key)
            if self.mode == 'optimistic_abort' and opti_val is not None:
                if rb.value != opti_val:
                    was_optimistic = True
                    bad_reads.append(self._op(o=rb, opti=True))
            elif rb.key in self.cache.values:
                if rb.value != self.cache.values[rb.key]:
                    bad_reads.append(self._op(o=rb, opti=True))
            else:
                # cache miss; we can't do anything smart with this TXN
                return self._sendToStore(req)

        if len(bad_reads) > 0:
            return self._sendToClient(TxnMsg(replyto=req, ops=bad_reads, from_switch=1,
                    status=STATUS_OPTIMISTIC_ABORT if was_optimistic else STATUS_ABORT))

        # the client only issued some RB() to check its state
        if len(rb_ops) and len(rb_ops) == len(req.ops):
            return self._sendToClient(TxnMsg(replyto=req, from_switch=1, status=STATUS_OK))

        # Update the optimistic cache with write values
        if self.mode == 'optimistic_abort':
            for o in w_ops: self.cache.optimisticInsert(o=o)

        self._sendToStore(req) # just forward the packet

    def _storeHandler(self):
        while True:
            res = self.res_queue.get()
            if res == False: break # it's time to stop

            if self.store_delay: sleep(self.store_delay)

            if self.mode == 'forward':
                self._sendToClient(res)
                continue

            # Update our cache with any VALUE op from the store
            if self.mode == 'read_cache' or res.status == STATUS_ABORT or res.status == STATUS_OPTIMISTIC_ABORT:
                for o in [o for o in res.ops if o.type == TXN_VALUE or o.type == TXN_UPDATED]:
                    self.cache.insert(o=o)

            self._sendToClient(res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
    parser.add_argument("--server-delta", "-D", help="delay (s) sending/receiving with server",
                        type=float, required=False, default=None)
    parser.add_argument("--client-delta", "-d", help="delay (s)  sending/receiving with client",
                        type=float, required=False, default=None)
    parser.add_argument("--mode", "-m", choices=['forward', 'read_cache', 'optimistic_abort'], type=str, default="optimistic_abort")
    parser.add_argument("--verbosity", "-v", type=int, help="set verbosity level", default=0, required=False)
    parser.add_argument("store_host", type=str, help="store hostname")
    parser.add_argument("store_port", type=int, help="store port")
    args = parser.parse_args()

    store_addr = (args.store_host, args.store_port)
    sw = SoftwareSwitch(store_addr=store_addr,
                        verbosity=args.verbosity,
                        bind_addr=('', args.port),
                        store_delay=args.server_delta,
                        client_delay=args.client_delta,
                        mode=args.mode)

    def signal_handler(signal, frame):
        sw.stop()
    signal.signal(signal.SIGINT, signal_handler)

    sw.loop()
