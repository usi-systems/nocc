#!/usr/bin/env python
import json
import hashlib
import argparse
import sys
from pygotthard import *

parser = argparse.ArgumentParser()
parser.add_argument("log", type=str, help="JSON log filename", nargs='?')
parser.add_argument('--checksum', '-c', help="print value checksum", action='store_true', default=False)
parser.add_argument('--pretty', '-p', help="pretty print", action='store_true', default=False)
parser.add_argument('--tsv', '-t', help="output tsv data", action='store_true', default=False)
args = parser.parse_args()

tsv_fields = ['msg_type', 'cl_id', 'req_id', 'frag_seq', 'frag_cnt', 'op_cnt', 'rb_cnt', 'r_cnt', 'w_cnt']

def parseFile(f):
    line_num = 0
    for line in f.readlines():
        line_num += 1
        line = unicode(line, errors='replace')
        try:
            e = json.loads(line)
        except:
            sys.stderr.write("JSON parse error on line %s:%d\n" % (f.name, line_num))
            raise
        #e = json.loads(line, encoding='ascii')
        if 'req' not in e and 'res' not in e: continue
        msg_type = 'req' if 'req' in e else 'res'
        m = e[msg_type]

        if args.checksum:
            for o in m['ops']:
                o['v'] = hashlib.md5(o['v'].encode('utf-8')).hexdigest()[:4]

        if args.tsv:
            extra = dict(msg_type=msg_type,
                    rb_cnt=len([o for o in m['ops'] if o['t'] == 'V']),
                    w_cnt=len([o for o in m['ops'] if o['t'] == 'W']),
                    r_cnt=len([o for o in m['ops'] if o['t'] == 'R']),
                    op_cnt=len(m['ops']))
            row = map(str, [m[k] if k in m else extra[k] for k in tsv_fields])
            print '\t'.join(row)
        elif args.pretty:
            m['ops'] = sorted(m['ops'], key=lambda o: (['V', 'R', 'W', 'U'].index(o['t']), o['k']))
            pretty = '%s (%d): ' % (msg_type, m['req_id'])
            pretty += '%17s: ' % (m['status'] if 'status' in m else '')
            pretty += ' '.join(['%s(%d, %s)' %(o['t'], o['k'], o['v']) for o in m['ops']])
            print pretty
        else:
            print json.dumps(e)

if args.tsv:
    print '\t'.join(tsv_fields)

if not args.log or args.log == '-':
    parseFile(sys.stdin)
else:
    with open(args.log, 'r') as f:
        parseFile(f)

