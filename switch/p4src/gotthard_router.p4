#define MAX_REG_INST 65000

#define GOTTHARD_PORT 9999

#define GOTTHARD_TYPE_REQ 0
#define GOTTHARD_TYPE_RES 1

#define GOTTHARD_STATUS_OK                  0
#define GOTTHARD_STATUS_ABORT               1
#define GOTTHARD_STATUS_OPTIMISTIC_ABORT    2
#define GOTTHARD_STATUS_BADREQ              3

#define GOTTHARD_OP_NOP     0
#define GOTTHARD_OP_READ    1
#define GOTTHARD_OP_WRITE   2
#define GOTTHARD_OP_VALUE   3
#define GOTTHARD_OP_UPDATE  4

#include "header.p4"
#include "parser.p4"

metadata intrinsic_metadata_t intrinsic_metadata;


action _nop () {
}


action do_direction_swap (in bit<8> udp_payload_size) { // return the packet to the sender
    // Save old dst IP and port in tmp variable
    req_meta.tmp_ipv4_dstAddr = ipv4.dstAddr;
    req_meta.tmp_udp_dstPort = udp.dstPort;

    ipv4.dstAddr = ipv4.srcAddr;
    ipv4.srcAddr = req_meta.tmp_ipv4_dstAddr;
    ipv4.totalLen = IPV4_HDR_LEN + UDP_HDR_LEN + udp_payload_size;

    udp.dstPort = udp.srcPort;
    udp.srcPort = req_meta.tmp_udp_dstPort;
    udp.length_ = UDP_HDR_LEN + udp_payload_size;
    udp.checksum = (bit<16>)0; // TODO: update the UDP checksum

    gotthard_hdr.from_switch = (bit<1>)1;
    gotthard_hdr.msg_type = GOTTHARD_TYPE_RES;
}

register is_cached_register {
    width: 1;
    instance_count: MAX_REG_INST;
}
register value_register {
    width: 800;
    instance_count: MAX_REG_INST;
}

register is_opti_cached_register {
    width: 1;
    instance_count: MAX_REG_INST;
}
register opti_value_register {
    width: 800;
    instance_count: MAX_REG_INST;
}

metadata req_meta_t req_meta;

action do_check_op1() {
    req_meta.is_r = req_meta.is_r | (gotthard_op[0].op_type == GOTTHARD_OP_READ ? (bit<1>) 1:0);
    req_meta.is_w = req_meta.is_w | (gotthard_op[0].op_type == GOTTHARD_OP_WRITE ? (bit<1>) 1:0);
    req_meta.is_rb = req_meta.is_rb | (gotthard_op[0].op_type == GOTTHARD_OP_VALUE ? (bit<1>) 1:0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[0].op_type == GOTTHARD_OP_READ ? (bit<1>)
        (~is_cached_register[gotthard_op[0].key] & ~is_opti_cached_register[gotthard_op[0].key]) : 0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[0].op_type == GOTTHARD_OP_VALUE ? (bit<1>)
        (~is_cached_register[gotthard_op[0].key] & ~is_opti_cached_register[gotthard_op[0].key]) : 0);
    req_meta.has_invalid_read = req_meta.has_invalid_read |
        (gotthard_op[0].op_type == GOTTHARD_OP_VALUE and
            value_register[gotthard_op[0].key] != gotthard_op[0].value and
            opti_value_register[gotthard_op[0].key] != gotthard_op[0].value ? (bit<1>) 1 : 0);
}

action do_check_op2() {
    do_check_op1();
    req_meta.is_r = req_meta.is_r | (gotthard_op[1].op_type == GOTTHARD_OP_READ ? (bit<1>) 1:0);
    req_meta.is_w = req_meta.is_w | (gotthard_op[1].op_type == GOTTHARD_OP_WRITE ? (bit<1>) 1:0);
    req_meta.is_rb = req_meta.is_rb | (gotthard_op[1].op_type == GOTTHARD_OP_VALUE ? (bit<1>) 1:0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[1].op_type == GOTTHARD_OP_READ ? (bit<1>)
        (~is_cached_register[gotthard_op[1].key] & ~is_opti_cached_register[gotthard_op[1].key]) : 0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[1].op_type == GOTTHARD_OP_VALUE ? (bit<1>)
        (~is_cached_register[gotthard_op[1].key] & ~is_opti_cached_register[gotthard_op[1].key]) : 0);
    req_meta.has_invalid_read = req_meta.has_invalid_read |
        (gotthard_op[1].op_type == GOTTHARD_OP_VALUE and
            value_register[gotthard_op[1].key] != gotthard_op[1].value and
            opti_value_register[gotthard_op[1].key] != gotthard_op[1].value ? (bit<1>) 1 : 0);
}

action do_check_op3() {
    do_check_op2();
    req_meta.is_r = req_meta.is_r | (gotthard_op[2].op_type == GOTTHARD_OP_READ ? (bit<1>) 1:0);
    req_meta.is_w = req_meta.is_w | (gotthard_op[2].op_type == GOTTHARD_OP_WRITE ? (bit<1>) 1:0);
    req_meta.is_rb = req_meta.is_rb | (gotthard_op[2].op_type == GOTTHARD_OP_VALUE ? (bit<1>) 1:0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[2].op_type == GOTTHARD_OP_READ ? (bit<1>)
        (~is_cached_register[gotthard_op[2].key] & ~is_opti_cached_register[gotthard_op[2].key]) : 0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[2].op_type == GOTTHARD_OP_VALUE ? (bit<1>)
        (~is_cached_register[gotthard_op[2].key] & ~is_opti_cached_register[gotthard_op[2].key]) : 0);
    req_meta.has_invalid_read = req_meta.has_invalid_read |
        (gotthard_op[2].op_type == GOTTHARD_OP_VALUE and
            value_register[gotthard_op[2].key] != gotthard_op[2].value and
            opti_value_register[gotthard_op[2].key] != gotthard_op[2].value ? (bit<1>) 1 : 0);
}

action do_check_op4() {
    do_check_op3();
    req_meta.is_r = req_meta.is_r | (gotthard_op[3].op_type == GOTTHARD_OP_READ ? (bit<1>) 1:0);
    req_meta.is_w = req_meta.is_w | (gotthard_op[3].op_type == GOTTHARD_OP_WRITE ? (bit<1>) 1:0);
    req_meta.is_rb = req_meta.is_rb | (gotthard_op[3].op_type == GOTTHARD_OP_VALUE ? (bit<1>) 1:0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[3].op_type == GOTTHARD_OP_READ ? (bit<1>)
        (~is_cached_register[gotthard_op[3].key] & ~is_opti_cached_register[gotthard_op[3].key]) : 0);
    req_meta.has_cache_miss = req_meta.has_cache_miss |
        (gotthard_op[3].op_type == GOTTHARD_OP_VALUE ? (bit<1>)
        (~is_cached_register[gotthard_op[3].key] & ~is_opti_cached_register[gotthard_op[3].key]) : 0);
    req_meta.has_invalid_read = req_meta.has_invalid_read |
        (gotthard_op[3].op_type == GOTTHARD_OP_VALUE and
            value_register[gotthard_op[3].key] != gotthard_op[3].value and
            opti_value_register[gotthard_op[0].key] != gotthard_op[0].value ? (bit<1>) 1 : 0);
}

table t_req_pass1 {
    reads {
        gotthard_hdr.op_cnt: exact;
    }
    actions {
        _nop;
        do_check_op1;
        do_check_op2;
        do_check_op3;
        do_check_op4;
    }
    size: 32;
}

action do_req_fix1() {
    gotthard_op[0].op_type = gotthard_op[0].op_type == GOTTHARD_OP_READ or gotthard_op[0].op_type == GOTTHARD_OP_VALUE ?
        (bit<8>) GOTTHARD_OP_VALUE : GOTTHARD_OP_NOP;
    gotthard_op[0].key = gotthard_op[0].key;
    gotthard_op[0].value = is_opti_cached_register[gotthard_op[0].key] == 1 ?
        opti_value_register[gotthard_op[0].key] : value_register[gotthard_op[0].key];
}

action do_req_fix2() {
    do_req_fix1();
    gotthard_op[1].op_type = gotthard_op[1].op_type == GOTTHARD_OP_READ or gotthard_op[1].op_type == GOTTHARD_OP_VALUE ?
        (bit<8>) GOTTHARD_OP_VALUE : GOTTHARD_OP_NOP;
    gotthard_op[1].key = gotthard_op[1].key;
    gotthard_op[1].value = is_opti_cached_register[gotthard_op[1].key] == 1 ?
        opti_value_register[gotthard_op[1].key] : value_register[gotthard_op[1].key];
}

action do_req_fix3() {
    do_req_fix2();
    gotthard_op[2].op_type = gotthard_op[2].op_type == GOTTHARD_OP_READ or gotthard_op[2].op_type == GOTTHARD_OP_VALUE ?
        (bit<8>) GOTTHARD_OP_VALUE : GOTTHARD_OP_NOP;
    gotthard_op[2].key = gotthard_op[2].key;
    gotthard_op[2].value = is_opti_cached_register[gotthard_op[2].key] == 1 ?
        opti_value_register[gotthard_op[2].key] : value_register[gotthard_op[2].key];
}

action do_req_fix4() {
    do_req_fix3();
    gotthard_op[3].op_type = gotthard_op[3].op_type == GOTTHARD_OP_READ or gotthard_op[3].op_type == GOTTHARD_OP_VALUE ?
        (bit<8>) GOTTHARD_OP_VALUE : GOTTHARD_OP_NOP;
    gotthard_op[3].key = gotthard_op[3].key;
    gotthard_op[3].value = is_opti_cached_register[gotthard_op[3].key] == 1 ?
        opti_value_register[gotthard_op[3].key] : value_register[gotthard_op[3].key];
}

table t_req_fix {
    reads {
        gotthard_hdr.op_cnt: exact;
    }
    actions {
        _nop;
        do_req_fix1;
        do_req_fix2;
        do_req_fix3;
        do_req_fix4;
    }
    size: 32;
}


action do_reply_abort() {
    gotthard_hdr.status = GOTTHARD_STATUS_ABORT;
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}
action do_reply_ok() {
    gotthard_hdr.status = GOTTHARD_STATUS_OK;
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}
table t_reply_client {
    reads {
        req_meta.has_invalid_read: exact;
    }
    actions {
        do_reply_abort;
        do_reply_ok;
    }
    size: 2;
}


action do_store_update1() {
    value_register[gotthard_op[0].key] =
        gotthard_op[0].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            gotthard_op[0].value : value_register[gotthard_op[0].key];
    is_cached_register[gotthard_op[0].key] =
        gotthard_op[0].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            (bit<1>)1 : is_cached_register[gotthard_op[0].key];
    is_opti_cached_register[gotthard_op[0].key] = (bit<1>)0;
}

action do_store_update2() {
    do_store_update1();
    value_register[gotthard_op[1].key] =
        gotthard_op[1].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            gotthard_op[1].value : value_register[gotthard_op[1].key];
    is_cached_register[gotthard_op[1].key] =
        gotthard_op[1].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            (bit<1>)1 : is_cached_register[gotthard_op[1].key];
    is_opti_cached_register[gotthard_op[1].key] = (bit<1>)0;
}

action do_store_update3() {
    do_store_update2();
    value_register[gotthard_op[2].key] =
        gotthard_op[2].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            gotthard_op[2].value : value_register[gotthard_op[2].key];
    is_cached_register[gotthard_op[2].key] =
        gotthard_op[2].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            (bit<1>)1 : is_cached_register[gotthard_op[2].key];
    is_opti_cached_register[gotthard_op[2].key] = (bit<1>)0;
}

action do_store_update4() {
    do_store_update3();
    value_register[gotthard_op[3].key] =
        gotthard_op[3].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            gotthard_op[3].value : value_register[gotthard_op[3].key];
    is_cached_register[gotthard_op[3].key] =
        gotthard_op[3].op_type == (bit<8>)GOTTHARD_OP_UPDATE ?
            (bit<1>)1 : is_cached_register[gotthard_op[3].key];
    is_opti_cached_register[gotthard_op[3].key] = (bit<1>)0;
}

table t_store_update {
    reads {
        gotthard_hdr.op_cnt: exact;
    }
    actions {
        _nop;
        do_store_update1;
        do_store_update2;
        do_store_update3;
        do_store_update4;
    }
    size: 32;
}

action do_opti_update1() {
    is_opti_cached_register[gotthard_op[0].key] = gotthard_op[0].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        (bit<1>) 1 : is_opti_cached_register[gotthard_op[0].key];
    opti_value_register[gotthard_op[0].key] = gotthard_op[0].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        gotthard_op[0].value : opti_value_register[gotthard_op[0].key];
}

action do_opti_update2() {
    do_opti_update1();
    is_opti_cached_register[gotthard_op[1].key] = gotthard_op[1].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        (bit<1>) 1 : is_opti_cached_register[gotthard_op[1].key];
    opti_value_register[gotthard_op[1].key] = gotthard_op[1].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        gotthard_op[1].value : opti_value_register[gotthard_op[1].key];
}

action do_opti_update3() {
    do_opti_update2();
    is_opti_cached_register[gotthard_op[2].key] = gotthard_op[2].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        (bit<1>) 1 : is_opti_cached_register[gotthard_op[2].key];
    opti_value_register[gotthard_op[2].key] = gotthard_op[2].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        gotthard_op[2].value : opti_value_register[gotthard_op[2].key];
}

action do_opti_update4() {
    do_opti_update3();
    is_opti_cached_register[gotthard_op[3].key] = gotthard_op[3].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        (bit<1>) 1 : is_opti_cached_register[gotthard_op[3].key];
    opti_value_register[gotthard_op[3].key] = gotthard_op[3].op_type == (bit<8>)GOTTHARD_OP_WRITE ?
        gotthard_op[3].value : opti_value_register[gotthard_op[3].key];
}

table t_opti_update {
    reads {
        gotthard_hdr.op_cnt: exact;
    }
    actions {
        _nop;
        do_opti_update1;
        do_opti_update2;
        do_opti_update3;
        do_opti_update4;
    }
    size: 32;
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
                apply(t_req_pass1);
                if ((req_meta.is_r == 1 and req_meta.has_cache_miss == 0) or
                    (req_meta.is_rb == 1 and req_meta.has_invalid_read == 1 and req_meta.has_cache_miss == 0)) {
                    apply(t_req_fix);
                    apply(t_reply_client);
                }
                else if (req_meta.is_w == 1) {
                    apply(t_opti_update);
                }
            }
            else {
                apply(t_store_update);
            }
        }

        apply(ipv4_lpm);
        apply(forward);
    }
}

control egress {
    apply(send_frame);
}
