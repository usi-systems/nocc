import sys
sys.path.insert(0, '..')

from switch2pc.minitxn import *
from switch2pc.client import Client
from switch2pc.participant import Participant
from switch2pc.coordinator import Coordinator

def getOp(key, txn):
    ops = filter(lambda op: op[1] == key, txn['ops'])
    return ops[0] if len(ops) > 0 else None

def stripValues(txn):
    txn['ops'] = map(lambda (t, k, v): (t, k, v.rstrip('\0')), txn['ops'])

co = Coordinator()
participants = []
participants.append(Participant(bind_addr=('', 8000), thread_count=3))
participants.append(Participant(bind_addr=('', 8001), thread_count=1))
for p in participants: co.connectParticipant(p)

co.start()
for p in participants: p.start()


cl = Client()
R, W, C, Txn = cl.R, cl.W, cl.C, cl.Txn

res = cl.issue(reset=True)

t2 = Txn(R(1))
res = cl.issue(t2)
assert res['msg_type'] == MSG_TYPE_RES
assert res['status'] == STATUS_OK
assert res['cl_id'] == t2['cl_id']
assert res['txn_id'] == t2['txn_id']
assert len(res['ops']) == 1
assert res['participant_cnt'] == 1
assert res['ops'][0][0] == OP_TYPE_VALUE
assert res['ops'][0][1] == 1
assert res['ops'][0][2].rstrip('\0') == ''

t3 = Txn(W(1, 'a'), W(2, 'b'), W(3, 'c'), W(4, 'd'), W(5, 'e'))
res = cl.issue(t3)
assert res['status'] == STATUS_OK
assert len(res['ops']) == 0
assert res['participant_cnt'] > 1

t4 = Txn(R(1), R(2), R(3), R(4), R(5))
res = cl.issue(t4)
assert res['status'] == STATUS_OK
assert res['participant_cnt'] > 1
assert len(res['ops']) == 5
stripValues(res)
for key in range(1, 6):
    assert getOp(key, t3)[2] == getOp(key, res)[2]

# Find the keys stored on each participant
node_keys = {}
for k in range(1, 6):
    node = co.hashring.get_node(k)
    if node not in node_keys: node_keys[node] = []
    node_keys[node].append(k)

# Keys on different participants
k1, k2 = node_keys.values()[0][0], node_keys.values()[1][0]

# Good compare should not abort
t5 = Txn(C(k1), W(k2, 'updated'))
res = cl.issue(t5)
assert res['status'] == STATUS_OK

# Bad compare should abort
t6 = Txn(C(k1, 'wrong'), W(k2, 'notwritten'))
res = cl.issue(t6)
assert res['status'] == STATUS_ABORT
assert res['participant_cnt'] == 2

# Check that the aborted TXN didn't do an update
t7 = Txn(R(k2))
res = cl.issue(t7)
stripValues(res)
assert getOp(k2, res)[2] == getOp(k2, t5)[2]

co.stop()
for p in participants: p.stop()
