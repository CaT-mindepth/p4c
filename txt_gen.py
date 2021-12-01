import sys


def main(argv):
    if len(argv) != 3:
        print("Usage: python3 " + argv[0] + " <allocation_info (e.g., /tmp/allocation_info.txt)> <program_info (e.g., /tmp/program_info.txt)>")
        sys.exit(1)
    # key: int type, val: corresponding type ID
    type_id = {
            "2B" : "01",
            "4B" : "10",
            "6B" : "11"
            }
    # key: int type, val: num of bytes
    bit_len_id = {
            "2B" : 2,
            "4B" : 4,
            "6B" : 6
            }
    # key: module name, val: module ID
    module_id = {
            "Parser": "000",
            "Deparser": "101",
            "KeyExtractConf": "001",
            "CAMMaskConf": "001",
            "CAMConf": "010",
            "RAMConf": "010"
            }
    allocation_info_filename = argv[1]
    f = open(allocation_info_filename, "r")
    # key: module name, val: stage they are allocated to (From file ILP collected)
    module_dic = {}
    # key: fields modified, val: operation, fulfill the ALU_list (From file codegen)
    ALU_dic = {}
    while 1:
        l = f.readline()
        if not l:
            break
        if l == "Module allocation:\n":
            idx = 0
        elif l == "ALU content:\n":
            idx = 1
        else:
            l = l[:-1]
            key = l.split(':')[0]
            # print("key = ", key)
            if idx == 0:
                # print("l.split(':')[1][0] = ",l.split(':')[1])
                module_dic[key] = int(l.split(':')[1])
            else:
                assert idx == 1
                ALU_dic[key] = []
                for e in l.split(':')[1].split(' '):
                    ALU_dic[key].append(e)
    f.close()
    # record all packet fields modified or matched (From file p4c)
    program_info_filename = argv[2]
    f = open(program_info_filename, "r")
    used_pkt = []
    action_field_dic = {} # key: action name, val: fields modified in this action
    match_keys = []
    while 1:
        l = f.readline()
        if not l:
            break
        elif l.find("Modified fields:") != -1:
            action_name = l.split(' ')[0]
            append_str = l.split(':')[1]
            while append_str[-1] == ' ' or append_str[-1] == '\n' or append_str[-1] == ';':
                append_str = append_str[:-1]
            if append_str not in used_pkt:
                used_pkt.append(append_str)
            action_field_dic[action_name] = append_str
        elif l.find("match key:") != -1:
            append_str = l.split(':')[1].split('.')[-1]
            # remove redundant ';', ' ' or '\n'
            while append_str[-1] == ' ' or append_str[-1] == '\n' or append_str[-1] == ';':
                append_str = append_str[:-1]
            if append_str not in match_keys:
                match_keys.append(append_str)
            if append_str not in used_pkt:
                used_pkt.append(append_str)
    print(action_field_dic)
    f.close()
    print("used_pkt =", used_pkt)
    # pkt_dic should read from file; key: name of a packet, val: how many bytes (From file collected)
    pkt_dic = {}
    f = open(program_info_filename, "r")
    while 1:
        l = f.readline()
        if not l or l == "--------------Output Table Info:\n":
            break
        elif l == "--------------Output packet field Info:\n":
            continue
        else:
            l = l[:-1]
            key = l.split(':')[0]
            if key in used_pkt:
                pkt_dic[key] = l.split(':')[1]
    f.close()
    # key: packet field name, val: match value (TODO: From file collected)
    #match_entry_val = {
    #        "pkt_2" : 13
    #        }
    match_entry_val = {}
    f = open(program_info_filename, "r")
    while 1:
        l = f.readline()
        if not l:
            break
        elif l.find("entry:") != -1:
            # Format: entry:{13};action_1();
            val = int(l.split('{')[1].split('}')[0])
            match_entry_val[curr_key] = val
        elif l.find("match key:") != -1:
            curr_key = l.split(':')[1]
            if curr_key.find('.') != -1:
                curr_key = curr_key.split('.')[-1]
            while curr_key[-1] == ' ' or curr_key[-1] == '\n' or curr_key[-1] == ';':
                curr_key = curr_key[:-1]
    f.close()
    # print(match_entry_val)
    l = ["Parser", "KeyExtractConf", "CAMMaskConf", "CAMConf", "RAMConf"]
    for e in l:
        if e == "Parser":
            stage = module_dic[e]
            binary_par = "{0:b}".format(stage)
            # Add leading zero
            binary_par = binary_par.zfill(5)
            
            stage = module_dic["Deparser"]
            binary_depar = "{0:b}".format(stage)
            binary_depar = binary_depar.zfill(5)

            to_print_str = "Parser " + binary_par + module_id["Parser"] + "0000000000000001 " +\
                    binary_depar + module_id["Deparser"] + "0000000000000001"
            print(to_print_str)
            # [000 + 7bit + 2bit + 3bit + 1bit] * 10
            key_pos_dic = {}
            key_list = list(pkt_dic.keys())
            content_str = "";
            curr_pos = 0
            container_index_id = {
                    "2B" : 1,
                    "4B" : 1,
                    "6B" : 1
                    }
            for i in range(10):
                if i >= len(pkt_dic):
                     content_str += "0000000000000000"
                else:
                     tmp_str = "000"
                     int_type = pkt_dic[key_list[i]] # "4B"
                     bit_len = bit_len_id[int_type]  # "4"
                     pos_in_pkt = "{0:b}".format(curr_pos)
                     pos_in_pkt = pos_in_pkt.zfill(7)
                     curr_pos += bit_len
                     tmp_str += pos_in_pkt
                     curr_type_id = type_id[int_type]
                     tmp_str += curr_type_id
                     container_index = container_index_id[int_type]
                     key_pos_dic[key_list[i]] = container_index
                     container_index_to_string = "{0:b}".format(container_index)
                     container_index_to_string = container_index_to_string.zfill(3)
                     container_index_id[int_type] += 1
                     tmp_str += container_index_to_string
                     tmp_str += "1"
                     content_str += tmp_str
            print(content_str)
        elif e == "KeyExtractConf":
            stage = module_dic[e]
            binary_par = "{0:b}".format(stage)
            # Add leading zero
            binary_par = binary_par.zfill(5)
            to_print_str = e + " " + binary_par + module_id[e] + "00000000" + "00000001"
            print(to_print_str)
            # 3 * 6 + 0011000000000000000000
            first_six = ["000", "000", "000", "000", "000", "000"]
            content_str = ""
            match_key_in_key_extract = {} #key: packet field, val:pos
            for e in match_keys:
                container_idx = key_pos_dic[e]
                if pkt_dic[e] == "6B":
                    if first_six[0] == "000":
                        first_six[0] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[0] = e
                    else:
                        assert first_six[1] == "000", "match too many fields"
                        first_six[1] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[1] = e
                elif pkt_dic[e] == "4B":
                    if first_six[2] == "000":
                        first_six[2] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[2] = e
                    else:
                        assert first_six[3] == "000", "match too many fields"
                        first_six[3] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[3] = e
                elif pkt_dic[e] == "2B":
                    if first_six[4] == "000":
                        first_six[4] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[4] = e
                    else:
                        assert first_six[5] == "000", "match too many fields"
                        first_six[15] = "{0:b}".format(container_idx).zfill(3)
                        match_key_in_key_extract[5] = e
            for i in range(len(first_six)):
                content_str += first_six[i]
            content_str += "0011000000000000000000"
            print(content_str)
        elif e == "CAMMaskConf":
            stage = module_dic[e]
            binary_par = "{0:b}".format(stage)
            # Add leading zero
            binary_par = binary_par.zfill(5)

            to_print_str = e + " " + binary_par + module_id[e] + "00001111" + "00000001"
            print(to_print_str)
            # 48 * 2 + 32 * 2 + 16 * 2 + 10000000 
            content_str = ""
            for i in range(len(first_six)):
                # 48-bit
                if i < 2:
                    if first_six[i] != "000":
                        content_str += "000000000000000000000000000000000000000000000000"
                    else:
                        content_str += "111111111111111111111111111111111111111111111111"
                # 32-bit
                elif i < 4:
                    if first_six[i] != "000":
                        content_str += "00000000000000000000000000000000"
                    else:
                        content_str += "11111111111111111111111111111111"
                # 16-bit
                else:
                    if first_six[i] != "000":
                        content_str += "0000000000000000"
                    else:
                        content_str += "1111111111111111"
            content_str += "10000000"
            print(content_str)
        elif e == "CAMConf":
            stage = module_dic[e]
            binary_par = "{0:b}".format(stage)
            # Add leading zero
            binary_par = binary_par.zfill(5)

            to_print_str = e + " " + binary_par + module_id[e] + "00000000" + "00000000"
            print(to_print_str)
            # 12bit + 48 * 2 + 32 * 2 + 16 * 2 + 0000
            vid_str = "000000000001" #TODO: right now we force vid to be one
            content_str = vid_str
            for i in range(len(first_six)):
                if i < 2:
                    if first_six[i] == "000":
                        content_str += "000000000000000000000000000000000000000000000000"
                    else:
                        val = match_entry_val[match_key_in_key_extract[i]]
                        content_str += "{0:b}".format(val).zfill(48)
                # 32-bit
                elif i < 4:
                    if first_six[i] == "000":
                        content_str += "00000000000000000000000000000000"
                    else:
                        val = match_entry_val[match_key_in_key_extract[i]]
                        content_str += "{0:b}".format(val).zfill(32)
                # 16-bit
                else:
                    if first_six[i] == "000":
                        content_str += "0000000000000000"
                    else:
                        val = match_entry_val[match_key_in_key_extract[i]]
                        content_str += "{0:b}".format(val).zfill(16)
            content_str += "0000"
            print(content_str)

        elif e == "RAMConf":
            stage = module_dic[e]
            binary_par = "{0:b}".format(stage)
            # Add leading zero
            binary_par = binary_par.zfill(5)
            # key: operation, val: corresponding ID
            op_to_code_dic = {
                    "set" : "1110"
                    }
            to_print_str = e + " " + binary_par + module_id[e] + "00001111" + "00000000"
            print(to_print_str)
            # 25bit * 25
            content_str = ""
            ALU_dic_key = list(ALU_dic.keys())
            Used_ALU_dic = {} # key: alu_num, val: field name
            for e in ALU_dic_key:
                byte_type = pkt_dic[e]
                if byte_type == "4B":
                    Used_ALU_dic[8 + 7 - key_pos_dic[e]] = e
                elif byte_type == "2B":
                    Used_ALU_dic[8*2 + 8 - key_pos_dic[e]] = e
                else:
                    assert byte_type == "6B"
                    Used_ALU_dic[8 - key_pos_dic[e]] = e

            for i in range(25):
                if i not in Used_ALU_dic:
                    content_str += "1111000000000000000000000"
                else:
                    pkt_field = Used_ALU_dic[i]
                    op = ALU_dic[pkt_field][0]
                    imme = int(ALU_dic[pkt_field][1])
                    content_str += op_to_code_dic[op]
                    if op == "set":
                        content_str += "00000"
                    content_str += "{0:b}".format(imme).zfill(16)
            content_str += "0000000"
            print(content_str)
                

if __name__ == '__main__':
    main(sys.argv)
