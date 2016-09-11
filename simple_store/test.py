import argparse
import socket
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

# Check that we can write multilpe value
for i in range(3):
    cl.req_id_seq += 1
    req_id = cl.req_id_seq
    value = str(unichr(97+i))
    resp = cl.req(req_id=req_id, w_key=i+1, w_value=value)
    assert(resp.status == STATUS_OK)
    assert(resp.req_id == req_id)
    assert(resp.key == i+1)
    assert(resp.version > 0)
    assert(resp.value[0] == value)

# Check that we can read those values
for i in range(3):
    cl.req_id_seq += 1
    req_id = cl.req_id_seq
    value = str(unichr(97+i))
    resp = cl.req(req_id=req_id, r_key=i+1)
    assert(resp.status == STATUS_OK)
    assert(resp.req_id == req_id)
    assert(resp.key == i+1)
    assert(resp.version > 0)
    assert(resp.value[0] == value)

# Try a good r/w
resp1 = cl.req(r_key=1)
resp2 = cl.req(r_key=1, r_version=resp1.version, w_key=1, w_value='x')
assert(resp1.status == STATUS_OK)
assert(resp2.version != resp1.version)
assert(resp2.value[0] == 'x')

# Try a bad r/w
resp = cl.req(r_key=1, r_version=9999, w_key=1, w_value='x')
assert(resp.status == STATUS_REJECT)

# Try inexistent key
resp = cl.req(r_key=999999)
assert(resp.status == STATUS_NOTFOUND)
