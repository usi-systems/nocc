#include <core.p4>
#include <v1model.p4>

#include "config.p4"
#include "header.p4"
#include "parser.p4"

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name("rewrite_mac") action rewrite_mac(bit<48> smac) {
        hdr.ethernet.srcAddr = smac;
    }
    @name("_drop") action _drop() {
        mark_to_drop();
    }
    @name("send_frame") table send_frame() {
        actions = {
            rewrite_mac;
            _drop;
            NoAction;
        }
        key = {
            standard_metadata.egress_port: exact;
        }
        size = 256;
        default_action = NoAction();
    }
    apply {
        send_frame.apply();
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name("is_cached_register") register<bit<1>>(MAX_REG_INST) is_cached_register;
    @name("value_register") register<bit<GOTTHARD_VALUE_BITS>>(MAX_REG_INST) value_register;

    @name("do_store_update0") action do_store_update0() {
        value_register.write(hdr.gotthard_op[0].key, hdr.gotthard_op[0].value);
        is_cached_register.write(hdr.gotthard_op[0].key, 1);
    }
    @name("do_store_update1") action do_store_update1() {
        do_store_update0();
        value_register.write(hdr.gotthard_op[1].key, hdr.gotthard_op[1].value);
        is_cached_register.write(hdr.gotthard_op[1].key, 1);
    }
    @name("do_store_update2") action do_store_update2() {
        do_store_update1();
        value_register.write(hdr.gotthard_op[2].key, hdr.gotthard_op[2].value);
        is_cached_register.write(hdr.gotthard_op[2].key, 1);
    }
    @name("do_store_update3") action do_store_update3() {
        do_store_update2();
        value_register.write(hdr.gotthard_op[3].key, hdr.gotthard_op[3].value);
        is_cached_register.write(hdr.gotthard_op[3].key, 1);
    }
    @name("do_store_update4") action do_store_update4() {
        do_store_update3();
        value_register.write(hdr.gotthard_op[4].key, hdr.gotthard_op[4].value);
        is_cached_register.write(hdr.gotthard_op[4].key, 1);
    }
    @name("do_store_update5") action do_store_update5() {
        do_store_update4();
        value_register.write(hdr.gotthard_op[5].key, hdr.gotthard_op[5].value);
        is_cached_register.write(hdr.gotthard_op[5].key, 1);
    }
    @name("do_store_update6") action do_store_update6() {
        do_store_update5();
        value_register.write(hdr.gotthard_op[6].key, hdr.gotthard_op[6].value);
        is_cached_register.write(hdr.gotthard_op[6].key, 1);
    }
    @name("do_store_update7") action do_store_update7() {
        do_store_update6();
        value_register.write(hdr.gotthard_op[7].key, hdr.gotthard_op[7].value);
        is_cached_register.write(hdr.gotthard_op[7].key, 1);
    }
    @name("do_store_update8") action do_store_update8() {
        do_store_update7();
        value_register.write(hdr.gotthard_op[8].key, hdr.gotthard_op[8].value);
        is_cached_register.write(hdr.gotthard_op[8].key, 1);
    }
    @name("do_store_update9") action do_store_update9() {
        do_store_update8();
        value_register.write(hdr.gotthard_op[9].key, hdr.gotthard_op[9].value);
        is_cached_register.write(hdr.gotthard_op[9].key, 1);
    }

    @name("do_satisfy_read0") action do_satisfy_read0() {
        hdr.gotthard_op[0].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[0].value, hdr.gotthard_op[0].key);
    }
    @name("do_satisfy_read1") action do_satisfy_read1() {
        do_satisfy_read0();
        hdr.gotthard_op[1].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[1].value, hdr.gotthard_op[1].key);
    }
    @name("do_satisfy_read2") action do_satisfy_read2() {
        do_satisfy_read1();
        hdr.gotthard_op[2].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[2].value, hdr.gotthard_op[2].key);
    }
    @name("do_satisfy_read3") action do_satisfy_read3() {
        do_satisfy_read2();
        hdr.gotthard_op[3].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[3].value, hdr.gotthard_op[3].key);
    }
    @name("do_satisfy_read4") action do_satisfy_read4() {
        do_satisfy_read3();
        hdr.gotthard_op[4].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[4].value, hdr.gotthard_op[4].key);
    }
    @name("do_satisfy_read5") action do_satisfy_read5() {
        do_satisfy_read4();
        hdr.gotthard_op[5].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[5].value, hdr.gotthard_op[5].key);
    }
    @name("do_satisfy_read6") action do_satisfy_read6() {
        do_satisfy_read5();
        hdr.gotthard_op[6].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[6].value, hdr.gotthard_op[6].key);
    }
    @name("do_satisfy_read7") action do_satisfy_read7() {
        do_satisfy_read6();
        hdr.gotthard_op[7].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[7].value, hdr.gotthard_op[7].key);
    }
    @name("do_satisfy_read8") action do_satisfy_read8() {
        do_satisfy_read7();
        hdr.gotthard_op[8].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[8].value, hdr.gotthard_op[8].key);
    }
    @name("do_satisfy_read9") action do_satisfy_read9() {
        do_satisfy_read8();
        hdr.gotthard_op[9].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[9].value, hdr.gotthard_op[9].key);
    }


    @name("do_direction_swap") action do_direction_swap() {
        // Save old dst IP and port in tmp variable
        meta.req_meta.tmp_ipv4_dstAddr = hdr.ipv4.dstAddr;
        meta.req_meta.tmp_udp_dstPort = hdr.udp.dstPort;

        hdr.ipv4.dstAddr = hdr.ipv4.srcAddr;
        hdr.ipv4.srcAddr = meta.req_meta.tmp_ipv4_dstAddr;

        hdr.udp.dstPort = hdr.udp.srcPort;
        hdr.udp.srcPort = meta.req_meta.tmp_udp_dstPort;
        hdr.udp.checksum = (bit<16>)0;

        hdr.gotthard.from_switch = (bit<1>)1;
        hdr.gotthard.msg_type = GOTTHARD_TYPE_RES;
        hdr.gotthard.frag_cnt = (bit<8>)1;
        hdr.gotthard.frag_seq = (bit<8>)1;
    }

    @name("do_reply_ok") action do_reply_ok() {
        hdr.gotthard.status = GOTTHARD_STATUS_OK;
        do_direction_swap();
    }
    @name("_drop") action _drop() {
        mark_to_drop();
    }
    @name("set_nhop") action set_nhop(bit<32> nhop_ipv4, bit<9> port) {
        meta.ingress_metadata.nhop_ipv4 = nhop_ipv4;
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl + 8w255;
    }
    @name("set_dmac") action set_dmac(bit<48> dmac) {
        hdr.ethernet.dstAddr = dmac;
    }

    @name("ipv4_lpm") table ipv4_lpm() {
        actions = {
            _drop;
            set_nhop;
            NoAction;
        }
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        size = 1024;
        default_action = NoAction();
    }
    @name("forward") table forward() {
        actions = {
            set_dmac;
            _drop;
            NoAction;
        }
        key = {
            meta.ingress_metadata.nhop_ipv4: exact;
        }
        size = 512;
        default_action = NoAction();
    }
    @name("t_reply_client") table t_reply_client() {
        actions = {
            do_reply_ok;
            NoAction;
        }
        size = 1;
        default_action = NoAction();
    }
    @name("t_store_update") table t_store_update() {
        actions = {
            do_store_update0;
            do_store_update1;
            do_store_update2;
            do_store_update3;
            do_store_update4;
            do_store_update5;
            do_store_update6;
            do_store_update7;
            do_store_update8;
            do_store_update9;
            NoAction;
        }
        key = {
            hdr.gotthard.op_cnt: exact;
        }
        size = 10;
        default_action = NoAction();
    }
    @name("t_satisfy_read") table t_satisfy_read() {
        actions = {
            do_satisfy_read0;
            do_satisfy_read1;
            do_satisfy_read2;
            do_satisfy_read3;
            do_satisfy_read4;
            do_satisfy_read5;
            do_satisfy_read6;
            do_satisfy_read7;
            do_satisfy_read8;
            do_satisfy_read9;
            NoAction;
        }
        key = {
            hdr.gotthard.op_cnt: exact;
        }
        size = 10;
        default_action = NoAction();
    }
    apply {
        if (hdr.ipv4.isValid()) {
            if (hdr.gotthard.isValid()) {
                if (hdr.gotthard.msg_type == GOTTHARD_TYPE_REQ && hdr.gotthard.frag_cnt == 1) {

                    bit cached0 = 0; bit cached1 = 0; bit cached2 = 0; bit cached3 = 0; bit cached4 = 0; bit cached5 = 0; bit cached6 = 0; bit cached7 = 0; bit cached8 = 0; bit cached9 = 0;
                    if (hdr.gotthard.op_cnt > 0) { is_cached_register.read(cached0, hdr.gotthard_op[0].key); }
                    if (hdr.gotthard.op_cnt > 1) { is_cached_register.read(cached1, hdr.gotthard_op[1].key); }
                    if (hdr.gotthard.op_cnt > 2) { is_cached_register.read(cached2, hdr.gotthard_op[2].key); }
                    if (hdr.gotthard.op_cnt > 3) { is_cached_register.read(cached3, hdr.gotthard_op[3].key); }
                    if (hdr.gotthard.op_cnt > 4) { is_cached_register.read(cached4, hdr.gotthard_op[4].key); }
                    if (hdr.gotthard.op_cnt > 5) { is_cached_register.read(cached5, hdr.gotthard_op[5].key); }
                    if (hdr.gotthard.op_cnt > 6) { is_cached_register.read(cached6, hdr.gotthard_op[6].key); }
                    if (hdr.gotthard.op_cnt > 7) { is_cached_register.read(cached7, hdr.gotthard_op[7].key); }
                    if (hdr.gotthard.op_cnt > 8) { is_cached_register.read(cached8, hdr.gotthard_op[8].key); }
                    if (hdr.gotthard.op_cnt > 9) { is_cached_register.read(cached9, hdr.gotthard_op[9].key); }

                    if ( // only reads AND no cache misses
                            (hdr.gotthard.op_cnt < 1 || (hdr.gotthard.op_cnt > 0 && hdr.gotthard_op[0].op_type == GOTTHARD_OP_READ && cached0 == 1)) &&
                            (hdr.gotthard.op_cnt < 2 || (hdr.gotthard.op_cnt > 1 && hdr.gotthard_op[1].op_type == GOTTHARD_OP_READ && cached1 == 1)) &&
                            (hdr.gotthard.op_cnt < 3 || (hdr.gotthard.op_cnt > 2 && hdr.gotthard_op[2].op_type == GOTTHARD_OP_READ && cached2 == 1)) &&
                            (hdr.gotthard.op_cnt < 4 || (hdr.gotthard.op_cnt > 3 && hdr.gotthard_op[3].op_type == GOTTHARD_OP_READ && cached3 == 1)) &&
                            (hdr.gotthard.op_cnt < 5 || (hdr.gotthard.op_cnt > 4 && hdr.gotthard_op[4].op_type == GOTTHARD_OP_READ && cached4 == 1)) &&
                            (hdr.gotthard.op_cnt < 6 || (hdr.gotthard.op_cnt > 5 && hdr.gotthard_op[5].op_type == GOTTHARD_OP_READ && cached5 == 1)) &&
                            (hdr.gotthard.op_cnt < 7 || (hdr.gotthard.op_cnt > 6 && hdr.gotthard_op[6].op_type == GOTTHARD_OP_READ && cached6 == 1)) &&
                            (hdr.gotthard.op_cnt < 8 || (hdr.gotthard.op_cnt > 7 && hdr.gotthard_op[7].op_type == GOTTHARD_OP_READ && cached7 == 1)) &&
                            (hdr.gotthard.op_cnt < 9 || (hdr.gotthard.op_cnt > 8 && hdr.gotthard_op[8].op_type == GOTTHARD_OP_READ && cached8 == 1)) &&
                            (hdr.gotthard.op_cnt < 10 || (hdr.gotthard.op_cnt > 9 && hdr.gotthard_op[9].op_type == GOTTHARD_OP_READ && cached9 == 1))
                       ) {
                        t_satisfy_read.apply();
                        t_reply_client.apply();
                    }
                }
                else if (hdr.gotthard.msg_type == GOTTHARD_TYPE_RES) {
                    t_store_update.apply();
                }
            }
            ipv4_lpm.apply();
            forward.apply();
        }
    }
}

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;
