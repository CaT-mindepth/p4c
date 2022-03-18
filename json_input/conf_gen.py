import sys

import math

module_id = {'Parser' : 0,
            'Deparser': 5,
            'KeyExtractConf': 1,
            'CAMMaskConf': 1,
            'CAMConf': 2,
            'RAMConf': 2}
num_of_phv = 64
num_of_stages = 12
num_of_tables_per_stage = 8
num_of_match_field = 8
entries_per_table = 256

def int_to_bin_str(v, length):
    return str(format(v, 'b').zfill(length))

def main(argv):
    # get useful info from ILP
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6']
    table_size_dic = {'T1':1} #key: table name, val: table size
    match_field_dic = {'T1' : ['pkt_0']} # key: table name, val: list of matched fields
    match_action_rule = {'T1' : [({'pkt_0' : 5}, 'A1')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6']}}
    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU1']], 
                'pkt_2':[['T1','A1','ALU2']],
                'pkt_3':[['T1','A1','ALU3']],
                'pkt_4':[['T1','A1','ALU4']],
                'pkt_5':[['T1','A1','ALU5']],
                'pkt_6':[['T1','A1','ALU6']]}
    stage_dic = {'T1_M0_A1_ALU1' : 0,
                'T1_M0_A1_ALU2' : 0,
                'T1_M0_A1_ALU3' : 0,
                'T1_M0_A1_ALU4' : 0,
                'T1_M0_A1_ALU5' : 0,
                'T1_M0_A1_ALU6' : 0} # key: variable name, val: stage number
    update_var_dic = {'T1_A1_ALU1' : 1,
                'T1_A1_ALU2' : 2,
                'T1_A1_ALU3' : 3,
                'T1_A1_ALU4' : 4,
                'T1_A1_ALU5' : 5,
                'T1_A1_ALU6' : 6}

    table_match_part_dic = {} # key: table name, val: how many match components
    for tbl in table_size_dic:
        table_size_dic[tbl] = math.ceil(table_size_dic[tbl] / float(entries_per_table))

    num_of_pkts_in_def = len(pkt_fields_def)
    pkt_container_dic = {} # key: pkt_field, val: container idx

    out_str = ""
    # Parse and Deparser (DONE)
    # Part I
    out_str += "Parser 00000" + int_to_bin_str(module_id['Parser'], 3) +\
    "0000000000000001 " + "00000" + int_to_bin_str(module_id['Deparser'], 3) +\
    "0000000000000001\n"
    # Part II
    tmp_str = ""
    curr_pos = 46 # start from 46
    idx_num = 0
    for i in range(num_of_phv):
        if i < num_of_pkts_in_def:
            tmp_str += "000000" # [23:18]
            tmp_str += int_to_bin_str(curr_pos, 9) # [17:9]
            curr_pos += 4
            tmp_str += "10" # all are 32-bit 4B [8:7]
            tmp_str += int_to_bin_str(idx_num, 6)   # [6:1]
            pkt_container_dic[pkt_fields_def[i]] = idx_num
            idx_num += 1
            tmp_str += "1"
            
        else:
            tmp_str += "000000000000000000000000"
    out_str += tmp_str + "\n"
    # print(out_str)
    cost = 1
    used_stage = cost
    used_table_dic = {0 : 1}
    for i in range(used_stage):
        used_table = used_table_dic[i]
        for j in range(used_table):
            # KeyExtractConf
            # get Info required (e.g., stage number, match field idx, table number etc.)
            table_name = 'T1' # TODO: get it from ILP's output
            key_extract_str = "KeyExtractConf " + int_to_bin_str(i, 5) + int_to_bin_str(module_id['KeyExtractConf'], 3) +\
                int_to_bin_str(j, 4) + "0000" + "00000001\n"
            match_fields_l = match_field_dic[table_name]
            for k in range(num_of_match_field):
                if k < len(match_fields_l):
                    field_name = match_fields_l[k]
                    key_extract_str += int_to_bin_str(pkt_container_dic[field_name], 6)
                else:
                    key_extract_str += "000000"
            key_extract_str += "11"
            key_extract_str += "000000000"
            key_extract_str += "000000000"
            key_extract_str += "0000\n"
            out_str += key_extract_str
            
            # CAMMaskConf
            cam_mask_conf_str = "CAMMaskConf " + int_to_bin_str(i, 5) + int_to_bin_str(module_id['CAMMaskConf'], 3) +\
                int_to_bin_str(j, 4) + "1111" + "00000001\n"
            for k in range(num_of_match_field):
                if k < len(match_fields_l):
                    cam_mask_conf_str += "00000000000000000000000000000000"
                else:
                    cam_mask_conf_str += "11111111111111111111111111111111"
            cam_mask_conf_str += "1"
            cam_mask_conf_str += "0000000\n"
            out_str += cam_mask_conf_str
            
            # CAMConf
            cam_conf_str = "CAMConf " + int_to_bin_str(i, 5) + int_to_bin_str(module_id['CAMConf'], 3) +\
                int_to_bin_str(j, 4) + "0000" + "00000000\n"
            cam_conf_str += "000000000001"
            for k in range(num_of_match_field):
                if k < len(match_fields_l):
                    field_name = match_fields_l[k]
                    # TODO: consider more than one match action rule
                    # match_action_rule = {'T1' : [({'pkt_0' : 5}, 'A1')]}
                    val = match_action_rule[table_name][0][0][field_name]
                    cam_conf_str += int_to_bin_str(val, 32)
                else:
                    cam_conf_str += int_to_bin_str(0, 32)

            cam_conf_str += "0"
            cam_conf_str += "000\n"
            out_str += cam_conf_str

            # RAMConf
            ram_conf_str = "RAMConf " + int_to_bin_str(i, 5) + int_to_bin_str(module_id['RAMConf'], 3) +\
                int_to_bin_str(j, 4) + "1111" + "00000000\n"
            action_name = match_action_rule[table_name][0][1]
            alu_l = action_alu_dic[table_name][action_name]
            for k in range(num_of_phv - 1, -1, -1):
                if k < len(pkt_fields_def):
                    packet_field = pkt_fields_def[k]
                    if packet_field not in pkt_alu_dic:
                        ram_conf_str += "0000000000000000000000000000000000000000000000000000000000000000"
                        continue
                    for mem in pkt_alu_dic[packet_field]:
                        for size in range(table_size_dic[table_name]):
                            alu_name = '%s_M%s_%s_%s' % (mem[0], size, mem[1], mem[2])
                            if stage_dic[alu_name] == i:
                                # TODO: expand to more functions in addition to set
                                alu_func_name = '%s_%s_%s' % (mem[0], mem[1], mem[2])
                                update_val = update_var_dic[alu_func_name]
                                ram_conf_str += "00001110" + int_to_bin_str(pkt_container_dic[packet_field], 6) +\
                                     int_to_bin_str(update_val, 50)
                            else:
                                ram_conf_str += "0000000000000000000000000000000000000000000000000000000000000000"
                else:
                    ram_conf_str += "0000000000000000000000000000000000000000000000000000000000000000"
            ram_conf_str += "0000000000000000000000000000000000000000000000000000000000000000\n"
            
            out_str += ram_conf_str
            

    if out_str[-1] == '\n':
        out_str = out_str[:-1]
    print(out_str)

if __name__ == '__main__':
    main(sys.argv)