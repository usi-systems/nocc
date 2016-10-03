#!/usr/bin/env python
import json
import re
import argparse
import multiprocessing
import sys
import numpy as np
from os import path, listdir
sys.path.append('..')
from pygotthard import *

args = None

def parseLog(func, filename):
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = unicode(line, errors='replace')
            event = json.loads(line)
            func(event)

default_st = dict(abort_count=0, optimistic_abort_count=0,
                    sent_count=0, recv_count=0,
                    start=None, end=None)


def getClientStats(filename):
    st = default_st.copy()

    outstanding_req_time = {} # the time of req_ids awaiting a response
    req_rtts = [] # the RTT for each txn msg

    cur_txn = dict(start_time=None) # the last req time before a successful response
    txn_times = [] # the times it takes to successfully complete a TXN
    def clientHook(e):
        if e['event'] == 'sent':
            if st['start'] is None: st['start'] = e['time']
            st['sent_count'] += 1
            if cur_txn['start_time'] is None:
                cur_txn['start_time'] = e['time']
            if e['req']['req_id'] not in outstanding_req_time:
                outstanding_req_time[e['req']['req_id']] = e['time']
        elif e['event'] == 'received':
            st['end'] = e['time']
            st['recv_count'] += 1
            if e['res']['status'] == 'OPTIMISTIC_ABORT': st['optimistic_abort_count'] += 1
            if e['res']['status'] == 'ABORT': st['abort_count'] += 1
            if e['res']['status'] == 'OK' and cur_txn['start_time']:
                txn_times.append(e['time'] - cur_txn['start_time'])
                cur_txn['start_time'] = None

            if e['res']['req_id'] in outstanding_req_time:
                req_rtts.append(e['time'] - outstanding_req_time[e['res']['req_id']])

    parseLog(clientHook, filename)
    st['avg_txn_time'] = np.mean(txn_times)
    st['avg_req_rtt'] = np.mean(req_rtts)
    return st

def getServerStats(filename):
    st = default_st.copy()
    def serverHook(e):
        if e['event'] == 'sent':
            st['sent_count'] += 1
            st['end'] = e['time']
            if e['res']['status'] == 'ABORT': st['abort_count'] += 1
        elif e['event'] == 'received':
            if st['start'] is None: st['start'] = e['time']
            st['recv_count'] += 1
    parseLog(serverHook, filename)
    return st

re_abort = re.compile('DEBUG: cl_id (\d+): (.*) \(TXN (\d+)\.(\d+)\): Gotthard(Optimistic)?AbortFrom(Store|Switch)')

def getTpccStats(filename):
    st = dict(tpcc_aborts=0,tpcc_opti_aborts=0,tpcc_switch_aborts=0,tpcc_num_clients=0)
    cl_aborts = {}
    txn_aborts = {}
    results = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            if len(results) or line.strip().startswith('Execution Results after '):
                results.append(line)
            elif 'DEBUG: Creating client pool with ' in line:
                st['tpcc_num_clients'] = int(line.strip().split()[-2])
            else:
                m = re_abort.findall(line)
                if not m: continue
                assert len(m) == 1
                cl_id, txn_name, txn_num, abort_cnt, optimistic, abort_from = m[0]
                st['tpcc_aborts'] += 1
                if optimistic == 'Optimistic': st['tpcc_opti_aborts'] += 1
                if abort_from == 'Switch': st['tpcc_switch_aborts'] += 1
                if cl_id not in cl_aborts: cl_aborts[cl_id] = {}
                cl_aborts[cl_id][txn_num] = int(abort_cnt)
                if txn_name not in txn_aborts: txn_aborts[txn_name] = {}
                txn_aborts[txn_name][txn_num] = int(abort_cnt)

    for line in map(lambda l: l.strip(), results[3:]):
        if line.startswith('----'): continue
        r = line.split()
        st_name = r[0].lower()
        st['tpcc_' + st_name + '_cnt'] = int(r[1].strip())
        st['tpcc_' + st_name + '_rate'] = float(r[3].strip())

    # How many times is a TXN retried until commit (i.e. abort cnt)?
    retry_cnts = sum([cl_aborts[cl_id].values() for cl_id in cl_aborts], [])
    for t in txn_aborts:
        st['tpcc_%s_avg_retry' % t.lower()] = np.mean(txn_aborts[t].values())
    st['tpcc_avg_retry_cnt'] = np.mean(retry_cnts)
    st['tpcc_max_retry_cnt'] = max(retry_cnts)

    return st


def getExperimentStats(experiment_dir):
    experiment_dir = path.abspath(experiment_dir)
    log_dir = path.join(experiment_dir, "logs")
    with open(path.join(experiment_dir, "experiment.json"), 'r') as f:
        conf = json.load(f)
    if not path.exists(log_dir): raise Exception('Directory does not exist: %s'%log_dir)
    if not path.isdir(log_dir): raise Exception('Log directory is not a directory: %s'%log_dir)

    log_filenames = filter(path.isfile, [path.join(log_dir, f) for f in listdir(log_dir) if f.endswith('.log')])

    server_log_filenames = [f for f in log_filenames if 'server' in path.basename(f)]
    if len(server_log_filenames) < 1: raise Exception("No server logs found in: %s"%log_dir)

    stdout_log_filenames = [f for f in log_filenames if f.endswith('stdout.log')]

    client_log_filenames = [f for f in log_filenames if f not in server_log_filenames + stdout_log_filenames]
    if len(client_log_filenames) < 1: raise Exception("No client logs found in: %s"%log_dir)
    client_names = [path.basename(f).split('.log')[0] for f in client_log_filenames]

    srv_stats = getServerStats(server_log_filenames[0])
    cl_stats = [dict(getClientStats(f), **dict(name=name)) for name, f
            in zip(client_names, client_log_filenames)]

    summary = dict()
    summary['total_aborts'] = sum([st['abort_count'] for st in cl_stats]) + sum([st['optimistic_abort_count'] for st in cl_stats])
    summary['total_sent'] = sum([st['sent_count'] for st in cl_stats])
    summary['total_recv'] = sum([st['recv_count'] for st in cl_stats])
    summary['avg_txn_time'] = np.mean([st['avg_txn_time'] for st in cl_stats])
    summary['avg_req_rtt'] = np.mean([st['avg_req_rtt'] for st in cl_stats])
    summary['srv_sent'] = srv_stats['sent_count']
    summary['srv_recv'] = srv_stats['recv_count']
    summary['srv_abort'] = srv_stats['abort_count']

    summary['switch_abort_ratio'] = 0 if summary['total_aborts'] == 0 else float(summary['total_aborts'] - summary['srv_abort']) / summary['total_aborts']

    summary['first_start_time'] = min([st['start'] for st in cl_stats])
    summary['last_start_time'] = max([st['start'] for st in cl_stats])
    summary['first_end_time'] = min([st['end'] for st in cl_stats])
    summary['last_end_time'] = max([st['end'] for st in cl_stats])
    summary['elapsed_time'] = summary['last_end_time'] - summary['first_start_time']
    summary['concurrent_time'] = summary['first_end_time'] - summary['last_start_time']

    if args.tpcc:
        assert len(stdout_log_filenames) == 1
        tpcc_stats = getTpccStats(stdout_log_filenames[0])
        for k, v in tpcc_stats.items(): summary[k] = v


    total_delta = conf['total_delay'] if 'total_delay' in conf else conf['server']['delay'] + conf['clients'][0]['delay']

    experiment_params = dict(client_d=conf['clients'][0]['delay'],
                store_D=conf['server']['delay'],
                total_delta=total_delta,
                num_clients=len(conf['clients']),
                think=conf['think_s'] if 'think_s' in conf else 0,
                think_var=conf['think_v'] if 'think_v' in conf else 0,
                mode=conf['switch']['mode'])
    if 'req_count' in conf: experiment_params['req_count'] = conf['req_count']
    D, d = float(experiment_params['store_D']), float(experiment_params['client_d'])
    #experiment_params['delta_ratio'] = D / d
    #experiment_params['delta_diff_ratio'] = (D-d) / (D+d)
    experiment_params['client_d_ratio'] = d / (D+d)


    return dict(summary, **experiment_params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=str, help="experiment directory", nargs='*')
    parser.add_argument("--jobs", "-j", type=int, action="store", default=None, help="number of parallel jobs")
    parser.add_argument("--json", "-J", action="store_true", help="output as JSON")
    parser.add_argument("--tpcc", "-t", action="store_true", help="parse TPCC data from client STDOUT log file")
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
