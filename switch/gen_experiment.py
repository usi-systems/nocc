import argparse
import json
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument("dir", type=str, help="directory to initialize experiment in")
parser.add_argument("--num-clients", "-n", type=int, help="number of parallel clients", default=2)
parser.add_argument("--client-cmd", "-c", type=str, help="command to execute on clients", required=True)
parser.add_argument("--server-cmd", "-s", type=str, help="command to execute on server", required=True)
parser.add_argument("--think-time", "-t", type=int, help="client think time (s)", default=None)
parser.add_argument('--server-delta', help='Delay (ms) between switch and server',
                    type=int, required=False, default=0)
parser.add_argument('--client-delta', help='Delay (ms) between switch and client',
                    type=int, required=False, default=0)
parser.add_argument('--disable-cache', help="disable the switch cach",
                    action="store_true", required=False, default=False)
args = parser.parse_args()

conf = dict(clients=[])
conf['gen_input'] = ' '.join(['"%s"'%a if ' ' in a else a for a in sys.argv])
conf['server'] = dict(cmd=args.server_cmd)
conf['switch'] = dict(disable_cache=args.disable_cache)
if args.server_delta: conf['server']['delay'] = args.server_delta
for n in xrange(args.num_clients):
    cl = dict(cmd=args.client_cmd)
    if args.think_time: cl['think_s'] = args.think_time
    if args.client_delta: cl['delay'] = args.client_delta
    conf['clients'].append(cl)


experiment_dir = os.path.abspath(args.dir)
if os.path.exists(experiment_dir): raise Exception('Experiment directory already exists: %s'%experiment_dir)
os.mkdir(experiment_dir)

conf_filename = os.path.join(experiment_dir, 'experiment.json')
with os.fdopen(os.open(conf_filename, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0666), 'a') as f:
    json.dump(conf, f, indent=4)
