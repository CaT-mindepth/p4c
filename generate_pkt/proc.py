from scapy.all import *
import sys, os
import socket, struct
import random
import argparse

#TODO: get the path of NetFPGA-SUME-live
scripts_path = "/home/xiangyug/NetFPGA-SUME-live/tools/scripts"
nftest_path = "/home/xiangyug/NetFPGA-SUME-live/tools/scripts/NFTest/"
sys.path.append(scripts_path)
sys.path.append(nftest_path)

from axitools import *

dirname = os.getcwd()
common_func_path = os.path.join(dirname, 'common_func')
sys.path.append(common_func_path)
import common_func.func as func


##
parser = argparse.ArgumentParser(description='convert from pcap to axi file or vince visa')
parser.add_argument('--direction', type=str, default='conf_to_ctrl_pkt', 
                        choices=['conf_to_ctrl_pkt','gen_data_pkt', 'pkt_to_conf'])
parser.add_argument('--inputconf', type=str)
parser.add_argument('--outputpkt', type=str, required=True)
args = parser.parse_args()

DATA_WIDTH=256

def main():
    if (args.direction == 'conf_to_ctrl_pkt'):
        if args.inputconf == None:
            print("Error: missing --inputconf")
            sys.exit(1)
        pkts = func.parse_configuration(args.inputconf)

        # pkt.tuser_dport = 4
        # wrpcap("input.pcap", pkts)
        f = open(args.outputpkt, "w")

        axis_dump(pkts, f, DATA_WIDTH, 1e-9)

    elif (args.direction == 'gen_data_pkt'):
        pkts = []
        # pkt = func.gen_data_pkt("000d000000020000000400000000"+1440*"00", 1)
        # pkts.append(pkt)
        pkt = func.gen_data_pkt("001a000000040000000200000000"+4*"00", 1)
        pkts.append(pkt)
        pkt = func.gen_data_pkt("000d0000000200000000"+8*"00", 1)
        pkts.append(pkt)
        pkt = func.gen_data_pkt("001a00000002ffffffff"+8*"00", 1)
        pkts.append(pkt)

        # test for src routing
        # pkt = func.gen_data_pkt("0018" + 16*"00", 2, '0.0.0.5')
        # pkts.append(pkt)

        # test for netcache
        # pkt = func.gen_data_pkt("000d00000000aaaaaaaa"+8*"00", 2)
        # pkts.append(pkt)

        # test for NetChain
        # pkt = func.gen_data_pkt("03ff00000000aaaaaaaa"+8*"00", 2)
        # pkts.append(pkt)


        f = open(args.outputpkt, "w")

        axis_dump(pkts, f, DATA_WIDTH, 1e-9)
    else :
        filename = "/tmp/record1.axi"
        f = open(filename, "r")
        # f = open("./test0.axi", "r")
        # pkts = axis_load(f, 10000*1e-9)
        pkts = axis_load(f, 1e-9)
        # print pkts

        wrpcap("output.pcap", pkts)

if __name__ == "__main__":
    main()











# def convert_bstr_to_hstr(bstr):
#     hstr = '%0*X' % ((len(bstr) + 3) // 4, int(bstr, 2))
#     return hstr
# 
# def gen_data_pkt(data, vid):
#     pkt = Ether(src='00:01:02:03:04:05', dst='06:07:08:09:0a:0b')/Dot1Q(vlan=vid) \
#                 /IP(src='111.111.111.111', dst='222.222.222.222')/UDP(sport=1234, dport=4321) \
#                 /Raw(load=bytes.fromhex(data))
#     return pkt
# 
# def gen_ctrl_pkt(module_info, data):
#     raw_load = bytes.fromhex(module_info)
#     raw_load = raw_load + b'\x00'*15
#     raw_load = raw_load + bytes.fromhex(data)
#     pkt = Ether(src='00:01:02:03:04:05', dst='06:07:08:09:0a:0b')/Dot1Q(vlan=0xf) \
#                 /IP(src='111.111.111.111', dst='222.222.222.222')/UDP(sport=1234, dport=0xf1f2) \
#                 /Raw(load=raw_load)
#     return pkt
# 
# def parse_configuration(filename):
#     pkts = []
#     f = open(filename, "r")
#     line = f.readline()
#     while line:
#         strs = line.strip().split(" ")
#         print ("process", strs[0])
#         if (strs[0] == "Parser"):
#             data = f.readline().strip()
#             pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[1]), convert_bstr_to_hstr(data))
#             pkts.append(pkt)
#             pkt.tuser_sport = 1
#             pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[2]), convert_bstr_to_hstr(data))
#             pkts.append(pkt)
#             pkt.tuser_sport = 1
#         else:
#             data = f.readline().strip()
#             pkt = gen_ctrl_pkt(convert_bstr_to_hstr(strs[1]), convert_bstr_to_hstr(data))
#             pkt.tuser_sport = 1
#             pkts.append(pkt)
#         line = f.readline()
# 
#     return pkts
