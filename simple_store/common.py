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

VALUE_SIZE = 100

status_to_string = ['STATUS_OK', 'STATUS_ABORT', 'STATUS_OPTIMISTIC_ABORT']

OP_R =  1
OP_W =  2
OP_RW = 3

reqmsg_fmt = '!B I i i i %ds %ds' % (VALUE_SIZE, VALUE_SIZE)
REQMSG_SIZE = struct.Struct(reqmsg_fmt).size

class BaseMsg:
    flags = 0
    FLAGS = ['type', 'updated', 'from_switch']

    def __init__(self):
        for f in self.FLAGS: setattr(self, f, 0) # init flags to 0

    def _packflags(self):
        binary = (''.join(['1' if getattr(self, f) else '0' for f in self.FLAGS])).ljust(8, '0')
        self.flags = int(binary, 2)

    def _unpackflags(self):
        binary = bin(self.flags)[2:].rjust(8, '0')
        for i, f in enumerate(self.FLAGS):
            setattr(self, f, int(binary[i]))

class ReqMsg(BaseMsg):
    cl_id = 0
    req_id = 0
    r_key = 0
    w_key = 0
    r_value = ''
    w_value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, r_key=0, w_key=0, r_value='', w_value=''):
        BaseMsg.__init__(self)
        self.type = TYPE_REQ
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.r_key, self.w_key, self.r_value, self.w_value = cl_id, req_id, r_key, w_key, r_value, w_value

    def op(self):
        if self.r_key != 0 and self.w_key != 0: return OP_RW
        elif self.r_key != 0: return OP_R
        elif self.w_key != 0: return OP_W

    def unpack(self, binstr):
        self.flags, self.cl_id, self.req_id, self.r_key, self.w_key, self.r_value, self.w_value = struct.unpack(reqmsg_fmt, binstr)
        self._unpackflags()

    def pack(self):
        self._packflags()
        return struct.pack(reqmsg_fmt, self.flags, self.cl_id, self.req_id, self.r_key, self.w_key, self.r_value, self.w_value)

    def __str__(self):
        return "ReqMsg(%s)" % dict(self)

    def __iter__(self):
        yield 'w_value', self.w_value.rstrip('\0')
        yield 'r_value', self.r_value.rstrip('\0')
        for f in ['cl_id', 'req_id', 'r_key', 'w_key', 'updated']:
            yield f, getattr(self, f)


respmsg_fmt = '!B I i B i %ds' % (VALUE_SIZE)
RESPMSG_SIZE = struct.Struct(respmsg_fmt).size

class RespMsg(BaseMsg):
    cl_id = 0
    req_id = 0
    status = STATUS_OK
    key = 0
    value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, status=0, key=0, value='', updated=0, from_switch=0):
        BaseMsg.__init__(self)
        self.type = TYPE_RES
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.status, self.key, self.value, self.updated, self.from_switch = cl_id, req_id, status, key, value, updated, from_switch

    def unpack(self, binstr):
        self.flags, self.cl_id, self.req_id, self.status, self.key, self.value = struct.unpack(respmsg_fmt, binstr)
        self._unpackflags()

    def pack(self):
        self._packflags()
        return struct.pack(respmsg_fmt, self.flags, self.cl_id, self.req_id, self.status, self.key, self.value)

    def __str__(self):
        return "RespMsg(%s)" % dict(self)

    def __iter__(self):
        yield 'value', self.value.rstrip('\0')
        yield 'status', status_to_string[self.status]
        for f in ['cl_id', 'req_id', 'key', 'updated', 'from_switch']:
            yield f, getattr(self, f)

class Store:
    values = {}
    sequences = {}
    seq = 0

    def read(self, key=None):
        return (STATUS_OK, key,
                self.values[key] if key in self.values else '')

    def write(self, key=None, value=None):
        if value is None: # w(key, None) is treated as remove
            if key in self.values.keys():
                del self.values[key]
                del self.sequences[key]
            new_value = ''
        else:
            self.values[key] = value
            self.seq += 1
            self.sequences[key] = self.seq
            new_value = value
        return (STATUS_OK, key, new_value)

    def readwrite(self, r_key=None, r_value=None, w_key=None, w_value=None):
        assert(r_key != 0)
        if r_key in self.values.keys() and self.values[r_key] != r_value:
            return (STATUS_ABORT, r_key, self.values[r_key])
        return self.write(key=w_key, value=w_value)

    def __str__(self):
        s = "key\tvers\tvalue\n"
        for key in self.values.keys():
            s += "%d\t%d\t%s\n" % (key, self.sequences[key], self.values[key])
        return s

class StoreClient:

    def __init__(self, store_addr=None, logger=None, log_filename=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10.0)
        self.sock.bind(('', 0))
        self.cl_addr = self.sock.getsockname()
        self.cl_name = ':'.join(map(str, self.cl_addr))
        self.cl_id = abs(hash(self.cl_name)) % 2**32
        self.store_addr = store_addr
        self.req_id_seq = 0
        self.closed = False
        self.log = None
        if logger: self.log = logger
        elif log_filename: self.log = GotthardLogger(log_filename)

    def close(self):
        if self.closed: return
        self.sock.close()
        if self.log: self.log.close()
        self.closed = True

    def _log(self, *args, **kwargs):
        if self.log: self.log.log(*args, **kwargs)

    def __exit__(self):
        if self.log: self.log.exit()

    def req(self, req_id=None, r_key=0, r_value='', w_key=0, w_value=''):
        req = self.buildreq(req_id=req_id, r_key=r_key, r_value=r_value, w_key=w_key, w_value=w_value)
        self.sendreq(req)
        return self.recvresp()

    def reqAsync(self, req_id=None, r_key=0, r_value='', w_key=0, w_value=''):
        req = self.buildreq(req_id=req_id, r_key=r_key, r_value=r_value, w_key=w_key, w_value=w_value)
        self.sendreq(req)

    def buildreq(self, req_id=None, r_key=0, r_value='', w_key=0, w_value=''):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq
        req = ReqMsg(cl_id=self.cl_id, req_id=req_id, r_key=r_key, r_value=r_value, w_key=w_key, w_value=w_value)
        return req

    def sendreq(self, req):
        req_data = req.pack()
        self.sock.sendto(req_data, self.store_addr)
        self._log("sent", req=req)

    def recvresp(self):
        data, fromaddr = self.sock.recvfrom(RESPMSG_SIZE)
        assert(fromaddr == self.store_addr)
        res = RespMsg(binstr=data)
        self._log("received", res=res)
        return res


class GotthardLogger:
    def __init__(self, filename):
        self.logfile = os.fdopen(os.open(filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a')
        self.closed = threading.Event()
        self.last_log = 0

        def heartbeat():
            while not self.closed.wait(1):
                if time.time() - self.last_log > 5: self.log("heartbeat")
                self.logfile.flush()
        t = threading.Thread(target=heartbeat)
        t.daemon = True
        t.start()

    def log(self, event, req=None, res=None):
        self.last_log = time.time()
        l = dict(time=self.last_log, event=event)
        if req: l['req'] = dict(req)
        if res: l['res'] = dict(res)
        self.logfile.write(json.dumps(l, sort_keys=True) + "\n")

    def close(self):
        if self.closed.isSet(): return
        self.closed.set()
        self.logfile.flush()
        self.logfile.close()

    def __exit__(self):
        if not self.closed.isSet():
            self.close()
