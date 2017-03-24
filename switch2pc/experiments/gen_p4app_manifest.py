#!/usr/bin/env python

import os
import json
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load Experiment Generator')
    parser.add_argument('-o', '--out-dir', help='path to parent directory to save experiment in',
            type=str, required=True)
    parser.add_argument('--manifest', '-m', help='path to manifest file to be extended',
            type=str, required=True)
    parser.add_argument("parameters", help='Set parameters. E.g.: load=1000 count=10000',
        type=lambda kv: kv.split("="), nargs='*')
    args = parser.parse_args()

    exp_name = '_'.join(['%s_%s' % (p[1], p[0]) for p in args.parameters])
    exp_dir_path = os.path.join(args.out_dir, exp_name)
    os.mkdir(exp_dir_path)

    manifest_path = os.path.join(exp_dir_path, 'p4app.json')

    with open(args.manifest, 'r') as f:
        manifest = json.load(f)

    if 'parameters' not in manifest['targets']['default']:
        manifest['targets']['default']['parameters'] = dict()

    manifest['targets']['default']['parameters'].update(dict(args.parameters))

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=4)

    print manifest_path
