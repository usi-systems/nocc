import json
import argparse
import multiprocessing
import sys
import numpy as np
from os import path, listdir
sys.path.append('../simple_store')
from common import *

def parseLog(func, filename):
    with open(filename, 'r') as f:
        for line in f.readlines():
            event = json.loads(line)
            func(event)

default_st = dict(abort_count=0, optimistic_abort_count=0,
                    sent_count=0, recv_count=0,
                    start=None, end=None)

def getClientStats(filename):
    st = default_st.copy()

    outstanding_req_time = {} # the time of req_ids awaiting a response
    req_rtts = [] # the RTT for each txn msg

    st['txn_start_time'] = None # the last req time before a successful response
    txn_times = [] # the times it takes to successfully complete a TXN
    def clientHook(e):
        if e['event'] == 'sent':
            if st['start'] is None: st['start'] = e['time']
            st['sent_count'] += 1
            if st['txn_start_time'] is None:
                st['txn_start_time'] = e['time']
            outstanding_req_time[e['req']['req_id']] = e['time']
        elif e['event'] == 'received':
            st['end'] = e['time']
            st['recv_count'] += 1
            if e['res']['status'] == 'OPTIMISTIC_ABORT': st['optimistic_abort_count'] += 1
            if e['res']['status'] == 'ABORT': st['abort_count'] += 1
            if e['res']['status'] == 'OK':
                assert(st['txn_start_time'] is not None)
                txn_times.append(e['time'] - st['txn_start_time'])
                st['txn_start_time'] = None

            assert(e['res']['req_id'] in outstanding_req_time)
            req_rtts.append(e['time'] - outstanding_req_time[e['res']['req_id']])
            del outstanding_req_time[e['res']['req_id']]
    parseLog(clientHook, filename)
    del st['txn_start_time']
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


def getExperimentStats(experiment_dir):
    experiment_dir = path.abspath(experiment_dir)
    log_dir = path.join(experiment_dir, "logs")
    with open(path.join(experiment_dir, "experiment.json"), 'r') as f:
        conf = json.load(f)
    if not path.exists(log_dir): raise Exception('Directory does not exist: %s'%log_dir)
    if not path.isdir(log_dir): raise Exception('Log directory is not a directory: %s'%log_dir)

    log_filenames = filter(path.isfile, [path.join(log_dir, f) for f in listdir(log_dir) if f[-4:] == '.log'])
    client_log_filenames = [f for f in log_filenames if not 'server' in path.basename(f)]
    if len(client_log_filenames) < 1: raise Exception("No client logs found in: %s"%log_dir)
    server_log_filenames = [f for f in log_filenames if 'server' in path.basename(f)]
    if len(server_log_filenames) < 1: raise Exception("No server logs found in: %s"%log_dir)
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

    experiment_params = dict(client_d=conf['clients'][0]['delay'],
                store_D=conf['server']['delay'],
                num_clients=len(conf['clients']),
                think=conf['think_s'] if 'think_s' in conf else 0,
                think_var=conf['think_v'] if 'think_v' in conf else 0,
                mode=conf['switch']['mode'],
                req_count=conf['req_count'])
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
        print '\n'.join(['\t'.join([str(s[k]) for k in keys]) for s in summaries])
