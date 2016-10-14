#!/usr/bin/env python
import json
import sys
from collections import defaultdict
import numpy
from numpy import mean, percentile
import pandas
import re

TYPE_READ=1
TYPE_WRITE=2

clients_re=re.compile(".*-n([0-9]+).*")
read_p_re=re.compile(".*-p([0-9]+(?:.?[0-9]+)?).*")
def params_from_filename(fname):
    c = int(clients_re.findall(fname)[0])
    r = float(read_p_re.findall(fname)[0])
    return (c, r)

if __name__ == '__main__':
    for fname in sys.argv[1:]:
        reqs=defaultdict(lambda: None)
        clients, read_p = params_from_filename(fname)
        read_latencies=[]
        write_latencies=[]
        write_aborts=[]
        with open(fname) as f:
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
        print clients, read_p,
        print len(all_latencies),
        print mean(all_latencies),
        print percentile(all_latencies, 99),
        print percentile(all_latencies, 95),
        print mean(write_aborts),
        print
