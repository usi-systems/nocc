
#define IP_PROTOCOLS_TCP 6
#define IP_PROTOCOLS_UDP 17

#define ETHERTYPE_IPV4 0x0800
#define GOTTHARD_PORT 9998
#define GOTTHARD_MAX_OP 10
#define IPTYPE_UDP 0x11

parser start {
    return parse_ethernet;
}

header ethernet_t ethernet;

parser parse_ethernet {
    extract(ethernet);
    return select(latest.etherType) {
        0x800 : parse_ipv4;
        default: ingress;
    }
}

header ipv4_t ipv4;

field_list ipv4_field_list {
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

field_list_calculation ipv4_chksum_calc {
    input {
        ipv4_field_list;
    }
    algorithm : csum16;
    output_width: 16;
}

calculated_field ipv4.hdrChecksum {
    update ipv4_chksum_calc;
}

parser parse_ipv4 {
    extract(ipv4);
    return select(latest.fragOffset, latest.protocol) {
        IP_PROTOCOLS_UDP : parse_udp;
        default: ingress;
    }
}

header udp_t udp;

parser parse_udp {
    extract(udp);
    return select(latest.dstPort) {	
        GOTTHARD_PORT : parse_gotthard;
        default : ingress;
    }
}

header gotthard_hdr_t gotthard_hdr;
header gotthard_op_t gotthard_op[GOTTHARD_MAX_OP];

header op_parse_meta_t parse_meta;

parser parse_op {
    extract(gotthard_op[next]);
     set_metadata(ig_prsr_ctrl.parser_counter, ig_prsr_ctrl.parser_counter -1);
    return select(ig_prsr_ctrl.parser_counter) {
        0: ingress;
        default: parse_op;
    }
}

parser parse_gotthard {
    extract(gotthard_hdr);
    set_metadata(ig_prsr_ctrl.parser_counter, gotthard_hdr.op_cnt);
    return select(ig_prsr_ctrl.parser_counter) {
        0: ingress;
        default: parse_op;
    }
}
