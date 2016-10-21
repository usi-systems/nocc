#!/usr/bin/env python2
import argparse

parser = argparse.ArgumentParser(description='Zipf distribution workload generator')

parser.add_argument('--write-ratio', '-w', help='write ratio', type=float, action="store", required=True)
parser.add_argument('--pop-size', '-n', help='population size', type=int, action="store", required=True)
parser.add_argument('--exponent', '-s', help='zipf exponent', type=float, action="store", required=True)
parser.add_argument('--keys', '-k', help='keys to use',
        type=lambda s: [k.strip() for k in s.split(',')], action="store", default=None, required=False)
args = parser.parse_args()

def zipf(s, N):
   """
   s - exponent
   N - pop. size
   """
   return [(1.0/pow(k, s)) / sum((1.0/pow(n, s) for n in range(1, N+1))) for k in range(1, N+1)]

def zipf_pdf(pwrite, s, N):
   ranks = zipf(s, N)
   return ','.join(['%f,%f' % (p*pwrite, p*(1-pwrite)) for p in zipf(s, N)])

probabilities = zipf_pdf(args.write_ratio, args.exponent, args.pop_size)

keyspace = args.keys or ['a','b','c','d','e','f','g','h','i','j']
keys = keyspace[:args.pop_size]
#transactions = '|'.join(['A(%(k)s,%(k)s)W(%(k)s,%(k)s+1)|R(%(k)s)' % {'k': k} for k in keys])
transactions = '|'.join(['A(%(k)s,%(k)s)W(%(k)s,RND)|R(%(k)s)' % {'k': k} for k in keys])

print "%s\t%s" % (probabilities, transactions)
