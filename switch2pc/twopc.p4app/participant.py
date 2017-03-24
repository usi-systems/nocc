#!/usr/bin/env python
import argparse
import signal
import sys
import threading
import socket
import select
import time
import itertools
from Queue import Queue

from minitxn import *
from minitxn import MiniTxnParser
from minitxn import writeSet, readSet, compareSet, valueSet

def log(*args):
    sys.stderr.write(' '.join(map(str, args)))

class FakeLock:
    def __enter__(self):
        pass
    def __exit__(self, t, v, tb):
        pass

class Participant(threading.Thread):

    def __init__(self, bind_addr=('', 8000), thread_count=1):
        threading.Thread.__init__(self)
        self.thread_count = thread_count
        self.msg_queue = Queue()
        self.msg_handlers = []
        self.parser = MiniTxnParser()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(bind_addr)

        self.instances = {}

        self.store = {}
        self.store_lock = threading.Lock() if thread_count > 1 else FakeLock()

    def port(self):
        return self.addr()[1]

    def addr(self):
        return self.sock.getsockname()

    def started(self):
        pass

    def run(self):
        if self.thread_count > 1:
            self.msg_handlers = [threading.Thread(target=self._msgHandler) for _ in xrange(self.thread_count)]
            for t in self.msg_handlers: t.start()

        self.started()
        while True:
            readable, _, x = select.select([self.sock], [], [])
            if self.sock in readable:
                data, addr = self.sock.recvfrom(TXN_MSG_MAX_SIZE)
                if addr is None: break
                if self.thread_count > 1:
                    self.msg_queue.put((data, addr))
                else:
                    self._handleMsg(data, addr)
            else:
                break

        self.sock.close()
        for _ in self.msg_handlers: self.msg_queue.put(None)

    def stop(self):
        for s in [self.sock]:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass
        for _ in self.msg_handlers: self.msg_queue.put(None)
        for t in self.msg_handlers: t.join()


    def _msgHandler(self):
        while True:
            r = self.msg_queue.get()
            if r == None: break
            data, addr = r
            self._handleMsg(data, addr)

    def _handleMsg(self, data, addr):
            msg = self.parser.loads(data)
            if msg['msg_type'] == MSG_TYPE_PREPARE:
                self._handlePrepare(msg, addr)
            elif msg['msg_type'] == MSG_TYPE_COMMIT:
                #if msg['from_switch']: log('p from_switch! ')
                self._handleCommit(msg, addr)
            else:
                assert False, "Unexpected message type: " + str(msg['msg_type'])


    def _handlePrepare(self, msg, addr):

        inst = dict(rlocks=[], wlocks=[])
        bad_compares = []
        bad_lock = False

        with self.store_lock:
            # Get all the read locks
            for _, key, value in itertools.chain(compareSet(msg), readSet(msg)):
                if key not in self.store:
                    self.store[key] = dict(value='', rlock=0, wlock=0)

                if self.store[key]['wlock'] > 0:
                    bad_lock = True
                    break

                self.store[key]['rlock'] += 1
                inst['rlocks'].append(key)

            # Get all the write locks
            for _, key, value in writeSet(msg):
                if key not in self.store:
                    self.store[key] = dict(value='', rlock=0, wlock=0)

                if self.store[key]['wlock'] > 0:
                    bad_lock = True
                    break

                self.store[key]['wlock'] = 1
                inst['wlocks'].append(key)

            # Release locks if we could not get them
            if bad_lock:
                for key in inst['rlocks']: self.store[key]['rlock'] -= 1
                for key in inst['wlocks']: self.store[key]['wlock'] = 0
                inst['rlocks'], inst['wlocks'] = [], []

        if not bad_lock:
            for _, key, value in compareSet(msg):
                if value.rstrip('\0') != self.store[key]['value']:
                    bad_compares.append((OP_TYPE_VALUE, key, self.store[key]['value']))

        result = []
        status = STATUS_ABORT
        if len(bad_compares) > 0:
            result = bad_compares
        elif not bad_lock:
            for _, key, value in readSet(msg):
                result.append((OP_TYPE_VALUE, key, self.store[key]['value']))
            inst['writes'] = writeSet(msg)
            status = STATUS_OK

        inst['addr'] = addr
        self.instances[msg['txn_id']] = inst

        if msg['reset'] == 1:
            self.store = {}

        res = dict(msg, msg_type=MSG_TYPE_VOTE, status=status, ops=result, from_switch=0)
        self.send(res, addr)


    def _handleCommit(self, msg, addr):

        if msg['txn_id'] not in self.instances: return

        inst = self.instances[msg['txn_id']]

        if msg['status'] == STATUS_OK:
            for _, key, value in inst['writes']:
                self.store[key]['value'] = value.rstrip('\0')

        with self.store_lock:
            for key in inst['rlocks']: self.store[key]['rlock'] -= 1
            for key in inst['wlocks']: self.store[key]['wlock'] = 0

        coordinator_addr = inst['addr']
        del self.instances[msg['txn_id']]

        res = dict(msg, msg_type=MSG_TYPE_COMMITTED, status=STATUS_OK, ops=[], from_switch=0)
        self.send(res, coordinator_addr)

        #wcnt, rcnt = 0, 0
        #for o in self.store.values():
        #    rcnt += o['rlock']
        #    wcnt += o['wlock']
        #if wcnt+rcnt > 0:
        #    print "wcnt:", wcnt, "rcnt:", rcnt



    def send(self, msg, addr):
        self.sock.sendto(self.parser.dumps(msg), addr)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
    parser.add_argument("-t", "--threads", type=int, help="number of threads", default=2)
    parser.add_argument("--verbosity", "-v", type=int, help="set verbosity level", default=0, required=False)
    args = parser.parse_args()

    p = Participant(bind_addr=('', args.port), thread_count=args.threads)
    def signal_handler(signal, frame):
        p.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    p.run()
