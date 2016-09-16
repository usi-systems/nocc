#!/usr/bin/env python2

# This tests that the switch is doing optimistic aborts

# XXX when running this test, make sure the delta between switch-server is a
# lot bigger than the client-switch delta. Try these values:
# ./software_switch.py -p 9991 -d 0.01 -D 0.5 -m optimistic_abort 127.0.0.1 9999

import argparse
from time import sleep
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

cl1 = StoreClient(store_addr=(args.host, args.port))
cl1.cl_id = 1
cl2 = StoreClient(store_addr=(args.host, args.port))
cl2.cl_id = 2

# Populate the store with one key:
resp = cl1.req(w_key=1, w_value='a')
assert(resp.status == STATUS_OK)

# Issue T1:
cl1.reqAsync(r_key=1, r_value='a', w_key=1, w_value='b')
# Issue T2 before T1 commits:
cl2.reqAsync(r_key=1, r_value='a', w_key=1, w_value='b')

resp1, resp2 = cl1.recvresp(), cl2.recvresp()

assert(resp1.status == STATUS_OK) # T1 should have succeeded
assert(resp2.status == STATUS_OPTIMISTIC_ABORT) # T2 not
assert(resp2.key == 1)
assert(resp2.value.rstrip('\0') == 'b')

# Use the value in the ABORT msg to make another request:
cl1.reqAsync(r_key=1, r_value='b', w_key=1, w_value='c') # T1
t2resp1 = cl2.req(r_key=1, r_value='b', w_key=1, w_value='c') # T2
assert(t2resp1.status == STATUS_OPTIMISTIC_ABORT)

t2resp2 = cl2.req(r_key=1, r_value=t2resp1.value, w_key=1, w_value='d') # T2'
assert(t2resp2.status == STATUS_OK)
assert(t2resp2.value.rstrip('\0') == 'd')

t1resp = cl1.recvresp()
assert(t1resp.status == STATUS_OK)
assert(t1resp.value.rstrip('\0') == 'c')

# Try three RW while the first TXN is still in flight:
cl1.reqAsync(w_key=1, w_value='a') # T1
sleep(0.005)
cl2.reqAsync(r_key=1, r_value='a', w_key=1, w_value='b') # T2
sleep(0.005)
cl2.reqAsync(r_key=1, r_value='b', w_key=1, w_value='c') # T3
sleep(0.005)
cl2.reqAsync(r_key=1, r_value='c', w_key=1, w_value='d') # T4

t1resp = cl1.recvresp()
t2resp, t3resp, t4resp = cl2.recvresp(), cl2.recvresp(), cl2.recvresp()
assert(t1resp.status == STATUS_OK)
assert(t1resp.value.rstrip('\0') == 'a')
assert(t2resp.status == STATUS_OK)
assert(t2resp.value.rstrip('\0') == 'b')
assert(t3resp.status == STATUS_OK)
assert(t3resp.value.rstrip('\0') == 'c')
assert(t4resp.status == STATUS_OK)
assert(t4resp.value.rstrip('\0') == 'd')

# cleanup
resp = cl1.req(w_key=1, w_value='')
assert(resp.status == STATUS_OK)
