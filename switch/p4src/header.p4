#ifndef __HEADER_H__
#define __HEADER_H__ 1

struct ingress_metadata_t {
    bit<32> nhop_ipv4;
}

struct intrinsic_metadata_t {
    bit<48> ingress_global_timestamp;
    bit<32> lf_field_list;
    bit<16> mcast_grp;
    bit<16> egress_rid;
}

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

#define IPV4_HDR_LEN 20
header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

#define UDP_HDR_LEN 8
header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length_;
    bit<16> checksum;
}

#define GOTTHARD_HDR_LEN 13
header gotthard_t {
    bit<1> msg_type;
    bit<1> from_switch;
    bit<6> unused_flags;
    bit<32> cl_id;
    bit<32> req_id;
    bit<8> frag_seq;
    bit<8> frag_cnt;
    bit<8> status;
    bit<8> op_cnt;
}

header gotthard_op_t {
    bit<8> op_type;
    bit<32> key;
    bit<GOTTHARD_VALUE_BITS> value;
}


header parse_metadata_t {
    bit<8> remaining_cnt;
}

header req_meta_t {
    bit<1> has_cache_miss;
    bit<1> has_bad_compare;
    bit<1> has_bad_opti_compare;

    // tmp variables for doing swaps:
    bit<32> tmp_ipv4_dstAddr;
    bit<16> tmp_udp_dstPort;
}


struct metadata {
    @name("ingress_metadata")
    ingress_metadata_t   ingress_metadata;
    @name("intrinsic_metadata")
    intrinsic_metadata_t intrinsic_metadata;
    @name("parse_metadata")
    parse_metadata_t   parse_metadata;
    @name("req_meta")
    req_meta_t req_meta;
}

struct headers {
    @name("ethernet")
    ethernet_t ethernet;
    @name("ipv4")
    ipv4_t     ipv4;
    @name("udp")
    udp_t     udp;
    @name("gotthard")
    gotthard_t gotthard;
    @name("gotthard_op")
    gotthard_op_t[GOTTHARD_MAX_OP] gotthard_op;
}

#endif // __HEADER_H__
