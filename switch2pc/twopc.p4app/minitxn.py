import struct

VALUE_SIZE = 64
KEY_SIZE = 4

MSG_TYPE_REQ = 1
MSG_TYPE_RES = 2

MSG_TYPE_PREPARE = 3
MSG_TYPE_VOTE = 4
MSG_TYPE_COMMIT = 5
MSG_TYPE_COMMITTED = 6

OP_TYPE_READ = 1
OP_TYPE_WRITE = 2
OP_TYPE_VALUE = 3
OP_TYPE_COMPARE = 4

STATUS_OK = 1
STATUS_ABORT = 2

msg_type_to_str = {MSG_TYPE_REQ: 'MSG_TYPE_REQ', MSG_TYPE_RES: 'MSG_TYPE_RES', MSG_TYPE_PREPARE: 'MSG_TYPE_PREPARE', MSG_TYPE_VOTE: 'MSG_TYPE_VOTE', MSG_TYPE_COMMIT: 'MSG_TYPE_COMMIT', MSG_TYPE_COMMITTED: 'MSG_TYPE_COMMITTED'}

hdr_fmt = '!B B I I B B B B'
op_fmt = 'B I %ds' % (VALUE_SIZE)

HDR_SIZE = struct.Struct(hdr_fmt).size
OP_SIZE = struct.Struct(op_fmt).size

TXN_MSG_MAX_SIZE = HDR_SIZE + 10*OP_SIZE

def writeSet(txn):
    for o in txn['ops'] if 'ops' in txn else []:
        if o[0] == OP_TYPE_WRITE: yield o

def readSet(txn):
    for o in txn['ops'] if 'ops' in txn else []:
        if o[0] == OP_TYPE_READ: yield o

def compareSet(txn):
    for o in txn['ops'] if 'ops' in txn else []:
        if o[0] == OP_TYPE_COMPARE: yield o

def valueSet(txn):
    for o in txn['ops'] if 'ops' in txn else []:
        if o[0] == OP_TYPE_VALUE: yield o

class MiniTxnParser:

    def __init__(self, cl_id=None):
        self.hdr_struct = struct.Struct(hdr_fmt)
        self.op_struct = struct.Struct(op_fmt)
        self.cl_id = cl_id

    def loads(self, data):
        msg_type, status, cl_id, txn_id, reset, op_cnt, participant_cnt, from_switch = self.hdr_struct.unpack(data[:HDR_SIZE])
        ops = []
        for ofst in range(HDR_SIZE, HDR_SIZE+(OP_SIZE*op_cnt), OP_SIZE):
            op_type, key, val = self.op_struct.unpack(data[ofst:ofst+OP_SIZE])
            ops.append((op_type, key, val))
        return dict(msg_type=msg_type, status=status, cl_id=cl_id, txn_id=txn_id,
                participant_cnt=participant_cnt, ops=ops, reset=reset, from_switch=from_switch)

    def dumps(self, txn):
        ops = txn['ops'] if 'ops' in txn else []
        status = txn['status'] if 'status' in txn else STATUS_OK
        participant_cnt = txn['participant_cnt'] if 'participant_cnt' in txn else 0
        reset = txn['reset'] if 'reset' in txn else 0
        from_switch = txn['from_switch'] if 'from_switch' in txn else 0
        assert self.cl_id is not None or 'cl_id' in txn
        cl_id = txn['cl_id'] if 'cl_id' in txn else self.cl_id
        data = self.hdr_struct.pack(txn['msg_type'], status, cl_id, txn['txn_id'],
                reset, len(ops), participant_cnt, from_switch)
        for op_type, key, val in ops:
            data += self.op_struct.pack(op_type, key, val)
        assert len(data) <= TXN_MSG_MAX_SIZE
        return data




if __name__ == '__main__':
    parser = MiniTxnParser()
    ops = [(OP_TYPE_READ, 0, '')]
    t1 = dict(msg_type=MSG_TYPE_REQ, status=STATUS_OK, cl_id=1, txn_id=2, ops=ops)

    d = parser.dumps(t1)
    t = parser.loads(d)

    assert t['msg_type'] == t1['msg_type']
    assert t['status'] == t1['status']
    assert t['cl_id'] == t1['cl_id']
    assert t['txn_id'] == t1['txn_id']
    assert len(t['ops']) == len(t1['ops'])
    assert t['ops'][0][0] == t1['ops'][0][0]
    assert t['ops'][0][1] == t1['ops'][0][1]
    assert t['ops'][0][2].rstrip('\0') == t1['ops'][0][2]

    ops = [(OP_TYPE_READ, 0, ''), (OP_TYPE_COMPARE, 1, 'a')]
    t2 = dict(msg_type=MSG_TYPE_REQ, status=STATUS_OK, cl_id=1, txn_id=2, ops=ops)
    d = parser.dumps(t2)
    t = parser.loads(d)
    assert len(t['ops']) == len(t2['ops'])
    assert t['ops'][0][1] == t2['ops'][0][1]
    assert t['ops'][1][1] == t2['ops'][1][1]
