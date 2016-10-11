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

default_st = dict(store_abort_cnt=0, switch_abort_cnt=0, opti_abort_cnt=0,
                    sent_count=0, recv_count=0,
                    start=None, end=None)


def getClientStats(filename):
    st = default_st.copy()
    req_rtts = [] # list of the RTT for all requests
    txns = []    # stats per TXN (includes TXNs from all clients)
    clients = {} # per-client request and TXN state

    def clientHook(e):
        if e['event'] == 'sent':
            if e['req']['cl_id'] not in clients:
                clients[e['req']['cl_id']] = dict(reqs={}, txn=dict(start=None, abrt_cnt=0, has_assert=None))
            reqs, txn = clients[e['req']['cl_id']]['reqs'], clients[e['req']['cl_id']]['txn']
            if st['start'] is None: st['start'] = e['time']
            st['sent_count'] += 1
            if txn['start'] is None:
                txn.update(dict(start=e['time'], abrt_cnt=0,
                    has_assert=len(filter(lambda o: o['t'] == 'V', e['req']['ops'])) > 0))
            if e['req']['req_id'] not in reqs:
                reqs[e['req']['req_id']] = e['time']
        elif e['event'] == 'received':
            reqs, txn = clients[e['res']['cl_id']]['reqs'], clients[e['res']['cl_id']]['txn']
            if 'from_switch' not in e['res']: e['res']['from_switch'] = False
            st['end'] = e['time']
            st['recv_count'] += 1

            if e['res']['status'] == 'ABORT' and e['res']['from_switch']:
                st['switch_abort_cnt'] += 1
            elif e['res']['status'] == 'ABORT':
                st['store_abort_cnt'] += 1
            elif e['res']['status'] == 'OPTIMISTIC_ABORT':
                st['opti_abort_cnt'] += 1

            if e['res']['status'] in ['ABORT', 'OPTIMISTIC_ABORT']: txn['abrt_cnt'] += 1

            if e['res']['status'] == 'OK' and txn['start']:
                txns.append(dict(latency=e['time'] - txn['start'],
                                    abrt_cnt=txn['abrt_cnt'],
                                    has_assert=txn['has_assert']))
                txn['start'] = None

            if e['res']['req_id'] in reqs:
                req_rtts.append(e['time'] - reqs[e['res']['req_id']])
                del reqs[e['res']['req_id']]

    parseLog(clientHook, filename)
    st['txns'] = txns
    st['avg_req_rtt'] = np.mean(req_rtts)
    return st

def getServerStats(filename):
    st = default_st.copy()
    def serverHook(e):
        if e['event'] == 'sent':
            st['sent_count'] += 1
            st['end'] = e['time']
            if e['res']['status'] == 'ABORT': st['store_abort_cnt'] += 1
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

    cl_stats = [dict(getClientStats(f), **dict(name=name)) for name, f
            in zip(client_names, client_log_filenames)]

    summary = dict()

    #srv_stats = getServerStats(server_log_filenames[0])
    #summary['srv_sent'] = srv_stats['sent_count']
    #summary['srv_recv'] = srv_stats['recv_count']
    #summary['srv_abort'] = srv_stats['store_abort_cnt']

    summary['first_start_time'] = min([st['start'] for st in cl_stats])
    summary['last_start_time'] = max([st['start'] for st in cl_stats])
    summary['first_end_time'] = min([st['end'] for st in cl_stats])
    summary['last_end_time'] = max([st['end'] for st in cl_stats])
    summary['elapsed_time'] = summary['last_end_time'] - summary['first_start_time']
    summary['concurrent_time'] = summary['first_end_time'] - summary['last_start_time']

    summary['store_abort_cnt'] = sum([st['store_abort_cnt'] for st in cl_stats]) # aborted by store
    summary['switch_abort_cnt'] = sum([st['switch_abort_cnt'] for st in cl_stats])  # normally aborted by switch
    summary['opti_abort_cnt'] = sum([st['opti_abort_cnt'] for st in cl_stats]) # optimistically aborted by switch
    summary['total_abort_cnt'] = summary['store_abort_cnt'] + summary['switch_abort_cnt'] + summary['opti_abort_cnt']
    summary['total_sent'] = sum([st['sent_count'] for st in cl_stats])
    summary['total_recv'] = sum([st['recv_count'] for st in cl_stats])
    summary['avg_req_rtt'] = np.mean([st['avg_req_rtt'] for st in cl_stats])


    all_txns = sum([st['txns'] for st in cl_stats], [])
    all_txn_latencies = [t['latency'] for t in all_txns]
    asrt_txn_latencies = [t['latency'] for t in all_txns if t['has_assert']]
    othr_txn_latencies = [t['latency'] for t in all_txns if not t['has_assert']]
    all_txn_abrt_cnts = [t['abrt_cnt'] for t in all_txns]

    summary['asrt_txn_latency'] = np.mean(asrt_txn_latencies) if asrt_txn_latencies else 0
    summary['p99_asrt_txn_latency'] = np.percentile(asrt_txn_latencies, 99) if asrt_txn_latencies else 0
    summary['p95_asrt_txn_latency'] = np.percentile(asrt_txn_latencies, 95) if asrt_txn_latencies else 0
    summary['othr_txn_latency'] = np.mean(othr_txn_latencies)

    summary['all_txn_latency'] = np.mean(all_txn_latencies)
    summary['p99_all_txn_latency'] = np.percentile(all_txn_latencies, 99)
    summary['p95_all_txn_latency'] = np.percentile(all_txn_latencies, 95)

    summary['all_txn_rate'] = len(all_txn_latencies) / sum(all_txn_latencies)
    summary['asrt_txn_rate'] = len(asrt_txn_latencies) / sum(asrt_txn_latencies) if asrt_txn_latencies else 0
    summary['othr_txn_rate'] = len(othr_txn_latencies) / sum(othr_txn_latencies)

    summary['all_txn_abrt_cnt'] = np.mean(all_txn_abrt_cnts)

    summary['asrt_txn_ratio'] = len(asrt_txn_latencies) / float(len(all_txn_latencies))

    summary['switch_abort_ratio'] = 0 if summary['total_abort_cnt'] == 0 else float(summary['switch_abort_cnt'] + summary['opti_abort_cnt']) / summary['total_abort_cnt']
    summary['opti_abort_ratio'] = 0 if summary['total_abort_cnt'] == 0 else float(summary['opti_abort_cnt']) / summary['total_abort_cnt']

    if args.latencies:
        summary['all_txn_latencies'] = ','.join(map(str, all_txn_latencies))
        summary['asrt_txn_latencies'] = ','.join(map(str, asrt_txn_latencies))

    if args.tpcc:
        assert len(stdout_log_filenames) == 1
        tpcc_stats = getTpccStats(stdout_log_filenames[0])
        for k, v in tpcc_stats.items(): summary[k] = v

    total_delta = conf['total_delay'] if 'total_delay' in conf else conf['server']['delay'] + conf['clients'][0]['delay']

    experiment_params = dict(client_d=conf['clients'][0]['delay'],
                store_D=conf['server']['delay'],
                total_delta=total_delta,
                delta_ratio=conf['delta_ratio'] if 'delta_ratio' in conf else float(total_delta)/conf['clients'][0]['delay'],
                num_clients=len(conf['clients']),
                think=conf['think_s'] if 'think_s' in conf else 0,
                think_var=conf['think_v'] if 'think_v' in conf else 0,
                mode=conf['switch']['mode'])
    if 'parameters' in conf: experiment_params.update(conf['parameters'])
    if 'req_count' in conf: experiment_params['req_count'] = conf['req_count']


    return dict(summary, **experiment_params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=str, help="experiment directory", nargs='*')
    parser.add_argument("--jobs", "-j", type=int, action="store", default=None, help="number of parallel jobs")
    parser.add_argument("--json", "-J", action="store_true", help="output as JSON")
    parser.add_argument("--tpcc", "-t", action="store_true", help="parse TPCC data from client STDOUT log file")
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
