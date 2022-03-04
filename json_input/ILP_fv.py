import sys

import math

import gurobipy as gp
from gurobipy import GRB

num_of_entries_per_table = 256
num_of_alus_per_stage = 64
num_of_table_per_stage = 8
num_of_stages = 12
global_cnt = 0

def solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def, 
    table_act_dic, table_size_dic, action_alu_dic, alu_dep_dic,
    pkt_alu_dic, tmp_alu_dic, state_alu_dic,
    match_dep, action_dep, reverse_dep):
    num_of_fields = len(pkt_fields_def)

    m = gp.Model("ILP")
    cost = m.addVar(name='cost', vtype=GRB.INTEGER)

    '''Build a dict showing how many match components per table'''
    table_match_dic = {} # key: table name, val: number of match components, {T1: 2}
    for table in  table_size_dic:
        size = table_size_dic[table]
        table_match_dic[table] = math.ceil(float(size) / num_of_entries_per_table)

    alu_components_var = []
    match_components_var = []
    alu_loc_var_vec = []

    for table in table_size_dic:
        num_of_match_components = table_match_dic[table]
        for i in range(num_of_match_components):
            match_components_var.append(m.addVar(name="%s_M%s" % (table, i), vtype=GRB.INTEGER))
            list_of_actions = table_act_dic[table]
            for action in list_of_actions:
                alu_list = action_alu_dic[table][action]
                for alu in alu_list:
                    alu_components_var.append(m.addVar(name="%s_M%s_%s_%s" % (table, i, action, alu), vtype=GRB.INTEGER))
                    tmp_l = []
                    for j in range(num_of_stages):
                        tmp_l.append(m.addVar(name="%s_M%s_%s_%s_stage%s" % (table, i, action, alu, j), vtype=GRB.BINARY))
                    alu_loc_var_vec.append(tmp_l) 
    
    # Add prelimianry constraints >=0
    for var in match_components_var:
        m.addConstr(var >= 0)
        m.addConstr(cost >= var)
    for var in alu_components_var:
        m.addConstr(var >= 0)
        m.addConstr(cost >= var)
    '''it is necessary to update model before later processing
    ref: https://support.gurobi.com/hc/en-us/community/posts/360059768191-GurobiError-No-variable-names-available-to-index
    '''
    m.update()

    # Add alu-level dependency within an action

    # Add table-level dependency

    # All alus must be allocated to one and only one stage
    for alu_vec in alu_loc_var_vec:
        m.addConstr(sum(alu_vec) == 1)

    # restrict the number of tables used within a stage should be smaller than or equal to number of tables per stage
    
    table_loc_var_vec = []
    for table in table_size_dic:
        num_of_match_components = table_match_dic[table]
        for i in range(num_of_match_components):
            tmp_list = []
            for j in range(num_of_stages):
                tmp_list.append(m.addVar(name="%s_M%s_stage%s" % (table, i, j), vtype=GRB.BINARY))
            table_loc_var_vec.append(tmp_list)
    m.update()
    for table in table_size_dic:
        for i in range(table_size_dic[table]):
            match_var = m.getVarByName("%s_M%s" % (table, i))
            action_list = table_act_dic[table] 
            for action in action_list:
                alu_list = action_alu_dic[table][action]
                for alu in alu_list:
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    for j in range(num_of_stages):
                        alu_stage_var = m.getVarByName("%s_M%s_%s_%s_stage%s" % (table, i, action, alu, j))
                        match_var_stage = m.getVarByName("%s_M%s_stage%s" % (table, i, j))
                        m.addConstr((alu_stage_var == 1) >> (match_var_stage == 1))
                        m.addConstr((alu_stage_var == 1) >> (alu_var == j))
                        m.addConstr((match_var_stage == 1) >> (match_var >= j))

    table_loc_var_vec_transpose = [[table_loc_var_vec[i][j] for i in range(len(table_loc_var_vec))] for j in range(len(table_loc_var_vec[0]))]
    for i in range(len(table_loc_var_vec_transpose)):
        m.addConstr(sum(table_loc_var_vec_transpose[i]) <= num_of_table_per_stage)


    '''Start solving the ILP optimization problem'''
    m.setObjective(cost, GRB.MINIMIZE)
    m.optimize()
    if m.status == GRB.OPTIMAL:    
        print('Optimal objective: %g' % m.objVal)
        print("Following is the result we want:*****************")
        for v in m.getVars():
            # if v.varName != 'cost' and v.varName.find('stage') == -1:
            if v.varName != 'cost':
                print('%s %g' % (v.varName, v.x))
        print("************************************************")
        print('Obj: %g' % m.objVal)
    else:
        print("Sad")


def main(argv):
    # List all info needed for ILP
    pkt_fields_def = ['pkt_0', 'pkt_1'] # all packet fields in definition
    tmp_fields_def = [] # all temporary variables
    stateful_var_def = [] # all stateful variables

    table_act_dic = {'T1':['A1'], 'T2':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1, 'T2':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1']},
                        'T2': {'A1' : ['ALU1']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    alu_dep_dic = {'T1': {'A1': []}, 'T2': {'A1': []}} #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    
    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1']], 
                    'pkt_1':[['T2','A1','ALU1']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1', 'T2']] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1

    solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def, 
    table_act_dic, table_size_dic, action_alu_dic, alu_dep_dic,
    pkt_alu_dic, tmp_alu_dic, state_alu_dic,
    match_dep, action_dep, reverse_dep)

    # TODO: List all info needed for txt gen
    table_match_dic = {} #key: table name, val: list of packet fields for match
    table_match_val_dic = {} #key: table name, val: list of match value
    alu_content_dic = {} #key: alu name, val: content of this alu



if __name__ == '__main__':
    main(sys.argv)