#!/usr/bin/env python2
import argparse

parser = argparse.ArgumentParser(description='Normal distribution workload generator')

parser.add_argument('--write-ratio', '-w', help='write ratio', type=float, action="store", required=True)
parser.add_argument('--pop-size', '-n', help='population size', type=int, action="store", required=True)
parser.add_argument('--locality', '-l', help='locality factor', type=float, action="store", required=True)
parser.add_argument('--local-keys', '-L', help='keys local to this client',
        type=lambda s: [k.strip() for k in s.split(',')], action="store", required=True)
parser.add_argument('--keys', '-k', help='keys to use',
        type=lambda s: [k.strip() for k in s.split(',')], action="store",
        default=[chr(i) for i in xrange(97, 123)], required=False)
args = parser.parse_args()

assert 0 <= args.write_ratio and args.write_ratio <= 1
assert 0 <= args.locality and args.locality <= 1
assert len(args.local_keys) == len(set(args.local_keys))
assert len(args.keys) == len(set(args.keys))

remote_keys = list(set(args.keys) - set(args.local_keys))[:args.pop_size-len(args.local_keys)]
all_keys = args.local_keys + remote_keys

key_pdf = [args.locality/len(args.local_keys)]*len(args.local_keys) + [(1-args.locality)/len(remote_keys)]*len(remote_keys)
txn_pdf = [t for p in key_pdf for t in (args.write_ratio*p, (1-args.write_ratio)*p)]

transactions = '|'.join(['A(%(k)s,%(k)s)W(%(k)s,RND)|R(%(k)s)' % {'k': k} for k in all_keys])

print "%s\t%s" % (','.join(map(str, txn_pdf)), transactions)
