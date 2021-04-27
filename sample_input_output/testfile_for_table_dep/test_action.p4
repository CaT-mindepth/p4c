#include <core.p4>
#include <v1model.p4>

const bit<32> N = 30;

header hop_metadata_t {
        bit<12> vrf;
        bit<64> ipv6_prefix;
        bit<16> next_hop_index;
        bit<16> mcast_grp;
        bit<4> urpf_fail;
        bit<8> drop_reason;
}

header ethernet_t {
        bit<48> dstAddr;
        bit<48> srcAddr;
}

header vlan_tag_t {
        bit<8> vid;
}

struct headers {
    vlan_tag_t[2]                           vlan_tag_;
    ethernet_t                              ethernet; 
}

struct metadata {
    hop_metadata_t        hop_metadata;
    bit<32>               sample;
}

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        transition accept;
    }
    
}

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {
    }
}

control ingress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action A1(bit<9> e_port) {
        standard_metadata.egress_spec = e_port;
    }

    table smac_vlan {
        key = {
            hdr.ethernet.srcAddr : exact;
            standard_metadata.ingress_port : exact;
        }
        actions = {
            A1;
        }
        size = 160000;
    }
    
    action set_egress_port(bit<9> e_port) {
        standard_metadata.egress_spec = e_port;
    }

    table dmac_vlan {
        key = {
            hdr.ethernet.dstAddr : exact;
            hdr.vlan_tag_[0].vid : exact;
            standard_metadata.ingress_port : exact;
        }
        actions = {
            set_egress_port;
        }
        size = 160000;
    }

    apply {
        smac_vlan.apply();
        dmac_vlan.apply();
    }
}

control egress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {
    }
}

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {  }
}

control MyDeparser(packet_out packet, in headers hdr) {
    apply { }
}

V1Switch(
MyParser(),
MyVerifyChecksum(),
ingress(),
egress(),
MyComputeChecksum(),
MyDeparser()
) main;
