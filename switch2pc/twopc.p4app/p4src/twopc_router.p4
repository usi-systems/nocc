#include <core.p4>
#include <v1model.p4>

#include "config.p4"
#include "header.p4"
#include "parser.p4"

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    action rewrite_mac(bit<48> smac) {
        hdr.ethernet.srcAddr = smac;
    }
    action _drop() {
        mark_to_drop();
    }
    table send_frame() {
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
        if (hdr.ipv4.isValid()) {
          send_frame.apply();
        }
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    register<bit<8>>(MAX_TXN_REGISTERS) participant_cnt_register;
    register<bit<8>>(MAX_TXN_REGISTERS) prepare_cnt_register;
    register<bit<8>>(MAX_TXN_REGISTERS) commit_cnt_register;
    register<bit<48>>(MAX_TXN_REGISTERS) start_ts_register;
    register<bit<1>>(MAX_TXN_REGISTERS) abort_sent_register;
    action _drop() {
        mark_to_drop();
    }
    action set_nhop(bit<32> nhop_ipv4, bit<9> port) {
        meta.ingress_metadata.nhop_ipv4 = nhop_ipv4;
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl + 8w255;
    }
    action broadcast() {
        meta.intrinsic_metadata.mcast_grp = 1;
        meta.ingress_metadata.nhop_ipv4 = hdr.ipv4.dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl + 8w255;
    }
    action set_dmac(bit<48> dmac) {
        hdr.ethernet.dstAddr = dmac;
    }
    action do_early_commit(bit<8> status) {
        hdr.twopc.msg_type = MSG_TYPE_COMMIT;
        hdr.twopc.status = status;
        hdr.twopc.from_switch = 1;
        hdr.ipv4.srcAddr = hdr.ipv4.dstAddr;
        hdr.ipv4.dstAddr = 0xffffffff;
        hdr.udp.srcPort = COORDINATOR_PORT;
        hdr.udp.dstPort = PARTICIPANT_PORT;
        hdr.udp.checksum = (bit<16>)0;
    }
    table ipv4_lpm() {
        actions = {
            _drop;
            set_nhop;
            broadcast;
            NoAction;
        }
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        size = 1024;
        default_action = NoAction();
    }
    table forward() {
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
    table early_commit() {
        actions = {
            do_early_commit;
            NoAction;
        }
        key = {
            hdr.twopc.status: exact;
        }
        size = 2;
        default_action = NoAction();
    }

    apply {
        if (hdr.ipv4.isValid()) {

          if (hdr.twopc.isValid()) {
            if (hdr.twopc.msg_type == MSG_TYPE_PREPARE) {
              bit<32> txn_idx = hdr.twopc.txn_id % 65536;
              bit<48> start_ts;
              start_ts_register.read(start_ts, txn_idx);

              if (start_ts == 0 ||
                  start_ts + INST_EXPIRE_US < meta.intrinsic_metadata.ingress_global_timestamp) {
                participant_cnt_register.write(txn_idx, hdr.twopc.participant_cnt);
                commit_cnt_register.write(txn_idx, 0);
                start_ts_register.write(txn_idx, meta.intrinsic_metadata.ingress_global_timestamp);
              }
            }
            else if (hdr.twopc.msg_type == MSG_TYPE_VOTE) {
              bit<32> txn_idx = hdr.twopc.txn_id % 65536;

              if (hdr.twopc.status == STATUS_OK) {
                bit<8> participant_cnt;
                bit<8> commit_cnt;
                commit_cnt_register.read(commit_cnt, txn_idx);
                participant_cnt_register.read(participant_cnt, txn_idx);

                commit_cnt = commit_cnt + 1;
                commit_cnt_register.write(txn_idx, commit_cnt);

                if (commit_cnt == participant_cnt) {
                  early_commit.apply();
                }
              }
              else if (hdr.twopc.status == STATUS_ABORT) {
                bit<1> abort_sent;
                abort_sent_register.read(abort_sent, txn_idx);
                if (abort_sent == 0) { // abort wasn't already sent
                    abort_sent_register.write(txn_idx, 1);
                    early_commit.apply();
                }
              }
            }
          }

          ipv4_lpm.apply();
          forward.apply();
        }
    }
}

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;
