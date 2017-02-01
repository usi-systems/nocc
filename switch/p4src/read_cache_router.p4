//#define MAX_REG_INST 2097152
#define MAX_REG_INST 1048576

#define GOTTHARD_VALUE_BITS 1024

#define GOTTHARD_VALUE_LEN (GOTTHARD_VALUE_BITS / 8)
#define GOTTHARD_OP_HDR_LEN 5
#define GOTTHARD_OP_LEN (GOTTHARD_OP_HDR_LEN + GOTTHARD_VALUE_LEN)

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

#include "loop_tables.generated.p4"

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
    gotthard_hdr.frag_cnt = (bit<8>)1;
    gotthard_hdr.frag_seq = (bit<8>)1;
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

metadata req_meta_t req_meta;


action do_reply_abort() {
    gotthard_hdr.status = GOTTHARD_STATUS_ABORT;
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}
action do_reply_opti_abort() {
    gotthard_hdr.status = GOTTHARD_STATUS_OPTIMISTIC_ABORT;
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}
action do_reply_ok() {
    gotthard_hdr.status = GOTTHARD_STATUS_OK;
    do_direction_swap(GOTTHARD_HDR_LEN + (gotthard_hdr.op_cnt*GOTTHARD_OP_LEN));
}
table t_reply_client {
    reads {
        req_meta.has_bad_compare: exact;
        req_meta.has_bad_opti_compare: exact;
    }
    actions {
        do_reply_abort;
        do_reply_opti_abort;
        do_reply_ok;
    }
    size: 4;
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
            if (gotthard_hdr.msg_type == GOTTHARD_TYPE_REQ and
                gotthard_hdr.frag_cnt == (bit<8>)1
                ) {

                if ( // only reads AND no cache misses
                    (gotthard_hdr.op_cnt < 1 or (gotthard_hdr.op_cnt > 0 and gotthard_op[0].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[0].key] == 1)) and
                    (gotthard_hdr.op_cnt < 2 or (gotthard_hdr.op_cnt > 1 and gotthard_op[1].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[1].key] == 1)) and
                    (gotthard_hdr.op_cnt < 3 or (gotthard_hdr.op_cnt > 2 and gotthard_op[2].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[2].key] == 1)) and
                    (gotthard_hdr.op_cnt < 4 or (gotthard_hdr.op_cnt > 3 and gotthard_op[3].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[3].key] == 1)) and
                    (gotthard_hdr.op_cnt < 5 or (gotthard_hdr.op_cnt > 4 and gotthard_op[4].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[4].key] == 1)) and
                    (gotthard_hdr.op_cnt < 6 or (gotthard_hdr.op_cnt > 5 and gotthard_op[5].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[5].key] == 1)) and
                    (gotthard_hdr.op_cnt < 7 or (gotthard_hdr.op_cnt > 6 and gotthard_op[6].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[6].key] == 1)) and
                    (gotthard_hdr.op_cnt < 8 or (gotthard_hdr.op_cnt > 7 and gotthard_op[7].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[7].key] == 1)) and
                    (gotthard_hdr.op_cnt < 9 or (gotthard_hdr.op_cnt > 8 and gotthard_op[8].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[8].key] == 1)) and
                    (gotthard_hdr.op_cnt < 10 or (gotthard_hdr.op_cnt > 9 and gotthard_op[9].op_type == GOTTHARD_OP_READ and is_cached_register[gotthard_op[9].key] == 1))
                   ) {
                    if (gotthard_hdr.op_cnt > 0) {
                        apply(t_satisfy_read0);
                    }
                    if (gotthard_hdr.op_cnt > 1) {
                        apply(t_satisfy_read1);
                    }
                    if (gotthard_hdr.op_cnt > 2) {
                        apply(t_satisfy_read2);
                    }
                    if (gotthard_hdr.op_cnt > 3) {
                        apply(t_satisfy_read3);
                    }
                    if (gotthard_hdr.op_cnt > 4) {
                        apply(t_satisfy_read4);
                    }
                    if (gotthard_hdr.op_cnt > 5) {
                        apply(t_satisfy_read5);
                    }
                    if (gotthard_hdr.op_cnt > 6) {
                        apply(t_satisfy_read6);
                    }
                    if (gotthard_hdr.op_cnt > 7) {
                        apply(t_satisfy_read7);
                    }
                    if (gotthard_hdr.op_cnt > 8) {
                        apply(t_satisfy_read8);
                    }
                    if (gotthard_hdr.op_cnt > 9) {
                        apply(t_satisfy_read9);
                    }

                    apply(t_reply_client);
                }

            }
            else if (gotthard_hdr.msg_type == GOTTHARD_TYPE_RES) {
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
