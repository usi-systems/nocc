#!/usr/bin/env python2

# This tests that the switch is forwarding/shortcutting correctly

import argparse
from time import sleep
from gotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

r, w = StoreClient.r, StoreClient.w

with StoreClient(store_addr=(args.host, args.port), log_filename=args.log) as cl:

    # Populate the store with two keys:
    res = cl.req([w(1, 'a'), w(2, 'b')])
    assert(res.status == STATUS_OK)
    assert(res.flags.from_switch == 0) # should not have originated at the switch, but store
    assert(len(res.ops) == 2)
    assert(res.op(k=1).value.rstrip('\0') == 'a')
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # Switch should return cached key:
    res = cl.req(r(1))
    assert(res.status == STATUS_OK)
    assert(res.flags.from_switch == 1) # should be cached on switch
    assert(res.ops[0].key == 1)
    assert(res.ops[0].value.rstrip('\0') == 'a')

    # Switch should abort bad RW transaction
    res = cl.req([r(1, 'somethingelse'), w(1, 'x')])
    assert(res.status == STATUS_ABORT)
    assert(res.flags.from_switch == 1) # switch should do the abort
    assert(res.ops[0].key == 1) # and tell us current key state
    assert(res.ops[0].value.rstrip('\0') == 'a')

    # Concurrent requests; should only work for Optimistic Abort enabled switches
    t1_id = cl.reqAsync([r(1, 'a'), w(1, 'b')]) # T1
    sleep(0.001)
    t2_id = cl.reqAsync([r(1, 'b'), w(1, 'c')]) # T2
    t1res, t2res = cl.recvres(req_id=t1_id), cl.recvres(req_id=t2_id)
    assert(t1res.status == STATUS_OK)
    assert(t2res.status == STATUS_ABORT) # opti abort would accept this; early abort only should not

    # Try a bad RB to get their values from cache
    res = cl.req([r(1, 'wrong'), r(2, 'wrong')])
    assert(res.status == STATUS_ABORT)
    assert(res.flags.from_switch == 1) # should be cached on switch
    assert(len(res.ops) == 2)
    assert(res.op(k=1).value.rstrip('\0') == 'b')
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # cleanup
    for k in xrange(1, 3):
        res = cl.req(w(k, ''))
        assert(res.status == STATUS_OK)
