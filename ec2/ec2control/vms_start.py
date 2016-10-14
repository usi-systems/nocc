#!/usr/bin/env python
import boto.ec2 as ec2
import argparse
import time

from common import *

def get_args():
    parser = argparse.ArgumentParser(description='Create/start ec2 vms')
    parser.add_argument('-c', '--create', help='Create vms if they do not exist', action='store_true', default=False)
    parser.add_argument('-t', '--token', type=str, help='Token for idempotent operations', required=True)
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    instances = {}
    for node in NODES:
        print node
        (name, region, zone, subnet, image, kind) = node
        conn = ec2.connect_to_region(region)
        named = instances_by_name(conn, name)
        if named:
            # instance already exists, start it
            instances[name] = named[0]
            named[0].start()
        else:
            # instance with the name does not exist
            print 'Instance does not exist: %s %s' % (region, name)
            if args.create:
                print 'Creating...'
                reserv = instance_create(
                    conn,
                    image,
                    token = name + args.token,
                    subnet = subnet,
                    #dry_run = True
                )
                instances[name] = reserv.instances[0]
    print 'Tagging instances...'
    for (name, instance) in instances.items():
        instance.add_tag('Name', name)
    print 'Waiting for instances to start...',
    for (name, instance) in instances.items():
        status = instance.update()
        while status != 'running':
            time.sleep(5)
            status = instance.update()
    print 'done!'
