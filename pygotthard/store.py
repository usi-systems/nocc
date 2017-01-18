#!/usr/bin/env python
import argparse
import socket
import time
import signal
import errno
from threading import Thread, Lock
from gotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("-l", "--log", type=str, help="log file to write to", required=False)
parser.add_argument("-d", "--dump", type=str, help="dump store to this file on exit", required=False)
parser.add_argument("-r", "--recover", type=str, help="recover store from this file", required=False)
parser.add_argument("-v", "--verbosity", type=int, help="set verbosity level", default=0, required=False)
parser.add_argument("-t", "--think", type=float, help="think time for requests", default=0, required=False)
parser.add_argument("-s", "--serial", action='store_true', help="Process requests serially", default=False, required=False)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store = Store()

def recover(filename):
    with open(args.recover, 'r') as f:
        store.load(f)
    if args.verbosity > 0:
        print "Recovered %d objects from %s" % (len(store.values), filename)

if args.recover: recover(args.recover)

log = None
if args.log:
    log = GotthardLogger(args.log)
def handler(signum, frame):
    if args.dump:
        with open(args.dump, 'w') as f:
            store.dump(f)
    if log: log.close()
    sock.close()
signal.signal(signal.SIGINT, handler)

class RecvQueue:
    clients = {}

    def __init__(self):
        self.lock = Lock()

    def pushpop(self, req):
        with self.lock:
            return self._pushpop(req)

    # TODO: prune fragmented message queues with missing frags
    def _pushpop(self, req):
        if req.frag_cnt == 1:
            return req.ops
        if req.cl_id not in self.clients:
            self.clients[req.cl_id] = {}
        if req.req_id not in self.clients[req.cl_id]:
            self.clients[req.cl_id][req.req_id] = {}
        self.clients[req.cl_id][req.req_id][req.frag_seq] = req
        if len(self.clients[req.cl_id][req.req_id]) == req.frag_cnt:
            assert set(xrange(1, req.frag_cnt+1)) == set(self.clients[req.cl_id][req.req_id].keys())
            frags = [self.clients[req.cl_id][req.req_id][f] for f in xrange(1, req.frag_cnt+1)]
            ops = [o for req in frags for o in req.ops]
            del self.clients[req.cl_id][req.req_id]
            return ops
        return None

recvq = RecvQueue()

def sendResp(req, status, ops, addr):
    frag_cnt = int(math.ceil(len(ops) / float(GOTTHARD_MAX_OP)))

    res = []
    for i in xrange(0, frag_cnt):
        res.append(TxnMsg(replyto=req, status=status,
            frag_seq=i+1, frag_cnt=frag_cnt,
            ops=ops[i*GOTTHARD_MAX_OP:(i*GOTTHARD_MAX_OP)+GOTTHARD_MAX_OP]))

    if len(res) == 0:
        res.append(TxnMsg(replyto=req, status=status))

    for r in res:
        sock.sendto(r.pack(), addr)
        if args.verbosity > 1: print "<=", r
        if log: log.log("sent", res=r)
        wait = min(MIN_INTER_MSG_SEND_WAIT * req.frag_seq, MAX_INTER_MSG_SEND_WAIT)
        if wait:
            time.sleep(wait)

def handleReq(data, addr):
    req = TxnMsg(binstr=data)
    if log: log.log("received", req=req)
    time.sleep(args.think)
    assert req.flags.type == TYPE_REQ

    resp_ready = True
    if args.verbosity > 1: print "=>", req

    if req.flags.reset:
        if args.verbosity > 0: print "Removing all %d objects" % len(store.values)
        store.clear()
        if args.recover: recover(args.recover)
        status, ops = STATUS_OK, []
    else:
        txn_ops = recvq.pushpop(req)
        if txn_ops is None:
            return
        status, ops = store.applyTxn(txn_ops)

    sendResp(req, status, ops, addr)

while True:
    try:
        data, addr = sock.recvfrom(MAX_TXNMSG_SIZE)
    except socket.error as (code, msg):
        if code != errno.EINTR:
            raise
        break
    if args.serial:
        handleReq(data, addr)
    else:
        thread = Thread(target=handleReq, args=(data, addr))
        thread.start()


if log: log.close()
