import struct
import socket

TYPE_REQ = 0
TYPE_RES = 1

STATUS_OK = 0
STATUS_NOTFOUND = 1
STATUS_REJECT = 2

status_to_string = ['STATUS_OK', 'STATUS_NOTFOUND', 'STATUS_REJECT']

OP_R =  1
OP_W =  2
OP_RW = 3

reqmsg_fmt = '!B I i i i i 100s'
REQMSG_SIZE = struct.Struct(reqmsg_fmt).size

class BaseMsg:
    flags = 0
    FLAGS = ['type', 'rm', 'updated']

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
    r_version = 0
    w_key = 0
    w_value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, rm=0, r_key=0, r_version=0, w_key=0, w_value=''):
        BaseMsg.__init__(self)
        self.type = TYPE_REQ
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.rm, self.r_key, self.r_version, self.w_key, self.w_value = cl_id, req_id, rm, r_key, r_version, w_key, w_value

    def op(self):
        if self.r_key != 0 and self.w_key != 0: return OP_RW
        elif self.r_key != 0: return OP_R
        elif self.w_key != 0 : return OP_W

    def unpack(self, binstr):
        self.flags, self.cl_id, self.req_id, self.r_key, self.r_version, self.w_key, self.w_value = struct.unpack(reqmsg_fmt, binstr)
        self._unpackflags()

    def pack(self):
        self._packflags()
        return struct.pack(reqmsg_fmt, self.flags, self.cl_id, self.req_id, self.r_key, self.r_version, self.w_key, self.w_value)

    def __str__(self):
        return "ReqMsg(cl_id=%d, req_id=%d, rm=%d, r_key=%d, r_version=%d, w_key=%d, w_value='%s')" % (self.cl_id, self.req_id, self.rm, self.r_key, self.r_version, self.w_key, self.w_value.rstrip('\0'))

respmsg_fmt = '!B I i B i i 100s'
RESPMSG_SIZE = struct.Struct(respmsg_fmt).size

class RespMsg(BaseMsg):
    cl_id = 0
    req_id = 0
    status = STATUS_OK
    key = 0
    version = 0
    value = ''

    def __init__(self, binstr=None, cl_id=0, req_id=0, status=0, key=0, version=0, value='', updated=0):
        BaseMsg.__init__(self)
        self.type = TYPE_RES
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.cl_id, self.req_id, self.status, self.key, self.version, self.value, self.updated = cl_id, req_id, status, key, version, value, updated

    def unpack(self, binstr):
        self.flags, self.cl_id, self.req_id, self.status, self.key, self.version, self.value = struct.unpack(respmsg_fmt, binstr)
        self._unpackflags()

    def pack(self):
        self._packflags()
        return struct.pack(respmsg_fmt, self.flags, self.cl_id, self.req_id, self.status, self.key, self.version, self.value)

    def __str__(self):
        return "RespMsg(cl_id=%d, req_id=%d, status=%d, key=%d, version=%d, value='%s', updated=%d)" % (self.cl_id, self.req_id, self.status, self.key, self.version, self.value.rstrip('\0'), self.updated)

class Store:
    values = {}
    versions = {}
    seq = 0

    def read(self, key=None):
        if not key in self.values:
            return (STATUS_NOTFOUND, 0, '', 0)
        return (STATUS_OK, key, self.values[key], self.versions[key])

    def write(self, key=None, value=None):
        if value is None: # w(key, None) is treated as remove
            if key in self.values.keys():
                del self.values[key]
                del self.versions[key]
            new_value, new_version = '', 0
        else:
            self.values[key] = value
            self.seq += 1
            self.versions[key] = self.seq
            new_value, new_version = value, self.seq
        return (STATUS_OK, key, new_value, new_version)

    def readwrite(self, r_key=None, r_version=None, w_key=None, w_value=None):
        assert(r_key != 0)
        if r_key in self.values.keys() and self.versions[r_key] != r_version:
            return (STATUS_REJECT, w_key, '', 0)
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
        self.cl_id = abs(hash(self.cl_name)) % 2**32
        self.store_addr = store_addr
        self.req_id_seq = 0

    def req(self, req_id=None, r_key=0, r_version=0, w_key=0, w_value='', rm=0):
        req = self.buildreq(req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value, rm=rm)
        return self.sendreq(req)

    def buildreq(self, req_id=None, r_key=0, r_version=0, w_key=0, w_value='', rm=0):
        if req_id is None:
            self.req_id_seq += 1
            req_id = self.req_id_seq
        req = ReqMsg(cl_id=self.cl_id, req_id=req_id, r_key=r_key, r_version=r_version, w_key=w_key, w_value=w_value, rm=rm)
        return req

    def sendreq(self, req):
        self.sock.sendto(req.pack(), self.store_addr)
        data, fromaddr = self.sock.recvfrom(RESPMSG_SIZE)
        assert(fromaddr == self.store_addr)
        return RespMsg(binstr=data)


