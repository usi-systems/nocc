#!/usr/bin/env python
import argparse
from threading import Thread
from gotthard import *
from random import gauss, randint
from time import sleep
import time
from numpy.random import choice
import re

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

op_name_to_type = {'R': TXN_READ, 'W': TXN_WRITE, 'A': TXN_VALUE}

class TxnEngine:
    re_tmpl = re.compile('([a-zA-Z]+)\(([^,]+),?\s*([^)]+)?\)')
    re_value = re.compile('^([0-9]+|[a-zA-Z])\s*(([+-])\s*([0-9]+|[a-zA-Z]))?$')

    def __init__(self, templates, p, count=None, duration=None):
        assert len(templates) == len(p)
        assert count is not None or duration is not None
        self.p = p
        self.key_symbols = [] # all the symbols. e.g. [x, y, z]
        self.symbol_to_key = {} # maps a symbol to a concrete key. e.g. x:1, y:2
        self.key_to_symbol = {} # maps a concrete key to a symbol. e.g. 1:x, 2:y
        self.symbol_state = {} # the current value for each symbol. e.g. x=23, y=14
        self.max_count = count
        self.count = 0      # number of successfully executed TXNs
        self.duration = duration # optionally, the max duration in seconds
        self.current_txn = None # currently executing TXN

        self.transactions = []
        for tmpl in templates: # for each TXN
            op_tuples = self.re_tmpl.findall(tmpl)
            txn = map(self._parseOp, op_tuples)
            self.transactions.append(txn)

        for n, symbol in enumerate(sorted(self.key_symbols)):
            self.key_to_symbol[n+1] = symbol
            self.symbol_to_key[symbol] = n+1
            self.symbol_state[symbol] = 0

        self._chooseTxn()

    def _parseOp(self, op_tuple):
        op_name, key_symbol = op_tuple[:2]
        op_type = op_name_to_type[op_name]
        if key_symbol not in self.key_symbols: self.key_symbols.append(key_symbol)

        def makeExprLambda(e):
            if len(e) == 0: return (lambda: 0)
            if e.isdigit(): return (lambda: int(e))
            else: return (lambda: self.symbol_state[e])

        if len(op_tuple[2]) > 0:
            val_def = op_tuple[2].strip()
            if val_def.upper() == 'RND':
                value_gen = lambda: str(randint(1, 100))
            elif self.re_value.findall(val_def):
                e = self.re_value.findall(val_def)[0]
                a = makeExprLambda(e[0])
                b = makeExprLambda(e[3])
                value_gen = (lambda: str(a() + b())) if e[2] == '+' else (lambda: str(a() - b()))
            else:
                assert False, "Could not parse value definition: %s" % val_def
        else:
            value_gen = lambda: ''

        return (lambda: TxnOp(key=self.symbol_to_key[key_symbol], t=op_type,
                          value=value_gen()))

    def uponResponse(self, res):
        for op in res.ops:
            if op.type not in [TXN_VALUE, TXN_UPDATED]: continue
            if op.key not in self.key_to_symbol: continue
            symbol = self.key_to_symbol[op.key]
            val_str = op.value.rstrip('\0')
            self.symbol_state[symbol] = int(val_str) if len(val_str) else ''

        successful = False
        if res.status == STATUS_OK:
            successful = True
            self.count += 1
            self._chooseTxn()

        return successful


    def getTxn(self):
        return [opgen() for opgen in self.current_txn]

    def _chooseTxn(self):
        self.current_txn = choice(self.transactions, p=self.p)

    def getInitTxn(self):
        if self.duration is not None:
            self.end_time = time.time() + self.duration
        return [W(key, str(0)) for symbol,key in self.symbol_to_key.items()]

    def done(self):
        if self.duration is not None:
            return time.time() > self.end_time
        else:
            return self.count > self.max_count


class EngineClient(Thread, GotthardClient):
    def __init__(self, count, duration, log, store_addr, think, think_var, txn_templates, pdf, resend_timeout):
        GotthardClient.__init__(self, store_addr=store_addr, logger=log, resend_timeout=resend_timeout)
        Thread.__init__(self)
        self.think = think
        self.think_var = think_var

        self.engine = TxnEngine(txn_templates, pdf, count=count, duration=duration)

    def run(self):
        if self.think and self.think_var: think_sigma = self.think * self.think_var
        with self:
            init_txn = self.engine.getInitTxn()
            res = self.req(init_txn)
            assert res.status == STATUS_OK
            self.engine.uponResponse(res)
            while not self.engine.done():
                txn = self.engine.getTxn()
                res = self.req(txn)
                successful = self.engine.uponResponse(res)
                if successful and self.think:
                    sleep(abs(gauss(self.think, think_sigma)) if self.think_var else self.think)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=1)
    parser.add_argument("--count", "-c", type=int, help="number of transactions to perform", default=None)
    parser.add_argument("--resend-timeout", "-r", type=float, help="timeout to resend request, in secs", default=None)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    parser.add_argument("--id", "-i", type=int, help="assign cl_id starting from this value", default=None)
    parser.add_argument("--think", "-t", type=float, help="think time (s) between successful transactions", default=None)
    parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=None)
    parser.add_argument("--duration", "-d", type=float, help="Maximum duration of experiment", default=None)
    parser.add_argument("--pdf", "-p", type=lambda s: map(float, s.split(',')), help="Probability of each transaction. Each within [0.0, 1.0]",
            default=[0.85, 0.15])
    parser.add_argument("--transactions", "-T", help="Transactions to execute", required=False,
            type=lambda s: map(lambda t: t.strip(), s.split('|')),
            default=['R(1)', 'A(1, RND) W(1, RND)'])
    args = parser.parse_args()

    if args.count is None and args.duration is None:
        parser.error("Either --count or --duration is required")

    store_addr = (args.host, args.port)

    logger = GotthardLogger(args.log) if args.log else None

    pdf = args.pdf
    missing_p = len(args.transactions) - len(args.pdf)
    if missing_p > 0:
        pdf += [(1.0-sum(pdf))/missing_p,]*missing_p

    if sum(pdf) != 1.0:
        missing = 1 - sum(pdf)
        assert sum(pdf) + missing == 1
        for n in xrange(len(pdf)):
            if pdf[n] + missing < 0: continue
            print "Warning: sum(pdf)=%f! Adding %f to pdf[%d]" % (sum(pdf), missing, n)
            pdf[n] += missing
            break

    for txn, p in zip(args.transactions, pdf):
        print "P=%s: %s" % (str(p), txn)

    clients = []
    for n in xrange(args.num_clients):
        cl = EngineClient(args.count, args.duration, logger, store_addr, args.think, args.think_var, args.transactions, pdf, args.resend_timeout)
        if not args.id is None: cl.cl_id = args.id + n
        clients.append(cl)

    for cl in clients: cl.start()
    for cl in clients: cl.join()
    if logger: logger.close()
