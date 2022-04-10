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
                    if table not in used_table_dict[i]:
                        used_table_dict[i].append(table)
    return used_table_dict

def get_modified_pkt(table_name, action_name, alu, pkt_alu_dic):
    l_to_find = [table_name, action_name, alu]
    # print("l_to_find =",l_to_find)
    for pkt_field in pkt_alu_dic:
        if l_to_find in pkt_alu_dic[pkt_field]:
            return pkt_field
    return -1

def valid_ram_list(ram_list):
    for mem in ram_list:
        if mem != "0000000000000000000000000000000000000000000000000000000000000000":
            return True
    return False

def main(argv):
    '''
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
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16']
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0', 's1'] # all stateful variables

    table_size_dic = {'ingress_port_properties':288, 
                        'validate_outer_ipv4_packet':512,
                        'marple_tcp_nmo_table':1}
    match_field_dic = {'ingress_port_properties' : ['pkt_7'],
                        'validate_outer_ipv4_packet': ['pkt_12', 'pkt_15', 'pkt_16'],
                        'marple_tcp_nmo_table' : ['pkt_0']} # key: table name, val: list of matched fields
    match_action_rule = {'ingress_port_properties' : [({'pkt_7' : 5}, 'set_ingress_port_properties')],
                        'validate_outer_ipv4_packet': [({'pkt_12' : 5, 'pkt_15' : 5, 'pkt_16' : 5}, 'set_valid_outer_ipv4_packet')],
                        "marple_tcp_nmo_table": [({'pkt_0' : 5}, 'marple_tcp_nmo')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'ingress_port_properties': {'set_ingress_port_properties' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                        'validate_outer_ipv4_packet': {'set_valid_outer_ipv4_packet':['ALU1','ALU2','ALU3'], 'set_malformed_outer_ipv4_packet':['ALU1','ALU2']},
                        'marple_tcp_nmo_table': {'marple_tcp_nmo':['ALU1','ALU2','ALU3']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    pkt_alu_dic = {
        'pkt_0':[['ingress_port_properties','set_ingress_port_properties','ALU1']],
        'pkt_1':[['ingress_port_properties','set_ingress_port_properties','ALU2']],
        'pkt_2':[['ingress_port_properties','set_ingress_port_properties','ALU3']],
        'pkt_3':[['ingress_port_properties','set_ingress_port_properties','ALU4']],
        'pkt_4':[['ingress_port_properties','set_ingress_port_properties','ALU5']],
        'pkt_5':[['ingress_port_properties','set_ingress_port_properties','ALU6']],
        'pkt_6':[['ingress_port_properties','set_ingress_port_properties','ALU7']],
        'pkt_8':[['validate_outer_ipv4_packet','set_valid_outer_ipv4_packet','ALU1']],
        'pkt_9':[['validate_outer_ipv4_packet','set_valid_outer_ipv4_packet','ALU2']],
        'pkt_11':[['validate_outer_ipv4_packet','set_valid_outer_ipv4_packet','ALU3']],
        'pkt_13':[['validate_outer_ipv4_packet','set_malformed_outer_ipv4_packet','ALU1']],
        'pkt_14':[['validate_outer_ipv4_packet','set_malformed_outer_ipv4_packet','ALU2']],
        'tmp_0' : [['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU2']]
    }
    update_var_dic = {'ingress_port_properties_set_ingress_port_properties_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU2':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU3':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU4':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU5':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU6':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'ingress_port_properties_set_ingress_port_properties_ALU7':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'validate_outer_ipv4_packet_set_valid_outer_ipv4_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
    'validate_outer_ipv4_packet_set_valid_outer_ipv4_packet_ALU2':{"opcode": 2, "operand0": "pkt_10", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
    'validate_outer_ipv4_packet_set_valid_outer_ipv4_packet_ALU3':{"opcode": 2, "operand0": "pkt_12", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
    'validate_outer_ipv4_packet_set_malformed_outer_ipv4_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
    'validate_outer_ipv4_packet_set_malformed_outer_ipv4_packet_ALU2':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
    'marple_tcp_nmo_table_marple_tcp_nmo_ALU2':{"opcode": 12, "operand0": "pkt_1", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 0}
    }
    update_state_dic = {
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000000" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "100001" + "000000" + "000000" + "00000000000100000000000000001000000000"
    }

    tmp_pkt_pos_dic = {} #key: tmp field name, value: the position they are put
    # update_var_dic = {'T1_A1_ALU1' : 1,
    #             'T1_A1_ALU2' : 2,
    #             'T1_A1_ALU3' : 3,
    #             'T1_A1_ALU4' : 4,
    #             'T1_A1_ALU5' : 5,
    #             'T1_A1_ALU6' : 6}
    table_match_part_dic = {} # key: table name, val: how many match components
    for tbl in table_size_dic:
        table_match_part_dic[tbl] = math.ceil(table_size_dic[tbl] / float(entries_per_table))
    
    # TODO: read from json file
    # turn ILP's allocation output to a dictionary (Only have non-zero value)
    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 4.8290014266967773e-02, "Work": 3.1811585189190909e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 7, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "ingress_port_properties_M0", "X": 3}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1", "X": 3}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "ingress_port_properties_M0_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_stage1", "X": 1}, { "VarName": "ingress_port_properties_M0_stage2", "X": 1}, { "VarName": "ingress_port_properties_M0_stage3", "X": 1}, { "VarName": "ingress_port_properties_M1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_stage1", "X": 1}, { "VarName": "ingress_port_properties_M1_stage2", "X": 1}, { "VarName": "ingress_port_properties_M1_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage3", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 4}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "tmp_0_stage3", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x7", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 6}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s1_stage4", "X": 1}, { "VarName": "s1_stage5", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x57", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x59", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x74", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x105", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x107", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}]}
    var_val_dict = parse_json(ILP_alloc)
    # print("var_val_dict =", var_val_dict)

    # get total number of stages from json output
    if 'cost' in var_val_dict:
        cost = var_val_dict['cost'] + 1 
    else:
        cost = 1
    used_stage = cost

    stage_dic = {}
    for i in range(used_stage):
        stage_dic[i] = len(pkt_fields_def)
    # fill in tmp_pkt_pos_dic
    for tmp_field in tmp_fields_def:
        beg_val = tmp_field + "_beg"
        end_val = tmp_field + "_end"
        beg_stage = var_val_dict[beg_val]
        tmp_pkt_pos_dic[tmp_field] = stage_dic[beg_stage]
        stage_dic[beg_stage] += 1
    print("tmp_pkt_pos_dic =", tmp_pkt_pos_dic)

    num_of_pkts_in_def = len(pkt_fields_def)
    pkt_container_dic = {} # key: pkt_field, val: container idx

    for tmp_field in tmp_pkt_pos_dic:
        pkt_container_dic[tmp_field] = tmp_pkt_pos_dic[tmp_field]

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
    
    
    used_table_dict = {} # key: stage number; val: list of tables appear in that stage
    used_table_dict = gen_table_stage_alloc(var_val_dict, table_match_part_dic, cost)
    print("used_table_dict =",used_table_dict)
    # print("used_table_dict =", used_table_dict)
    for i in range(used_stage):
        used_table = len(used_table_dict[i])
        for j in range(used_table):
            # For now, we think if more than one match component of a table is in the same stage,
            # then only one of them will be used to execute the match/action rule
            if j > 0 and used_table_dict[i][j] == used_table_dict[i][j - 1]:
                continue
            # KeyExtractConf
            # get Info required (e.g., stage number, match field idx, table number etc.)
            table_name = used_table_dict[i][j] # get it from ILP's output
            print("table_name =", table_name)
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
                        # print("packet_field =", packet_field)
                        if packet_field == -1:
                            # TODO: consider the case where the ALU is used to modify tmp field/stateful vars
                            variable_name = table_name + "_" + action_name + "_" + alu
                            assert variable_name in update_state_dic ,"Not modify fields in definition"
                            tmp_str = update_state_dic[variable_name]
                            ram_list[num_of_phv - 1 - stage_dic[j]] = tmp_str
                            stage_dic[j] += 1
                        else:
                            alu_func_name = "%s_%s_%s" % (table_name, action_name, alu)
                            # print("alu_func_name =", alu_func_name)
                            update_val_dict = update_var_dic[alu_func_name]
                            # TODO generate stateless alu from update_val_dict
                            # {'opcode': 0, 'operand0': 'pkt_0', 'operand1': 'pkt_0', 'operand2': 'pkt_0', 'immediate_operand': 7}
                            opcode = update_val_dict['opcode']
                            if opcode == 0:
                                immediate_operand = update_val_dict['immediate_operand']
                                tmp_str = "00001110" + int_to_bin_str(pkt_container_dic[packet_field], 6) +\
                                    int_to_bin_str(immediate_operand, 50)
                            elif opcode == 2:
                                operand0 = update_val_dict['operand0']
                                immediate_operand = update_val_dict['immediate_operand']
                                tmp_str = "00001001" + int_to_bin_str(pkt_container_dic[operand0], 6) + int_to_bin_str(immediate_operand, 50)
                            elif opcode == 12:
                                print("Come here\n")
                                print("packet_field =", packet_field)
                                # operand0 < operand1
                                operand0 = update_val_dict['operand0']
                                operand1 = update_val_dict['operand1']
                                tmp_str = "00011100" + int_to_bin_str(pkt_container_dic[operand0], 6) + int_to_bin_str(pkt_container_dic[operand1], 6) + int_to_bin_str(0, 44)
                            else:
                                assert False, "not yet support"     

                            ram_list[num_of_phv - 1 - pkt_container_dic[packet_field]] = tmp_str

            # Add to ram_conf_str
            for content in ram_list:
                ram_conf_str += content
            ram_conf_str += "\n"
            
            #TODO: only add int out_str if there is some ALU in ram_conf_str is used
            if valid_ram_list(ram_list):
                out_str += key_extract_str
                out_str += cam_mask_conf_str
                out_str += cam_conf_str
                out_str += ram_conf_str
            

    if out_str[-1] == '\n':
        out_str = out_str[:-1]
    print(out_str)

if __name__ == '__main__':
    main(sys.argv)