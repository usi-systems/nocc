import argparse
import socket
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', 0))

req_id_seq = 0

def sendreq(req_id=None, r_key=0, r_version=0, w_key=0, w_value=''):
    global req_id_seq
    if req_id is None:
        req_id_seq += 1
        req_id = req_id_seq
    req = ReqMsg(req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value)
    sock.sendto(req.pack(), (args.host, args.port))
    data, fromaddr = sock.recvfrom(RESPMSG_SIZE)
    return RespMsg(binstr=data)


# Check that we can write multilpe value
for i in range(3):
    req_id_seq += 1
    req_id = req_id_seq
    value = str(unichr(97+i))
    resp = sendreq(req_id=req_id, w_key=i+1, w_value=value)
    assert(resp.status == STATUS_OK)
    assert(resp.req_id == req_id)
    assert(resp.key == i+1)
    assert(resp.version > 0)
    assert(resp.value[0] == value)

# Check that we can read those values
for i in range(3):
    req_id_seq += 1
    req_id = req_id_seq
    value = str(unichr(97+i))
    resp = sendreq(req_id=req_id, r_key=i+1)
    assert(resp.status == STATUS_OK)
    assert(resp.req_id == req_id)
    assert(resp.key == i+1)
    assert(resp.version > 0)
    assert(resp.value[0] == value)

# Try a good r/w
resp1 = sendreq(r_key=1)
resp2 = sendreq(r_key=1, r_version=resp1.version, w_key=1, w_value='x')
assert(resp1.status == STATUS_OK)
assert(resp2.version != resp1.version)
assert(resp2.value[0] == 'x')

# Try a bad r/w
resp = sendreq(r_key=1, r_version=9999, w_key=1, w_value='x')
assert(resp.status == STATUS_REJECT)

# Try inexistent key
resp = sendreq(r_key=999999)
assert(resp.status == STATUS_NOTFOUND)
