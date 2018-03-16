#!/usr/bin/env python

import sys
import multiprocessing
import json
import numpy as np
from os import path, listdir

done_dir = sys.argv[-1]
exp_dirs = [path.join(done_dir, d) for d in listdir(done_dir)]

TXN_NAMES = ['delivery', 'new_order', 'order_status', 'payment', 'stock_level']

def loadResultFile(filename):
    results = {}

    if filename.endswith('baseline_results.txt'):
        results['mode'] = 'baseline'
    else:
        results['mode'] = 'gotthard'

    txn_lats = dict((name, []) for name in TXN_NAMES)
    txn_aborts = dict((name, 0) for name in TXN_NAMES)
    txn_switch_aborts = dict((name, 0) for name in TXN_NAMES)

    results['num_clients'] = 0
    stats_section = False
    with open(filename, 'r') as f:
        for line in f:
            if '] INFO : Executing benchmark for' in line:
                results['num_clients'] += 1
                continue
            if '] INFO : CLIENT_STATS: ' in line:
                js = line[line.index('] INFO : CLIENT_STATS: ')+23:]
                try:
                    client_stats = json.loads(js)
                except Exception as e:
                    print "failed parsing %s" % filename
                    raise e

                for txn, lats in client_stats['txn_lats'].iteritems():
                    txn_lats[txn.lower()].extend(lats)
                for txn, aborts in client_stats['txn_aborts'].iteritems():
                    txn_aborts[txn.lower()] += aborts
                for txn, switch_aborts in client_stats['txn_switch_aborts'].iteritems():
                    txn_switch_aborts[txn.lower()] += switch_aborts

                continue
            if '] INFO : STORE_CPU_PCT: ' in line:
                pct = float(line.split()[-1])
                results['store_cpu_pct'] = pct
                continue
            if line.startswith('Execution Results after '):
                results['duration'] = int(line.split()[-2])
                stats_section = True
                continue
            if stats_section:
                parts = line.split()
                name = parts[0].lower()
                if name not in TXN_NAMES+['total']: continue
                executed, exec_time, rate = parts[1:4]
                results[name + '_rate'] = float(rate)

    with open(filename + '_pay_lats.tsv', 'w') as f:
        f.write('\n'.join(map(str, txn_lats['payment'])))

    for txn, lats in txn_lats.iteritems():
        results[txn + '_avg_lat'] = np.mean(lats)

    txn_counts = dict((name, len(lats)) for name,lats in txn_lats.iteritems())

    txn_store_aborts = dict((name, txn_aborts[name]-txn_switch_aborts[name]) for name in txn_aborts)

    for txn in TXN_NAMES:
        results[txn + '_store_aborts_per_txn'] = txn_store_aborts[txn] / float(txn_counts[txn])

    return results


filenames = []
for exp_dir in exp_dirs:
    filenames.append(path.join(exp_dir, 'out', 'baseline_results.txt'))
    filenames.append(path.join(exp_dir, 'out', 'gotthard_results.txt'))

n_job = None
if n_job is None:
    n_cpu = multiprocessing.cpu_count()
    n_job = n_cpu if n_cpu == 1 else n_cpu - 1

if n_job > 1:
    p = multiprocessing.Pool(n_job)
    results = p.map(loadResultFile, filenames)
else:
    results = map(loadResultFile, filenames)


fields = ['mode', 'num_clients', 'duration', 'total_rate', 'store_cpu_pct']
fields += ['payment_store_aborts_per_txn']
fields += ['order_status_store_aborts_per_txn']

for txn in TXN_NAMES:
    fields.extend([txn + '_rate', txn + '_avg_lat'])


print '\t'.join(fields)
for row in results:
    print '\t'.join(str(row[f]) for f in fields)
