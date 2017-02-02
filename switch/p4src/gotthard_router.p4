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
    @name("is_opti_cached_register") register<bit<1>>(MAX_REG_INST) is_opti_cached_register;
    @name("opti_value_register") register<bit<GOTTHARD_VALUE_BITS>>(MAX_REG_INST) opti_value_register;

    @name("do_store_update0") action do_store_update0() {
        value_register.write(hdr.gotthard_op[0].key, hdr.gotthard_op[0].value);
        is_cached_register.write(hdr.gotthard_op[0].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[0].key);
        is_opti_cached_register.write(hdr.gotthard_op[0].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update1") action do_store_update1() {
        value_register.write(hdr.gotthard_op[1].key, hdr.gotthard_op[1].value);
        is_cached_register.write(hdr.gotthard_op[1].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[1].key);
        is_opti_cached_register.write(hdr.gotthard_op[1].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update2") action do_store_update2() {
        value_register.write(hdr.gotthard_op[2].key, hdr.gotthard_op[2].value);
        is_cached_register.write(hdr.gotthard_op[2].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[2].key);
        is_opti_cached_register.write(hdr.gotthard_op[2].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update3") action do_store_update3() {
        value_register.write(hdr.gotthard_op[3].key, hdr.gotthard_op[3].value);
        is_cached_register.write(hdr.gotthard_op[3].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[3].key);
        is_opti_cached_register.write(hdr.gotthard_op[3].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update4") action do_store_update4() {
        value_register.write(hdr.gotthard_op[4].key, hdr.gotthard_op[4].value);
        is_cached_register.write(hdr.gotthard_op[4].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[4].key);
        is_opti_cached_register.write(hdr.gotthard_op[4].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update5") action do_store_update5() {
        value_register.write(hdr.gotthard_op[5].key, hdr.gotthard_op[5].value);
        is_cached_register.write(hdr.gotthard_op[5].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[5].key);
        is_opti_cached_register.write(hdr.gotthard_op[5].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update6") action do_store_update6() {
        value_register.write(hdr.gotthard_op[6].key, hdr.gotthard_op[6].value);
        is_cached_register.write(hdr.gotthard_op[6].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[6].key);
        is_opti_cached_register.write(hdr.gotthard_op[6].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update7") action do_store_update7() {
        value_register.write(hdr.gotthard_op[7].key, hdr.gotthard_op[7].value);
        is_cached_register.write(hdr.gotthard_op[7].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[7].key);
        is_opti_cached_register.write(hdr.gotthard_op[7].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update8") action do_store_update8() {
        value_register.write(hdr.gotthard_op[8].key, hdr.gotthard_op[8].value);
        is_cached_register.write(hdr.gotthard_op[8].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[8].key);
        is_opti_cached_register.write(hdr.gotthard_op[8].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
    }
    @name("do_store_update9") action do_store_update9() {
        value_register.write(hdr.gotthard_op[9].key, hdr.gotthard_op[9].value);
        is_cached_register.write(hdr.gotthard_op[9].key, 1);
        // clear if this is an abort:
        bit old_val;
        is_opti_cached_register.read(old_val, hdr.gotthard_op[9].key);
        is_opti_cached_register.write(hdr.gotthard_op[9].key, (((bit<1>)hdr.gotthard.status) ^ 1) & old_val);
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

    @name("do_reply_abort") action do_reply_abort() {
        hdr.gotthard.status = GOTTHARD_STATUS_ABORT;
        do_direction_swap();
    }
    @name("do_reply_opti_abort") action do_reply_opti_abort() {
        hdr.gotthard.status = GOTTHARD_STATUS_OPTIMISTIC_ABORT;
        do_direction_swap();
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
    @name("do_cache_miss") action do_cache_miss() {
        meta.req_meta.has_cache_miss = 1;
    }
    @name("do_bad_compare0") action do_bad_compare0() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[0].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[0].value, hdr.gotthard_op[0].key);
    }
    @name("do_bad_compare1") action do_bad_compare1() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[1].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[1].value, hdr.gotthard_op[1].key);
    }
    @name("do_bad_compare2") action do_bad_compare2() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[2].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[2].value, hdr.gotthard_op[2].key);
    }
    @name("do_bad_compare3") action do_bad_compare3() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[3].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[3].value, hdr.gotthard_op[3].key);
    }
    @name("do_bad_compare4") action do_bad_compare4() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[4].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[4].value, hdr.gotthard_op[4].key);
    }
    @name("do_bad_compare5") action do_bad_compare5() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[5].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[5].value, hdr.gotthard_op[5].key);
    }
    @name("do_bad_compare6") action do_bad_compare6() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[6].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[6].value, hdr.gotthard_op[6].key);
    }
    @name("do_bad_compare7") action do_bad_compare7() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[7].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[7].value, hdr.gotthard_op[7].key);
    }
    @name("do_bad_compare8") action do_bad_compare8() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[8].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[8].value, hdr.gotthard_op[8].key);
    }
    @name("do_bad_compare9") action do_bad_compare9() {
        meta.req_meta.has_bad_compare = 1;
        hdr.gotthard_op[9].op_type = GOTTHARD_OP_VALUE;
        value_register.read(hdr.gotthard_op[9].value, hdr.gotthard_op[9].key);
    }
    @name("do_bad_opti_compare0") action do_bad_opti_compare0() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[0].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[0].value, hdr.gotthard_op[0].key);
    }
    @name("do_bad_opti_compare1") action do_bad_opti_compare1() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[1].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[1].value, hdr.gotthard_op[1].key);
    }
    @name("do_bad_opti_compare2") action do_bad_opti_compare2() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[2].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[2].value, hdr.gotthard_op[2].key);
    }
    @name("do_bad_opti_compare3") action do_bad_opti_compare3() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[3].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[3].value, hdr.gotthard_op[3].key);
    }
    @name("do_bad_opti_compare4") action do_bad_opti_compare4() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[4].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[4].value, hdr.gotthard_op[4].key);
    }
    @name("do_bad_opti_compare5") action do_bad_opti_compare5() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[5].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[5].value, hdr.gotthard_op[5].key);
    }
    @name("do_bad_opti_compare6") action do_bad_opti_compare6() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[6].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[6].value, hdr.gotthard_op[6].key);
    }
    @name("do_bad_opti_compare7") action do_bad_opti_compare7() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[7].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[7].value, hdr.gotthard_op[7].key);
    }
    @name("do_bad_opti_compare8") action do_bad_opti_compare8() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[8].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[8].value, hdr.gotthard_op[8].key);
    }
    @name("do_bad_opti_compare9") action do_bad_opti_compare9() {
        meta.req_meta.has_bad_opti_compare = 1;
        hdr.gotthard_op[9].op_type = GOTTHARD_OP_VALUE;
        opti_value_register.read(hdr.gotthard_op[9].value, hdr.gotthard_op[9].key);
    }
    @name("do_handle_write0") action do_handle_write0() {
        is_opti_cached_register.write(hdr.gotthard_op[0].key, 1);
        is_cached_register.write(hdr.gotthard_op[0].key,  0);
        opti_value_register.write(hdr.gotthard_op[0].key, hdr.gotthard_op[0].value);
    }
    @name("do_handle_write1") action do_handle_write1() {
        is_opti_cached_register.write(hdr.gotthard_op[1].key, 1);
        is_cached_register.write(hdr.gotthard_op[1].key,  0);
        opti_value_register.write(hdr.gotthard_op[1].key, hdr.gotthard_op[1].value);
    }
    @name("do_handle_write2") action do_handle_write2() {
        is_opti_cached_register.write(hdr.gotthard_op[2].key, 1);
        is_cached_register.write(hdr.gotthard_op[2].key,  0);
        opti_value_register.write(hdr.gotthard_op[2].key, hdr.gotthard_op[2].value);
    }
    @name("do_handle_write3") action do_handle_write3() {
        is_opti_cached_register.write(hdr.gotthard_op[3].key, 1);
        is_cached_register.write(hdr.gotthard_op[3].key,  0);
        opti_value_register.write(hdr.gotthard_op[3].key, hdr.gotthard_op[3].value);
    }
    @name("do_handle_write4") action do_handle_write4() {
        is_opti_cached_register.write(hdr.gotthard_op[4].key, 1);
        is_cached_register.write(hdr.gotthard_op[4].key,  0);
        opti_value_register.write(hdr.gotthard_op[4].key, hdr.gotthard_op[4].value);
    }
    @name("do_handle_write5") action do_handle_write5() {
        is_opti_cached_register.write(hdr.gotthard_op[5].key, 1);
        is_cached_register.write(hdr.gotthard_op[5].key,  0);
        opti_value_register.write(hdr.gotthard_op[5].key, hdr.gotthard_op[5].value);
    }
    @name("do_handle_write6") action do_handle_write6() {
        is_opti_cached_register.write(hdr.gotthard_op[6].key, 1);
        is_cached_register.write(hdr.gotthard_op[6].key,  0);
        opti_value_register.write(hdr.gotthard_op[6].key, hdr.gotthard_op[6].value);
    }
    @name("do_handle_write7") action do_handle_write7() {
        is_opti_cached_register.write(hdr.gotthard_op[7].key, 1);
        is_cached_register.write(hdr.gotthard_op[7].key,  0);
        opti_value_register.write(hdr.gotthard_op[7].key, hdr.gotthard_op[7].value);
    }
    @name("do_handle_write8") action do_handle_write8() {
        is_opti_cached_register.write(hdr.gotthard_op[8].key, 1);
        is_cached_register.write(hdr.gotthard_op[8].key,  0);
        opti_value_register.write(hdr.gotthard_op[8].key, hdr.gotthard_op[8].value);
    }
    @name("do_handle_write9") action do_handle_write9() {
        is_opti_cached_register.write(hdr.gotthard_op[9].key, 1);
        is_cached_register.write(hdr.gotthard_op[9].key,  0);
        opti_value_register.write(hdr.gotthard_op[9].key, hdr.gotthard_op[9].value);
    }
    @name("do_delete_op0") action do_delete_op0() {
        hdr.gotthard_op[0].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op1") action do_delete_op1() {
        hdr.gotthard_op[1].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op2") action do_delete_op2() {
        hdr.gotthard_op[2].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op3") action do_delete_op3() {
        hdr.gotthard_op[3].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op4") action do_delete_op4() {
        hdr.gotthard_op[4].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op5") action do_delete_op5() {
        hdr.gotthard_op[5].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op6") action do_delete_op6() {
        hdr.gotthard_op[6].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op7") action do_delete_op7() {
        hdr.gotthard_op[7].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op8") action do_delete_op8() {
        hdr.gotthard_op[8].op_type = GOTTHARD_OP_NOP;
    }
    @name("do_delete_op9") action do_delete_op9() {
        hdr.gotthard_op[9].op_type = GOTTHARD_OP_NOP;
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
            do_reply_abort;
            do_reply_opti_abort;
            NoAction;
        }
        key = {
            meta.req_meta.has_bad_compare: exact;
            meta.req_meta.has_bad_opti_compare: exact;
        }
        size = 4;
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
    @name("t_cache_miss") table t_cache_miss() {
        actions = {
            do_cache_miss;
            NoAction;
        }
        size = 1;
        default_action = NoAction();
    }
    @name("t_bad_compare0") table t_bad_compare0() {
        actions = { do_bad_compare0; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare1") table t_bad_compare1() {
        actions = { do_bad_compare1; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare2") table t_bad_compare2() {
        actions = { do_bad_compare2; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare3") table t_bad_compare3() {
        actions = { do_bad_compare3; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare4") table t_bad_compare4() {
        actions = { do_bad_compare4; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare5") table t_bad_compare5() {
        actions = { do_bad_compare5; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare6") table t_bad_compare6() {
        actions = { do_bad_compare6; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare7") table t_bad_compare7() {
        actions = { do_bad_compare7; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare8") table t_bad_compare8() {
        actions = { do_bad_compare8; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_compare9") table t_bad_compare9() {
        actions = { do_bad_compare9; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare0") table t_bad_opti_compare0() {
        actions = { do_bad_opti_compare0; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare1") table t_bad_opti_compare1() {
        actions = { do_bad_opti_compare1; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare2") table t_bad_opti_compare2() {
        actions = { do_bad_opti_compare2; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare3") table t_bad_opti_compare3() {
        actions = { do_bad_opti_compare3; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare4") table t_bad_opti_compare4() {
        actions = { do_bad_opti_compare4; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare5") table t_bad_opti_compare5() {
        actions = { do_bad_opti_compare5; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare6") table t_bad_opti_compare6() {
        actions = { do_bad_opti_compare6; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare7") table t_bad_opti_compare7() {
        actions = { do_bad_opti_compare7; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare8") table t_bad_opti_compare8() {
        actions = { do_bad_opti_compare8; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_bad_opti_compare9") table t_bad_opti_compare9() {
        actions = { do_bad_opti_compare9; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write0") table t_handle_write0() {
        actions = { do_handle_write0; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write1") table t_handle_write1() {
        actions = { do_handle_write1; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write2") table t_handle_write2() {
        actions = { do_handle_write2; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write3") table t_handle_write3() {
        actions = { do_handle_write3; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write4") table t_handle_write4() {
        actions = { do_handle_write4; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write5") table t_handle_write5() {
        actions = { do_handle_write5; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write6") table t_handle_write6() {
        actions = { do_handle_write6; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write7") table t_handle_write7() {
        actions = { do_handle_write7; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write8") table t_handle_write8() {
        actions = { do_handle_write8; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_handle_write9") table t_handle_write9() {
        actions = { do_handle_write9; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op0") table t_delete_op0() {
        actions = { do_delete_op0; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op1") table t_delete_op1() {
        actions = { do_delete_op1; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op2") table t_delete_op2() {
        actions = { do_delete_op2; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op3") table t_delete_op3() {
        actions = { do_delete_op3; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op4") table t_delete_op4() {
        actions = { do_delete_op4; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op5") table t_delete_op5() {
        actions = { do_delete_op5; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op6") table t_delete_op6() {
        actions = { do_delete_op6; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op7") table t_delete_op7() {
        actions = { do_delete_op7; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op8") table t_delete_op8() {
        actions = { do_delete_op8; NoAction; }
        size = 1; default_action = NoAction();
    }
    @name("t_delete_op9") table t_delete_op9() {
        actions = { do_delete_op9; NoAction; }
        size = 1; default_action = NoAction();
    }
    apply {
        if (hdr.ipv4.isValid()) {
            if (hdr.gotthard.isValid()) {
                if (hdr.gotthard.msg_type == GOTTHARD_TYPE_REQ && hdr.gotthard.frag_cnt == 1) {

                    bit cached0 = 0; bit cached1 = 0; bit cached2 = 0; bit cached3 = 0; bit cached4 = 0; bit cached5 = 0; bit cached6 = 0; bit cached7 = 0; bit cached8 = 0; bit cached9 = 0;
                    bit opti_cached0 = 0; bit opti_cached1 = 0; bit opti_cached2 = 0; bit opti_cached3 = 0; bit opti_cached4 = 0; bit opti_cached5 = 0; bit opti_cached6 = 0; bit opti_cached7 = 0; bit opti_cached8 = 0; bit opti_cached9 = 0;
                    if (hdr.gotthard.op_cnt > 0) { is_cached_register.read(cached0, hdr.gotthard_op[0].key); is_opti_cached_register.read(opti_cached0, hdr.gotthard_op[0].key); }
                    if (hdr.gotthard.op_cnt > 1) { is_cached_register.read(cached1, hdr.gotthard_op[1].key); is_opti_cached_register.read(opti_cached1, hdr.gotthard_op[1].key); }
                    if (hdr.gotthard.op_cnt > 2) { is_cached_register.read(cached2, hdr.gotthard_op[2].key); is_opti_cached_register.read(opti_cached2, hdr.gotthard_op[2].key); }
                    if (hdr.gotthard.op_cnt > 3) { is_cached_register.read(cached3, hdr.gotthard_op[3].key); is_opti_cached_register.read(opti_cached3, hdr.gotthard_op[3].key); }
                    if (hdr.gotthard.op_cnt > 4) { is_cached_register.read(cached4, hdr.gotthard_op[4].key); is_opti_cached_register.read(opti_cached4, hdr.gotthard_op[4].key); }
                    if (hdr.gotthard.op_cnt > 5) { is_cached_register.read(cached5, hdr.gotthard_op[5].key); is_opti_cached_register.read(opti_cached5, hdr.gotthard_op[5].key); }
                    if (hdr.gotthard.op_cnt > 6) { is_cached_register.read(cached6, hdr.gotthard_op[6].key); is_opti_cached_register.read(opti_cached6, hdr.gotthard_op[6].key); }
                    if (hdr.gotthard.op_cnt > 7) { is_cached_register.read(cached7, hdr.gotthard_op[7].key); is_opti_cached_register.read(opti_cached7, hdr.gotthard_op[7].key); }
                    if (hdr.gotthard.op_cnt > 8) { is_cached_register.read(cached8, hdr.gotthard_op[8].key); is_opti_cached_register.read(opti_cached8, hdr.gotthard_op[8].key); }
                    if (hdr.gotthard.op_cnt > 9) { is_cached_register.read(cached9, hdr.gotthard_op[9].key); is_opti_cached_register.read(opti_cached9, hdr.gotthard_op[9].key); }

                    if (
                        (hdr.gotthard.op_cnt > 0 && hdr.gotthard_op[0].op_type == GOTTHARD_OP_VALUE && cached0 == 0 && opti_cached0 == 0) ||
                        (hdr.gotthard.op_cnt > 1 && hdr.gotthard_op[1].op_type == GOTTHARD_OP_VALUE && cached1 == 0 && opti_cached1 == 0) ||
                        (hdr.gotthard.op_cnt > 2 && hdr.gotthard_op[2].op_type == GOTTHARD_OP_VALUE && cached2 == 0 && opti_cached2 == 0) ||
                        (hdr.gotthard.op_cnt > 3 && hdr.gotthard_op[3].op_type == GOTTHARD_OP_VALUE && cached3 == 0 && opti_cached3 == 0) ||
                        (hdr.gotthard.op_cnt > 4 && hdr.gotthard_op[4].op_type == GOTTHARD_OP_VALUE && cached4 == 0 && opti_cached4 == 0) ||
                        (hdr.gotthard.op_cnt > 5 && hdr.gotthard_op[5].op_type == GOTTHARD_OP_VALUE && cached5 == 0 && opti_cached5 == 0) ||
                        (hdr.gotthard.op_cnt > 6 && hdr.gotthard_op[6].op_type == GOTTHARD_OP_VALUE && cached6 == 0 && opti_cached6 == 0) ||
                        (hdr.gotthard.op_cnt > 7 && hdr.gotthard_op[7].op_type == GOTTHARD_OP_VALUE && cached7 == 0 && opti_cached7 == 0) ||
                        (hdr.gotthard.op_cnt > 8 && hdr.gotthard_op[8].op_type == GOTTHARD_OP_VALUE && cached8 == 0 && opti_cached8 == 0) ||
                        (hdr.gotthard.op_cnt > 9 && hdr.gotthard_op[9].op_type == GOTTHARD_OP_VALUE && cached9 == 0 && opti_cached9 == 0)
                       ) {
                       t_cache_miss.apply();
                    }

                    if (meta.req_meta.has_cache_miss == 0) {
                        if (hdr.gotthard.op_cnt > 0) {
                            bit<GOTTHARD_VALUE_BITS> val0;
                            if (hdr.gotthard_op[0].op_type == GOTTHARD_OP_VALUE && opti_cached0 == 1) {
                                opti_value_register.read(val0, hdr.gotthard_op[0].key);
                                if (val0 != hdr.gotthard_op[0].value) {
                                    t_bad_opti_compare0.apply();
                                }
                            }
                            else if (hdr.gotthard_op[0].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val0, hdr.gotthard_op[0].key);
                                if (val0 != hdr.gotthard_op[0].value) {
                                    t_bad_compare0.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 1) {
                            bit<GOTTHARD_VALUE_BITS> val1;
                            if (hdr.gotthard_op[1].op_type == GOTTHARD_OP_VALUE && opti_cached1 == 1) {
                                opti_value_register.read(val1, hdr.gotthard_op[1].key);
                                if (val1 != hdr.gotthard_op[1].value) {
                                    t_bad_opti_compare1.apply();
                                }
                            }
                            else if (hdr.gotthard_op[1].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val1, hdr.gotthard_op[1].key);
                                if (val1 != hdr.gotthard_op[1].value) {
                                    t_bad_compare1.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 2) {
                            bit<GOTTHARD_VALUE_BITS> val2;
                            if (hdr.gotthard_op[2].op_type == GOTTHARD_OP_VALUE && opti_cached2 == 1) {
                                opti_value_register.read(val2, hdr.gotthard_op[2].key);
                                if (val2 != hdr.gotthard_op[2].value) {
                                    t_bad_opti_compare2.apply();
                                }
                            }
                            else if (hdr.gotthard_op[2].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val2, hdr.gotthard_op[2].key);
                                if (val2 != hdr.gotthard_op[2].value) {
                                    t_bad_compare2.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 3) {
                            bit<GOTTHARD_VALUE_BITS> val3;
                            if (hdr.gotthard_op[3].op_type == GOTTHARD_OP_VALUE && opti_cached3 == 1) {
                                opti_value_register.read(val3, hdr.gotthard_op[3].key);
                                if (val3 != hdr.gotthard_op[3].value) {
                                    t_bad_opti_compare3.apply();
                                }
                            }
                            else if (hdr.gotthard_op[3].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val3, hdr.gotthard_op[3].key);
                                if (val3 != hdr.gotthard_op[3].value) {
                                    t_bad_compare3.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 4) {
                            bit<GOTTHARD_VALUE_BITS> val4;
                            if (hdr.gotthard_op[4].op_type == GOTTHARD_OP_VALUE && opti_cached4 == 1) {
                                opti_value_register.read(val4, hdr.gotthard_op[4].key);
                                if (val4 != hdr.gotthard_op[4].value) {
                                    t_bad_opti_compare4.apply();
                                }
                            }
                            else if (hdr.gotthard_op[4].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val4, hdr.gotthard_op[4].key);
                                if (val4 != hdr.gotthard_op[4].value) {
                                    t_bad_compare4.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 5) {
                            bit<GOTTHARD_VALUE_BITS> val5;
                            if (hdr.gotthard_op[5].op_type == GOTTHARD_OP_VALUE && opti_cached5 == 1) {
                                opti_value_register.read(val5, hdr.gotthard_op[5].key);
                                if (val5 != hdr.gotthard_op[5].value) {
                                    t_bad_opti_compare5.apply();
                                }
                            }
                            else if (hdr.gotthard_op[5].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val5, hdr.gotthard_op[5].key);
                                if (val5 != hdr.gotthard_op[5].value) {
                                    t_bad_compare5.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 6) {
                            bit<GOTTHARD_VALUE_BITS> val6;
                            if (hdr.gotthard_op[6].op_type == GOTTHARD_OP_VALUE && opti_cached6 == 1) {
                                opti_value_register.read(val6, hdr.gotthard_op[6].key);
                                if (val6 != hdr.gotthard_op[6].value) {
                                    t_bad_opti_compare6.apply();
                                }
                            }
                            else if (hdr.gotthard_op[6].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val6, hdr.gotthard_op[6].key);
                                if (val6 != hdr.gotthard_op[6].value) {
                                    t_bad_compare6.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 7) {
                            bit<GOTTHARD_VALUE_BITS> val7;
                            if (hdr.gotthard_op[7].op_type == GOTTHARD_OP_VALUE && opti_cached7 == 1) {
                                opti_value_register.read(val7, hdr.gotthard_op[7].key);
                                if (val7 != hdr.gotthard_op[7].value) {
                                    t_bad_opti_compare7.apply();
                                }
                            }
                            else if (hdr.gotthard_op[7].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val7, hdr.gotthard_op[7].key);
                                if (val7 != hdr.gotthard_op[7].value) {
                                    t_bad_compare7.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 8) {
                            bit<GOTTHARD_VALUE_BITS> val8;
                            if (hdr.gotthard_op[8].op_type == GOTTHARD_OP_VALUE && opti_cached8 == 1) {
                                opti_value_register.read(val8, hdr.gotthard_op[8].key);
                                if (val8 != hdr.gotthard_op[8].value) {
                                    t_bad_opti_compare8.apply();
                                }
                            }
                            else if (hdr.gotthard_op[8].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val8, hdr.gotthard_op[8].key);
                                if (val8 != hdr.gotthard_op[8].value) {
                                    t_bad_compare8.apply();
                                }
                            }
                        }
                        if (hdr.gotthard.op_cnt > 9) {
                            bit<GOTTHARD_VALUE_BITS> val9;
                            if (hdr.gotthard_op[9].op_type == GOTTHARD_OP_VALUE && opti_cached9 == 1) {
                                opti_value_register.read(val9, hdr.gotthard_op[9].key);
                                if (val9 != hdr.gotthard_op[9].value) {
                                    t_bad_opti_compare9.apply();
                                }
                            }
                            else if (hdr.gotthard_op[9].op_type == GOTTHARD_OP_VALUE) {
                                value_register.read(val9, hdr.gotthard_op[9].key);
                                if (val9 != hdr.gotthard_op[9].value) {
                                    t_bad_compare9.apply();
                                }
                            }
                        }
                    }

                    if (meta.req_meta.has_bad_compare == 0 && meta.req_meta.has_bad_opti_compare == 0) {
                        if (hdr.gotthard.op_cnt > 0 && hdr.gotthard_op[0].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write0.apply();
                        }
                        if (hdr.gotthard.op_cnt > 1 && hdr.gotthard_op[1].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write1.apply();
                        }
                        if (hdr.gotthard.op_cnt > 2 && hdr.gotthard_op[2].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write2.apply();
                        }
                        if (hdr.gotthard.op_cnt > 3 && hdr.gotthard_op[3].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write3.apply();
                        }
                        if (hdr.gotthard.op_cnt > 4 && hdr.gotthard_op[4].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write4.apply();
                        }
                        if (hdr.gotthard.op_cnt > 5 && hdr.gotthard_op[5].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write5.apply();
                        }
                        if (hdr.gotthard.op_cnt > 6 && hdr.gotthard_op[6].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write6.apply();
                        }
                        if (hdr.gotthard.op_cnt > 7 && hdr.gotthard_op[7].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write7.apply();
                        }
                        if (hdr.gotthard.op_cnt > 8 && hdr.gotthard_op[8].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write8.apply();
                        }
                        if (hdr.gotthard.op_cnt > 9 && hdr.gotthard_op[9].op_type == GOTTHARD_OP_WRITE) {
                            t_handle_write9.apply();
                        }
                    }

                    if ((meta.req_meta.has_bad_compare == 1 || meta.req_meta.has_bad_opti_compare == 1) || !(
                         // no reads or writes:
                         (hdr.gotthard.op_cnt > 0 && (hdr.gotthard_op[0].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[0].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 1 && (hdr.gotthard_op[1].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[1].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 2 && (hdr.gotthard_op[2].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[2].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 3 && (hdr.gotthard_op[3].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[3].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 4 && (hdr.gotthard_op[4].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[4].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 5 && (hdr.gotthard_op[5].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[5].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 6 && (hdr.gotthard_op[6].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[6].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 7 && (hdr.gotthard_op[7].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[7].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 8 && (hdr.gotthard_op[8].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[8].op_type == GOTTHARD_OP_WRITE)) ||
                         (hdr.gotthard.op_cnt > 9 && (hdr.gotthard_op[9].op_type == GOTTHARD_OP_READ || hdr.gotthard_op[9].op_type == GOTTHARD_OP_WRITE))
                        )) {
                        if (hdr.gotthard.op_cnt > 0 && hdr.gotthard_op[0].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op0.apply();
                        }
                        if (hdr.gotthard.op_cnt > 1 && hdr.gotthard_op[1].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op1.apply();
                        }
                        if (hdr.gotthard.op_cnt > 2 && hdr.gotthard_op[2].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op2.apply();
                        }
                        if (hdr.gotthard.op_cnt > 3 && hdr.gotthard_op[3].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op3.apply();
                        }
                        if (hdr.gotthard.op_cnt > 4 && hdr.gotthard_op[4].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op4.apply();
                        }
                        if (hdr.gotthard.op_cnt > 5 && hdr.gotthard_op[5].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op5.apply();
                        }
                        if (hdr.gotthard.op_cnt > 6 && hdr.gotthard_op[6].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op6.apply();
                        }
                        if (hdr.gotthard.op_cnt > 7 && hdr.gotthard_op[7].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op7.apply();
                        }
                        if (hdr.gotthard.op_cnt > 8 && hdr.gotthard_op[8].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op8.apply();
                        }
                        if (hdr.gotthard.op_cnt > 9 && hdr.gotthard_op[9].op_type != GOTTHARD_OP_VALUE) {
                            t_delete_op9.apply();
                        }
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
