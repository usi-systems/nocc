import json
import argparse
import multiprocessing
import sys
from os import path, listdir
sys.path.append('../simple_store')
from common import *

def parseLog(func, filename):
    with open(filename, 'r') as f:
        for line in f.readlines():
            event = json.loads(line)
            func(event)

default_st = dict(abort_count=0, sent_count=0, recv_count=0,
            start=None, end=None)

def getClientStats(filename):
    st = default_st.copy()
    def clientHook(e):
        if e['event'] == 'sent':
            if st['start'] is None: st['start'] = e['time']
            st['sent_count'] += 1
        elif e['event'] == 'received':
            st['end'] = e['time']
            st['recv_count'] += 1
            if e['res']['status'] == 'STATUS_REJECT': st['abort_count'] += 1
    parseLog(clientHook, filename)
    return st

def getServerStats(filename):
    st = default_st.copy()
    def serverHook(e):
        if e['event'] == 'sent':
            st['sent_count'] += 1
            st['end'] = e['time']
            if e['res']['status'] == 'STATUS_REJECT': st['abort_count'] += 1
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
    server_log_filename = [f for f in log_filenames if 'server' in path.basename(f)][0]
    client_names = [path.basename(f).split('.log')[0] for f in client_log_filenames]

    srv_stats = getServerStats(server_log_filename)
    cl_stats = [dict(getClientStats(f), **dict(name=name)) for name, f
            in zip(client_names, client_log_filenames)]

    summary = dict()
    summary['total_aborts'] = sum([st['abort_count'] for st in cl_stats])
    summary['total_sent'] = sum([st['sent_count'] for st in cl_stats])
    summary['total_recv'] = sum([st['recv_count'] for st in cl_stats])
    summary['srv_sent'] = srv_stats['sent_count']
    summary['srv_recv'] = srv_stats['recv_count']
    summary['srv_abort'] = srv_stats['abort_count']

    summary['pct_shortcut_abort'] = float(summary['total_aborts'] - summary['srv_abort']) / summary['total_aborts']

    summary['elapsed_time'] = max([st['end'] for st in cl_stats]) - min([st['start'] for st in cl_stats])

    experiment_params = dict(d=conf['clients'][0]['delay'],
                D=conf['server']['delay'],
                num_clients=len(conf['clients']),
                think=conf['think_s'] if 'think_s' in conf else 0,
                think_var=conf['think_v'] if 'think_v' in conf else 0,
                disabled=conf['switch']['disable_cache'],
                req_count=conf['req_count'])


    return dict(summary, **experiment_params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", type=str, help="experiment directory", nargs='*')
    parser.add_argument("--json", "-j", action="store_true", help="output as JSON")
    parser.add_argument("--header", "-H", action="store_true", help="print header")
    args = parser.parse_args()

    n_cpu = multiprocessing.cpu_count()
    n_job = n_cpu if n_cpu == 1 else n_cpu - 1
    p = multiprocessing.Pool(n_job)
    summaries = p.map(getExperimentStats, args.dir)

    if args.json:
        print json.dumps(summaries, indent=1, sort_keys=True)
    else:
        keys = sorted(summaries[0].keys())
        if args.header:
            print '\t'.join(keys)
        print '\n'.join(['\t'.join([str(s[k]) for k in keys]) for s in summaries])
