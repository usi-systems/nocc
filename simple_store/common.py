import struct
import socket
import json
import time
import os
import threading

TYPE_REQ = 0
TYPE_RES = 1

STATUS_OK = 0
STATUS_ABORT = 1
STATUS_OPTIMISTIC_ABORT = 2

TXN_READ    = 0 # request: I would like to get the value of this obj
TXN_WRITE   = 1 # request: write this value to the object
TXN_VALUE   = 2 # response: this is the current value of the object
TXN_UPDATED = 3 # response: the value the object was just set to

txn_obj_type_to_string = {TXN_VALUE: 'V', TXN_READ: 'R', TXN_WRITE: 'W', TXN_UPDATED: 'U'}

VALUE_SIZE = 100

status_to_string = ['OK', 'ABORT', 'OPTIMISTIC_ABORT']

class BitFlags:

    def __init__(self, size=1, flags=[], value=0):
        self.size = size
        self.bits = size * 8
        self.flags = flags
        self.unpack(value)

    def pack(self): # XXX This probably won't work for anything bigger than a byte
        binary = (''.join(['1' if getattr(self, f) else '0' for f in self.flags])).ljust(self.bits, '0')
        self.value = int(binary, 2)
        return self.value

    def unpack(self, value=None):
        if not value is None: self.value = value
        binary = bin(self.value)[2:].rjust(self.bits, '0')
        for i, f in enumerate(self.flags):
            setattr(self, f, int(binary[i]))
        return self

    def __str__(self):
        return str(dict(self))

    def __iter__(self):
        for f in self.flags: yield f, getattr(self, f)


txnobj_fmt = '!B i %ds' % VALUE_SIZE
TXNOBJ_SIZE = struct.Struct(txnobj_fmt).size
MAX_TXNOBJ = 10

class TxnObj:

    def __init__(self, binstr=None, key=None, value='', t=None):
        if binstr is not None:
            self.unpack(binstr)
        else:
            assert(t in [TXN_VALUE, TXN_READ, TXN_WRITE, TXN_UPDATED])
            assert(type(key) is int)
            assert(type(value) is str)
            self.type, self.key, self.value = t, key, value

    def unpack(self, binstr):
        self.type, self.key, self.value = struct.unpack(txnobj_fmt, binstr)

    def pack(self):
        return struct.pack(txnobj_fmt, self.type, self.key, self.value)

    def __str__(self):
        return str(dict(self))

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        yield 't', txn_obj_type_to_string[self.type]
        yield 'k', self.key
        yield 'v', self.value.rstrip('\0')


txnmsg_fmt = '!B I i B B %ds' % (TXNOBJ_SIZE*MAX_TXNOBJ)
TXNMSG_SIZE = struct.Struct(txnmsg_fmt).size

class TxnMsg:
    flags = None
    cl_id = 0
    req_id = 0
    status = 0
    txn = []

    def __init__(self, binstr=None, req=False, res=False, replyto=None, cl_id=0, req_id=0, status=0, from_switch=0, txn=[]):
        self.flags = BitFlags(flags=['type', 'from_switch'])
        self.flags.from_switch = from_switch
        if binstr is not None:
            self.unpack(binstr)
        elif replyto is not None:
            self.flags.type = TYPE_REQ if replyto.flags.type == TYPE_RES else TYPE_RES
            self.cl_id, self.req_id, self.status, self.txn = replyto.cl_id, replyto.req_id, status, txn
        else:
            assert((req or res) and not (req and res))
            self.flags.type = TYPE_REQ if req else TYPE_RES
            self.cl_id, self.req_id, self.status, self.txn = cl_id, req_id, status, txn

    def unpack(self, binstr):
        flags_value, self.cl_id, self.req_id, self.status, txn_cnt, txn_binstr = struct.unpack(txnmsg_fmt, binstr)
        assert(txn_cnt <= MAX_TXNOBJ)
        self.flags.unpack(flags_value)
        self.txn = [TxnObj(binstr=txn_binstr[i:i+TXNOBJ_SIZE]) for i in xrange(0, txn_cnt*TXNOBJ_SIZE, TXNOBJ_SIZE)]

    def pack(self):
        txn_binstr = ''.join([txn.pack() for txn in self.txn])
        return struct.pack(txnmsg_fmt, self.flags.pack(), self.cl_id, self.req_id,
                self.status, len(self.txn), txn_binstr)

    def __str__(self):
        return "Txn%s(%s)" % ('Req' if self.flags.type == TYPE_REQ else 'Res', dict(self))

    def __iter__(self):
        if self.flags.type == TYPE_RES: yield 'status', status_to_string[self.status]
        if self.flags.from_switch: yield 'from_switch', self.flags.from_switch
        for f in ['cl_id', 'req_id', 'txn']:
            yield f, getattr(self, f)



class Store:
    values = {}
    sequences = {}
    seq = 0

    def _get(self, o=None, k=None, t=TXN_VALUE):
        assert(k or (o and o.key))
        return TxnObj(t=t, key=o.key if o else k,
                value=self.values[o.key if o else k])

    def applyTxn(self, txn=[]):
        r_ops = [o for o in txn if o.type == TXN_READ]
        w_ops = [o for o in txn if o.type == TXN_WRITE]

        # If it's a RW TXN, check that the reads are valid:
        if len(r_ops) > 0 and len(w_ops) > 0:
            bad_reads = [self._get(o=o) for o in r_ops if self.values[o.key] != o.value]
            if len(bad_reads) > 0:
                return (STATUS_ABORT, bad_reads)

        # Process all the write operations:
        if len(w_ops) > 0:
            for o in w_ops:
                self.seq += 1
                self.sequences[o.key] = self.seq
                self.values[o.key] = o.value
            return (STATUS_OK, [self._get(o=o, t=TXN_UPDATED) for o in w_ops])

        # Otherwise, this was simply a read TXN
        return (STATUS_OK, [self._get(o=o) for o in r_ops])

    def __str__(self):
        s = "key\tseq\tvalue\n"
        for key in self.values.keys():
            s += "%d\t%d\t%s\n" % (key, self.sequences[key], self.values[key].rstrip('\0'))
        return s

class StoreClient:

    def __init__(self, store_addr=None, logger=None, log_filename=None, cl_id=None):
        self.store_addr = store_addr
        self.recv_queue = {}
        self.req_id_seq = 0
        self.closed = True
        self.cl_id = cl_id
        self.log = logger
        self.log_filename = log_filename

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10.0)
        self.sock.bind(('', 0))
        self.cl_addr = self.sock.getsockname()
        self.cl_name = ':'.join(map(str, self.cl_addr))
        if not self.cl_id:
            self.cl_id = abs(hash(self.cl_name)) % 2**32
        if self.log_filename: self.log = GotthardLogger(self.log_filename)
        self.closed = False
        return self

    def __enter__(self):
        if self.closed: return self.open()

    def close(self):
        if self.closed: return
        self.sock.close()
        if self.log: self.log.close()
        self.closed = True

    def _log(self, *args, **kwargs):
        if self.log: self.log.log(*args, **kwargs)

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def req(self, txn, req_id=None):
        req = self.buildreq(req_id=req_id, txn=txn)
        self.sendreq(req)
        return self.recvres(req_id=req.req_id)

    def reqAsync(self, txn, req_id=None):
        req = self.buildreq(req_id=req_id, txn=txn)
        self.sendreq(req)
        return req.req_id

    def buildreq(self, req_id=None, txn=None):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq
        if type(txn) != list: txn = [txn]
        req = TxnMsg(req=True, cl_id=self.cl_id, req_id=req_id, txn=txn)
        return req

    def sendreq(self, req):
        req_data = req.pack()
        self.sock.sendto(req_data, self.store_addr)
        self._log("sent", req=req)

    def recvres(self, req_id=None):
        if not req_id is None and req_id in self.recv_queue:
            res = self.recv_queue[req_id]
            del self.recv_queue[req_id]
            return res
        while True:
            data, fromaddr = self.sock.recvfrom(TXNMSG_SIZE)
            assert(fromaddr == self.store_addr)
            res = TxnMsg(binstr=data)
            self._log("received", res=res)
            if not req_id is None:
                if req_id != res.req_id:
                    self.recv_queue[res.req_id] = res
                    continue
            return res

    @staticmethod
    def w(key, val):
        return TxnObj(t=TXN_WRITE, key=key, value=val)

    @staticmethod
    def r(key, val=''):
        return TxnObj(t=TXN_READ, key=key, value=val)


class GotthardLogger:
    def __init__(self, filename, stdout=False):
        self.logfile = os.fdopen(os.open(filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a')
        self.closed = threading.Event()
        self.stdout = stdout
        self.last_log = 0

        def heartbeat():
            while not self.closed.wait(1):
                if time.time() - self.last_log > 5: self.log("heartbeat")
                self.logfile.flush()
        t = threading.Thread(target=heartbeat)
        t.daemon = False
        t.start()

    def log(self, event, req=None, res=None):
        self.last_log = time.time()
        l = dict(time=self.last_log, event=event)
        if req: l['req'] = dict(req)
        if res: l['res'] = dict(res)
        line = json.dumps(l, default=lambda x: dict(x), sort_keys=True)
        if self.stdout:
            print line
        self.logfile.write(line + "\n")

    def close(self):
        if self.closed.isSet(): return
        self.closed.set()
        self.logfile.flush()
        self.logfile.close()

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.closed.isSet():
            self.close()
