import struct
import math
import socket
import json
import time
import os
import threading
from base64 import b64encode
import pickle

GOTTHARD_MAX_OP = 7

TYPE_REQ = 0
TYPE_RES = 1

STATUS_OK = 0
STATUS_ABORT = 1
STATUS_OPTIMISTIC_ABORT = 2
STATUS_BADREQ = 3

TXN_NOP     = 0
TXN_READ    = 1 # request: I would like to get the value of this obj
TXN_WRITE   = 2 # request: write this value to the object
TXN_VALUE   = 3 # fact: this is what (I think) the value is
TXN_UPDATED = 4 # response: the object was just updated to this value


txn_op_type_to_string = {TXN_NOP: 'N', TXN_VALUE: 'V', TXN_READ: 'R', TXN_WRITE: 'W', TXN_UPDATED: 'U'}

MIN_INTER_MSG_SEND_WAIT = 0.000050
MAX_INTER_MSG_SEND_WAIT = 0.000400

VALUE_SIZE = 16
NULL_VALUE = '\0'*VALUE_SIZE

status_to_string = ['OK', 'ABORT', 'OPTIMISTIC_ABORT', 'STATUS_BADREQ']


class GotthardAbortException(Exception):
    def __init__(self, from_switch=None, optimistic=None):
        super(GotthardAbortException, self).__init__('')
        self.from_switch, self.optimistic = from_switch, optimistic

    def __str__(self):
        return "Gotthard%sAbortFrom%s" % ('Optimistic' if self.optimistic else '',
                                        'Switch' if self.from_switch else 'Store')

def printable(s):
    return len(s)+2 == len(repr(s))


# TODO: use this instead: http://stackoverflow.com/questions/142812/does-python-have-a-bitfield-type
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


txnop_fmt = '!B I %ds' % VALUE_SIZE
TXNOP_SIZE = struct.Struct(txnop_fmt).size

class TxnOp:

    def __init__(self, binstr=None, key=None, value='', t=None):
        if binstr is not None:
            self.unpack(binstr)
        else:
            assert(t in [TXN_NOP, TXN_VALUE, TXN_READ, TXN_WRITE, TXN_UPDATED])
            assert(type(key) is int)
            assert(type(value) is str)
            self.type, self.key, self.value = t, key, value.ljust(VALUE_SIZE, '\0')

    def unpack(self, binstr):
        if len(binstr) < TXNOP_SIZE: raise Exception("TxnOp should be at least %d bytes, but received %d" % (TXNOP_SIZE, len(binstr)))
        self.type, self.key, self.value = struct.unpack(txnop_fmt, binstr)

    def pack(self):
        return struct.pack(txnop_fmt, self.type, self.key, self.value)

    def __str__(self):
        return str(dict(self))

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        yield 't', txn_op_type_to_string[self.type]
        yield 'k', self.key
        v = self.value.rstrip('\0')
        yield 'v', v if printable(v) else b64encode(v)


txnhdr_fmt = '!B I i B B B B'
TXNHDR_SIZE = struct.Struct(txnhdr_fmt).size
MAX_TXNMSG_SIZE = TXNHDR_SIZE + TXNOP_SIZE*GOTTHARD_MAX_OP

class TxnMsg:

    def __init__(self, binstr=None, req=False, res=False, replyto=None,
            cl_id=0, req_id=0, status=0, frag_seq=1, frag_cnt=1, from_switch=0, ops=[]):

        self.flags = BitFlags(flags=['type', 'from_switch', 'reset'])
        self.flags.from_switch = from_switch
        self.cl_id = cl_id
        self.req_id = req_id
        self.frag_seq = frag_seq
        self.frag_cnt = frag_cnt
        self.status = status
        self.ops = ops

        if binstr is not None:
            self.unpack(binstr)
        elif replyto is not None:
            self.flags.type = TYPE_REQ if replyto.flags.type == TYPE_RES else TYPE_RES
            self.cl_id, self.req_id, self.status, self.ops = replyto.cl_id, replyto.req_id, status, ops
        else:
            assert((req or res) and not (req and res))
            self.flags.type = TYPE_REQ if req else TYPE_RES

    def unpack(self, binstr):
        if len(binstr) < TXNHDR_SIZE: raise Exception("TxnMsg should be at least %d bytes, but received %d" % (TXNHDR_SIZE, len(binstr)))
        flags_value, self.cl_id, self.req_id, self.frag_seq, self.frag_cnt, self.status, op_cnt = struct.unpack(txnhdr_fmt, binstr[:TXNHDR_SIZE])
        assert(op_cnt <= GOTTHARD_MAX_OP)
        self.flags.unpack(flags_value)
        ops_binstr = binstr[TXNHDR_SIZE:]
        self.ops = [TxnOp(binstr=ops_binstr[i:i+TXNOP_SIZE]) for i in xrange(0, op_cnt*TXNOP_SIZE, TXNOP_SIZE)]
        # Remove NOP ops:
        self.ops = [o for o in self.ops if o.type != TXN_NOP]

    def pack(self):
        ops_binstr = ''.join([op.pack() for op in self.ops])
        return struct.pack(txnhdr_fmt, self.flags.pack(), self.cl_id, self.req_id,
                self.frag_seq, self.frag_cnt, self.status, len(self.ops)) + ops_binstr

    def op(self, k=None, t=None):
        found = [o for o in self.ops if (k and o.key == k) or (t and o.type == t)]
        return found[0] if len(found) == 1 else found

    def __str__(self):
        return "Txn%s(%s)" % ('Req' if self.flags.type == TYPE_REQ else 'Res', dict(self))

    def __iter__(self):
        if self.flags.type == TYPE_RES: yield 'status', status_to_string[self.status]
        if self.flags.from_switch: yield 'from_switch', self.flags.from_switch
        for f in ['cl_id', 'req_id', 'ops', 'frag_seq', 'frag_cnt']:
            yield f, getattr(self, f)



class Store:
    values = {}
    sequences = {}
    seq = 0

    def __init__(self):
        self.lock = threading.Lock()

    def clear(self):
        self.values, self.sequences, self.seq = {}, {}, 0

    def _val(self, key):
        return self.values[key] if key in self.values else NULL_VALUE

    def _get(self, o=None, k=None, t=TXN_VALUE):
        assert(k or (o and o.key))
        return TxnOp(t=t, key=o.key if o else k,
                value=self._val(o.key if o else k))

    def applyTxn(self, ops=[]):
        with self.lock:
            return self._applyTxn(ops)

    def _applyTxn(self, ops=[]):
        if len(ops) < 1: return (STATUS_BADREQ, [])

        rb_ops = [o for o in ops if o.type == TXN_VALUE] # read before
        r_ops = [o for o in ops if o.type == TXN_READ]
        w_ops = [o for o in ops if o.type == TXN_WRITE]
        res_ops = []

        # Check that the read-befores are valid:
        bad_reads = [self._get(o=o) for o in rb_ops if o.value != self._val(o.key)]
        if len(bad_reads) > 0:
            # also, invalidate any optimistic writes that may be cached at the switch:
            undo_w = [self._get(o=o) for o in w_ops if o.key not in [b.key for b in bad_reads]]
            return (STATUS_ABORT, bad_reads + undo_w)

        # Process all the write operations:
        for o in w_ops:
            self.seq += 1
            self.sequences[o.key] = self.seq
            self.values[o.key] = o.value
            res_ops.append(self._get(o=o, t=TXN_UPDATED))

        # Process all the reads
        res_ops += [self._get(o=o) for o in r_ops]

        return (STATUS_OK, res_ops)

    def __str__(self):
        s = "key\tseq\tvalue\n"
        for key in self.values.keys():
            s += "%d\t%d\t%s\n" % (key, self.sequences[key], self.values[key].rstrip('\0'))
        return s

    def dump(self, f):
        d = dict(values=self.values, sequences=self.sequences, seq=self.seq)
        pickle.dump(d, f)

    def load(self, f):
        d = pickle.load(f)
        self.values, self.sequences, self.seq = d['values'], d['sequences'], d['seq']

class GotthardClient:

    def __init__(self, store_addr=None, logger=None, log_filename=None, log_dir=None, cl_id=None, resend_timeout=None):
        self.store_addr = store_addr
        self.resolved_store_addr = None
        self.recv_queue = {}
        # maps outstanding requests with the time they were sent
        self.outstanding = {}
        self.req_id_seq = 0
        self.closed = True
        self.cl_id = cl_id
        self.log = logger
        self.log_filename = log_filename
        self.log_dir = log_dir
        self.resend_timeout = resend_timeout

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.store_addr[0]:
            self.resolved_store_addr = (socket.gethostbyname_ex(self.store_addr[0])[2][0],
                                    self.store_addr[1])
        if self.resend_timeout:
            # recvfrom will timeout every 100ms and then we'll check whether resend_timeout has elapsed
            self.sock.settimeout(0.1)
        else:
            self.sock.settimeout(10)
        self.sock.bind(('', 0))
        self.cl_addr = self.sock.getsockname()
        self.cl_name = ':'.join(map(str, self.cl_addr))
        if self.cl_id is None:
            self.cl_id = abs(hash(self.cl_name)) % 2**32
        if self.log_filename: self.log = GotthardLogger(self.log_filename)
        elif self.log_dir: self.log = GotthardLogger(os.path.join(self.log_dir, 'cl%d.log'%self.cl_id))
        if self.log: self.log.open()
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

    def req(self, *ops, **kwargs):
        req_id = kwargs['req_id'] if 'req_id' in kwargs else None
        if len(ops) == 1 and type(ops[0]) == list: ops = ops[0]
        reqs = self.buildreq(req_id=req_id, ops=ops)
        self.sendreq(reqs)
        return self.recvres(req_id=reqs[0].req_id)

    def reset(self):
        reqs = self.buildreq()
        reqs[0].flags.reset = True
        self.sendreq(reqs)
        return self.recvres(req_id=reqs[0].req_id)

    def reqAsync(self, ops, req_id=None):
        reqs = self.buildreq(req_id=req_id,
                ops=ops if type(ops) is list else [ops])
        self.sendreq(reqs)
        return reqs[0].req_id

    def buildreq(self, req_id=None, ops=[]):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq

        if len(ops) == 0:
            return [TxnMsg(req=True, cl_id=self.cl_id, req_id=req_id)]

        frag_cnt = int(math.ceil(len(ops) / float(GOTTHARD_MAX_OP)))
        reqs = []
        for i in xrange(0, frag_cnt):
            reqs.append(TxnMsg(req=True, cl_id=self.cl_id, req_id=req_id,
                frag_seq=i+1, frag_cnt=frag_cnt,
                ops=ops[i*GOTTHARD_MAX_OP:(i*GOTTHARD_MAX_OP)+GOTTHARD_MAX_OP]))
        return reqs

    def sendreq(self, reqs, is_resend=False):
        if reqs:
            # store together with send time, for resending on timeout
            self.outstanding[reqs[0].req_id] = (time.time(), reqs)
        for req in reqs:
            req_data = req.pack()
            self.sock.sendto(req_data, self.store_addr)
            if is_resend:
                self._log("resent", req=req)
            else:
                self._log("sent", req=req)
            wait = min(MIN_INTER_MSG_SEND_WAIT * req.frag_seq, MAX_INTER_MSG_SEND_WAIT)
            if wait:
                time.sleep(wait)

    def _reassemble(self, resps):
        assert len(resps)
        r = resps[-1]
        m = TxnMsg(res=True, cl_id=r.cl_id, req_id=r.req_id, status=r.status,
                ops=[o for res in resps for o in res.ops])
        m.flags = r.flags
        return m

    def _push_recvqueue(self, res):
        if res.req_id not in self.recv_queue:
            self.recv_queue[res.req_id] = dict(ready=False,q=[])
        self.recv_queue[res.req_id]['q'].append(res)
        if not len(self.recv_queue[res.req_id]['q']) <= res.frag_cnt:
            print [str(m) for m in self.recv_queue[res.req_id]['q']]
            print len(self.recv_queue[res.req_id]['q']), res.frag_cnt
        assert len(self.recv_queue[res.req_id]['q']) <= res.frag_cnt
        if len(self.recv_queue[res.req_id]['q']) == res.frag_cnt:
            self.recv_queue[res.req_id]['ready'] = True

    def _pop_recvqueue(self, req_id):
        ready = [i for i, r in self.recv_queue.items() if req_id==i and r['ready']]
        if req_id is None:
            ready = [i for i, r in self.recv_queue.items() if r['ready']]

        if len(ready) == 0: return None

        res = self._reassemble(self.recv_queue[ready[0]]['q'])
        del self.recv_queue[ready[0]]
        del self.outstanding[res.req_id]
        return res

    def recvres(self, req_id=None):
        res = self._pop_recvqueue(req_id)
        if res: return res

        while True:
            try:
                data, fromaddr = self.sock.recvfrom(MAX_TXNMSG_SIZE)
                assert(fromaddr == self.resolved_store_addr)
            except:
                # if resend_timeout is set, resend every transaction that has timed out
                if self.resend_timeout:
                    now = time.time()
                    for (req_id, (send_time, req)) in self.outstanding.items():
                        if now - send_time > self.resend_timeout:
                            if req[0].req_id in self.recv_queue: del self.recv_queue[req[0].req_id]
                            self.sendreq(req, is_resend=True)
                    continue
                else:
                    print 'Client %d Waiting for req_id: %d' % (self.cl_id, req_id)
                    raise
            res = TxnMsg(binstr=data)
            self._log("received", res=res)
            self._push_recvqueue(res)
            res = self._pop_recvqueue(req_id)
            if res: return res

    @staticmethod
    def W(key, val):
        return TxnOp(t=TXN_WRITE, key=key, value=val)

    @staticmethod
    def R(key):
        return TxnOp(t=TXN_READ, key=key, value='')

    @staticmethod
    def RB(key, val):
        return TxnOp(t=TXN_VALUE, key=key, value=val)


class GotthardLogger:
    def __init__(self, filename, stdout=False):
        self.logfile = os.fdopen(os.open(filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a')
        self.closed = threading.Event()
        self.stdout = stdout
        self.last_log = 0
        self.connected_cnt = 0

        def heartbeat():
            while not self.closed.wait(1):
                if time.time() - self.last_log > 5: self.log("heartbeat")
                self.logfile.flush()
        t = threading.Thread(target=heartbeat)
        t.daemon = False
        t.start()

    def open(self):
        self.connected_cnt += 1

    def log(self, event, req=None, res=None):
        self.last_log = time.time()
        l = dict(time=self.last_log, event=event)
        if req: l['req'] = dict(req)
        if res: l['res'] = dict(res)
        line = json.dumps(l, ensure_ascii=False, default=lambda x: dict(x), sort_keys=True)
        if self.stdout:
            print line
        self.logfile.write(line + "\n")

    def close(self):
        self.connected_cnt -= 1
        if self.connected_cnt > 0: return
        if self.closed.isSet(): return
        self.closed.set()
        self.logfile.flush()
        self.logfile.close()

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.closed.isSet():
            self.close()

if __name__ == '__main__':
    print 'TXNHDR_SIZE', TXNHDR_SIZE
    print 'TXNOP_SIZE', TXNOP_SIZE
    print 'MAX_TXNMSG_SIZE', MAX_TXNMSG_SIZE
