#!/usr/bin/env python
import argparse
import socket
import time
import signal
import errno
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("-l", "--log", type=str, help="log file to write to", required=False)
parser.add_argument("-v", "--verbosity", type=int, help="set verbosity level", default=0, required=False)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store = Store()

log = None
if args.log:
    log = GotthardLogger(args.log)
    def handler(signum, frame):
        log.close()
        sock.close()
    signal.signal(signal.SIGINT, handler)


while True:
    try:
        data, addr = sock.recvfrom(REQMSG_SIZE)
    except socket.error as (code, msg):
        if code != errno.EINTR:
            raise
        break
    req = ReqMsg(binstr=data)
    if log: log.log("received", req=req)
    op = req.op()

    if op == OP_RW:
        (status, key, value) = store.readwrite(r_key=req.r_key, r_value=req.r_value,
                                                     w_key=req.w_key, w_value=req.w_value)
    elif op == OP_R:
        (status, key, value) = store.read(key=req.r_key)
    elif op == OP_W:
        (status, key, value) = store.write(key=req.w_key, value=req.w_value)
    else:
        raise Exception("Received a message with empty read and write fields")

    updated = 1 if status == STATUS_OK and (op == OP_W or op == OP_RW) else 0

    resp = RespMsg(cl_id=req.cl_id, req_id=req.req_id, updated=updated,
            status=status, key=key, value=value)

    if args.verbosity > 1: print req, " => ", resp
    sock.sendto(resp.pack(), addr)
    if log: log.log("sent", res=resp)

if log: log.close()
