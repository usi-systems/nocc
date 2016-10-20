#!/usr/bin/env python
import subprocess
import shutil
from os import path
from collections import defaultdict
import time
import json
import itertools
import re
import numpy
from numpy import mean, percentile
import sys

TYPE_READ=1
TYPE_WRITE=2

LOGDIR='/home/pacheco/workspace/gotthard/ec2/3S_LOGS/'

number_re=re.compile("([0-9]+(?:.?[0-9]+)?)")
def process_file_name(fpath):
    """
    example: 0.050rw_8ctotal_0.750l_optimistic_abort_sw1_loc
    """
    fname = path.basename(fpath)
    parts = fname.split('_')
    rw = number_re.findall(parts[0])[0]
    clients = number_re.findall(parts[1])[0]
    locality = number_re.findall(parts[2])[0]
    mode = '_'.join(parts[3:])
    return [mode, clients, rw, locality]

def process_files(fpaths):
    read_latencies=[]
    write_latencies=[]
    write_aborts=[]
    for fpath in fpaths:
        with open(fpath) as f:
            reqs=defaultdict(lambda: None)
            for line in f.readlines():
                event = json.loads(line)
                if 'req' in event:
                    req = event['req']
                    cid = req['cl_id']
                    rid = req['req_id']
                    prev_req = reqs.get(cid)
                    if prev_req:
                        # request resend... ignore
                        continue
                    else:
                        # new request
                        req['aborts'] = 0
                        req['type'] = TYPE_READ if len(req['ops']) == 1 else TYPE_WRITE
                        req['time'] = event['time']
                        reqs[cid] = req
                elif 'res' in event:
                    res = event['res']
                    cid = res['cl_id']
                    req = reqs.get(cid)
                    # print req
                    # print res
                    if not req:
                        continue # ignore
                    else:
                        if res['status'] == 'OK':
                            # print "%s %s %s %s %s" % (
                            #     req['time'],
                            #     cid,
                            #     event['time'] - req['time'],
                            #     req['aborts'],
                            #     req['type'],
                            # )
                            reqs[req['cl_id']] = None
                            if req['type'] == TYPE_READ:
                                read_latencies.append(event['time'] - req['time'])
                            else:
                                write_latencies.append(event['time'] - req['time'])
                                write_aborts.append(req['aborts'])
                        else:
                            req['aborts'] += 1
        # read_latencies=numpy.array(read_latencies)
        # write_latencies=numpy.array(write_latencies)
    all_latencies=numpy.array(read_latencies + write_latencies)
    write_aborts=numpy.array(write_aborts)
    return [
        len(all_latencies),
        mean(all_latencies),
        percentile(all_latencies, 99),
        percentile(all_latencies, 95),
        mean(write_aborts),
    ]

if __name__ == '__main__':
    #sorted_files = sorted(sys.argv[1:])
    fname_re=re.compile("(.*)_..._...\.raw$")
    grouped = itertools.groupby(sys.argv[1:], lambda x: fname_re.findall(x)[0])
    print "mode\tclients\tpwrite\tlocality\ttput\tmean_lat\t99_lat\t95_lat\taborts_per_wr"
    for g in grouped:
        fixed = process_file_name(g[0])
        columns = process_files(g[1])
        print "\t".join(map(str, fixed + columns))
