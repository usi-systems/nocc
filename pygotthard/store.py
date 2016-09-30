#!/usr/bin/env python
import argparse
import socket
import time
import signal
import errno
from gotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("-l", "--log", type=str, help="log file to write to", required=False)
parser.add_argument("-d", "--dump", type=str, help="dump store to this file on exit", required=False)
parser.add_argument("-r", "--recover", type=str, help="recover store from this file", required=False)
parser.add_argument("-v", "--verbosity", type=int, help="set verbosity level", default=0, required=False)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store = Store()

def recover(filename):
    with open(args.recover, 'r') as f:
        store.load(f)
    if args.verbosity > 0:
        print "Recovered objects from %s" % filename

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


while True:
    try:
        data, addr = sock.recvfrom(MAX_TXNMSG_SIZE)
    except socket.error as (code, msg):
        if code != errno.EINTR:
            raise
        break
    req = TxnMsg(binstr=data)
    if log: log.log("received", req=req)
    assert req.flags.type == TYPE_REQ

    if req.flags.reset:
        store.clear()
        if args.recover: recover(args.recover)
        status, ops = STATUS_OK, []
    else:
        status, ops = store.applyTxn(req.ops)

    resp = TxnMsg(replyto=req, status=status, ops=ops)

    if args.verbosity > 1: print req, " => ", resp
    sock.sendto(resp.pack(), addr)
    if log: log.log("sent", res=resp)

if log: log.close()
