import argparse
import socket
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
parser.add_argument("store_host", type=str, help="store hostname")
parser.add_argument("store_port", type=int, help="store port")
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', args.port))

store_addr = (args.store_host, args.store_port)
store_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
store_sock.bind(('', 0))

value_cache = {}
version_cache = {}


while True:
    data, cl_addr = sock.recvfrom(REQMSG_SIZE)
    req = ReqMsg(binstr=data)

    if req.r_key != 0 and req.w_key != 0: # RW operation
        if req.r_key in version_cache.keys() and req.r_version != version_cache[req.r_key]:
            # Do an early reject:
            reject_msg = RespMsg(req_id=req.req_id, status=STATUS_REJECT)
            sock.sendto(reject_msg.pack(), cl_addr)
            continue
    elif req.r_key != 0:                  # R operation
        if req.r_key in value_cache.keys(): # check for cache hit
            resp = RespMsg(req_id=req.req_id, status=STATUS_OK,
                    key=req.r_key, value=value_cache[req.r_key], version=version_cache[req.r_key])
            sock.sendto(resp.pack(), cl_addr)
            continue

    # Otherwise, just forward packet:
    store_sock.sendto(data, store_addr)
    data2, fromaddr = store_sock.recvfrom(RESPMSG_SIZE)
    assert(fromaddr == store_addr)

    # Update our cache, if necessary:
    resp = RespMsg(binstr=data2)
    if resp.key != 0:
        value_cache[resp.key], version_cache[resp.key] = resp.value, resp.version

    # Finally, forward the response:
    sock.sendto(data2, cl_addr)
