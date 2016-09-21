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

header gotthard_hdr_t gotthard_hdr;
header gotthard_txn_t gotthard_txn[GOTTHARD_MAX_TXN];

header txn_meta_t parsed_meta;

parser parse_txn {
    extract(gotthard_txn[next]);
    set_metadata(parsed_meta.txn_cnt, parsed_meta.txn_cnt - 1);
    return select(parsed_meta.txn_cnt) {
        0: ingress;
        default: parse_txn;
    }
}

parser parse_gotthard {
    extract(gotthard_hdr);
    set_metadata(parsed_meta.txn_cnt, gotthard_hdr.txn_cnt);
    return select(gotthard_hdr.txn_cnt) {
        0: ingress;
        default: parse_txn;
    }
}
