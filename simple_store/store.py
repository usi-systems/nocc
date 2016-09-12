import argparse
import socket
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store = Store()

while True:
    data, addr = sock.recvfrom(REQMSG_SIZE)
    req = ReqMsg(binstr=data)
    key, value, version = 0, 0, 0
    op = req.op()

    if op == OP_RW:
        (status, key, value, version) = store.readwrite(r_key=req.r_key, r_version=req.r_version,
                                                     w_key=req.w_key, w_value=req.w_value)
    elif op == OP_R:
        (status, key, value, version) = store.read(key=req.r_key)
    elif op == OP_W:
        value = None if req.rm else req.w_value # w(key, None) is treated as remove
        (status, key, value, version) = store.write(key=req.w_key, value=value)
    else:
        raise Exception("Received a message with empty read and write fields")

    resp = RespMsg(cl_id=req.cl_id, req_id=req.req_id, status=status, key=key, version=version, value=value)

    print req, " => ", resp
    sock.sendto(resp.pack(), addr)
