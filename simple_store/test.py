#!/usr/bin/env python2
import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port), log_filename=args.log)

# Check that we can write multilpe value
for i in range(3):
    cl.req_id_seq += 1
    req_id = cl.req_id_seq
    value = str(unichr(97+i))
    resp = cl.req(req_id=req_id, w_key=i+1, w_value=value)
    assert(resp.type == TYPE_RES)
    assert(resp.status == STATUS_OK)
    assert(resp.req_id == req_id)
    assert(resp.key == i+1)
    assert(resp.updated == 1)
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
    assert(resp.updated == 0)
    assert(resp.value[0] == value)

# Try a good r/w
resp1 = cl.req(r_key=1)
resp2 = cl.req(r_key=1, r_value=resp1.value, w_key=1, w_value='x')
assert(resp1.status == STATUS_OK)
assert(resp2.updated == 1)
assert(resp2.value[0] == 'x')

# Try a bad r/w
resp = cl.req(r_key=1, r_value='notthesame', w_key=1, w_value='x')
assert(resp.status == STATUS_ABORT)
assert(resp.updated == 0)
assert(resp.type == TYPE_RES)

# Write null to the keys
for i in range(3):
    resp1 = cl.req(w_key=i+1, w_value='')
    assert(resp1.status == STATUS_OK)
    assert(resp1.key == i+1)
    assert(resp1.value.rstrip('\0') == '')
    resp2 = cl.req(r_key=i+1)
    assert(resp2.status == STATUS_OK)
    assert(resp2.value.rstrip('\0') == '')
