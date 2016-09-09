import struct

STATUS_OK = 0
STATUS_NOTFOUND = 1
STATUS_REJECT = 2

reqmsg_fmt = '!i i i i 100s'
REQMSG_SIZE = struct.Struct(reqmsg_fmt).size

class ReqMsg:
    req_id = 0
    r_key = 0
    r_version = 0
    w_key = 0
    w_value = ''

    def __init__(self, binstr=None, req_id=0, r_key=0, r_version=0, w_key=0, w_value=''):
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.req_id, self.r_key, self.r_version, self.w_key, self.w_value = req_id, r_key, r_version, w_key, w_value

    def unpack(self, binstr):
        self.req_id, self.r_key, self.r_version, self.w_key, self.w_value = struct.unpack(reqmsg_fmt, binstr)

    def pack(self):
        return struct.pack(reqmsg_fmt, self.req_id, self.r_key, self.r_version, self.w_key, self.w_value)

    def __str__(self):
        return "ReqMsg(req_id=%d, r_key=%d, r_version=%d, w_key=%d, w_value='%s')" % (self.req_id, self.r_key, self.r_version, self.w_key, self.w_value.rstrip('\0'))

respmsg_fmt = '!i B i i 100s'
RESPMSG_SIZE = struct.Struct(respmsg_fmt).size

class RespMsg:
    req_id = 0
    status = STATUS_OK
    key = 0
    version = 0
    value = ''

    def __init__(self, binstr=None, req_id=0, status=0, key=0, version=0, value=''):
        if binstr is not None:
            self.unpack(binstr)
        else:
            self.req_id, self.status, self.key, self.version, self.value = req_id, status, key, version, value

    def unpack(self, binstr):
        self.req_id, self.status, self.key, self.version, self.value = struct.unpack(respmsg_fmt, binstr)

    def pack(self):
        return struct.pack(respmsg_fmt, self.req_id, self.status, self.key, self.version, self.value)

    def __str__(self):
        return "RespMsg(req_id=%d, status=%d, key=%d, version=%d, value='%s')" % (self.req_id, self.status, self.key, self.version, self.value.rstrip('\0'))

class Store:
    values = {}
    versions = {}
    seq = 0

    def read(self, key=None):
        if not key in self.values:
            return (STATUS_NOTFOUND, '', 0)
        return (STATUS_OK, self.values[key], self.versions[key])

    def write(self, key=None, value=None):
        self.values[key] = value
        self.seq += 1
        self.versions[key] = self.seq
        return (STATUS_OK, self.values[key], self.versions[key])

    def readwrite(self, r_key=None, r_version=None, w_key=None, w_value=None):
        if self.versions[r_key] != r_version:
            return (STATUS_REJECT, '', 0)
        return self.write(key=w_key, value=w_value)

    def __str__(self):
        s = "key\tvers\tvalue\n"
        for key in self.values.keys():
            s += "%d\t%d\t%s\n" % (key, self.versions[key], self.values[key])
        return s


