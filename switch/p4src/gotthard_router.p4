#define MAX_REG_INST 65000

#define GOTTHARD_PORT 9999

#define GOTTHARD_TYPE_REQ 0
#define GOTTHARD_TYPE_RES 1

#define GOTTHARD_STATUS_OK                  0
#define GOTTHARD_STATUS_ABORT               1
#define GOTTHARD_STATUS_OPTIMISTIC_ABORT    2

#define GOTTHARD_MAX_TXN 10

#include "header.p4"
#include "parser.p4"

metadata intrinsic_metadata_t intrinsic_metadata;


action _no_op () {
}

header_type gotthard_req_metadata_t {
    fields {
        bit<1> is_key_cached;
        bit<1> is_value_match;
        bit<1> is_pending_write;
        bit<1> is_pending_value_match;
        bit<1> is_aborted_by_switch;

        // tmp variables for doing swaps:
        bit<32> tmp_ipv4_dstAddr;
        bit<16> tmp_udp_dstPort;
    }
}
metadata gotthard_req_metadata_t gotthard_req_metadata;


action do_direction_swap (in bit<8> udp_payload_size) { // return the packet to the sender
    // Save old dst IP and port in tmp variable
    gotthard_req_metadata.tmp_ipv4_dstAddr = ipv4.dstAddr;
    gotthard_req_metadata.tmp_udp_dstPort = udp.dstPort;

    ipv4.dstAddr = ipv4.srcAddr;
    ipv4.srcAddr = gotthard_req_metadata.tmp_ipv4_dstAddr;
    ipv4.totalLen = IPV4_HDR_LEN + UDP_HDR_LEN + udp_payload_size;

    udp.dstPort = udp.srcPort;
    udp.srcPort = gotthard_req_metadata.tmp_udp_dstPort;
    udp.checksum = (bit<16>)0; // TODO: update the UDP checksum
    udp.length_ = UDP_HDR_LEN + udp_payload_size;
}


register req_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}
register res_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}
register txn_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}

register loop_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}

register remaining_register {
    width: 8;
    instance_count: MAX_REG_INST;
}

register req_check_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}

register resubmit_count_register {
    width: 32;
    instance_count: MAX_REG_INST;
}
metadata req_txn_meta_t req_txn_meta;

action do_req_check() {
    req_count_register[0] = req_count_register[0] + 1;
    req_count_register[gotthard_hdr.req_id] = req_count_register[0];
    req_txn_meta.remaining_cnt = gotthard_hdr.txn_cnt;
    loop_count_register[gotthard_hdr.req_id] = (bit<32>)0;
    req_txn_meta.loop_started = (bit<1>)1;
    req_check_count_register[gotthard_hdr.req_id] = req_check_count_register[gotthard_hdr.req_id] + 1;
}

table t_req {
    actions {
        do_req_check;
        _drop;
    }
    size: 1;
}

action do_res_check() {
    res_count_register[0] = res_count_register[0] + 1;
}

table t_res {
    actions {
        do_res_check;
        _drop;
    }
    size: 1;
}


field_list resubmit_FL {
    //standard_metadata;
    req_txn_meta;
}

action do_loop_req_txn() {
    txn_count_register[gotthard_hdr.req_id] = gotthard_hdr.txn_cnt;
    req_txn_meta.remaining_cnt = req_txn_meta.remaining_cnt - 1;
    loop_count_register[gotthard_hdr.req_id] = loop_count_register[gotthard_hdr.req_id] + (bit<32>)1;
    remaining_register[gotthard_hdr.req_id] = req_txn_meta.remaining_cnt;
}

table t_loop_req_txn {
    actions {
        do_loop_req_txn;
        _drop;
    }
    size: 1;
}

action do_resubmit_loop_req_txn() {
    resubmit_count_register[gotthard_hdr.req_id] = resubmit_count_register[gotthard_hdr.req_id] + 1;
    resubmit(resubmit_FL);
}


table t_resubmit_loop_req_txn {
    actions {
        do_resubmit_loop_req_txn;
        _no_op;
    }
    size: 1;
}


action _drop() {
    drop();
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
        _drop;
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
        _drop;
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
        _drop;
    }
    size: 256;
}

control ingress {
    if (valid(ipv4)) {
        if (valid(gotthard_hdr)) {
            if (gotthard_hdr.msg_type == GOTTHARD_TYPE_REQ) {
                if (req_txn_meta.loop_started == 0) {
                    apply(t_req);
                }

                if (req_txn_meta.remaining_cnt > 0) {
                    apply(t_loop_req_txn);
                    if (req_txn_meta.remaining_cnt > 0) {
                        apply(t_resubmit_loop_req_txn);
                    }
                }
            }
            else {
                apply(t_res);
            }

        }

        if(req_txn_meta.remaining_cnt == 0) {
            apply(ipv4_lpm);
            apply(forward);
        }
    }
}

control egress {
    apply(send_frame);
}
