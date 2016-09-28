#!/usr/bin/env python2

# This tests that the switch is doing optimistic aborts

# XXX when running this test, make sure the delta between switch-server is a
# lot bigger than the client-switch delta. Try these values:
# ./software_switch.py -p 9991 -d 0.01 -D 0.5 -m optimistic_abort 127.0.0.1 9999

import argparse
from time import sleep
from gotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

r, w = StoreClient.r, StoreClient.w

logger = GotthardLogger(args.log, stdout=False) if args.log else None

with StoreClient(store_addr=(args.host, args.port), logger=logger, cl_id=1) as cl1, StoreClient(store_addr=(args.host, args.port), logger=logger, cl_id=2) as cl2:

    # Populate the store with one key:
    res = cl1.req(w(1, 'a'))
    assert(res.status == STATUS_OK)

    # Issue T1:
    cl1.reqAsync([r(1, 'a'), w(1, 'b')])
    # Issue T2 before T1 commits:
    cl2.reqAsync([r(1, 'a'), w(1, 'b')])

    res1, res2 = cl1.recvres(), cl2.recvres()

    assert(res1.status == STATUS_OK) # T1 should have succeeded
    assert(res2.status == STATUS_OPTIMISTIC_ABORT) # T2 not
    assert(res1.flags.from_switch == 0) # store should have commited it
    assert(res2.flags.from_switch == 1) # should be aborted by switch
    assert(res2.ops[0].key == 1)
    assert(res2.ops[0].value.rstrip('\0') == 'b')

    # Use the value in the ABORT msg to make another request:
    cl1.reqAsync([r(1, 'b'), w(1, 'c')]) # T1
    t2res1 = cl2.req([r(1, 'b'), w(1, 'c')]) # T2
    assert(t2res1.status == STATUS_OPTIMISTIC_ABORT)
    assert(t2res1.flags.from_switch == 1) # should be aborted by switch
    assert(t2res1.ops[0].type == TXN_VALUE) # the optimistic value
    assert(t2res1.ops[0].value.rstrip('\0') == 'c')

    cl2.reqAsync([r(1, t2res1.ops[0].value), w(1, 'd')]) # T2'

    t1res = cl1.recvres() # In the meantime, T1 should have succeeded
    assert(t1res.status == STATUS_OK)
    assert(t1res.ops[0].value.rstrip('\0') == 'c')

    t2res2 = cl2.recvres()
    assert(t2res2.status == STATUS_OK)
    assert(t2res2.ops[0].value.rstrip('\0') == 'd')


    # Try three RW while the first TXN is still in flight:
    cl1.reqAsync(w(1, 'a')) # T1
    sleep(0.005)
    cl2.reqAsync([r(1, 'a'), w(1, 'b')]) # T2
    sleep(0.005)
    cl2.reqAsync([r(1, 'b'), w(1, 'c')]) # T3
    sleep(0.005)
    cl2.reqAsync([r(1, 'c'), w(1, 'd')]) # T4

    t1res = cl1.recvres()
    t2res, t3res, t4res = cl2.recvres(), cl2.recvres(), cl2.recvres()
    assert(t1res.status == STATUS_OK)
    assert(t1res.ops[0].value.rstrip('\0') == 'a')
    assert(t2res.status == STATUS_OK)
    assert(t2res.ops[0].value.rstrip('\0') == 'b')
    assert(t3res.status == STATUS_OK)
    assert(t3res.ops[0].value.rstrip('\0') == 'c')
    assert(t4res.status == STATUS_OK)
    assert(t4res.ops[0].value.rstrip('\0') == 'd')

    # Should be able to perform an optimistic R
    cl1.reqAsync(w(1, 'opti')) # T1
    sleep(0.001)
    t2res = cl2.req(r(1, 'garbage')) # T2
    t1res = cl1.recvres()
    assert(t2res.status == STATUS_OPTIMISTIC_ABORT)
    assert(len(t2res.ops) == 1)
    assert(t2res.op(k=1).value.rstrip('\0') == 'opti') # early abort would return the old value


    # cleanup
    res = cl1.req(w(1, ''))
    assert(res.status == STATUS_OK)
