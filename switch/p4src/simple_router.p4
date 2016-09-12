/* Copyright 2013-present Barefoot Networks, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#define MAX_REG_INST 65000

header_type ethernet_t {
    fields {
        bit<48> dstAddr;
        bit<48> srcAddr;
        bit<16> etherType;
    }
}

header_type ipv4_t {
    fields {
        bit<4> version;
        bit<4> ihl;
        bit<8> diffserv;
        bit<16> totalLen;
        bit<16> identification;
        bit<3> flags;
        bit<13> fragOffset;
        bit<8> ttl;
        bit<8> protocol;
        bit<16> hdrChecksum;
        bit<32> srcAddr;
        bit<32> dstAddr;
    }
}

header_type udp_t {
    fields {
        bit<16> srcPort;
        bit<16> dstPort;
        bit<16> length_;
        bit<16> checksum;
    }
}

#define GOTTHARD_PORT 9999

#define GOTTHARD_TYPE_REQ 0
#define GOTTHARD_TYPE_RES 1

#define GOTTHARD_STATUS_OK          0
#define GOTTHARD_STATUS_NOTFOUND    1
#define GOTTHARD_STATUS_REJECT      2

header_type gotthard_flags_t {
    fields {
        bit<1> msg_type;
        bit<1> rm;
        bit<1> updated;
        bit<5> other;
    }
}

header_type gotthard_req_t {
    fields {
        bit<32> cl_id;
        bit<32> req_id;
        bit<32> r_key;
        bit<32> r_version;
        bit<32> w_key;
        bit<800> w_value;
    }
}

header_type gotthard_res_t {
    fields {
        bit<32> cl_id;
        bit<32> req_id;
        bit<8> status;
        bit<32> key;
        bit<32> version;
        bit<800> value;
    }
}



parser start {
    return parse_ethernet;
}

#define ETHERTYPE_IPV4 0x0800

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        ETHERTYPE_IPV4 : parse_ipv4;
        default: ingress;
    }
}

header ipv4_t ipv4;

field_list ipv4_checksum_list {
    ipv4.version;
    ipv4.ihl;
    ipv4.diffserv;
    ipv4.totalLen;
    ipv4.identification;
    ipv4.flags;
    ipv4.fragOffset;
    ipv4.ttl;
    ipv4.protocol;
    ipv4.srcAddr;
    ipv4.dstAddr;
}

field_list_calculation ipv4_checksum {
    input {
        ipv4_checksum_list;
    }
    algorithm : csum16;
    output_width : 16;
}

calculated_field ipv4.hdrChecksum  {
    verify ipv4_checksum;
    update ipv4_checksum;
}

#define IPTYPE_UDP 0x11

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.protocol) {
        IPTYPE_UDP: parse_udp;
        default: ingress;
    }
}


header udp_t udp;

parser parse_udp {
    extract(udp);
    return parse_gotthard;
}

header gotthard_flags_t gotthard_flags;
header gotthard_req_t gotthard_req;
header gotthard_res_t gotthard_res;

parser parse_gotthard_req {
    extract(gotthard_req);
    return ingress;
}

parser parse_gotthard_res {
    extract(gotthard_res);
    return ingress;
}

parser parse_gotthard {
    extract(gotthard_flags);
    return select(gotthard_flags.msg_type) {
        GOTTHARD_TYPE_REQ: parse_gotthard_req;
        GOTTHARD_TYPE_RES: parse_gotthard_res;
    }
}

register version_register {
    width: 32;
    instance_count: MAX_REG_INST;
}

register value_register {
    width: 100;
    instance_count: MAX_REG_INST;
}

action do_gotthard_res () {
    value_register[gotthard_res.key] = gotthard_res.value;
    version_register[gotthard_res.key] = gotthard_res.version;
}

table gotthard_res_table {
    actions {
        do_gotthard_res;
    }
    size: 1;
}

header_type gotthard_req_metadata_t {
    fields {
        bit<1> is_same_version;
        bit<1> is_cache_hit;
        bit<1> is_rw;
    }
}
metadata gotthard_req_metadata_t gotthard_req_metadata;

action do_gotthard_cache () {
    gotthard_req_metadata.is_cache_hit = version_register[gotthard_req.r_key] != 0;
    gotthard_req_metadata.is_same_version = version_register[gotthard_req.r_key] == gotthard_req.r_version;
    gotthard_req_metadata.is_rw = gotthard_req.w_key != 0;
}

table gotthard_cache_table {
    actions {
        do_gotthard_cache;
    }
    size: 1;
}

action do_gotthard_reject () {
}
action do_gotthard_hit () {
}
action do_nothing () {
}

table gotthard_req_forward_table {
    reads {
        gotthard_req_metadata.is_cache_hit: exact;
        gotthard_req_metadata.is_same_version: exact;
        gotthard_req_metadata.is_rw: exact;
    }
    actions {
        do_gotthard_reject;
        do_gotthard_hit;
        do_nothing;
    }
    size: 1;
}

header_type routing_metadata_t {
    fields {
        bit<32> nhop_ipv4;
    }
}

metadata routing_metadata_t routing_metadata;


action set_nhop(in bit<32> nhop_ipv4, in bit<9> port) {
    routing_metadata.nhop_ipv4 = nhop_ipv4;
    standard_metadata.egress_spec = port;
    ipv4.ttl = ipv4.ttl - 1;
}

table ipv4_lpm {
    reads {
        ipv4.dstAddr : lpm;
    }
    actions {
        set_nhop;
    }
    size: 1024;
}

action set_dmac(in bit<48> dmac) {
    ethernet.dstAddr = dmac;
}

table forward {
    reads {
        routing_metadata.nhop_ipv4 : exact;
    }
    actions {
        set_dmac;
    }
    size: 512;
}

action rewrite_mac(in bit<48> smac) {
    ethernet.srcAddr = smac;
}

table send_frame {
    reads {
        standard_metadata.egress_port: exact;
    }
    actions {
        rewrite_mac;
    }
    size: 256;
}

control ingress {
    if (valid(ipv4)) {
        if (valid(gotthard_res) and gotthard_flags.updated == 1) {
            apply(gotthard_res_table);
        }
        else if (valid(gotthard_req)) {
            if (gotthard_req.r_key != 0) {
                apply(gotthard_cache_table);
            }
            apply(gotthard_req_forward_table);
        }
        apply(ipv4_lpm);
        apply(forward);
    }
}

control egress {
    apply(send_frame);
}
