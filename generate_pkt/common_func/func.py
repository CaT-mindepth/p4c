from scapy.all import *

def convert_bstr_to_hstr(bstr):
    hstr = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))
    return hstr

def gen_data_pkt(data, vid, ip_dst_addr='0.0.0.9', udp_src_port=19):
    pkt = Ether(src='3c:fd:fe:bd:01:a4', dst='00:00:00:00:00:05')/Dot1Q(vlan=vid) \
                /IP(src='111.111.111.111', dst=ip_dst_addr)/UDP(sport=udp_src_port, dport=19) \
                /Raw(load=bytes.fromhex(data))
    return pkt

def gen_ctrl_pkt(module_info, data):
    raw_load = bytes.fromhex(module_info)
    raw_load = raw_load + b'\x00'*15
    raw_load = raw_load + bytes.fromhex(data)
    pkt = Ether(src='00:01:02:03:04:05', dst='06:07:08:09:0a:0b')/Dot1Q(vlan=0xf) \
                /IP(src='111.111.111.111', dst='222.222.222.222')/UDP(sport=1234, dport=0xf1f2) \
                /Raw(load=raw_load)
    return pkt

def parse_configuration(filename):
    pkts = []
    f = open(filename, "r")
    line = f.readline()
    while line:
        strs = line.strip().split(" ")
        print ("process", strs[0])
        if (strs[0] == "Parser"):
            data = f.readline().strip()
            pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[1]), convert_bstr_to_hstr(data))
            pkts.append(pkt)
            pkt.tuser_sport = 1
            pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[2]), convert_bstr_to_hstr(data))
            pkts.append(pkt)
            pkt.tuser_sport = 1
        else:
            data = f.readline().strip()
            pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[1]), convert_bstr_to_hstr(data))
            pkt.tuser_sport = 1
            pkts.append(pkt)
        line = f.readline()

    return pkts
