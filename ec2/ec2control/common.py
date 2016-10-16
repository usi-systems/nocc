NODES=[
    ('store', 'us-east-1', 'a', 'subnet-108edc66', 'ami-2d39803a', 't2.medium'),
    ('switch', 'us-west-1', 'a', 'subnet-c86afdad',  'ami-48db9d28', 't2.medium'),
    #('load', 'us-west-1', 'a', 'subnet-c86afdad', 'ami-48db9d28', 't2.medium'),
    ('client', 'us-west-2', 'a', 'subnet-aa66d2ce', 'ami-d732f0b7', 't2.medium'),
]

REGIONS=set(node[1] for node in NODES)

KEYNAME='macubuntu'

SECGROUP='default'

SUBNET='default'


def instances_by_name(conn, name):
    instances = conn.get_only_instances()
    with_name = []
    for inst in instances:
        if 'Name' in inst.tags and inst.tags['Name'] == name:
            with_name.append(inst)
    return with_name



def instance_create(conn,
                    image,
                    token='',
                    inst_type='t2.medium',
                    placement_letter='a',
                    subnet='default',
                    dry_run=False):
    return conn.run_instances(image,
                              instance_type = inst_type,
                              placement = conn.region.name + placement_letter,
                              key_name = KEYNAME,
                              #security_groups = [SECGROUP],
                              subnet_id = subnet,
                              client_token = token,
                              dry_run = dry_run)

if __name__ == '__main__':
    pass
