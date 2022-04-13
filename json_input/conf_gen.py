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

    # two table benchmark 1
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
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000100" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "010001" + "000000" + "000000" + "00000000000100000000000000001000000000"
    }
    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 4.8290014266967773e-02, "Work": 3.1811585189190909e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 7, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "ingress_port_properties_M0", "X": 3}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1", "X": 3}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "ingress_port_properties_M0_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_stage1", "X": 1}, { "VarName": "ingress_port_properties_M0_stage2", "X": 1}, { "VarName": "ingress_port_properties_M0_stage3", "X": 1}, { "VarName": "ingress_port_properties_M1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_stage1", "X": 1}, { "VarName": "ingress_port_properties_M1_stage2", "X": 1}, { "VarName": "ingress_port_properties_M1_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage3", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 4}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "tmp_0_stage3", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x7", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 6}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s1_stage4", "X": 1}, { "VarName": "s1_stage5", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x57", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x59", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x74", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x105", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x107", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}]}
    '''
    # two table benchmark 2
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16','pkt_17','pkt_18','pkt_19','pkt_20','pkt_21','pkt_22','pkt_23','pkt_24','pkt_25','pkt_26','pkt_27','pkt_28','pkt_29','pkt_30','pkt_31','pkt_32','pkt_33','pkt_34']
    tmp_fields_def = ['tmp_0']
    stateful_var_def = ['s0', 's1']
    table_size_dic = {'fabric_ingress_dst_lkp':1,
                        'storm_control':512,
                        'marple_tcp_nmo_table':1}
    match_field_dic = {'fabric_ingress_dst_lkp' : ['pkt_10'],
                        'storm_control': ['pkt_33', 'pkt_34'],
                        'marple_tcp_nmo_table' : ['pkt_0']}
    match_action_rule = {'fabric_ingress_dst_lkp' : [({'pkt_10' : 5}, 'switch_fabric_multicast_packet')],
                        'storm_control': [({'pkt_33' : 5, 'pkt_34' : 5}, 'set_storm_control_meter')],
                        "marple_tcp_nmo_table": [({'pkt_0' : 5}, 'marple_tcp_nmo')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'fabric_ingress_dst_lkp': {'terminate_cpu_packet':['ALU1','ALU2','ALU3','ALU4'], 
                                                'switch_fabric_unicast_packet':['ALU1','ALU2','ALU3'], 
                                                'terminate_fabric_unicast_packet':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7'],
                                                'switch_fabric_multicast_packet':['ALU1','ALU2'], 
                                                'terminate_fabric_multicast_packet':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                        'storm_control': {'set_storm_control_meter':['ALU1']},
                        'marple_tcp_nmo_table': {'marple_tcp_nmo':['ALU1','ALU2','ALU3']}
                        }
    pkt_alu_dic = {
        'pkt_0':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU1'],['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU1']],
        'pkt_2':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU2']],
        'pkt_4':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU3'],['fabric_ingress_dst_lkp','switch_fabric_multicast_packet','ALU2'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU6']],
        'pkt_6':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU4'],['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU7'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU7']],
        'pkt_8':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU1'],['fabric_ingress_dst_lkp','switch_fabric_multicast_packet','ALU1']],
        'pkt_9':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU2']],
        'pkt_11':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU3']],
        'pkt_14':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU2'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU1']],
        'pkt_16':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU3'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU2']],
        'pkt_18':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU4'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU3']],
        'pkt_20':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU5'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU4']],
        'pkt_22':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU6'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU5']],
        'pkt_32':[['storm_control','set_storm_control_meter','ALU1']],
        'tmp_0' : [['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU2']]
    }
    update_var_dic = {
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU1':{"opcode": 2, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU2':{"opcode": 2, "operand0": "pkt_3", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU3':{"opcode": 2, "operand0": "pkt_5", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU4':{"opcode": 2, "operand0": "pkt_7", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_10", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU3':{"opcode": 2, "operand0": "pkt_12", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU1':{"opcode": 2, "operand0": "pkt_13", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_15", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU3':{"opcode": 2, "operand0": "pkt_17", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU4':{"opcode": 2, "operand0": "pkt_19", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU5':{"opcode": 2, "operand0": "pkt_21", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU6':{"opcode": 2, "operand0": "pkt_23", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU7':{"opcode": 2, "operand0": "pkt_24", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_multicast_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'fabric_ingress_dst_lkp_switch_fabric_multicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_25", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU1':{"opcode": 2, "operand0": "pkt_26", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_27", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU3':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU4':{"opcode": 2, "operand0": "pkt_28", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU5':{"opcode": 2, "operand0": "pkt_29", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU6':{"opcode": 2, "operand0": "pkt_30", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU7':{"opcode": 2, "operand0": "pkt_31", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'storm_control_set_storm_control_meter_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU2':{"opcode": 12, "operand0": "pkt_1", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 0}
    }
    update_state_dic = {
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000100" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "100011" + "000000" + "000000" + "00000000000100000000000000001000000000"
    }   
    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 4.5564174652099609e-02, "Work": 3.2485365664351125e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 8, 9, 10]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "fabric_ingress_dst_lkp_M0", "X": 3}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU4_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU5_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU6_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU7_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_multicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_multicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU4_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU5_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU6_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU7_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU4_stage0", "X": 1}, { "VarName": "storm_control_M0", "X": 3}, { "VarName": "storm_control_M0_set_storm_control_meter_ALU1_stage0", "X": 1}, { "VarName": "storm_control_M1", "X": 3}, { "VarName": "storm_control_M1_set_storm_control_meter_ALU1_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage1", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage2", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage3", "X": 1}, { "VarName": "storm_control_M0_stage0", "X": 1}, { "VarName": "storm_control_M0_stage1", "X": 1}, { "VarName": "storm_control_M0_stage2", "X": 1}, { "VarName": "storm_control_M0_stage3", "X": 1}, { "VarName": "storm_control_M1_stage0", "X": 1}, { "VarName": "storm_control_M1_stage1", "X": 1}, { "VarName": "storm_control_M1_stage2", "X": 1}, { "VarName": "storm_control_M1_stage3", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 3}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 4}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x74", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}]}
    '''
    # two table benchmark 3
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11']
    tmp_fields_def = ['tmp_0']
    stateful_var_def = ['s0', 's1']
    match_field_dic = {'ipv6_multicast_route_star_g' : ['pkt_7','pkt_8'],
                        'bd_flood': ['pkt_10', 'pkt_11'],
                        'marple_tcp_nmo_table' : ['pkt_0']}
    table_size_dic = {'ipv6_multicast_route_star_g':1024,
                        'bd_flood':1024,
                        'marple_tcp_nmo_table':1}
    match_action_rule = {'ipv6_multicast_route_star_g' : [({'pkt_7' : 5, 'pkt_8' : 5}, 'multicast_route_star_g_miss_1')],
                        'bd_flood': [({'pkt_10' : 5, 'pkt_11' : 5}, 'set_bd_flood_mc_index')],
                        "marple_tcp_nmo_table": [({'pkt_0' : 5}, 'marple_tcp_nmo')]}
    action_alu_dic = {
        'ipv6_multicast_route_star_g':{'multicast_route_star_g_miss_1':['ALU1'],
        'multicast_route_sm_star_g_hit_1':['ALU1','ALU2','ALU3','ALU4'],
        'multicast_route_bidir_star_g_hit_1':['ALU1','ALU2','ALU3','ALU4']},
        'bd_flood':{'set_bd_flood_mc_index':['ALU1']},
        'marple_tcp_nmo_table': {'marple_tcp_nmo':['ALU1','ALU2','ALU3']}
    }
    pkt_alu_dic = {
        'pkt_0':[['ipv6_multicast_route_star_g','multicast_route_star_g_miss_1','ALU1']],
        'pkt_1':[['ipv6_multicast_route_star_g','multicast_route_sm_star_g_hit_1','ALU1'],['ipv6_multicast_route_star_g','multicast_route_bidir_star_g_hit_1','ALU1']],
        'pkt_2':[['ipv6_multicast_route_star_g','multicast_route_sm_star_g_hit_1','ALU2'],['ipv6_multicast_route_star_g','multicast_route_bidir_star_g_hit_1','ALU2']],
        'pkt_3':[['ipv6_multicast_route_star_g','multicast_route_sm_star_g_hit_1','ALU3'],['ipv6_multicast_route_star_g','multicast_route_bidir_star_g_hit_1','ALU3']],
        'pkt_4':[['ipv6_multicast_route_star_g','multicast_route_sm_star_g_hit_1','ALU4'],['ipv6_multicast_route_star_g','multicast_route_bidir_star_g_hit_1','ALU4']],
        'pkt_9':[['bd_flood','set_bd_flood_mc_index','ALU1']],
        'tmp_0' : [['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU2']]
    }
    update_var_dic = {
        'ipv6_multicast_route_star_g_multicast_route_star_g_miss_1_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv6_multicast_route_star_g_multicast_route_sm_star_g_hit_1_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv6_multicast_route_star_g_multicast_route_sm_star_g_hit_1_ALU2':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'ipv6_multicast_route_star_g_multicast_route_sm_star_g_hit_1_ALU3':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv6_multicast_route_star_g_multicast_route_sm_star_g_hit_1_ALU4':{"opcode": 2, "operand0": "pkt_5", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'ipv6_multicast_route_star_g_multicast_route_bidir_star_g_hit_1_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv6_multicast_route_star_g_multicast_route_bidir_star_g_hit_1_ALU2':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'ipv6_multicast_route_star_g_multicast_route_bidir_star_g_hit_1_ALU3':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv6_multicast_route_star_g_multicast_route_bidir_star_g_hit_1_ALU4':{"opcode": 2, "operand0": "pkt_6", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'bd_flood_set_bd_flood_mc_index_ALU1':{"opcode": 0, "operand0": "pkt_5", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU2':{"opcode": 12, "operand0": "pkt_1", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 0}
    }
    update_state_dic = {
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000100" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "001100" + "000000" + "000000" + "00000000000100000000000000001000000000"
    }
    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 5.8511972427368164e-02, "Work": 4.4105074637359888e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 8, 9, 10]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "ipv6_multicast_route_star_g_M0", "X": 3}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_star_g_miss_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_sm_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_sm_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_sm_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_sm_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_bidir_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_bidir_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_bidir_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_multicast_route_bidir_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1", "X": 3}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_star_g_miss_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_sm_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_sm_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_sm_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_sm_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_bidir_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_bidir_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_bidir_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_multicast_route_bidir_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2", "X": 3}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_star_g_miss_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_sm_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_sm_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_sm_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_sm_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_bidir_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_bidir_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_bidir_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_multicast_route_bidir_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3", "X": 3}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_star_g_miss_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_sm_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_sm_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_sm_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_sm_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_bidir_star_g_hit_1_ALU1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_bidir_star_g_hit_1_ALU2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_bidir_star_g_hit_1_ALU3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_multicast_route_bidir_star_g_hit_1_ALU4_stage0", "X": 1}, { "VarName": "bd_flood_M0", "X": 3}, { "VarName": "bd_flood_M0_set_bd_flood_mc_index_ALU1_stage0", "X": 1}, { "VarName": "bd_flood_M1", "X": 3}, { "VarName": "bd_flood_M1_set_bd_flood_mc_index_ALU1_stage0", "X": 1}, { "VarName": "bd_flood_M2", "X": 3}, { "VarName": "bd_flood_M2_set_bd_flood_mc_index_ALU1_stage0", "X": 1}, { "VarName": "bd_flood_M3", "X": 3}, { "VarName": "bd_flood_M3_set_bd_flood_mc_index_ALU1_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_stage1", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_stage2", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M0_stage3", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_stage1", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_stage2", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M1_stage3", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_stage1", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_stage2", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M2_stage3", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_stage0", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_stage1", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_stage2", "X": 1}, { "VarName": "ipv6_multicast_route_star_g_M3_stage3", "X": 1}, { "VarName": "bd_flood_M0_stage0", "X": 1}, { "VarName": "bd_flood_M1_stage0", "X": 1}, { "VarName": "bd_flood_M2_stage0", "X": 1}, { "VarName": "bd_flood_M3_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 3}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 4}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x74", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}]}
    '''
    # two table benchmark 4
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9']
    tmp_fields_def = ['tmp_0']
    stateful_var_def = ['s0', 's1']
    match_field_dic = {'ipv4_dest_vtep' : ['pkt_2','pkt_3','pkt_4'],
                        'ipv4_urpf': ['pkt_2', 'pkt_9'],
                        'marple_tcp_nmo_table' : ['pkt_0']}
    table_size_dic = {'ipv4_dest_vtep':1024,
                        'ipv4_urpf':1024,
                        'marple_tcp_nmo_table':1}
    match_action_rule = {'ipv4_dest_vtep' : [({'pkt_2' : 5, 'pkt_3' : 5, 'pkt_4' : 5}, 'set_tunnel_termination_flag')],
                        'ipv4_urpf': [({'pkt_2' : 5, 'pkt_9' : 5}, 'ipv4_urpf_hit')],
                        "marple_tcp_nmo_table": [({'pkt_0' : 5}, 'marple_tcp_nmo')]}
    action_alu_dic = {
        'ipv4_dest_vtep':{'set_tunnel_termination_flag':['ALU1'],
        '‘set_tunnel_vni_and_termination_flag’':['ALU1','ALU2']},
        'ipv4_urpf':{'ipv4_urpf_hit':['ALU1','ALU2','ALU3']},
        'marple_tcp_nmo_table': {'marple_tcp_nmo':['ALU1','ALU2','ALU3']}
    }
    update_var_dic = {
        'ipv4_dest_vtep_set_tunnel_termination_flag_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv4_dest_vtep_‘set_tunnel_vni_and_termination_flag’_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'ipv4_dest_vtep_‘set_tunnel_vni_and_termination_flag’_ALU2':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv4_urpf_ipv4_urpf_hit_ALU1':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'ipv4_urpf_ipv4_urpf_hit_ALU2':{"opcode": 0, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'ipv4_urpf_ipv4_urpf_hit_ALU3':{"opcode": 2, "operand0": "pkt_8", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU2':{"opcode": 12, "operand0": "pkt_1", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 0}
    }
    pkt_alu_dic = {
        'pkt_0':[['ipv4_dest_vtep','set_tunnel_termination_flag','ALU1'],['ipv4_dest_vtep','set_tunnel_vni_and_termination_flag','ALU2']],
        'pkt_1':[['ipv4_dest_vtep','set_tunnel_vni_and_termination_flag','ALU1']],
        'pkt_5':[['ipv4_urpf','ipv4_urpf_hit','ALU1']],
        'pkt_6':[['ipv4_urpf','ipv4_urpf_hit','ALU2']],
        'pkt_7':[['ipv4_urpf','ipv4_urpf_hit','ALU3']],
        'tmp_0' : [['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU2']]
    }
    
    update_state_dic = {
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000100" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "001010" + "000000" + "000000" + "00000000000100000000000000001000000000"
    }

    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 4.8604011535644531e-02, "Work": 3.2259244845960107e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 9, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "ipv4_dest_vtep_M0", "X": 3}, { "VarName": "ipv4_dest_vtep_M0_set_tunnel_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_set_tunnel_vni_and_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_set_tunnel_vni_and_termination_flag_ALU2_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M1", "X": 3}, { "VarName": "ipv4_dest_vtep_M1_set_tunnel_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_set_tunnel_vni_and_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_set_tunnel_vni_and_termination_flag_ALU2_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M2", "X": 3}, { "VarName": "ipv4_dest_vtep_M2_set_tunnel_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_set_tunnel_vni_and_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_set_tunnel_vni_and_termination_flag_ALU2_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M3", "X": 3}, { "VarName": "ipv4_dest_vtep_M3_set_tunnel_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_set_tunnel_vni_and_termination_flag_ALU1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_set_tunnel_vni_and_termination_flag_ALU2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M0", "X": 3}, { "VarName": "ipv4_urpf_M0_ipv4_urpf_hit_ALU1_stage0", "X": 1}, { "VarName": "ipv4_urpf_M0_ipv4_urpf_hit_ALU2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M0_ipv4_urpf_hit_ALU3_stage0", "X": 1}, { "VarName": "ipv4_urpf_M1", "X": 3}, { "VarName": "ipv4_urpf_M1_ipv4_urpf_hit_ALU1_stage0", "X": 1}, { "VarName": "ipv4_urpf_M1_ipv4_urpf_hit_ALU2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M1_ipv4_urpf_hit_ALU3_stage0", "X": 1}, { "VarName": "ipv4_urpf_M2", "X": 3}, { "VarName": "ipv4_urpf_M2_ipv4_urpf_hit_ALU1_stage0", "X": 1}, { "VarName": "ipv4_urpf_M2_ipv4_urpf_hit_ALU2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M2_ipv4_urpf_hit_ALU3_stage0", "X": 1}, { "VarName": "ipv4_urpf_M3", "X": 3}, { "VarName": "ipv4_urpf_M3_ipv4_urpf_hit_ALU1_stage0", "X": 1}, { "VarName": "ipv4_urpf_M3_ipv4_urpf_hit_ALU2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M3_ipv4_urpf_hit_ALU3_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_stage1", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_stage2", "X": 1}, { "VarName": "ipv4_dest_vtep_M0_stage3", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_stage1", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_stage2", "X": 1}, { "VarName": "ipv4_dest_vtep_M1_stage3", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_stage1", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_stage2", "X": 1}, { "VarName": "ipv4_dest_vtep_M2_stage3", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_stage0", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_stage1", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_stage2", "X": 1}, { "VarName": "ipv4_dest_vtep_M3_stage3", "X": 1}, { "VarName": "ipv4_urpf_M0_stage0", "X": 1}, { "VarName": "ipv4_urpf_M0_stage1", "X": 1}, { "VarName": "ipv4_urpf_M0_stage2", "X": 1}, { "VarName": "ipv4_urpf_M0_stage3", "X": 1}, { "VarName": "ipv4_urpf_M1_stage0", "X": 1}, { "VarName": "ipv4_urpf_M1_stage1", "X": 1}, { "VarName": "ipv4_urpf_M1_stage2", "X": 1}, { "VarName": "ipv4_urpf_M1_stage3", "X": 1}, { "VarName": "ipv4_urpf_M2_stage0", "X": 1}, { "VarName": "ipv4_urpf_M2_stage1", "X": 1}, { "VarName": "ipv4_urpf_M2_stage2", "X": 1}, { "VarName": "ipv4_urpf_M2_stage3", "X": 1}, { "VarName": "ipv4_urpf_M3_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 3}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 6}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s1_stage4", "X": 1}, { "VarName": "s1_stage5", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x57", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x59", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x74", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x105", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x107", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}]}
    '''
    # two table benchmark 11
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16']
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0', 's1', 's2'] # all stateful variables

    table_size_dic = {'ingress_port_properties':288, 
                        'validate_outer_ipv4_packet':512,
                        'rcp_table':1}
    match_field_dic = {'ingress_port_properties' : ['pkt_7'],
                        'validate_outer_ipv4_packet': ['pkt_12', 'pkt_15', 'pkt_16'],
                        'rcp_table' : ['pkt_0']} # key: table name, val: list of matched fields
    match_action_rule = {'ingress_port_properties' : [({'pkt_7' : 5}, 'set_ingress_port_properties')],
                        'validate_outer_ipv4_packet': [({'pkt_12' : 5, 'pkt_15' : 5, 'pkt_16' : 5}, 'set_valid_outer_ipv4_packet')],
                        "rcp_table": [({'pkt_0' : 5}, 'rcp')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'ingress_port_properties': {'set_ingress_port_properties' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                        'validate_outer_ipv4_packet': {'set_valid_outer_ipv4_packet':['ALU1','ALU2','ALU3'], 'set_malformed_outer_ipv4_packet':['ALU1','ALU2']},
                        'rcp_table': {'rcp':['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
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
        'tmp_0' : [['rcp_table', 'rcp', 'ALU2']]
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
    'rcp_table_rcp_ALU2':{"opcode": 13, "operand0": "tmp_0", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 30}
    }
    update_state_dic = {
        'rcp_table_rcp_ALU1': "00001100" + "000001" + "000000" + "000000" + "00000000000100000000000000001000000000",
        'rcp_table_rcp_ALU3': "00001100" + "010001" + "000000" + "000010" + "00000000000100000010000101000000000000",
        'rcp_table_rcp_ALU4': "00001100" + "010001" + "000000" + "000000" + "00000000000100000010001001000000000000"
    }

    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 6.1382055282592773e-02, "Work": 4.2422770846283771e-02, "ObjVal": 2, "ObjBound": 2, "ObjBoundC": 2, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 2, "PoolObjVal": [ 2, 6, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 2}, { "VarName": "ingress_port_properties_M0", "X": 2}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1", "X": 2}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0", "X": 2}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1", "X": 2}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "rcp_table_M0", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU1_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU3", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU3_stage2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU4", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU4_stage2", "X": 1}, { "VarName": "ingress_port_properties_M0_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_stage1", "X": 1}, { "VarName": "ingress_port_properties_M0_stage2", "X": 1}, { "VarName": "ingress_port_properties_M1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_stage1", "X": 1}, { "VarName": "ingress_port_properties_M1_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage2", "X": 1}, { "VarName": "rcp_table_M0_stage1", "X": 1}, { "VarName": "rcp_table_M0_stage2", "X": 1}, { "VarName": "tmp_0_beg", "X": 1}, { "VarName": "tmp_0_end", "X": 3}, { "VarName": "tmp_0_stage1", "X": 1}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x2", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 3}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s0_stage2", "X": 1}, { "VarName": "s1_beg", "X": 2}, { "VarName": "s1_end", "X": 4}, { "VarName": "s1_stage2", "X": 1}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s2_beg", "X": 2}, { "VarName": "s2_end", "X": 3}, { "VarName": "s2_stage2", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x29", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x52", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x77", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x98", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x100", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}, { "VarName": "x121", "X": 1}, { "VarName": "x123", "X": 1}, { "VarName": "x124", "X": 1}, { "VarName": "x125", "X": 1}, { "VarName": "x126", "X": 1}, { "VarName": "x127", "X": 1}, { "VarName": "x128", "X": 1}, { "VarName": "x130", "X": 1}, { "VarName": "x132", "X": 1}, { "VarName": "x134", "X": 1}, { "VarName": "x136", "X": 1}, { "VarName": "x138", "X": 1}, { "VarName": "x140", "X": 1}, { "VarName": "x142", "X": 1}, { "VarName": "x145", "X": 1}, { "VarName": "x147", "X": 1}, { "VarName": "x148", "X": 1}, { "VarName": "x149", "X": 1}, { "VarName": "x150", "X": 1}, { "VarName": "x152", "X": 1}, { "VarName": "x154", "X": 1}, { "VarName": "x156", "X": 1}, { "VarName": "x158", "X": 1}, { "VarName": "x160", "X": 1}, { "VarName": "x162", "X": 1}, { "VarName": "x164", "X": 1}, { "VarName": "x166", "X": 1}, { "VarName": "x169", "X": 1}, { "VarName": "x170", "X": 1}, { "VarName": "x171", "X": 1}, { "VarName": "x172", "X": 1}, { "VarName": "x173", "X": 1}, { "VarName": "x174", "X": 1}, { "VarName": "x176", "X": 1}, { "VarName": "x178", "X": 1}, { "VarName": "x180", "X": 1}, { "VarName": "x182", "X": 1}, { "VarName": "x184", "X": 1}, { "VarName": "x186", "X": 1}, { "VarName": "x188", "X": 1}, { "VarName": "x190", "X": 1}, { "VarName": "x193", "X": 1}, { "VarName": "x195", "X": 1}, { "VarName": "x196", "X": 1}, { "VarName": "x197", "X": 1}, { "VarName": "x198", "X": 1}, { "VarName": "x199", "X": 1}, { "VarName": "x200", "X": 1}, { "VarName": "x202", "X": 1}, { "VarName": "x204", "X": 1}, { "VarName": "x206", "X": 1}, { "VarName": "x208", "X": 1}, { "VarName": "x210", "X": 1}, { "VarName": "x212", "X": 1}, { "VarName": "x214", "X": 1}, { "VarName": "x217", "X": 1}, { "VarName": "x219", "X": 1}, { "VarName": "x220", "X": 1}, { "VarName": "x221", "X": 1}, { "VarName": "x222", "X": 1}, { "VarName": "x224", "X": 1}, { "VarName": "x226", "X": 1}, { "VarName": "x228", "X": 1}, { "VarName": "x230", "X": 1}, { "VarName": "x232", "X": 1}, { "VarName": "x234", "X": 1}, { "VarName": "x236", "X": 1}, { "VarName": "x238", "X": 1}]}
    '''
    # two table benchmark 12
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16','pkt_17','pkt_18','pkt_19','pkt_20','pkt_21','pkt_22','pkt_23','pkt_24','pkt_25','pkt_26','pkt_27','pkt_28','pkt_29','pkt_30','pkt_31','pkt_32','pkt_33','pkt_34']
    tmp_fields_def = ['tmp_0']
    stateful_var_def = ['s0', 's1']
    table_size_dic = {'fabric_ingress_dst_lkp':1,
                        'storm_control':512,
                        'rcp_table':1}
    match_field_dic = {'fabric_ingress_dst_lkp' : ['pkt_10'],
                        'storm_control': ['pkt_33', 'pkt_34'],
                        'rcp_table' : ['pkt_0']}
    match_action_rule = {'fabric_ingress_dst_lkp' : [({'pkt_10' : 5}, 'switch_fabric_multicast_packet')],
                        'storm_control': [({'pkt_33' : 5, 'pkt_34' : 5}, 'set_storm_control_meter')],
                        "rcp_table": [({'pkt_0' : 5}, 'rcp')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'fabric_ingress_dst_lkp': {'terminate_cpu_packet':['ALU1','ALU2','ALU3','ALU4'], 
                                                'switch_fabric_unicast_packet':['ALU1','ALU2','ALU3'], 
                                                'terminate_fabric_unicast_packet':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7'],
                                                'switch_fabric_multicast_packet':['ALU1','ALU2'], 
                                                'terminate_fabric_multicast_packet':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                        'storm_control': {'set_storm_control_meter':['ALU1']},
                        'rcp_table': {'rcp':['ALU1','ALU2','ALU3','ALU4']}
                        }
    pkt_alu_dic = {
        'pkt_0':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU1'],['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU1']],
        'pkt_2':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU2']],
        'pkt_4':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU3'],['fabric_ingress_dst_lkp','switch_fabric_multicast_packet','ALU2'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU6']],
        'pkt_6':[['fabric_ingress_dst_lkp','terminate_cpu_packet','ALU4'],['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU7'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU7']],
        'pkt_8':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU1'],['fabric_ingress_dst_lkp','switch_fabric_multicast_packet','ALU1']],
        'pkt_9':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU2']],
        'pkt_11':[['fabric_ingress_dst_lkp','switch_fabric_unicast_packet','ALU3']],
        'pkt_14':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU2'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU1']],
        'pkt_16':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU3'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU2']],
        'pkt_18':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU4'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU3']],
        'pkt_20':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU5'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU4']],
        'pkt_22':[['fabric_ingress_dst_lkp','terminate_fabric_unicast_packet','ALU6'],['fabric_ingress_dst_lkp','terminate_fabric_multicast_packet','ALU5']],
        'pkt_32':[['storm_control','set_storm_control_meter','ALU1']],
        'tmp_0' : [['rcp_table', 'rcp', 'ALU2']]
    }
    update_var_dic = {
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU1':{"opcode": 2, "operand0": "pkt_1", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU2':{"opcode": 2, "operand0": "pkt_3", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU3':{"opcode": 2, "operand0": "pkt_5", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_cpu_packet_ALU4':{"opcode": 2, "operand0": "pkt_7", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_10", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_unicast_packet_ALU3':{"opcode": 2, "operand0": "pkt_12", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU1':{"opcode": 2, "operand0": "pkt_13", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_15", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU3':{"opcode": 2, "operand0": "pkt_17", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU4':{"opcode": 2, "operand0": "pkt_19", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU5':{"opcode": 2, "operand0": "pkt_21", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU6':{"opcode": 2, "operand0": "pkt_23", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_unicast_packet_ALU7':{"opcode": 2, "operand0": "pkt_24", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_switch_fabric_multicast_packet_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 1},
        'fabric_ingress_dst_lkp_switch_fabric_multicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_25", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU1':{"opcode": 2, "operand0": "pkt_26", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU2':{"opcode": 2, "operand0": "pkt_27", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU3':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU4':{"opcode": 2, "operand0": "pkt_28", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU5':{"opcode": 2, "operand0": "pkt_29", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU6':{"opcode": 2, "operand0": "pkt_30", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'fabric_ingress_dst_lkp_terminate_fabric_multicast_packet_ALU7':{"opcode": 2, "operand0": "pkt_31", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 0},
        'storm_control_set_storm_control_meter_ALU1':{"opcode": 0, "operand0": "pkt_0", "operand1": "pkt_0", "operand2": "pkt_0", "immediate_operand": 7},
        'rcp_table_rcp_ALU2':{"opcode": 13, "operand0": "pkt_2", "operand1": "tmp_0", "operand2": "pkt_0", "immediate_operand": 30}
    }
    update_state_dic = {
        'rcp_table_rcp_ALU1': "00001100" + "000001" + "000000" + "000000" + "00000000000100000000000000001000000000",
        'rcp_table_rcp_ALU3': "00001100" + "100011" + "000000" + "000010" + "00000000000100000010000101000000000000",
        'rcp_table_rcp_ALU4': "00001100" + "100011" + "000000" + "000000" + "00000000000100000010001001000000000000"
    }

    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 7.7869176864624023e-02, "Work": 5.3277812829116505e-02, "ObjVal": 2, "ObjBound": 2, "ObjBoundC": 2, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 2, "PoolObjVal": [ 2, 8, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 2}, { "VarName": "fabric_ingress_dst_lkp_M0", "X": 2}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_unicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU4_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU5_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU6_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_unicast_packet_ALU7_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_multicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_switch_fabric_multicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU4_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU5_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU6_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_fabric_multicast_packet_ALU7_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU1_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU2_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU3_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_terminate_cpu_packet_ALU4_stage0", "X": 1}, { "VarName": "storm_control_M0", "X": 2}, { "VarName": "storm_control_M0_set_storm_control_meter_ALU1_stage0", "X": 1}, { "VarName": "storm_control_M1", "X": 2}, { "VarName": "storm_control_M1_set_storm_control_meter_ALU1_stage0", "X": 1}, { "VarName": "rcp_table_M0", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU1_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU3", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU3_stage2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU4", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU4_stage2", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage0", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage1", "X": 1}, { "VarName": "fabric_ingress_dst_lkp_M0_stage2", "X": 1}, { "VarName": "storm_control_M0_stage0", "X": 1}, { "VarName": "storm_control_M0_stage1", "X": 1}, { "VarName": "storm_control_M0_stage2", "X": 1}, { "VarName": "storm_control_M1_stage0", "X": 1}, { "VarName": "storm_control_M1_stage1", "X": 1}, { "VarName": "storm_control_M1_stage2", "X": 1}, { "VarName": "rcp_table_M0_stage1", "X": 1}, { "VarName": "rcp_table_M0_stage2", "X": 1}, { "VarName": "tmp_0_beg", "X": 1}, { "VarName": "tmp_0_end", "X": 2}, { "VarName": "tmp_0_stage1", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x2", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 2}, { "VarName": "s1_end", "X": 5}, { "VarName": "s1_stage2", "X": 1}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s1_stage4", "X": 1}, { "VarName": "s2_beg", "X": 2}, { "VarName": "s2_end", "X": 3}, { "VarName": "s2_stage2", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x52", "X": 1}, { "VarName": "x53", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x55", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x57", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x76", "X": 1}, { "VarName": "x77", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x98", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x100", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}, { "VarName": "x121", "X": 1}, { "VarName": "x123", "X": 1}, { "VarName": "x124", "X": 1}, { "VarName": "x125", "X": 1}, { "VarName": "x126", "X": 1}, { "VarName": "x127", "X": 1}, { "VarName": "x128", "X": 1}, { "VarName": "x129", "X": 1}, { "VarName": "x130", "X": 1}, { "VarName": "x132", "X": 1}, { "VarName": "x134", "X": 1}, { "VarName": "x136", "X": 1}, { "VarName": "x138", "X": 1}, { "VarName": "x140", "X": 1}, { "VarName": "x142", "X": 1}, { "VarName": "x145", "X": 1}, { "VarName": "x147", "X": 1}, { "VarName": "x148", "X": 1}, { "VarName": "x149", "X": 1}, { "VarName": "x150", "X": 1}, { "VarName": "x152", "X": 1}, { "VarName": "x154", "X": 1}, { "VarName": "x156", "X": 1}, { "VarName": "x158", "X": 1}, { "VarName": "x160", "X": 1}, { "VarName": "x162", "X": 1}, { "VarName": "x164", "X": 1}, { "VarName": "x166", "X": 1}, { "VarName": "x169", "X": 1}, { "VarName": "x170", "X": 1}, { "VarName": "x171", "X": 1}, { "VarName": "x172", "X": 1}, { "VarName": "x174", "X": 1}, { "VarName": "x176", "X": 1}, { "VarName": "x178", "X": 1}, { "VarName": "x180", "X": 1}, { "VarName": "x182", "X": 1}, { "VarName": "x184", "X": 1}, { "VarName": "x186", "X": 1}, { "VarName": "x188", "X": 1}, { "VarName": "x190", "X": 1}, { "VarName": "x193", "X": 1}, { "VarName": "x195", "X": 1}, { "VarName": "x196", "X": 1}, { "VarName": "x197", "X": 1}, { "VarName": "x198", "X": 1}, { "VarName": "x199", "X": 1}, { "VarName": "x200", "X": 1}, { "VarName": "x201", "X": 1}, { "VarName": "x202", "X": 1}, { "VarName": "x204", "X": 1}, { "VarName": "x206", "X": 1}, { "VarName": "x208", "X": 1}, { "VarName": "x210", "X": 1}, { "VarName": "x212", "X": 1}, { "VarName": "x214", "X": 1}, { "VarName": "x217", "X": 1}, { "VarName": "x219", "X": 1}, { "VarName": "x220", "X": 1}, { "VarName": "x221", "X": 1}, { "VarName": "x222", "X": 1}, { "VarName": "x224", "X": 1}, { "VarName": "x226", "X": 1}, { "VarName": "x228", "X": 1}, { "VarName": "x230", "X": 1}, { "VarName": "x232", "X": 1}, { "VarName": "x234", "X": 1}, { "VarName": "x236", "X": 1}, { "VarName": "x238", "X": 1}]}
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16']
    tmp_fields_def = ['tmp_0','tmp_1'] # all temporary variables
    stateful_var_def = ['s0', 's1', 's2', 's3', 's4'] # all stateful variables

    table_size_dic = {'ingress_port_properties':288, 
                        'validate_outer_ipv4_packet':512,
                        'marple_tcp_nmo_table':1,
                        'rcp_table' :1}
    match_field_dic = {'ingress_port_properties' : ['pkt_7'],
                        'validate_outer_ipv4_packet': ['pkt_12', 'pkt_15', 'pkt_16'],
                        'marple_tcp_nmo_table' : ['pkt_0'],
                        'rcp_table' : ['pkt_0']} # key: table name, val: list of matched fields
    match_action_rule = {'ingress_port_properties' : [({'pkt_7' : 5}, 'set_ingress_port_properties')],
                        'validate_outer_ipv4_packet': [({'pkt_12' : 5, 'pkt_15' : 5, 'pkt_16' : 5}, 'set_valid_outer_ipv4_packet')],
                        "marple_tcp_nmo_table": [({'pkt_0' : 5}, 'marple_tcp_nmo')],
                        "rcp_table": [({'pkt_0' : 6}, 'rcp')]}  # key: table name, val: [({field: value}, action_name)]
    action_alu_dic = {'ingress_port_properties': {'set_ingress_port_properties' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                        'validate_outer_ipv4_packet': {'set_valid_outer_ipv4_packet':['ALU1','ALU2','ALU3'], 'set_malformed_outer_ipv4_packet':['ALU1','ALU2']},
                        'marple_tcp_nmo_table': {'marple_tcp_nmo':['ALU1','ALU2','ALU3']},
                        'rcp_table': {'rcp':['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
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
        'tmp_0' : [['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU2']],
        'tmp_1' : [['rcp_table', 'rcp', 'ALU2']]
    }
    state_var_op_dic = {
        's0':[['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU1']],
        's1':[['marple_tcp_nmo_table', 'marple_tcp_nmo', 'ALU3']],
        's2':[['rcp_table', 'rcp', 'ALU1']],
        's3':[['rcp_table', 'rcp', 'ALU3']],
        's4':[['rcp_table', 'rcp', 'ALU4']]
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
    'marple_tcp_nmo_table_marple_tcp_nmo_ALU2':{"opcode": 12, "operand0": "pkt_1", "operand1": "s0", "operand2": "pkt_0", "immediate_operand": 0},
    'rcp_table_rcp_ALU2':{"opcode": 13, "operand0": "pkt_2", "operand1": "tmp0", "operand2": "pkt_0", "immediate_operand": 30}
    }
    update_state_dic = {
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU1': "00001100" + "000001" + "000100" + "000000" + "00000000000100000000010001001000000000",
        'marple_tcp_nmo_table_marple_tcp_nmo_ALU3': "00001100" + "010001" + "000000" + "000000" + "00000000000100000000000000001000000000",
        'rcp_table_rcp_ALU1': "00001100" + "000001" + "000000" + "000000" + "00000000000100000000000000001000000000",
        'rcp_table_rcp_ALU3': "00001100" + "010001" + "000000" + "000010" + "00000000000100000010000101000000000000",
        'rcp_table_rcp_ALU4': "00001100" + "010001" + "000000" + "000000" + "00000000000100000010001001000000000000"
    }

    ILP_alloc = { "SolutionInfo": { "Status": 2, "Runtime": 9.5463991165161133e-02, "Work": 6.5379762029069116e-02, "ObjVal": 3, "ObjBound": 3, "ObjBoundC": 3, "MIPGap": 0, "IntVio": 0, "BoundVio": 0, "ConstrVio": 0, "IterCount": 0, "BarIterCount": 0, "NodeCount": 0, "SolCount": 4, "PoolObjBound": 3, "PoolObjVal": [ 3, 9, 10, 11]}, "Vars": [ { "VarName": "cost", "X": 3}, { "VarName": "ingress_port_properties_M0", "X": 3}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1", "X": 3}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU2_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU3_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU4_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU5_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU6_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_set_ingress_port_properties_ALU7_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1", "X": 3}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_valid_outer_ipv4_packet_ALU3_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_set_malformed_outer_ipv4_packet_ALU2_stage0", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU1_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2", "X": 2}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU2_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3", "X": 3}, { "VarName": "marple_tcp_nmo_table_M0_marple_tcp_nmo_ALU3_stage3", "X": 1}, { "VarName": "rcp_table_M0", "X": 3}, { "VarName": "rcp_table_M0_rcp_ALU1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU1_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU2_stage1", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU3", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU3_stage2", "X": 1}, { "VarName": "rcp_table_M0_rcp_ALU4", "X": 2}, { "VarName": "rcp_table_M0_rcp_ALU4_stage2", "X": 1}, { "VarName": "ingress_port_properties_M0_stage0", "X": 1}, { "VarName": "ingress_port_properties_M0_stage1", "X": 1}, { "VarName": "ingress_port_properties_M0_stage2", "X": 1}, { "VarName": "ingress_port_properties_M0_stage3", "X": 1}, { "VarName": "ingress_port_properties_M1_stage0", "X": 1}, { "VarName": "ingress_port_properties_M1_stage1", "X": 1}, { "VarName": "ingress_port_properties_M1_stage2", "X": 1}, { "VarName": "ingress_port_properties_M1_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M0_stage3", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage0", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage1", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage2", "X": 1}, { "VarName": "validate_outer_ipv4_packet_M1_stage3", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage1", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage2", "X": 1}, { "VarName": "marple_tcp_nmo_table_M0_stage3", "X": 1}, { "VarName": "rcp_table_M0_stage1", "X": 1}, { "VarName": "rcp_table_M0_stage2", "X": 1}, { "VarName": "rcp_table_M0_stage3", "X": 1}, { "VarName": "tmp_0_beg", "X": 2}, { "VarName": "tmp_0_end", "X": 3}, { "VarName": "tmp_0_stage2", "X": 1}, { "VarName": "tmp_1_beg", "X": 1}, { "VarName": "tmp_1_end", "X": 2}, { "VarName": "tmp_1_stage1", "X": 1}, { "VarName": "x1", "X": 1}, { "VarName": "x3", "X": 1}, { "VarName": "x4", "X": 1}, { "VarName": "x5", "X": 1}, { "VarName": "x6", "X": 1}, { "VarName": "x8", "X": 1}, { "VarName": "x10", "X": 1}, { "VarName": "x12", "X": 1}, { "VarName": "x14", "X": 1}, { "VarName": "x16", "X": 1}, { "VarName": "x18", "X": 1}, { "VarName": "x20", "X": 1}, { "VarName": "x22", "X": 1}, { "VarName": "x25", "X": 1}, { "VarName": "x26", "X": 1}, { "VarName": "x27", "X": 1}, { "VarName": "x28", "X": 1}, { "VarName": "x30", "X": 1}, { "VarName": "x32", "X": 1}, { "VarName": "x34", "X": 1}, { "VarName": "x36", "X": 1}, { "VarName": "x38", "X": 1}, { "VarName": "x40", "X": 1}, { "VarName": "x42", "X": 1}, { "VarName": "x44", "X": 1}, { "VarName": "x46", "X": 1}, { "VarName": "s0_beg", "X": 1}, { "VarName": "s0_end", "X": 2}, { "VarName": "s0_stage1", "X": 1}, { "VarName": "s1_beg", "X": 3}, { "VarName": "s1_end", "X": 6}, { "VarName": "s1_stage3", "X": 1}, { "VarName": "s1_stage4", "X": 1}, { "VarName": "s1_stage5", "X": 1}, { "VarName": "s2_beg", "X": 1}, { "VarName": "s2_end", "X": 4}, { "VarName": "s2_stage1", "X": 1}, { "VarName": "s2_stage2", "X": 1}, { "VarName": "s2_stage3", "X": 1}, { "VarName": "s3_beg", "X": 2}, { "VarName": "s3_end", "X": 5}, { "VarName": "s3_stage2", "X": 1}, { "VarName": "s3_stage3", "X": 1}, { "VarName": "s3_stage4", "X": 1}, { "VarName": "s4_beg", "X": 2}, { "VarName": "s4_end", "X": 3}, { "VarName": "s4_stage2", "X": 1}, { "VarName": "x49", "X": 1}, { "VarName": "x50", "X": 1}, { "VarName": "x51", "X": 1}, { "VarName": "x52", "X": 1}, { "VarName": "x54", "X": 1}, { "VarName": "x56", "X": 1}, { "VarName": "x58", "X": 1}, { "VarName": "x60", "X": 1}, { "VarName": "x62", "X": 1}, { "VarName": "x64", "X": 1}, { "VarName": "x66", "X": 1}, { "VarName": "x68", "X": 1}, { "VarName": "x70", "X": 1}, { "VarName": "x73", "X": 1}, { "VarName": "x75", "X": 1}, { "VarName": "x77", "X": 1}, { "VarName": "x78", "X": 1}, { "VarName": "x79", "X": 1}, { "VarName": "x80", "X": 1}, { "VarName": "x81", "X": 1}, { "VarName": "x82", "X": 1}, { "VarName": "x83", "X": 1}, { "VarName": "x84", "X": 1}, { "VarName": "x86", "X": 1}, { "VarName": "x88", "X": 1}, { "VarName": "x90", "X": 1}, { "VarName": "x92", "X": 1}, { "VarName": "x94", "X": 1}, { "VarName": "x97", "X": 1}, { "VarName": "x98", "X": 1}, { "VarName": "x99", "X": 1}, { "VarName": "x100", "X": 1}, { "VarName": "x101", "X": 1}, { "VarName": "x102", "X": 1}, { "VarName": "x103", "X": 1}, { "VarName": "x104", "X": 1}, { "VarName": "x106", "X": 1}, { "VarName": "x108", "X": 1}, { "VarName": "x110", "X": 1}, { "VarName": "x112", "X": 1}, { "VarName": "x114", "X": 1}, { "VarName": "x116", "X": 1}, { "VarName": "x118", "X": 1}, { "VarName": "x121", "X": 1}, { "VarName": "x123", "X": 1}, { "VarName": "x124", "X": 1}, { "VarName": "x125", "X": 1}, { "VarName": "x126", "X": 1}, { "VarName": "x127", "X": 1}, { "VarName": "x128", "X": 1}, { "VarName": "x129", "X": 1}, { "VarName": "x130", "X": 1}, { "VarName": "x132", "X": 1}, { "VarName": "x134", "X": 1}, { "VarName": "x136", "X": 1}, { "VarName": "x138", "X": 1}, { "VarName": "x140", "X": 1}, { "VarName": "x142", "X": 1}, { "VarName": "x145", "X": 1}, { "VarName": "x147", "X": 1}, { "VarName": "x148", "X": 1}, { "VarName": "x149", "X": 1}, { "VarName": "x150", "X": 1}, { "VarName": "x152", "X": 1}, { "VarName": "x154", "X": 1}, { "VarName": "x156", "X": 1}, { "VarName": "x158", "X": 1}, { "VarName": "x160", "X": 1}, { "VarName": "x162", "X": 1}, { "VarName": "x164", "X": 1}, { "VarName": "x166", "X": 1}, { "VarName": "x169", "X": 1}, { "VarName": "x170", "X": 1}, { "VarName": "x171", "X": 1}, { "VarName": "x172", "X": 1}, { "VarName": "x174", "X": 1}, { "VarName": "x176", "X": 1}, { "VarName": "x178", "X": 1}, { "VarName": "x180", "X": 1}, { "VarName": "x182", "X": 1}, { "VarName": "x184", "X": 1}, { "VarName": "x186", "X": 1}, { "VarName": "x188", "X": 1}, { "VarName": "x190", "X": 1}, { "VarName": "x193", "X": 1}, { "VarName": "x195", "X": 1}, { "VarName": "x197", "X": 1}, { "VarName": "x198", "X": 1}, { "VarName": "x199", "X": 1}, { "VarName": "x200", "X": 1}, { "VarName": "x201", "X": 1}, { "VarName": "x202", "X": 1}, { "VarName": "x203", "X": 1}, { "VarName": "x204", "X": 1}, { "VarName": "x206", "X": 1}, { "VarName": "x208", "X": 1}, { "VarName": "x210", "X": 1}, { "VarName": "x212", "X": 1}, { "VarName": "x214", "X": 1}, { "VarName": "x217", "X": 1}, { "VarName": "x218", "X": 1}, { "VarName": "x219", "X": 1}, { "VarName": "x220", "X": 1}, { "VarName": "x221", "X": 1}, { "VarName": "x222", "X": 1}, { "VarName": "x223", "X": 1}, { "VarName": "x224", "X": 1}, { "VarName": "x226", "X": 1}, { "VarName": "x228", "X": 1}, { "VarName": "x230", "X": 1}, { "VarName": "x232", "X": 1}, { "VarName": "x234", "X": 1}, { "VarName": "x236", "X": 1}, { "VarName": "x238", "X": 1}, { "VarName": "x241", "X": 1}, { "VarName": "x243", "X": 1}, { "VarName": "x244", "X": 1}, { "VarName": "x245", "X": 1}, { "VarName": "x246", "X": 1}, { "VarName": "x247", "X": 1}, { "VarName": "x248", "X": 1}, { "VarName": "x249", "X": 1}, { "VarName": "x250", "X": 1}, { "VarName": "x252", "X": 1}, { "VarName": "x254", "X": 1}, { "VarName": "x256", "X": 1}, { "VarName": "x258", "X": 1}, { "VarName": "x260", "X": 1}, { "VarName": "x262", "X": 1}, { "VarName": "x265", "X": 1}, { "VarName": "x267", "X": 1}, { "VarName": "x268", "X": 1}, { "VarName": "x269", "X": 1}, { "VarName": "x270", "X": 1}, { "VarName": "x272", "X": 1}, { "VarName": "x274", "X": 1}, { "VarName": "x276", "X": 1}, { "VarName": "x278", "X": 1}, { "VarName": "x280", "X": 1}, { "VarName": "x282", "X": 1}, { "VarName": "x284", "X": 1}, { "VarName": "x286", "X": 1}, { "VarName": "x289", "X": 1}, { "VarName": "x290", "X": 1}, { "VarName": "x291", "X": 1}, { "VarName": "x292", "X": 1}, { "VarName": "x294", "X": 1}, { "VarName": "x296", "X": 1}, { "VarName": "x298", "X": 1}, { "VarName": "x300", "X": 1}, { "VarName": "x302", "X": 1}, { "VarName": "x304", "X": 1}, { "VarName": "x306", "X": 1}, { "VarName": "x308", "X": 1}, { "VarName": "x310", "X": 1}, { "VarName": "x313", "X": 1}, { "VarName": "x315", "X": 1}, { "VarName": "x317", "X": 1}, { "VarName": "x318", "X": 1}, { "VarName": "x319", "X": 1}, { "VarName": "x320", "X": 1}, { "VarName": "x321", "X": 1}, { "VarName": "x322", "X": 1}, { "VarName": "x323", "X": 1}, { "VarName": "x324", "X": 1}, { "VarName": "x326", "X": 1}, { "VarName": "x328", "X": 1}, { "VarName": "x330", "X": 1}, { "VarName": "x332", "X": 1}, { "VarName": "x334", "X": 1}, { "VarName": "x337", "X": 1}, { "VarName": "x338", "X": 1}, { "VarName": "x339", "X": 1}, { "VarName": "x340", "X": 1}, { "VarName": "x341", "X": 1}, { "VarName": "x342", "X": 1}, { "VarName": "x343", "X": 1}, { "VarName": "x344", "X": 1}, { "VarName": "x346", "X": 1}, { "VarName": "x348", "X": 1}, { "VarName": "x350", "X": 1}, { "VarName": "x352", "X": 1}, { "VarName": "x354", "X": 1}, { "VarName": "x356", "X": 1}, { "VarName": "x358", "X": 1}, { "VarName": "x361", "X": 1}, { "VarName": "x363", "X": 1}, { "VarName": "x364", "X": 1}, { "VarName": "x365", "X": 1}, { "VarName": "x366", "X": 1}, { "VarName": "x367", "X": 1}, { "VarName": "x368", "X": 1}, { "VarName": "x369", "X": 1}, { "VarName": "x370", "X": 1}, { "VarName": "x372", "X": 1}, { "VarName": "x374", "X": 1}, { "VarName": "x376", "X": 1}, { "VarName": "x378", "X": 1}, { "VarName": "x380", "X": 1}, { "VarName": "x382", "X": 1}, { "VarName": "x385", "X": 1}, { "VarName": "x387", "X": 1}, { "VarName": "x388", "X": 1}, { "VarName": "x389", "X": 1}, { "VarName": "x390", "X": 1}, { "VarName": "x392", "X": 1}, { "VarName": "x394", "X": 1}, { "VarName": "x396", "X": 1}, { "VarName": "x398", "X": 1}, { "VarName": "x400", "X": 1}, { "VarName": "x402", "X": 1}, { "VarName": "x404", "X": 1}, { "VarName": "x406", "X": 1}, { "VarName": "x409", "X": 1}, { "VarName": "x410", "X": 1}, { "VarName": "x411", "X": 1}, { "VarName": "x412", "X": 1}, { "VarName": "x414", "X": 1}, { "VarName": "x416", "X": 1}, { "VarName": "x418", "X": 1}, { "VarName": "x420", "X": 1}, { "VarName": "x422", "X": 1}, { "VarName": "x424", "X": 1}, { "VarName": "x426", "X": 1}, { "VarName": "x428", "X": 1}, { "VarName": "x430", "X": 1}, { "VarName": "x433", "X": 1}, { "VarName": "x435", "X": 1}, { "VarName": "x437", "X": 1}, { "VarName": "x438", "X": 1}, { "VarName": "x439", "X": 1}, { "VarName": "x440", "X": 1}, { "VarName": "x441", "X": 1}, { "VarName": "x442", "X": 1}, { "VarName": "x443", "X": 1}, { "VarName": "x444", "X": 1}, { "VarName": "x446", "X": 1}, { "VarName": "x448", "X": 1}, { "VarName": "x450", "X": 1}, { "VarName": "x452", "X": 1}, { "VarName": "x454", "X": 1}, { "VarName": "x457", "X": 1}, { "VarName": "x458", "X": 1}, { "VarName": "x459", "X": 1}, { "VarName": "x460", "X": 1}, { "VarName": "x461", "X": 1}, { "VarName": "x462", "X": 1}, { "VarName": "x463", "X": 1}, { "VarName": "x464", "X": 1}, { "VarName": "x466", "X": 1}, { "VarName": "x468", "X": 1}, { "VarName": "x470", "X": 1}, { "VarName": "x472", "X": 1}, { "VarName": "x474", "X": 1}, { "VarName": "x476", "X": 1}, { "VarName": "x478", "X": 1}, { "VarName": "x481", "X": 1}, { "VarName": "x483", "X": 1}, { "VarName": "x484", "X": 1}, { "VarName": "x485", "X": 1}, { "VarName": "x486", "X": 1}, { "VarName": "x487", "X": 1}, { "VarName": "x488", "X": 1}, { "VarName": "x489", "X": 1}, { "VarName": "x490", "X": 1}, { "VarName": "x492", "X": 1}, { "VarName": "x494", "X": 1}, { "VarName": "x496", "X": 1}, { "VarName": "x498", "X": 1}, { "VarName": "x500", "X": 1}, { "VarName": "x502", "X": 1}, { "VarName": "x505", "X": 1}, { "VarName": "x507", "X": 1}, { "VarName": "x508", "X": 1}, { "VarName": "x509", "X": 1}, { "VarName": "x510", "X": 1}, { "VarName": "x512", "X": 1}, { "VarName": "x514", "X": 1}, { "VarName": "x516", "X": 1}, { "VarName": "x518", "X": 1}, { "VarName": "x520", "X": 1}, { "VarName": "x522", "X": 1}, { "VarName": "x524", "X": 1}, { "VarName": "x526", "X": 1}, { "VarName": "x529", "X": 1}, { "VarName": "x530", "X": 1}, { "VarName": "x531", "X": 1}, { "VarName": "x532", "X": 1}, { "VarName": "x534", "X": 1}, { "VarName": "x536", "X": 1}, { "VarName": "x538", "X": 1}, { "VarName": "x540", "X": 1}, { "VarName": "x542", "X": 1}, { "VarName": "x544", "X": 1}, { "VarName": "x546", "X": 1}, { "VarName": "x548", "X": 1}, { "VarName": "x550", "X": 1}, { "VarName": "x553", "X": 1}, { "VarName": "x555", "X": 1}, { "VarName": "x557", "X": 1}, { "VarName": "x558", "X": 1}, { "VarName": "x559", "X": 1}, { "VarName": "x560", "X": 1}, { "VarName": "x561", "X": 1}, { "VarName": "x562", "X": 1}, { "VarName": "x563", "X": 1}, { "VarName": "x564", "X": 1}, { "VarName": "x566", "X": 1}, { "VarName": "x568", "X": 1}, { "VarName": "x570", "X": 1}, { "VarName": "x572", "X": 1}, { "VarName": "x574", "X": 1}, { "VarName": "x577", "X": 1}, { "VarName": "x578", "X": 1}, { "VarName": "x579", "X": 1}, { "VarName": "x580", "X": 1}, { "VarName": "x581", "X": 1}, { "VarName": "x582", "X": 1}, { "VarName": "x583", "X": 1}, { "VarName": "x584", "X": 1}, { "VarName": "x586", "X": 1}, { "VarName": "x588", "X": 1}, { "VarName": "x590", "X": 1}, { "VarName": "x592", "X": 1}, { "VarName": "x594", "X": 1}, { "VarName": "x596", "X": 1}, { "VarName": "x598", "X": 1}, { "VarName": "x601", "X": 1}, { "VarName": "x603", "X": 1}, { "VarName": "x604", "X": 1}, { "VarName": "x605", "X": 1}, { "VarName": "x606", "X": 1}, { "VarName": "x607", "X": 1}, { "VarName": "x608", "X": 1}, { "VarName": "x609", "X": 1}, { "VarName": "x610", "X": 1}, { "VarName": "x612", "X": 1}, { "VarName": "x614", "X": 1}, { "VarName": "x616", "X": 1}, { "VarName": "x618", "X": 1}, { "VarName": "x620", "X": 1}, { "VarName": "x622", "X": 1}, { "VarName": "x625", "X": 1}, { "VarName": "x627", "X": 1}, { "VarName": "x628", "X": 1}, { "VarName": "x629", "X": 1}, { "VarName": "x630", "X": 1}, { "VarName": "x632", "X": 1}, { "VarName": "x634", "X": 1}, { "VarName": "x636", "X": 1}, { "VarName": "x638", "X": 1}, { "VarName": "x640", "X": 1}, { "VarName": "x642", "X": 1}, { "VarName": "x644", "X": 1}, { "VarName": "x646", "X": 1}]}
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
    state_var_pos_dic = {} # key: stateful var name; val: the number of PHV containers to store its value
    for stateful_var in state_var_op_dic:
        table_name = state_var_op_dic[stateful_var][0][0]
        action_name = state_var_op_dic[stateful_var][0][1]
        alu_name = state_var_op_dic[stateful_var][0][2]
        var_name = table_name + "_M0_" +  action_name + "_" + alu_name
        stateful_alu_stage = var_val_dict[var_name]

        state_var_pos_dic[stateful_var] = stage_dic[stateful_alu_stage]
        stage_dic[stateful_alu_stage] += 1
        # print("var_name =",var_name,"stateful_alu_stage=",stateful_alu_stage)
    
    print("state_var_pos_dic =",state_var_pos_dic)

    num_of_pkts_in_def = len(pkt_fields_def)
    pkt_container_dic = {} # key: pkt_field, val: container idx

    for tmp_field in tmp_pkt_pos_dic:
        pkt_container_dic[tmp_field] = tmp_pkt_pos_dic[tmp_field]
    for state_var in state_var_pos_dic:
        pkt_container_dic[state_var] = state_var_pos_dic[state_var]
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
                            # print("variable_name =", variable_name)
                            assert variable_name in update_state_dic ,"Not modify fields in definition"
                            # print("stage_dic =",stage_dic)
                            # print("variable_name =", variable_name)
                            # print("i =", i)
                            tmp_str = update_state_dic[variable_name]
                            # print("tmp_str =", tmp_str)
                            # sys.exit(0)
                            for stateful_var in state_var_op_dic:
                                if [table_name, action_name, alu] in state_var_op_dic[stateful_var]:
                                    corresponding_state_name = stateful_var
                                    break
                            ram_list[num_of_phv - 1 - state_var_pos_dic[corresponding_state_name]] = tmp_str
                            stage_dic[i] += 1
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
                            elif opcode == 13:
                                operand0 = update_val_dict['operand0']
                                immediate_operand = update_val_dict['immediate_operand']
                                tmp_str = "00011101" + int_to_bin_str(pkt_container_dic[operand0], 6) + int_to_bin_str(immediate_operand, 50)
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