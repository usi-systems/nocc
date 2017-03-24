#!/usr/bin/env python
import json
import re
import argparse
import multiprocessing
import sys
import numpy as np
import os
from os import path, listdir
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'twopc.p4app'))

from minitxn import *

args = None

#import warnings
#warnings.simplefilter("error")

def getLogTimes(filename):
    try:
        with open(filename, 'rb') as fh:
            first_line = next(fh).decode(errors='replace')
            fh.seek(-4096, 2)
            last_line = fh.readlines()[-1].decode(errors='replace')
        first = json.loads(first_line)
        last = json.loads(last_line)
        return (first['time'], last['time'])
    except:
        sys.stderr.write("Error parsing file: %s\n" % filename)
        raise

def parseLog(func, filename):
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = unicode(line, errors='replace')
            event = json.loads(line)
            func(event)


def getClientStats(filename, start=None, end=None):
    st = dict(from_switch=0)
    req_rtts = [] # list of the RTT for all requests
    txns = []    # stats per TXN (includes TXNs from all clients)
    clients = {} # per-client request and TXN state

    def clientHook(e):
        if start is not None and e['time'] < start: return
        if end is not None and e['time'] > end: return
        if 'req' in e:
            if e['req']['cl_id'] not in clients:
                clients[e['req']['cl_id']] = dict(reqs={})
            reqs = clients[e['req']['cl_id']]['reqs']
            if e['req']['txn_id'] not in reqs:
                reqs[e['req']['txn_id']] = e['time']
        elif 'res' in e:
            if e['res']['cl_id'] not in clients: return
            reqs = clients[e['res']['cl_id']]['reqs']
            if 'from_switch' not in e['res']: e['res']['from_switch'] = False

            if e['res']['txn_id'] in reqs:
                req_rtts.append(e['time'] - reqs[e['res']['txn_id']])
                del reqs[e['res']['txn_id']]

    parseLog(clientHook, filename)
    st['req_cnt'] = len(req_rtts)
    st['avg_req_rtt'] = np.mean(req_rtts)
    return st


def getExperimentStats(experiment_dir):
    experiment_dir = path.abspath(experiment_dir)
    log_dir = path.join(experiment_dir, "logs")
    with open(path.join(experiment_dir, "p4app.json"), 'r') as f:
        manifest = json.load(f)
    if not path.exists(log_dir): raise Exception('Directory does not exist: %s'%log_dir)
    if not path.isdir(log_dir): raise Exception('Log directory is not a directory: %s'%log_dir)

    log_filenames = filter(path.isfile, [path.join(log_dir, f) for f in listdir(log_dir) if f.endswith('.log')])

    client_log_filenames = [f for f in log_filenames if 'client' in f]
    if len(client_log_filenames) < 1: raise Exception("No client logs found in: %s"%log_dir)
    client_names = [path.basename(f).split('.log')[0] for f in client_log_filenames]

    # Remove empty log files:
    client_log_filenames = [f for f in client_log_filenames if os.path.getsize(f) > 0]

    start_times, end_times = zip(*map(getLogTimes, client_log_filenames))
    start_cutoff, end_cutoff = max(start_times), min(end_times)
    start_cutoff += 0.5
    end_cutoff -= 0.5

    cl_stats = [dict(getClientStats(f, start=start_cutoff, end=end_cutoff), **dict(name=name)) for name, f
            in zip(client_names, client_log_filenames)]

    summary = dict()

    summary['total_duration'] = max(end_times) - min(start_times)
    summary['duration'] = end_cutoff - start_cutoff
    summary['req_cnt'] = sum([st['req_cnt'] for st in cl_stats])
    summary['req_rate'] = summary['req_cnt'] / summary['duration']
    summary['req_rtt'] = np.mean([st['avg_req_rtt'] for st in cl_stats])

    conf = manifest['targets']['default']
    params = conf['parameters'] if 'parameters' in conf else dict()
    experiment_params = dict(params,
            program=manifest['program'].split('/')[-1].split('.p4')[0]
            )


    return dict(summary, **experiment_params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=str, help="experiment directory", nargs='+')
    parser.add_argument("--jobs", "-j", type=int, action="store", default=None, help="number of parallel jobs")
    parser.add_argument("--json", "-J", action="store_true", help="output as JSON")
    parser.add_argument("--latencies", "-l", action="store_true", help="output lists of latencies for using in a CDF")
    parser.add_argument("--header", "-H", action="store_true", help="print header")
    args = parser.parse_args()

    n_job = args.jobs
    if n_job is None:
        n_cpu = multiprocessing.cpu_count()
        n_job = n_cpu if n_cpu == 1 else n_cpu - 1

    if n_job > 1:
        p = multiprocessing.Pool(n_job)
        summaries = p.map(getExperimentStats, args.dir)
    else:
        summaries = map(getExperimentStats, args.dir)

    if args.json:
        print json.dumps(summaries, indent=1, sort_keys=True)
    else:
        keys = sorted(summaries[0].keys())
        if args.header:
            print '\t'.join(keys)
        print '\n'.join(['\t'.join([str(s[k] if k in s else 0) for k in keys]) for s in summaries])
