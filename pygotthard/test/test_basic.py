#!/usr/bin/env python2
import argparse
import sys
sys.path.insert(0, '..')
from pygotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

with GotthardClient(store_addr=(args.host, args.port), log_filename=args.log) as cl:

    # Check that we can write multilpe values
    for i in range(3):
        cl.req_id_seq += 1
        req_id = cl.req_id_seq
        value = str(unichr(97+i))
        res = cl.req(W(i+1, value), req_id=req_id)
        assert(res.flags.type == TYPE_RES)
        assert(res.status == STATUS_OK)
        assert(res.cl_id == cl.cl_id)
        assert(res.req_id == req_id)
        assert(len(res.ops) == 1)
        assert(res.ops[0].key == i+1)
        assert(res.ops[0].type == TXN_UPDATED)
        assert(res.ops[0].value[0] == value)

    # Check that we can read those values
    for i in range(3):
        cl.req_id_seq += 1
        req_id = cl.req_id_seq
        value = str(unichr(97+i))
        res = cl.req(R(i+1), req_id=req_id)
        assert(res.flags.type == TYPE_RES)
        assert(res.status == STATUS_OK)
        assert(res.cl_id == cl.cl_id)
        assert(res.req_id == req_id)
        assert(len(res.ops) == 1)
        assert(res.ops[0].key == i+1)
        assert(res.ops[0].type == TXN_VALUE)
        assert(res.ops[0].value[0] == value)

    # Try reading multiple values
    res = cl.req([R(1), R(2)])
    assert(res.status == STATUS_OK)
    assert(len(res.ops) == 2)
    assert(res.op(k=1).key == 1)
    assert(res.op(k=1).type == TXN_VALUE)
    assert(res.op(k=1).value.rstrip('\0') == 'a')
    assert(res.op(k=2).key == 2)
    assert(res.op(k=2).type == TXN_VALUE)
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # Try writing multiple values
    res = cl.req([W(4, 'hello'), W(5, 'world')])
    assert(res.status == STATUS_OK)
    assert(len(res.ops) == 2)
    assert(res.op(k=4).type == TXN_UPDATED)
    assert(res.op(k=4).value.rstrip('\0') == 'hello')
    assert(res.op(k=5).type == TXN_UPDATED)
    assert(res.op(k=5).value.rstrip('\0') == 'world')

    # Try a single RB
    res = cl.req(RB(1, 'a'))
    assert(res.status == STATUS_OK)

    # Try a good r/w
    res1 = cl.req(R(1))
    assert(res1.status == STATUS_OK)
    res2 = cl.req([RB(1, res1.ops[0].value), W(1, 'x')])
    assert(len(res2.ops) == 1)
    assert(res2.ops[0].type == TXN_UPDATED)
    assert(res2.ops[0].value[0] == 'x')

    # Try a bad r/w
    res = cl.req([RB(1, 'notthesame'), W(1, 'x')])
    assert(res.status == STATUS_ABORT)
    assert(len(res.ops) == 1)
    assert(res.ops[0].type == TXN_VALUE)
    assert(res.ops[0].value == res2.ops[0].value)

    # Try writing multiple values
    res = cl.req([W(1, 'a'), W(2, 'b')])
    assert(res.status == STATUS_OK)
    assert(len(res.ops) == 2)
    assert(res.op(k=1).key == 1)
    assert(res.op(k=1).type == TXN_UPDATED)
    assert(res.op(k=1).value.rstrip('\0') == 'a')
    assert(res.op(k=2).key == 2)
    assert(res.op(k=2).type == TXN_UPDATED)
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # Try a good RW with multiple reads
    res = cl.req([RB(1, 'a'), RB(2, 'b'), W(3, 'zzz')])
    assert(res.status == STATUS_OK)
    assert(len(res.ops) == 1)
    assert(res.ops[0].key == 3)
    assert(res.ops[0].type == TXN_UPDATED)
    assert(res.ops[0].value.rstrip('\0') == 'zzz')

    # Try a good RW with multiple writes
    res = cl.req([RB(1, 'a'), RB(2, 'b'), W(3, 'c'), W(4, 'd')])
    assert(res.status == STATUS_OK)
    assert(len(res.ops) == 2)
    assert(res.op(k=3).key == 3)
    assert(res.op(k=3).type == TXN_UPDATED)
    assert(res.op(k=3).value.rstrip('\0') == 'c')
    assert(res.op(k=4).key == 4)
    assert(res.op(k=4).type == TXN_UPDATED)
    assert(res.op(k=4).value.rstrip('\0') == 'd')

    # Try a bad RW with multiple reads
    res = cl.req([RB(1, 'a'), RB(2, 'wrong'), W(3, 'x')])
    assert(res.status == STATUS_ABORT)
    assert(len(res.ops) > 0)
    assert(res.op(k=2).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # Try a bad RW with multiple bad reads
    res = cl.req([RB(1, 'wrong'), RB(2, 'wrong'), W(3, 'x')])
    assert(res.status == STATUS_ABORT)
    assert(len(res.ops) > 1)
    assert(res.op(k=1).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=1).value.rstrip('\0') == 'a')
    assert(res.op(k=2).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=2).value.rstrip('\0') == 'b')

    # Send some null operations
    res = cl.req([TxnOp(t=TXN_NOP, key=0), TxnOp(t=TXN_NOP, key=0)])
    assert(res.status == STATUS_BADREQ)

    # Access a 20-bit key
    res = cl.req(W(2**20, '20bits'))
    assert(res.status == STATUS_OK)
    res = cl.req(R(2**20))
    assert(res.op(k=2**20).value.rstrip('\0') == '20bits')
    assert(cl.req(W(2**20, '')).status == STATUS_OK)

    # Try the biggest frag size
    ops = [W(i+1, 'hi') for i in xrange(GOTTHARD_MAX_OP)]
    res = cl.req(ops)
    assert res.status == STATUS_OK
    assert len(res.ops) == GOTTHARD_MAX_OP
    assert set([o.value.rstrip('\0') for o in res.ops]) == set(('hi',))

    # Try 1.5x the biggest frag size
    op_cnt = int(GOTTHARD_MAX_OP * 1.5)
    ops = [W(i+1, 'hi') for i in xrange(op_cnt)]
    res = cl.req(ops)
    assert res.status == STATUS_OK
    assert len(res.ops) == op_cnt
    assert set([o.value.rstrip('\0') for o in res.ops]) == set(('hi',))

    # Try 2x the biggest frag size
    op_cnt = int(GOTTHARD_MAX_OP * 2)
    ops = [W(i+1, 'hi') for i in xrange(op_cnt)]
    res = cl.req(ops)
    assert res.status == STATUS_OK
    assert len(res.ops) == op_cnt
    assert set([o.value.rstrip('\0') for o in res.ops]) == set(('hi',))

    # Receive an abort for the first fragmented msg
    ops = [RB(1, 'garbage')] + [R(i+1) for i in xrange(GOTTHARD_MAX_OP)]
    res = cl.req(ops)
    assert(res.op(k=1).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=1).value.rstrip('\0') == 'hi')

    # Receive an abort for a middle fragmented msg
    ops = [R(i+1) for i in xrange(GOTTHARD_MAX_OP)] + [RB(1, 'garbage')] + [R(i+1) for i in xrange(GOTTHARD_MAX_OP)]
    res = cl.req(ops)
    assert(res.op(k=1).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=1).value.rstrip('\0') == 'hi')

    # Receive an abort for the last fragmented msg
    ops = [R(i+1) for i in xrange(GOTTHARD_MAX_OP)] + [RB(1, 'garbage')]
    res = cl.req(ops)
    assert(res.op(k=1).type == TXN_VALUE) # should contain correct value
    assert(res.op(k=1).value.rstrip('\0') == 'hi')

    # R and W in a single transaction
    res = cl.req([R(1), W(2, 'b')])
    assert res.status == STATUS_OK
    assert res.op(k=1).type == TXN_VALUE
    assert res.op(k=2).type == TXN_UPDATED

    # Assert a null value
    res = cl.req([RB(12345, '')])
    assert res.status == STATUS_OK, "Empty object should be null"


    # Cleanup: send reset flag to store
    res = cl.reset()
    assert res.status == STATUS_OK
    assert len(res.ops) == 0
    res = cl.req(R(1))
    assert res.status == STATUS_OK
    assert res.op(k=1).value.rstrip('\0') == ''
