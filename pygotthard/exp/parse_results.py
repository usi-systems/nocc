#!/usr/bin/env python

import sys
import multiprocessing
import json
import numpy as np
from os import path, listdir

done_dir = sys.argv[-1]
exp_dirs = [path.join(done_dir, d) for d in listdir(done_dir)]

def loadResultFile(filename):
    cached_filename = path.splitext(filename)[0] + '.cached.json'

    if path.isfile(cached_filename):
        with open(cached_filename, 'r') as f:
            return json.load(f)

    with open(filename, 'r') as f:
        results = json.load(f)

    if filename.endswith('baseline_results.json'):
        results['mode'] = 'baseline'
    else:
        results['mode'] = 'gotthard'

    if 'duration' not in results: results['duration'] = 180

    if results['zipf'] is None:
        results['write_ratio'] = results['pdf'][0]

    elapsed = np.mean(results['elapseds'])
    total_txns = sum(results['txn_counts'])
    total_reqs = sum(results['req_counts']) if 'req_counts' in results else 0
    #total_res = sum(results['res_counts'])
    #total_switch_res = sum(results['switch_res_counts'])
    total_aborts = sum(results['abort_counts'])
    total_switch_aborts = sum(results['switch_abort_counts'])
    #results['switch_ratio'] = total_switch_res / float(total_res)
    results['avg_req_rate'] = total_reqs / elapsed
    results['avg_txn_rate'] = total_txns / elapsed
    results['avg_txn_lat'] = 0
    results['avg_req_lat'] = 0
    #results['avg_txn_lat'] = np.mean([lat for lats in results['txn_lats'] for lat in lats]) * 1000 # convert to ms
    #results['avg_req_lat'] = np.mean([lat for lats in results['req_lats'] for lat in lats]) * 1000 # convert to ms
    if 'avg_txn_lats' in results:
        results['avg_txn_lat'] = np.mean(results['avg_txn_lats']) * 1000 # convert to ms

    results['store_aborts'] = total_aborts - total_switch_aborts
    results['store_aborts_per_txn'] = results['store_aborts'] / float(total_txns)

    #store_res_count = total_res - total_switch_res
    #results['store_msgs_per_txn'] = store_res_count / float(total_txns)
    if 'txn_lats' in results: del results['txn_lats']
    if 'req_lats' in results: del results['req_lats']

    with open(cached_filename, 'w') as f:
        json.dump(results, f)

    return results


filenames = []
for exp_dir in exp_dirs:
    filenames.append(path.join(exp_dir, 'out', 'baseline_results.json'))
    filenames.append(path.join(exp_dir, 'out', 'gotthard_results.json'))

n_job = 2
if n_job is None:
    n_cpu = multiprocessing.cpu_count()
    n_job = n_cpu if n_cpu == 1 else n_cpu - 1

if n_job > 1:
    p = multiprocessing.Pool(n_job)
    results = p.map(loadResultFile, filenames)
else:
    results = map(loadResultFile, filenames)


fields = ['mode', 'num_clients', 'write_ratio', 'zipf', 'duration', 'avg_txn_rate', 'avg_txn_lat', 'avg_req_lat', 'store_cpu_pct', 'store_aborts_per_txn']

print '\t'.join(fields)
for row in results:
    print '\t'.join(str(row[f]) for f in fields)
