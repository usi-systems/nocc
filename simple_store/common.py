import struct
import socket

STATUS_OK = 0
STATUS_NOTFOUND = 1
STATUS_REJECT = 2

OP_R =  1
OP_W =  2
OP_RW = 3
OP_RM = 4

reqmsg_fmt = '!i i B i i i 100s'
REQMSG_SIZE = struct.Struct(reqmsg_fmt).size

class ReqMsg:
    cl_id = 0
    req_id = 0
    op = None
    r_key = 0
    r_version = 0
    w_key = 0
    w_value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, op=None, r_key=0, r_version=0, w_key=0, w_value=''):
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.op, self.r_key, self.r_version, self.w_key, self.w_value = cl_id, req_id, op, r_key, r_version, w_key, w_value
            if self.op is None: # Guess operation type
                if r_key != 0 and w_key != 0: self.op = OP_RW
                elif r_key != 0: self.op = OP_R
                elif w_key != 0: self.op = OP_W

    def unpack(self, binstr):
        self.cl_id, self.req_id, self.op, self.r_key, self.r_version, self.w_key, self.w_value = struct.unpack(reqmsg_fmt, binstr)

    def pack(self):
        return struct.pack(reqmsg_fmt, self.cl_id, self.req_id, self.op, self.r_key, self.r_version, self.w_key, self.w_value)

    def __str__(self):
        return "ReqMsg(cl_id=%d, req_id=%d, op=%d, r_key=%d, r_version=%d, w_key=%d, w_value='%s')" % (self.cl_id, self.req_id, self.op, self.r_key, self.r_version, self.w_key, self.w_value.rstrip('\0'))

respmsg_fmt = '!i i B i i 100s'
RESPMSG_SIZE = struct.Struct(respmsg_fmt).size

class RespMsg:
    cl_id = 0
    req_id = 0
    status = STATUS_OK
    key = 0
    version = 0
    value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, status=0, key=0, version=0, value=''):
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.status, self.key, self.version, self.value = cl_id, req_id, status, key, version, value

    def unpack(self, binstr):
        self.cl_id, self.req_id, self.status, self.key, self.version, self.value = struct.unpack(respmsg_fmt, binstr)

    def pack(self):
        return struct.pack(respmsg_fmt, self.cl_id, self.req_id, self.status, self.key, self.version, self.value)

    def __str__(self):
        return "RespMsg(cl_id=%d, req_id=%d, status=%d, key=%d, version=%d, value='%s')" % (self.cl_id, self.req_id, self.status, self.key, self.version, self.value.rstrip('\0'))

class Store:
    values = {}
    versions = {}
    seq = 0

    def read(self, key=None):
        if not key in self.values:
            return (STATUS_NOTFOUND, '', 0)
        return (STATUS_OK, self.values[key], self.versions[key])

    def delete(self, key=None):
        if not key in self.values:
            return (STATUS_NOTFOUND, '', 0)
        del self.values[key]
        del self.versions[key]

    def write(self, key=None, value=None):
        self.values[key] = value
        self.seq += 1
        self.versions[key] = self.seq
        return (STATUS_OK, self.values[key], self.versions[key])

    def readwrite(self, r_key=None, r_version=None, w_key=None, w_value=None):
        assert(r_key != 0)
        if self.versions[r_key] != r_version:
            return (STATUS_REJECT, '', 0)
        return self.write(key=w_key, value=w_value)

    def __str__(self):
        s = "key\tvers\tvalue\n"
        for key in self.values.keys():
            s += "%d\t%d\t%s\n" % (key, self.versions[key], self.values[key])
        return s

class StoreClient:

    def __init__(self, store_addr=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.cl_addr = self.sock.getsockname()
        self.cl_name = ':'.join(map(str, self.cl_addr))
        self.cl_id = hash(self.cl_name)
        self.store_addr = store_addr
        self.req_id_seq = 0

    def req(self, req_id=None, r_key=0, r_version=0, w_key=0, w_value=''):
        req = self.buildreq(req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value)
        return self.sendreq(req)

    def buildreq(self, req_id=None, r_key=0, r_version=0, w_key=0, w_value=''):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq
        req = ReqMsg(cl_id=self.cl_id, req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value)
        return req

    def sendreq(self, req):
        self.sock.sendto(req.pack(), self.store_addr)
        data, fromaddr = self.sock.recvfrom(RESPMSG_SIZE)
        assert(fromaddr == self.store_addr)
        return RespMsg(binstr=data)


