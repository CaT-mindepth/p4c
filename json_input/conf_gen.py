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

def parse_json(ILP_alloc):
    var_val_dict = {}
    for i in range(len(ILP_alloc['Vars'])):
        curr_var = ILP_alloc['Vars'][i]['VarName']
        curr_value = ILP_alloc['Vars'][i]['X']
        var_val_dict[curr_var] = curr_value
    return var_val_dict

def gen_table_stage_alloc(var_val_dict, table_match_part_dic, cost):
    used_table_dict = {}
    for i in range(cost):
        used_table_dict[i] = []    
    for i in range(cost):
        for table in table_match_part_dic:
            for size in range(table_match_part_dic[table]):
                var_name = "%s_M%s_stage%s" % (table, size, i)
                # print("var_name =" ,var_name)
                if var_name in var_val_dict:
                    assert var_val_dict[var_name] == 1
                    used_table_dict[i].append(table)
    return used_table_dict

def get_modified_pkt(table_name, action_name, alu, pkt_alu_dic):
    l_to_find = [table_name, action_name, alu]
    for pkt_field in pkt_alu_dic:
        if l_to_find in pkt_alu_dic[pkt_field]:
            return pkt_field
    return -1

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

    update_var_dic = {'T1_A1_ALU1' : 1,
                'T1_A1_ALU2' : 2,
                'T1_A1_ALU3' : 3,
                'T1_A1_ALU4' : 4,
                'T1_A1_ALU5' : 5,
                'T1_A1_ALU6' : 6}

    table_match_part_dic = {} # key: table name, val: how many match components
    for tbl in table_size_dic:
        table_match_part_dic[tbl] = math.ceil(table_size_dic[tbl] / float(entries_per_table))
    
    # turn ILP's allocation output to a dictionary (Only have non-zero value)
    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 6.4218044281005859e-03, "Work": 2.6063138945517767e-03, "ObjVal": 0, "ObjBound": 0, "ObjBoundC": 0, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 1, "PoolObjBound": 0, "PoolObjVal": [ 0]}, "Vars": [ { "VarName": "T1_M0_A1_ALU1_stage0", "X": 1}, { "VarName": "T1_M0_A1_ALU2_stage0", "X": 1}, { "VarName": "T1_M0_A1_ALU3_stage0", "X": 1}, { "VarName": "T1_M0_A1_ALU4_stage0", "X": 1}, { "VarName": "T1_M0_A1_ALU5_stage0", "X": 1}, { "VarName": "T1_M0_A1_ALU6_stage0", "X": 1}, { "VarName": "T1_M0_stage0", "X": 1}]}
    var_val_dict = parse_json(ILP_alloc)
    # print("var_val_dict =", var_val_dict)

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
    
    # get total number of stages from json output
    if 'cost' in var_val_dict:
        cost = var_val_dict['cost'] + 1 
    else:
        cost = 1
    used_stage = cost
    used_table_dict = {} # key: stage number; val: list of tables appear in that stage
    used_table_dict = gen_table_stage_alloc(var_val_dict, table_match_part_dic, cost)
    # print("used_table_dict =", used_table_dict)
    for i in range(used_stage):
        used_table = len(used_table_dict[i])
        for j in range(used_table):
            # For now, we think if more than one match component of a table is in the same stage,
            # then only one of them will be used to execute the match/action rule
            if j > 0 and used_table_dict[j] == used_table_dict[j - 1]:
                continue
            # KeyExtractConf
            # get Info required (e.g., stage number, match field idx, table number etc.)
            table_name = used_table_dict[i][j] # get it from ILP's output
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
            # match_action_rule = {'T1' : [({'pkt_0' : 5}, 'A1')]}
            action_name = match_action_rule[table_name][0][1]
            alu_l = action_alu_dic[table_name][action_name]
            # print("alu_l =", alu_l)
            
            
            ram_list = ["0000000000000000000000000000000000000000000000000000000000000000"] * 65
            for k in range(num_of_match_field):
                for alu in alu_l:
                    var_name = "%s_M%s_%s_%s" % (table_name, k, action_name, alu)
                    # find which stage all alus in alu_l are allocated
                    if var_name not in var_val_dict:
                        stage_of_this_alu = 0
                    else:
                        stage_of_this_alu = var_val_dict[var_name]
                    # if one particular alu is allocated in this stage, we should set the configuration
                    if stage_of_this_alu == i:
                        # find which packet field is modified by this alu
                        packet_field = get_modified_pkt(table_name, action_name, alu, pkt_alu_dic)
                        if packet_field == -1:
                            # TODO: consider the case where the ALU is used to modify tmp field/stateful vars
                            print("Not modify fields in definition")
                            sys.exit(0)
                        else:
                            alu_func_name = "%s_%s_%s" % (table_name, action_name, alu)
                            update_val = update_var_dic[alu_func_name]
                            tmp_str = "00001110" + int_to_bin_str(pkt_container_dic[packet_field], 6) +\
                                    int_to_bin_str(update_val, 50)
                            
                            ram_list[num_of_phv - 1 - pkt_container_dic[packet_field]] = tmp_str

            # Add to ram_conf_str
            for content in ram_list:
                ram_conf_str += content
            ram_conf_str += "\n"
            
            out_str += ram_conf_str
            

    if out_str[-1] == '\n':
        out_str = out_str[:-1]
    print(out_str)

if __name__ == '__main__':
    main(sys.argv)