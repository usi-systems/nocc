#!/usr/bin/env python2
import argparse
import sys
sys.path.insert(0, '..')
from pygotthard import *

# XXX when running this test, make sure the delta between switch-server is a
# lot bigger than the client-switch delta. Try these values:
# ./software_switch.py -p 9991 -d 0.001 -D 0.005 -m read_cache 127.0.0.1 9999

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

with GotthardClient(store_addr=(args.host, args.port), log_filename=args.log) as cl:

    # Before we start, ensure cache is empty
    res = cl.reset()
    assert res.status == STATUS_OK

    # Initially, key 1 should not be in cache
    res = cl.req(R(1))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 0, "key 1 should not be cached"
    assert res.op(k=1).value.rstrip('\0') == ''

    # After the first read, key 1 should be cached
    res = cl.req(R(1))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 1, "key 1 should be cached"
    assert res.op(k=1).value.rstrip('\0') == ''

    # Key should be brought in after a write
    res = cl.req(W(2, 'b'))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 0, "store should handle write"
    assert res.op(k=2).value.rstrip('\0') == 'b'
    res = cl.req(R(2))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 1, "key 2 should be cached"
    assert res.op(k=2).value.rstrip('\0') =='b'

    # Key should be updated
    res = cl.req(W(2, 'bb'))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 0, "store should handle write"
    assert res.op(k=2).value.rstrip('\0') == 'bb'
    res = cl.req(R(2))
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 1, "key 2 should be cached"
    assert res.op(k=2).value.rstrip('\0') =='bb'

    # Cache should only be updated by store response
    # send two reqs in rapid succession. The second should get the old cached value
    t1_id, t2_id = cl.reqAsync(W(2, 'newer')), cl.reqAsync(R(2))
    res1, res2 = cl.recvres(t1_id), cl.recvres(t2_id)
    assert res1.status == STATUS_OK
    assert res1.flags.from_switch == 0, "store should handle write"
    assert res1.op(k=2).value.rstrip('\0') == 'newer', "should update store"
    assert res2.status == STATUS_OK
    assert res2.flags.from_switch == 1, "store should satisfy read"
    assert res2.op(k=2).value.rstrip('\0') == 'bb'
    res = cl.req(R(2)) # after, the switch should have the up-to-date value
    assert res.status == STATUS_OK
    assert res.flags.from_switch == 1, "key 2 should be cached"
    assert res.op(k=2).value.rstrip('\0') == 'newer', "should be latest value"


    # Cleanup: send reset flag to store
    res = cl.reset()
    assert res.status == STATUS_OK
