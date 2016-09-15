#!/usr/bin/env python
import argparse
import socket
import time
import signal
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("-l", "--log", type=str, help="log file to write to", required=False)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store = Store()

log = None
if args.log:
    log = GotthardLogger(args.log)
    def handler(signum, frame):
        log.close()
    signal.signal(signal.SIGINT, handler)


while True:
    data, addr = sock.recvfrom(REQMSG_SIZE)
    req = ReqMsg(binstr=data)
    if log: log.log("received", req=req)
    w_value = None if req.null_val else req.w_value # w(key, None) is treated as remove
    key, value, version = 0, 0, 0
    op = req.op()

    if op == OP_RW:
        (status, key, value, version) = store.readwrite(r_key=req.r_key, r_version=req.r_version,
                                                     w_key=req.w_key, w_value=req.w_value)
    elif op == OP_R:
        (status, key, value, version) = store.read(key=req.r_key)
    elif op == OP_W:
        (status, key, value, version) = store.write(key=req.w_key, value=w_value)
    else:
        raise Exception("Received a message with empty read and write fields")

    updated = 1 if status == STATUS_OK and (op == OP_W or op == OP_RW) else 0

    resp = RespMsg(cl_id=req.cl_id, req_id=req.req_id, updated=updated,
            status=status, key=key, version=version, value=value)

    #print req, " => ", resp
    sock.sendto(resp.pack(), addr)
    if log: log.log("sent", res=resp)

if log: log.close()
