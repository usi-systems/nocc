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

    if req.r_key != 0 and req.w_key != 0:
        key = req.w_key
        (status, value, version) = store.readwrite(r_key=req.r_key, r_version=req.r_version,
                                                     w_key=req.w_key, w_value=req.w_value)
    elif req.r_key != 0:
        key = req.r_key
        (status, value, version) = store.read(key=req.r_key)
    elif req.w_key != 0:
        key = req.w_key
        (status, value, version) = store.write(key=req.w_key, value=req.w_value)
    else:
        raise Exception("Received a message with empty read and write fields")

    resp = RespMsg(req_id=req.req_id, status=status, key=key, version=version, value=value)

    print req, " => ", resp
    sock.sendto(resp.pack(), addr)
