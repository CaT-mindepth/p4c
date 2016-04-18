#include "/home/cdodd/p4c/build/../p4include/core.p4"
#include "/home/cdodd/p4c/build/../p4include/v1model.p4"

header hdr2_t {
    bit<8>  f1;
    bit<8>  f2;
    bit<16> f3;
}

struct metadata {
}

struct headers {
    @name("hdr2") 
    hdr2_t hdr2;
}

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name("start") state start {
        packet.extract(hdr.hdr2);
        transition accept;
    }
}

control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
        bool hasReturned_0 = false;
    }
}

control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    @name("a21") action a21() {
        bool hasReturned_2 = false;
        standard_metadata.egress_spec = 9w3;
    }
    @name("a22") action a22() {
        bool hasReturned_3 = false;
        standard_metadata.egress_spec = 9w4;
    }
    @name("t_ingress_2") table t_ingress_2() {
        actions = {
            a21;
            a22;
            NoAction;
        }
        key = {
            hdr.hdr2.f1: exact;
        }
        size = 64;
        default_action = NoAction();
    }

    apply {
        bool hasReturned_1 = false;
        t_ingress_2.apply();
    }
}

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        bool hasReturned_4 = false;
        packet.emit(hdr.hdr2);
    }
}

control verifyChecksum(in headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
        bool hasReturned_5 = false;
    }
}

control computeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        bool hasReturned_6 = false;
    }
}

V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;