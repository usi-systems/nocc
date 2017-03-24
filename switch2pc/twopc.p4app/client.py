import socket

from minitxn import *
from minitxn import MiniTxnParser
from minitxn import writeSet, readSet, compareSet, valueSet

class Client:

    def __init__(self, server_addr=('127.0.0.1', 9000), bind_addr=('', 0), cl_id=None, logger=None):
        self.server_addr = server_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(bind_addr)
        self.sock.settimeout(10)
        self.logger = logger
        self.cl_addr = self.sock.getsockname()
        self.cl_name = ':'.join(map(str, self.cl_addr))
        self.parser = MiniTxnParser()

        self.recv_queue = {}

        self.cl_id = cl_id
        if self.cl_id is None:
            self.cl_id = abs(hash(self.cl_name)) % 2**32

        self.last_txn_id = 0
        self.cache = {}

    def connect(self, other):
        self.server_addr = other.addr()
        return other

    def Txn(self, *ops):
        return dict(msg_type=MSG_TYPE_REQ, ops=ops)

    def R(self, key):
        return (OP_TYPE_READ, key, '')

    def W(self, key, value):
        return (OP_TYPE_WRITE, key, value)

    def C(self, key, value=None):
        return (OP_TYPE_COMPARE, key, value)

    def prepareTxn(self, txn, reset=False):
        txn['reset'] = 1 if reset else 0

        if 'msg_type' not in txn: txn['msg_type'] = MSG_TYPE_REQ
        if 'ops' not in txn: txn['ops'] = []

        def opMapper((t, k, v)):
            if t == OP_TYPE_COMPARE and v is None and k in self.cache:
                v = self.cache[k]
            return (t, k, '' if v is None else v)

        txn['ops'] = map(opMapper, txn['ops'])

        if 'cl_id' not in txn:
            txn['cl_id'] = self.cl_id
        if 'txn_id' not in txn:
            self.last_txn_id += 1
            txn['txn_id'] = self.last_txn_id
        self.last_txn_id = txn['txn_id']

    def issue(self, txn=dict(), clear=False, reset=False):
        self.prepareTxn(txn, reset=reset)
        txn_res = self.send(txn)

        if txn_res['status'] == STATUS_OK:
            for _, key, value in writeSet(txn):
                self.cache[key] = value

        for _, key, value in valueSet(txn_res):
            self.cache[key] = value

        return txn_res

    def send(self, txn_req, blocking=True):
        if self.logger: self.logger.log(req=txn_req)
        self.sock.sendto(self.parser.dumps(txn_req), self.server_addr)
        if blocking:
            return self.recv(txn_id=txn_req['txn_id'])

    def recv(self, txn_id=None):
        while True:
            data, addr = self.sock.recvfrom(TXN_MSG_MAX_SIZE)
            txn_res = self.parser.loads(data)
            if self.logger: self.logger.log(res=txn_res)
            if txn_id is None or txn_id == txn_res['txn_id']:
                return txn_res

            self.recv_queue[txn_res['txn_id']] = txn_res
