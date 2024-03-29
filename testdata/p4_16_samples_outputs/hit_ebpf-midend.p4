#include <core.p4>
#include <ebpf_model.p4>

@ethernetaddress typedef bit<48> EthernetAddress;
@ipv4address typedef bit<32> IPv4Address;
header Ethernet_h {
    EthernetAddress dstAddr;
    EthernetAddress srcAddr;
    bit<16>         etherType;
}

header IPv4_h {
    bit<4>      version;
    bit<4>      ihl;
    bit<8>      diffserv;
    bit<16>     totalLen;
    bit<16>     identification;
    bit<3>      flags;
    bit<13>     fragOffset;
    bit<8>      ttl;
    bit<8>      protocol;
    bit<16>     hdrChecksum;
    IPv4Address srcAddr;
    IPv4Address dstAddr;
}

struct Headers_t {
    Ethernet_h ethernet;
    IPv4_h     ipv4;
}

parser prs(packet_in p, out Headers_t headers) {
    state start {
        p.extract<Ethernet_h>(headers.ethernet);
        transition select(headers.ethernet.etherType) {
            16w0x800: ip;
            default: reject;
        }
    }
    state ip {
        p.extract<IPv4_h>(headers.ipv4);
        transition accept;
    }
}

control pipe(inout Headers_t headers, out bool pass) {
    bool hasReturned;
    @noWarnUnused @name(".NoAction") action NoAction_0() {
    }
    @name("pipe.Reject") action Reject(IPv4Address add) {
        pass = false;
        headers.ipv4.srcAddr = add;
    }
    @name("pipe.Check_src_ip") table Check_src_ip_0 {
        key = {
            headers.ipv4.srcAddr: exact @name("headers.ipv4.srcAddr") ;
        }
        actions = {
            Reject();
            NoAction_0();
        }
        implementation = hash_table(32w1024);
        const default_action = NoAction_0();
    }
    @hidden action hit_ebpf63() {
        pass = false;
        hasReturned = true;
    }
    @hidden action hit_ebpf60() {
        hasReturned = false;
        pass = true;
    }
    @hidden table tbl_hit_ebpf60 {
        actions = {
            hit_ebpf60();
        }
        const default_action = hit_ebpf60();
    }
    @hidden table tbl_hit_ebpf63 {
        actions = {
            hit_ebpf63();
        }
        const default_action = hit_ebpf63();
    }
    apply {
        tbl_hit_ebpf60.apply();
        if (!headers.ipv4.isValid()) {
            tbl_hit_ebpf63.apply();
        }
        if (!hasReturned) {
            if (Check_src_ip_0.apply().hit) {
                ;
            }
        }
    }
}

ebpfFilter<Headers_t>(prs(), pipe()) main;

