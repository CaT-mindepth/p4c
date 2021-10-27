import sys

def main(argv):
    if len(argv) != 3:
        print("Usage python3 " + argv[0] + " <contrl plane packet file (e.g., /tmp/ctrl_pkt.txt)> <data plane packet file (e.g., /tmp/data_pkt.txt)>")
        sys.exit(1)
    control_plane_pkt = argv[1]
    data_plane_pkt = argv[2]
    f = open(control_plane_pkt, "r")
    output_str = "# vid 1\n"
    lines = f.readlines()
    # deal with control packet
    for l in lines:
        if len(l) > 0 and l[0] == '@':
            output_str += '@ 3000\n'
        elif len(l) > 0 and l[0] == '+':
            output_str += '+ 100\n'
        else:
            output_str += l
    f.close()

    output_str += "# pkts\n"
    # deal with data packet
    f = open(data_plane_pkt, "r")
    lines = f.readlines()
    for l in lines:
        if len(l) > 0 and (l[0] == '@' or l[0] == '+'):
            output_str += '+ 100\n'
        else:
            output_str += l
    f.close()
    print(output_str)
if __name__ == '__main__':
    main(sys.argv)
