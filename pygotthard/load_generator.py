#!/usr/bin/env python
import argparse
from threading import Thread
from gotthard import *
from random import gauss
from time import sleep
from numpy.random import choice
import re

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

op_name_to_type = {'R': TXN_READ, 'W': TXN_WRITE, 'A': TXN_VALUE}

def makeRTxn(txnstr):
    txnsr

class TxnFactory:
    re_tmpl = re.compile('([A-Z]+)\(([^,]+),?\s*([^)]+)?\)')

    def __init__(self, templates, p):
        self.templates = templates
        self.p = p

    def _makeOp(self, op_tuple):
        op_name, key = op_tuple[:2]
        value = op_tuple[2] if len(op_tuple) > 2 else ''
        if value.upper() == 'RAND': value = str(choice([chr(c) for c in xrange(97, 123)]))
        return TxnOp(key=int(key), value=value, t=op_name_to_type[op_name])

    def _makeTxn(self, tmpl):
        op_tuples = self.re_tmpl.findall(tmpl)
        assert op_tuples
        return map(self._makeOp, op_tuples)

    def generate(self):
        tmpl = choice(self.templates, p=self.p)
        return self._makeTxn(tmpl)


class RandomClient(Thread, GotthardClient):
    def __init__(self, count, log, store_addr, think, think_var, txn_templates, pdf):
        GotthardClient.__init__(self, store_addr=store_addr, logger=log)
        Thread.__init__(self)
        self.think = think
        self.think_var = think_var

        tf = TxnFactory(txn_templates, pdf)
        self.transactions = [tf.generate() for _ in xrange(count)]

    def run(self):
        if self.think and self.think_var: think_sigma = self.think * self.think_var
        with self:
            for txn in self.transactions:
                while True:
                    res = self.req(txn)
                    if res.status == STATUS_OK: break
                    # otherwise, fix the assertion operations
                    assertion_ops = [o for o in txn if o.type == TXN_VALUE]
                    for op in assertion_ops:
                        correction = res.op(k=op.key, t=TXN_VALUE)
                        if not correction: continue
                        op.value = correction.value

                if self.think:
                    sleep(abs(gauss(self.think, think_sigma)) if self.think_var else self.think)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=1)
    parser.add_argument("--count", "-c", type=int, help="number of transactions to perform", default=1000)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    parser.add_argument("--id", "-i", type=int, help="assign cl_id starting from this value", default=None)
    parser.add_argument("--think", "-t", type=float, help="think time (s) between successful transactions", default=None)
    parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=None)
    parser.add_argument("--pdf", "-p", type=lambda s: map(float, s.split(',')), help="Probability of each transaction. Each within [0.0, 1.0]",
            default=[0.85, 0.15])
    parser.add_argument("--transactions", "-T", type=lambda s: s.split('|'), help="Transactions to execute", required=False,
            default=['R(1)', 'A(1, RAND) W(1, RAND)'])
    args = parser.parse_args()

    store_addr = (args.host, args.port)

    logger = GotthardLogger(args.log) if args.log else None

    clients = []
    for n in xrange(args.num_clients):
        cl = RandomClient(args.count, logger, store_addr, args.think, args.think_var, args.transactions, args.pdf)
        if not args.id is None: cl.cl_id = args.id + n
        clients.append(cl)

    for cl in clients: cl.start()
    for cl in clients: cl.join()
    if logger: logger.close()
