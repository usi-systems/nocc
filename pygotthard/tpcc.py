import struct
import pickle
import time
import datetime
import re
from ReadWriteLock import ReadWriteLock
import threading
from gotthard import VALUE_SIZE

MAX_STR_SIZE=12

def sqlTypeToStructFormat(t):
    if re.match('^([xcbB?hHiIlLqQfdpP]|\d+(s|p))$', t): return t # already a struct fmt
    inttypes = dict(TINYINT='B', SMALLINT='h', BIGINT='q', INT='i', INTEGER='i',
                    FLOAT='f', DEC='d', DECIMAL='d', TIMESTAMP='q')
    intname = t.split('(')[0].upper()
    if intname in inttypes: return inttypes[intname]
    m = re.findall('\((.*)\)', t)
    if len(m) != 1: raise Exception("Unable to convert SQL type %s to a struct format" % t)
    size = int(m[0])
    return '%ds' % min(size, MAX_STR_SIZE)


class SerializableRecord(dict):

    def __init__(self, fielddefs=None, **kwargs):
        dict.__init__(self)

        if fielddefs is None: fielddefs = kwargs
        if type(fielddefs) is dict:
            fielddefs = list(fielddefs.iteritems())

        self.fieldnames = [] # order matters
        self.fielddefs = {}
        for fdef in fielddefs:
            fname, ftype = fdef[0], fdef[1]
            dont_pack = len(fdef) > 2 and fdef[2]
            self[fname] = None
            self.fieldnames.append(fname)
            self.fielddefs[fname] = (sqlTypeToStructFormat(ftype), dont_pack)

        self.pack_fields = [f for f in self.fieldnames if not self.fielddefs[f][1]]
        self.fmt = '!' + ' '.join([self.fielddefs[f][0] for f in self.pack_fields])
        self.struct = struct.Struct(self.fmt)


    def unpack(self, binstr):
        binstr = binstr[:self.size()]
        assert len(binstr) == self.size()
        for f, v in zip(self.pack_fields, self.struct.unpack(binstr)):
            self[f] = v.rstrip('\0') if 's' in self.fielddefs[f][0] else v
        return self

    def pack(self):
        vals = [self._fmtfield(f) for f in self.pack_fields]
        try:
            return self.struct.pack(*vals).ljust(VALUE_SIZE, '\0')
        except:
            print self.__class__.__name__
            print self.fieldnames, self.fmt
            print self.fielddefs
            print self
            raise

    def _fmtfield(self, f):
        if type(self[f]) is datetime.datetime:
            return time.mktime(self[f].timetuple())
        if self[f] is None and self.fielddefs[f][0] in ['b', 'B', 'f', 'd', 'h', 'i', 'I', 'q', 'Q']:
            return 0
        if self[f] is None and 's' in self.fielddefs[f][0]:
            return ''
        # Enable this to implicitly cast strings:
        #if 's' in self.fieldfmts[f]: return str(self[f])
        return self[f]

    def set(self, fields):
        """Set the values of the record's fields. Tuples should be in the same order as the record's fields."""
        if type(fields) in [list, tuple]:
            standard_fieldnames = [f for f in self.fieldnames if not f.startswith('_EXTRA')]
            if len(fields) != len(standard_fieldnames):
                print fields
                print standard_fieldnames
                print len(fields), len(standard_fieldnames)
            assert len(fields) == len(standard_fieldnames)
            for f, v in zip(standard_fieldnames, fields):
                self[f] = v
        elif type(fields) is dict:
            for f in fields:
                assert f in self, "Fieldname %s does not belong to %s" %(f, self.__class__.__name__)
                self[f] = fields[f]
        return self

    def reset(self):
        for f in self: self[f] = None

    def size(self):
        return self.struct.size

    def key(self):
        fmtkey = lambda k: ''.join(k.split('_ID'))
        return '.'.join(sum([(fmtkey(k), str(self[k])) for k in self.keyfields], ()))


class WarehouseRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('W_ID', "SMALLINT"),
                ('W_NAME', "VARCHAR(16)"),
                ('W_STREET_1', "VARCHAR(32)"),
                ('W_STREET_2', "VARCHAR(32)"),
                ('W_CITY', "VARCHAR(32)"),
                ('W_STATE', "VARCHAR(2)"),
                ('W_ZIP', "VARCHAR(9)"),
                ('W_TAX', "FLOAT"),
                ('W_YTD', "FLOAT")
                ))
        self.keyfields = ['W_ID']


class DistrictRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('D_ID', "TINYINT"),
                ('D_W_ID', "SMALLINT"),
                ('D_NAME', "VARCHAR(16)"),
                ('D_STREET_1', "VARCHAR(32)", True), # don't pack
                ('D_STREET_2', "VARCHAR(32)", True), # don't pack
                ('D_CITY', "VARCHAR(32)"),
                ('D_STATE', "VARCHAR(2)"),
                ('D_ZIP', "VARCHAR(9)"),
                ('D_TAX', "FLOAT"),
                ('D_YTD', "FLOAT"),
                ('D_NEXT_O_ID', "INT"),
                #('_EXTRA_LAST_O_ID1', "INT"), # unneccesary; same as D_NEXT_O_ID-1
                ('_EXTRA_LAST_O_ID2', "INT"),
                ('_EXTRA_LAST_O_ID3', "INT"),
                ('_EXTRA_LAST_O_ID4', "INT"),
                ('_EXTRA_LAST_O_ID5', "INT"),
                ('_EXTRA_LAST_O_ID6', "INT"),
                ('_EXTRA_LAST_O_ID7', "INT"),
                ('_EXTRA_LAST_O_ID8', "INT"),
                ('_EXTRA_LAST_O_ID9', "INT"),
                ('_EXTRA_LAST_O_ID10', "INT"),
                ('_EXTRA_LAST_O_ID11', "INT"),
                ('_EXTRA_LAST_O_ID12', "INT"),
                ('_EXTRA_LAST_O_ID13', "INT"),
                ('_EXTRA_LAST_O_ID14', "INT"),
                ('_EXTRA_LAST_O_ID15', "INT"),
                ('_EXTRA_LAST_O_ID16', "INT"),
                ('_EXTRA_LAST_O_ID17', "INT"),
                ('_EXTRA_LAST_O_ID18', "INT"),
                ('_EXTRA_LAST_O_ID19', "INT"),
                ('_EXTRA_LAST_O_ID20', "INT"),
                ))
        self.keyfields = ['D_W_ID', 'D_ID']

    def last20OrderIDs(self):
        return [self['D_NEXT_O_ID'] - 1] + [self['_EXTRA_LAST_O_ID%d'%i] for i in xrange(2, 21)]

    def incNextOrderID(self):
        last20 = self.last20OrderIDs()
        last21 = [self['D_NEXT_O_ID']] + last20
        self['D_NEXT_O_ID'] += 1
        for i,oid in zip(xrange(2, 21), last21[1:20]):
            self['_EXTRA_LAST_O_ID%d'%i] = oid

class ItemRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('I_ID', "INTEGER"),
                ('I_IM_ID', "INTEGER"),
                ('I_NAME', "VARCHAR(32)"),
                ('I_PRICE', "FLOAT"),
                ('I_DATA', "VARCHAR(64)")
                ))
        self.keyfields = ['I_ID']

class CustomerRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('C_ID', "INTEGER"),
                ('C_D_ID', "TINYINT"),
                ('C_W_ID', "SMALLINT"),
                ('C_FIRST', "VARCHAR(32)"),
                ('C_MIDDLE', "VARCHAR(2)"),
                ('C_LAST', "VARCHAR(32)"),
                ('C_STREET_1', "VARCHAR(32)", True), # don't pack
                ('C_STREET_2', "VARCHAR(32)", True), # don't pack
                ('C_CITY', "VARCHAR(32)", True), # don't pack
                ('C_STATE', "VARCHAR(2)", True), # don't pack
                ('C_ZIP', "VARCHAR(9)"),
                ('C_PHONE', "VARCHAR(32)"),
                ('C_SINCE', "TIMESTAMP"),
                ('C_CREDIT', "VARCHAR(2)"),
                ('C_CREDIT_LIM', "FLOAT"),
                ('C_DISCOUNT', "FLOAT"),
                ('C_BALANCE', "FLOAT"),
                ('C_YTD_PAYMENT', "FLOAT"),
                ('C_PAYMENT_CNT', "INTEGER"),
                ('C_DELIVERY_CNT', "INTEGER"),
                ('C_DATA', "VARCHAR(500)"),
                ('_EXTRA_LAST_O_ID', "INTEGER"),
                ))
        self.keyfields = ['C_W_ID', 'C_D_ID', 'C_ID']

class HistoryRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('H_C_ID', "INTEGER"),
                ('H_C_D_ID', "TINYINT"),
                ('H_C_W_ID', "SMALLINT"),
                ('H_D_ID', "TINYINT"),
                ('H_W_ID', "SMALLINT"),
                ('H_DATE', "TIMESTAMP"),
                ('H_AMOUNT', "FLOAT"),
                ('H_DATA', "VARCHAR(32)")
                ))
        self.keyfields = ['H_W_ID', 'H_D_ID', 'H_C_ID']

class StockRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('S_I_ID', "INTEGER"),
                ('S_W_ID', "SMALLINT"),
                ('S_QUANTITY', "INTEGER"),
                ('S_DIST_01', "VARCHAR(32)"),
                ('S_DIST_02', "VARCHAR(32)"),
                #('S_DIST_03', "VARCHAR(32)", True), # don't pack
                #('S_DIST_04', "VARCHAR(32)", True), # don't pack
                #('S_DIST_05', "VARCHAR(32)", True), # don't pack
                #('S_DIST_06', "VARCHAR(32)", True), # don't pack
                #('S_DIST_07', "VARCHAR(32)", True), # don't pack
                #('S_DIST_08', "VARCHAR(32)", True), # don't pack
                #('S_DIST_09', "VARCHAR(32)", True), # don't pack
                #('S_DIST_10', "VARCHAR(32)", True), # don't pack
                ('S_YTD', "INTEGER"),
                ('S_ORDER_CNT', "INTEGER"),
                ('S_REMOTE_CNT', "INTEGER"),
                ('S_DATA', "VARCHAR(64)")
                ))
        self.keyfields = ['S_W_ID', 'S_I_ID']

class OrderRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('O_ID', "INTEGER"),
                ('O_C_ID', "INTEGER"),
                ('O_D_ID', "TINYINT"),
                ('O_W_ID', "SMALLINT"),
                ('O_ENTRY_D', "TIMESTAMP"),
                ('O_CARRIER_ID', "INTEGER"),
                ('O_OL_CNT', "INTEGER"),
                ('O_ALL_LOCAL', "INTEGER")
                ))
        self.keyfields = ['O_W_ID', 'O_D_ID', 'O_ID']

class NewOrderRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('NO_O_ID', "INTEGER"),
                ('NO_D_ID', "TINYINT"),
                ('NO_W_ID', "SMALLINT")
                ))
        self.keyfields = ['NO_W_ID', 'NO_D_ID', 'NO_O_ID']

class OrderLineRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self, (
                ('OL_O_ID', "INTEGER"),
                ('OL_D_ID', "TINYINT"),
                ('OL_W_ID', "SMALLINT"),
                ('OL_NUMBER', "INTEGER"),
                ('OL_I_ID', "INTEGER"),
                ('OL_SUPPLY_W_ID', "SMALLINT"),
                ('OL_DELIVERY_D', "TIMESTAMP"),
                ('OL_QUANTITY', "INTEGER"),
                ('OL_AMOUNT', "FLOAT"),
                ('OL_DIST_INFO', "VARCHAR(32)")
                ))
        self.keyfields = ['OL_W_ID', 'OL_D_ID', 'OL_O_ID', 'OL_NUMBER']

tpcc_record_types = [WarehouseRec, DistrictRec, ItemRec, CustomerRec, HistoryRec, StockRec, OrderRec, NewOrderRec, OrderLineRec]

class BitKeyMap:
    """Map a string to a limited number of bits"""

    def __init__(self, bits=16, load=None):
        self.useBits(bits)
        self.mapping = {}
        self.unused_keys = [] # keys are added to this as they are deleted
        self.last_key = 0
        self.rwlock = ReadWriteLock()

        if load: self.load(load)

    def useBits(self, bits):
        self.bits = bits
        self.max_key = 2 ** bits

    def size(self):
        return len(self.mapping)

    def get(self, key_string):
        self.rwlock.acquire_read()
        if key_string not in self.mapping:
            self.rwlock.release_read()
            self.rwlock.acquire_write()
            try:
                if self.last_key < self.max_key-1:
                    self.last_key += 1
                    self.mapping[key_string] = self.last_key
                else:
                    if len(self.unused_keys) == 0:
                        raise Exception("Mapping is full; all bits have been exhausted")
                    self.mapping[key_string] = self.unused_keys.pop()
                return self.mapping[key_string]
            finally:
                self.rwlock.release_write()
            #print "BITKEYMAP_NEW_KEY\t%d\t%s\t%d" % (threading.current_thread().ident, key_string, self.mapping[key_string])
        k = self.mapping[key_string]
        self.rwlock.release_read()
        return k

    def contains(self, key_string):
        self.rwlock.acquire_read()
        b = key_string in self.mapping
        self.rwlock.release_read()
        return b

    def free(self, key_string):
        self.rwlock.acquire_write()
        if key_string in self.mapping:
            self.unused_keys.append(self.mapping[key_string])
            del self.mapping[key_string]
        self.rwlock.release_write()

    def dump(self, file_or_str):
        d = dict(max_key=self.max_key, mapping=self.mapping, unused_keys=self.unused_keys, last_key=self.last_key)
        if type(file_or_str) is str:
            with open(file_or_str, 'w') as f:
                pickle.dump(d, f)
        else: pickle.dump(d, file_or_str)

    def load(self, file_or_str):
        if type(file_or_str) is str:
            with open(file_or_str, 'r') as f:
                d = pickle.load(f)
        else: d = pickle.load(file_or_str)
        self.max_key, self.mapping, self.unused_keys, self.last_key = d['max_key'], d['mapping'], d['unused_keys'], d['last_key']


def test_records():
    r = SerializableRecord(a='i', b='i', s='5s')
    assert r.size() == 13
    r['a'] = 2
    r['b'] = 7
    r['s'] = 'hi'
    s = r.pack()
    assert len(s) == 128, len(s)
    assert 'hi' in s
    assert b'\x00' in s
    assert b'\x07' in s
    assert b'\x02' in s

    r2 = SerializableRecord(a='i', b='i', s='5s')
    r2.unpack(s)
    assert r2['a'] == 2
    assert r2['b'] == 7
    assert r2['s'] == 'hi'

    w = WarehouseRec()
    assert 'W_NAME' in w
    assert 'W_TAX' in w
    assert w.fieldnames[0] == 'W_ID', "fields should be in correct order"
    assert w.fieldnames[-1] == 'W_YTD', "fields should be in correct order"
    w['W_ID'] = 3
    w.set(dict(W_NAME="bar", W_STREET_1="zurigo", W_STREET_2="boh",
            W_CITY="Lugano", W_STATE="TI", W_ZIP="6900", W_TAX=12.2, W_YTD=123.33))
    s = w.pack()

    w2 = WarehouseRec()
    w2.unpack(s)
    assert w2['W_ID'] == 3
    assert w2['W_CITY'] == 'Lugano'

    no = NewOrderRec()
    no.set((1, 2, 3))
    assert no['NO_O_ID'] == 1, "inserted from correct index in tuple"
    assert no['NO_D_ID'] == 2, "inserted from correct index in tuple"
    assert no['NO_W_ID'] == 3, "inserted from correct index in tuple"

    for rt in tpcc_record_types:
        r = rt()
        #print r.__class__.__name__, r.size()
        assert r.size() < 128, "%s struct size is too big: %d bytes" % (r.__class__.__name__, r.size())



def test_bitkeymap():
    m = BitKeyMap(bits=4)
    keys = map(str, xrange(1, 16))
    for k in keys:
        assert m.get(k) == int(k) # should be inserted
        assert m.get(k) == int(k) # now it's in the map

    assert len(m.unused_keys) == 0

    try:
        m.get('17')
        assert "There shouldn't be any free bits left" and False
    except AssertionError:
        raise
    except Exception as e:
        assert 'exhausted' in e.message

    m.free('3')
    assert len(m.unused_keys) == 1
    assert m.get('unused3') == 3
    m.free('5')
    m.free('6')
    assert len(m.unused_keys) == 2
    assert m.get('unused6') == 6
    assert m.get('unused5') == 5

    try:
        m.get('nospace')
        assert "There shouldn't be any free bits left" and False
    except AssertionError:
        raise
    except Exception as e:
        assert 'exhausted' in e.message

if __name__ == '__main__':
    test_records()
    test_bitkeymap()
