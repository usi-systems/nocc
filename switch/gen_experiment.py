import argparse
import json
import sys
import os

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--out-dir", "-o", type=str, help="directory to initialize experiment in")
group.add_argument("--out-parent", "-p", type=str, help="parent directory to initialize experiment in, with generated name")
parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=1)
parser.add_argument("--client-cmd", "-c", type=str, help="command to execute on clients", nargs='*', required=True)
parser.add_argument("--server-cmd", "-s", type=str, help="command to execute on server", required=True)
parser.add_argument("--req-count", "-r", type=int, help="client request count (e.g. # of inc. transaction)", default=None)
parser.add_argument("--think-time", "-t", type=float, help="client think time (s)", default=None)
parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=None)
parser.add_argument("--sequential-clients", help="whether to run the clients sequentially", action='store_true', default=False)
parser.add_argument("--stdout-log", help="whether to dump the clients' STDOUT to a file", action='store_true', default=False)
parser.add_argument("--name", type=str, help="name of experiment", required=False, default=None)
parser.add_argument('--total-delta', help='End-to-end delay (ms) from client to server (through switch)',
                    type=int, required=False, default=None)
parser.add_argument('--delta-ratio', help='D/d (store/client delta) ratio',
                    type=float, required=False, default=1)
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

if args.total_delta:
    client_delta = float(args.total_delta) / (args.delta_ratio + 1)
    conf['server']['delay'] = args.total_delta - client_delta
else:
    conf['server']['delay'] = args.server_delta
    client_delta = args.client_delta


num_clients = max(args.num_clients, len(args.client_cmd))
for n in xrange(num_clients):
    conf['clients'].append(dict(cmd=args.client_cmd[n % len(args.client_cmd)],
              delay=client_delta, stdout_log=args.stdout_log))

conf['think_s'] = 0 if args.think_time is None else args.think_time
conf['think_v'] = 0 if args.think_var is None else args.think_var
if not args.req_count is None: conf['req_count'] = args.req_count

if args.out_dir:
    experiment_dir = os.path.abspath(args.out_dir)
else:
    thinkstr = '' if args.think_time is None else '%gthink%g_' % (args.think_time, args.think_var or 0)
    experiment_dir = os.path.join(os.path.abspath(args.out_parent),
            "%s%sd_%sD_%dclients_%sreqs_%s%s" % ('' if args.name is None else args.name + '_',
                str(client_delta), str(conf['server']['delay']),
                num_clients,
                'no' if args.req_count is None else str(args.req_count),
                thinkstr, args.mode))


if os.path.exists(experiment_dir): raise Exception('Experiment directory already exists: %s'%experiment_dir)
os.mkdir(experiment_dir)

conf_filename = os.path.join(experiment_dir, 'experiment.json')
with os.fdopen(os.open(conf_filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a') as f:
    json.dump(conf, f, indent=4)

print conf_filename
