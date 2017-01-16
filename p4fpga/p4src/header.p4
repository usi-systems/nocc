
#define IPV4_HDR_LEN 20
#define UDP_HDR_LEN 8
#define GOTTHARD_HDR_LEN 13


header_type ethernet_t {
    fields {
        dstAddr : 48;
        srcAddr : 48;
        etherType : 16;
    }
}

header_type vlan_tag_t {
    fields {
        pri     : 3;
        cfi     : 1;
        vlan_id : 12;
        etherType : 16;
    }
}

header_type ipv4_t {
    fields {
        version : 4;
        ihl : 4;
        diffserv : 8;
        totalLen : 16;
        identification : 16;
        flags : 3;
        fragOffset : 13;
        ttl : 8;
        protocol : 8;
        hdrChecksum : 16;
        srcAddr : 32;
        dstAddr: 32;
    }
}

header_type tcp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        seqNo : 32;
        ackNo : 32;
        dataOffset : 4;
        res : 3;
        ecn : 3;
        ctrl : 6;
        window : 16;
        checksum : 16;
        urgentPtr : 16;
    }
}

header_type udp_t {
    fields {
        srcPort : 16;
        dstPort : 16;
        hdr_length : 16;
        checksum : 16;
    }
}

header_type gotthard_hdr_t {
    fields {
        msg_type : 1;
        from_switch : 1;
        unused_flags : 6;
        cl_id : 32;
        req_id : 32;
        frag_seq : 8;
        frag_cnt : 8;
        status : 8;
        op_cnt : 8;
    }
}

header_type gotthard_op_t {
    fields {
        op_type : 8;
        key : 32;
        value : 32;
    }
}


header_type op_parse_meta_t {
    fields {
       remaining_cnt : 8;
    }
}


header_type req_meta_t {
    fields {
        r_cnt : 8;
        w_cnt : 8;
        rb_cnt : 8;
        has_cache_miss : 1;
        has_invalid_read : 1;
        has_opti_invalid_read : 1;

        read_cache_mode : 1;

        // tmp variables for doing swaps:
        tmp_ipv4_dstAddr : 32;
        tmp_udp_dstPort : 16;
	tmp_mac_addr : 48;
    }
}

header_type intrinsic_metadata_t {
    fields {
        mcast_grp : 4;
        egress_rid : 4;
        mcast_hash : 16;
        lf_field_list : 32;
        resubmit_flag : 16;
    }
}
