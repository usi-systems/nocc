
#define MAX_REG_INST 1048576

#define GOTTHARD_VALUE_BITS 1024

#define GOTTHARD_VALUE_LEN (GOTTHARD_VALUE_BITS / 8)
#define GOTTHARD_OP_HDR_LEN 5
#define GOTTHARD_OP_LEN (GOTTHARD_OP_HDR_LEN + GOTTHARD_VALUE_LEN)

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

#include <tofino/intrinsic_metadata.p4>
#include <tofino/constants.p4>


action nop() {
}

metadata req_meta_t req_meta;

action do_direction_swap (udp_payload_size) { // return the packet to the sender
    // Save old dst IP and port in tmp variable
    modify_field(req_meta.tmp_ipv4_dstAddr, ipv4.dstAddr);
    modify_field(req_meta.tmp_udp_dstPort, udp.dstPort);

    modify_field(ipv4.dstAddr, ipv4.srcAddr);
    modify_field(ipv4.srcAddr, req_meta.tmp_ipv4_dstAddr);
    modify_field(ipv4.totalLen, IPV4_HDR_LEN + UDP_HDR_LEN + udp_payload_size);

    modify_field(udp.dstPort, udp.srcPort);
    modify_field(udp.srcPort, req_meta.tmp_udp_dstPort);
    modify_field(udp.hdr_length, UDP_HDR_LEN + udp_payload_size);
    modify_field(udp.checksum, 0); // TODO: update the UDP checksum
    modify_field(standard_metadata.egress_spec, 1);
    modify_field(req_meta.tmp_mac_addr, ethernet.srcAddr);
    modify_field(ethernet.srcAddr, ethernet.dstAddr);
    modify_field(ethernet.dstAddr, req_meta.tmp_mac_addr);


    modify_field(gotthard_hdr.from_switch, 1);
    modify_field(gotthard_hdr.msg_type, GOTTHARD_TYPE_RES);
    modify_field(gotthard_hdr.frag_cnt, 1);
    modify_field(gotthard_hdr.frag_seq, 1);
}


register is_cached_register {
    width: 1;
    instance_count: MAX_REG_INST;
}
register value_register {
    width: GOTTHARD_VALUE_BITS;
    instance_count: MAX_REG_INST;
}

register is_opti_cached_register {
    width: 1;
    instance_count: MAX_REG_INST;
}
register opti_value_register {
    width: GOTTHARD_VALUE_BITS;
    instance_count: MAX_REG_INST;
}

action do_reply_abort() {
// TODO: ternary operator?
//    if (req_meta.has_opti_invalid_read == 1) {
//        if (1 == 1) {
//       modify_field(gotthard_hdr.status, GOTTHARD_STATUS_OPTIMISTIC_ABORT);
//    } else {
//       modify_field(gotthard_hdr.status, GOTTHARD_STATUS_ABORT);
//    }
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}

action do_reply_ok() {
    modify_field(gotthard_hdr.status, GOTTHARD_STATUS_OK);
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


action _drop() {
    drop();
}


header_type routing_metadata_t {
    fields {
        nhop_ipv4 : 32;
    }
}

metadata routing_metadata_t routing_metadata;

action rewrite_mac(smac) {
    modify_field(ethernet.srcAddr,smac);
}

action rewrite_addr(src_mac_addr, dst_addr, dst_mac_addr, out_port) {
    modify_field(ipv4.srcAddr, ipv4.dstAddr);
    modify_field(ipv4.dstAddr, dst_addr);
    modify_field(ethernet.srcAddr, src_mac_addr);
    modify_field(ethernet.dstAddr, dst_mac_addr);
    modify_field(standard_metadata.egress_spec,out_port);
}

table nat {
    reads {
        ipv4.srcAddr : exact;
    } actions {
        rewrite_addr;
        _drop;
	nop;
    }
    size : 128;
}

table drop_tbl {
    actions {
	_drop;
    }
}

/* Main control flow */
control ingress {
}


