import argparse
import json
import sys
import os

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--out-dir", "-o", type=str, help="directory to initialize experiment in")
group.add_argument("--out-parent", "-p", type=str, help="parent directory to initialize experiment in, with generated name")
parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=2)
parser.add_argument("--client-cmd", "-c", type=str, help="command to execute on clients", nargs='*', required=True)
parser.add_argument("--server-cmd", "-s", type=str, help="command to execute on server", required=True)
parser.add_argument("--req-count", "-r", type=int, help="client request count (e.g. # of inc. transaction)", default=None)
parser.add_argument("--think-time", "-t", type=float, help="client think time (s)", default=None)
parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=None)
parser.add_argument("--sequential-clients", help="whether to run the clients sequentially", action='store_true', default=False)
parser.add_argument('--server-delta', help='Delay (ms) between switch and server',
                    type=int, required=False, default=0)
parser.add_argument('--client-delta', help='Delay (ms) between switch and client',
                    type=int, required=False, default=0)
parser.add_argument("--mode", "-m", choices=['forward', 'early_abort', 'optimistic_abort'], type=str, default="early_abort")
args = parser.parse_args()

conf = dict(clients=[])
conf['gen_input'] = ' '.join(['"%s"'%a if ' ' in a else a for a in sys.argv])
conf['server'] = dict(cmd=args.server_cmd)
conf['switch'] = dict(mode=args.mode)
conf['sequential_clients'] = args.sequential_clients
if args.server_delta: conf['server']['delay'] = args.server_delta
num_clients = max(args.num_clients, len(args.client_cmd))
for n in xrange(num_clients):
    cl = dict(cmd=args.client_cmd[n % len(args.client_cmd)])
    if args.client_delta: cl['delay'] = args.client_delta
    conf['clients'].append(cl)

conf['think_s'] = 0 if args.think_time is None else args.think_time
conf['think_v'] = 0 if args.think_var is None else args.think_var
if not args.req_count is None: conf['req_count'] = args.req_count

if args.out_dir:
    experiment_dir = os.path.abspath(args.out_dir)
else:
    experiment_dir = os.path.join(os.path.abspath(args.out_parent),
            "%dd_%dD_%dclients_%sreqs_%gthink%g_%s" % (args.client_delta, args.server_delta,
                num_clients,
                'no' if args.req_count is None else str(args.req_count), args.think_time,
                args.think_var, args.mode))


if os.path.exists(experiment_dir): raise Exception('Experiment directory already exists: %s'%experiment_dir)
os.mkdir(experiment_dir)

conf_filename = os.path.join(experiment_dir, 'experiment.json')
with os.fdopen(os.open(conf_filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a') as f:
    json.dump(conf, f, indent=4)

print conf_filename
