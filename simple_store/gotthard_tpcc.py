import struct
import re

MAX_STR_SIZE=12

def sqlTypeToStructFormat(t):
    if re.match('^([xcbB?hHiIlLqQfdpP]|\d+(s|p))$', t): return t # already a struct fmt
    inttypes = dict(TINYINT='c', SMALLINT='h', BIGINT='q', INT='i', INTEGER='i',
                    FLOAT='d', DEC='d', DECIMAL='d', TIMESTAMP='q')
    intname = t.split('(')[0].upper()
    if intname in inttypes: return inttypes[intname]
    m = re.findall('\((.*)\)', t)
    if len(m) != 1: raise Exception("Unable to convert SQL type %s to a struct format" % t)
    size = int(m[0])
    return '%ds' % min(size, MAX_STR_SIZE)


class SerializableRecord:

    def __init__(self, fields=None, **field_dict):
        self.fieldtypes = map(lambda f: (f[0], sqlTypeToStructFormat(f[1])),
            fields if fields else list(field_dict.iteritems()))
        self.fieldnames = map(lambda x:x[0], self.fieldtypes)
        self.fmt = '!'
        self.fields = {}
        for f, t in self.fieldtypes:
            self.fields[f] = None
            self.fmt += t
        self.struct = struct.Struct(self.fmt)

    def unpack(self, binstr):
        binstr = binstr[:self.size()]
        assert len(binstr) == self.size()
        self.fields = dict(zip(self.fieldnames, self.struct.unpack(binstr)))
        for f in [f for f,t in self.fieldtypes if 's' in t]:
            self.fields[f] = self.fields[f].rstrip('\0')

    def pack(self):
        return self.struct.pack(*[self.fields[f] for f in self.fieldnames])

    def size(self):
        return self.struct.size

    def key(self):
        return '.'.join(map(str, sum([(k, self.fields[k]) for k in self.keyfields], ())))

    def __str__(self):
        return str(self.fields)


class WarehouseRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                W_ID="SMALLINT",
                W_NAME="VARCHAR(16)",
                W_STREET_1="VARCHAR(32)",
                W_STREET_2="VARCHAR(32)",
                W_CITY="VARCHAR(32)",
                W_STATE="VARCHAR(2)",
                W_ZIP="VARCHAR(9)",
                W_TAX="FLOAT",
                W_YTD="FLOAT")
        self.keyfields = ['W_ID']


class DistrictRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                D_ID="TINYINT",
                D_W_ID="SMALLINT",
                D_NAME="VARCHAR(16)",
                D_STREET_1="VARCHAR(32)",
                D_STREET_2="VARCHAR(32)",
                D_CITY="VARCHAR(32)",
                D_STATE="VARCHAR(2)",
                D_ZIP="VARCHAR(9)",
                D_TAX="FLOAT",
                D_YTD="FLOAT",
                D_NEXT_O_ID="INT")
        self.keyfields = ['D_W_ID', 'D_ID']

class ItemRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                I_ID="INTEGER",
                I_IM_ID="INTEGER",
                I_NAME="VARCHAR(32)",
                I_PRICE="FLOAT",
                I_DATA="VARCHAR(64)")

class CustomerRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                C_ID="INTEGER",
                C_D_ID="TINYINT",
                C_W_ID="SMALLINT",
                C_FIRST="VARCHAR(32)",
                C_MIDDLE="VARCHAR(2)",
                C_LAST="VARCHAR(32)",
                #C_STREET_1="VARCHAR(32)",
                #C_STREET_2="VARCHAR(32)",
                #C_CITY="VARCHAR(32)",
                #C_STATE="VARCHAR(2)",
                C_ZIP="VARCHAR(9)",
                C_PHONE="VARCHAR(32)",
                C_SINCE="TIMESTAMP",
                C_CREDIT="VARCHAR(2)",
                C_CREDIT_LIM="FLOAT",
                C_DISCOUNT="FLOAT",
                C_BALANCE="FLOAT",
                C_YTD_PAYMENT="FLOAT",
                C_PAYMENT_CNT="INTEGER",
                C_DELIVERY_CNT="INTEGER",
                C_DATA="VARCHAR(500)")
        self.keyfields = ['C_W_ID', 'C_D_ID', 'C_ID']

class HistoryRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                H_C_ID="INTEGER",
                H_C_D_ID="TINYINT",
                H_C_W_ID="SMALLINT",
                H_D_ID="TINYINT",
                H_W_ID="SMALLINT",
                H_DATE="TIMESTAMP",
                H_AMOUNT="FLOAT",
                H_DATA="VARCHAR(32)")
        self.keyfields = ['H_W_ID', 'H_D_ID', 'H_C_ID']

class StockRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                S_I_ID="INTEGER",
                S_W_ID="SMALLINT",
                S_QUANTITY="INTEGER",
                S_DIST_01="VARCHAR(32)",
                #S_DIST_02="VARCHAR(32)",
                #S_DIST_03="VARCHAR(32)",
                #S_DIST_04="VARCHAR(32)",
                #S_DIST_05="VARCHAR(32)",
                #S_DIST_06="VARCHAR(32)",
                #S_DIST_07="VARCHAR(32)",
                #S_DIST_08="VARCHAR(32)",
                #S_DIST_09="VARCHAR(32)",
                #S_DIST_10="VARCHAR(32)",
                S_YTD="INTEGER",
                S_ORDER_CNT="INTEGER",
                S_REMOTE_CNT="INTEGER",
                S_DATA="VARCHAR(64)")
        self.keyfields = ['S_W_ID', 'S_I_ID']

class OrderRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                O_ID="INTEGER",
                O_C_ID="INTEGER",
                O_D_ID="TINYINT",
                O_W_ID="SMALLINT",
                O_ENTRY_D="TIMESTAMP",
                O_CARRIER_ID="INTEGER",
                O_OL_CNT="INTEGER",
                O_ALL_LOCAL="INTEGER")
        self.keyfields = ['O_W_ID', 'O_D_ID', 'O_C_ID', 'O_ID']

class NewOrderRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                NO_O_ID="INTEGER",
                NO_D_ID="TINYINT",
                NO_W_ID="SMALLINT")
        self.keyfields = ['NO_W_ID', 'NO_D_ID', 'NO_O_ID']

class OrderLineRec(SerializableRecord):
    def __init__(self):
        SerializableRecord.__init__(self,
                OL_O_ID="INTEGER",
                OL_D_ID="TINYINT",
                OL_W_ID="SMALLINT",
                OL_NUMBER="INTEGER",
                OL_I_ID="INTEGER",
                OL_SUPPLY_W_ID="SMALLINT",
                OL_DELIVERY_D="TIMESTAMP",
                OL_QUANTITY="INTEGER",
                OL_AMOUNT="FLOAT",
                OL_DIST_INFO="VARCHAR(32)")
        self.keyfields = ['OL_W_ID', 'OL_D_ID', 'OL_O_ID', 'OL_I_ID']

tpcc_record_types = [WarehouseRec, DistrictRec, ItemRec, CustomerRec, HistoryRec, StockRec, OrderRec, NewOrderRec, OrderLineRec]

class BitKeyMap:
    """Map a string to a limited number of bits"""

    def __init__(self, bits=16):
        self.max_key = 2 ** bits
        self.mapping = {}
        self.unused_keys = [] # keys are added to this as they are deleted
        self.last_key = 0

    def get(self, key_string):
        if key_string not in self.mapping:
            if self.last_key < self.max_key-1:
                self.last_key += 1
                self.mapping[key_string] = self.last_key
            else:
                if len(self.unused_keys) == 0:
                    raise Exception("Mapping is full; all bits have been exhausted")
                self.mapping[key_string] = self.unused_keys.pop()
        return self.mapping[key_string]

    def free(self, key_string):
        self.unused_keys.append(self.mapping[key_string])
        del self.mapping[key_string]


def test_records():
    r = SerializableRecord(a='i', b='i', s='5s')
    assert r.size() == 13
    r.fields['a'] = 2
    r.fields['b'] = 7
    r.fields['s'] = 'hi'
    s = r.pack()
    assert len(s) == 13
    assert 'hi' in s
    assert b'\x00' in s
    assert b'\x07' in s
    assert b'\x02' in s

    r2 = SerializableRecord(a='i', b='i', s='5s')
    r2.unpack(s)
    assert r2.fields['a'] == 2
    assert r2.fields['b'] == 7
    assert r2.fields['s'] == 'hi'

    w = WarehouseRec()
    assert 'W_ID' in w.fields
    assert 'W_TAX' in w.fields
    w.fields = dict(W_ID=3, W_NAME="bar", W_STREET_1="zurigo", W_STREET_2="boh",
            W_CITY="Lugano", W_STATE="TI", W_ZIP="6900", W_TAX=12.2, W_YTD=123.33)
    s = w.pack()

    w2 = WarehouseRec()
    w2.unpack(s)
    assert w2.fields['W_ID'] == 3
    assert w2.fields['W_CITY'] == 'Lugano'

    for rt in tpcc_record_types:
        r = rt()
        print r.__class__.__name__, r.size()
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
