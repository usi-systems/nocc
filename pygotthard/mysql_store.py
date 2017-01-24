import mysql.connector
import time
from gotthard import *
from Queue import Queue

MYSQL_USER='gotthard'
MYSQL_PASS='1234'
MYSQL_DB='gotthard'

class MySQLStore:

    def __init__(self):
        self.connections = Queue()
        self.concurrent_connections = 10
        for _ in xrange(self.concurrent_connections):
            cnx = mysql.connector.connect(user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB)
            self.connections.put(cnx)

    def clear(self):
        cnx = self.connections.get()
        cur = cnx.cursor()
        cur.execute('TRUNCATE store')
        cur.execute('COMMIT')
        self.connections.put(cnx)

    def applyTxn(self, ops=[]):
        if len(ops) < 1: return (STATUS_BADREQ, [])

        rb_ops = [o for o in ops if o.type == TXN_VALUE] # read before
        r_ops = [o for o in ops if o.type == TXN_READ]
        w_ops = [o for o in ops if o.type == TXN_WRITE]
        res_ops = []

        cnx = self.connections.get()
        cur = cnx.cursor()
        cur.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")

        def readKeys(keys):
            if len(keys) == 0: return []
            cur.execute("SELECT k,v FROM store WHERE " + " OR ".join(["k=%s" for _ in xrange(len(keys))]), keys)
            return [TxnOp(t=TXN_VALUE, key=k, value=str(v)) for k,v in cur]

        def writeKeys(kv_tuples):
            cur.executemany("INSERT INTO store (k, v) VALUES (%s, %s) ON DUPLICATE KEY UPDATE v=VALUES(v)", kv_tuples)

        def tuplist(ops):
            return [(o.key, o.value) for o in ops]

        # Check that the read-befores are valid:
        if len(rb_ops):
            old = tuplist(rb_ops)
            sql = "SELECT k,v FROM store WHERE "
            sql += " OR ".join(["(k=%s AND v!=%s)" for _ in range(len(old))])
            cur.execute(sql, sum(old, ()))

            corrections = [TxnOp(t=TXN_VALUE, key=k, value=str(v)) for k,v in cur]
            if len(corrections):
                # also, invalidate any optimistic writes that may be cached at the switch:
                undo_w = readKeys([o.key for o in w_ops if o.key not in [c.key for c in corrections]])
                cur.execute('ROLLBACK')
                self.connections.put(cnx)
                return (STATUS_ABORT, corrections + undo_w)

        # Process all the write operations:
        res_ops += [TxnOp(t=TXN_UPDATED, key=o.key, value=o.value) for o in w_ops]
        writeKeys(tuplist(w_ops))

        # Process all the reads
        res_ops += readKeys([o.key for o in r_ops])
        res_ops += [TxnOp(t=TXN_VALUE, key=o.key) for o in r_ops if o.key not in [r.key for r in res_ops]]

        cur.execute('COMMIT')
        self.connections.put(cnx)

        return (STATUS_OK, res_ops)

    def dump(self):
        pass
    def load(self):
        pass
