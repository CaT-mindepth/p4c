import sys

import math

import gurobipy as gp
from gurobipy import GRB

# num_of_entries_per_table = 256
# num_of_alus_per_stage = 520
# num_of_table_per_stage = 25
# num_of_stages = 12

def solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def, 
    table_act_dic, table_size_dic, action_alu_dic, alu_dep_dic,
    pkt_alu_dic, tmp_alu_dic, state_alu_dic,
    match_dep, action_dep, successor_dep, reverse_dep, 
    num_of_entries_per_table, num_of_table_per_stage, num_of_stages, 
    opt = True):

    global_cnt = 0
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
    m.addConstr(cost >= 0)
    m.addConstr(cost <= num_of_stages - 1)
    '''it is necessary to update model before later processing
    ref: https://support.gurobi.com/hc/en-us/community/posts/360059768191-GurobiError-No-variable-names-available-to-index
    '''
    m.update()

    # Add alu-level dependency within an action
    for table in alu_dep_dic:
        num_of_match_components = table_match_dic[table]
        for i in range(num_of_match_components):
            for action in alu_dep_dic[table]:
                for pair in alu_dep_dic[table][action]:
                    alu1 = pair[0]
                    alu2 = pair[1]
                    alu1_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu1))
                    alu2_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu2))
                    m.addConstr(alu1_var <= alu2_var - 1) # alu1_var < alu2_var

    # Add table-level dependency
    for pair in match_dep:
        table1 = pair[0]
        table2 = pair[1]
        table1_size = table_match_dic[table1]
        table2_size = table_match_dic[table2]
        for i in range(table1_size):
            for j in range(table2_size):
                for table1_act in action_alu_dic[table1]:
                    for table2_act in action_alu_dic[table2]:
                        for table1_act_alu in action_alu_dic[table1][table1_act]:
                            for table2_act_alu in action_alu_dic[table2][table2_act]:
                                table1_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table1, i, table1_act, table1_act_alu))
                                table2_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table2, j, table2_act, table2_act_alu))
                                m.addConstr(table1_alu_var <= table2_alu_var - 1)
    for pair in action_dep:
        table1 = pair[0]
        table2 = pair[1]
        table1_size = table_match_dic[table1]
        table2_size = table_match_dic[table2]
        for i in range(table1_size):
            for j in range(table2_size):
                for table1_act in action_alu_dic[table1]:
                    for table2_act in action_alu_dic[table2]:
                        for table1_act_alu in action_alu_dic[table1][table1_act]:
                            for table2_act_alu in action_alu_dic[table2][table2_act]:
                                table1_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table1, i, table1_act, table1_act_alu))
                                table2_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table2, j, table2_act, table2_act_alu))
                                m.addConstr(table1_alu_var <= table2_alu_var - 1)

    for pair in reverse_dep:
        table1 = pair[0]
        table2 = pair[1]
        table1_size = table_match_dic[table1]
        table2_size = table_match_dic[table2]
        for i in range(table1_size):
            for j in range(table2_size):
                for table1_act in action_alu_dic[table1]:
                    for table2_act in action_alu_dic[table2]:
                        for table1_act_alu in action_alu_dic[table1][table1_act]:
                            for table2_act_alu in action_alu_dic[table2][table2_act]:
                                table1_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table1, i, table1_act, table1_act_alu))
                                table2_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table2, j, table2_act, table2_act_alu))
                                m.addConstr(table1_alu_var <= table2_alu_var)
    
    for pair in successor_dep:
        table1 = pair[0]
        table2 = pair[1]
        table1_size = table_match_dic[table1]
        table2_size = table_match_dic[table2]
        for i in range(table1_size):
            for j in range(table2_size):
                for table1_act in action_alu_dic[table1]:
                    for table2_act in action_alu_dic[table2]:
                        for table1_act_alu in action_alu_dic[table1][table1_act]:
                            for table2_act_alu in action_alu_dic[table2][table2_act]:
                                table1_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table1, i, table1_act, table1_act_alu))
                                table2_alu_var = m.getVarByName("%s_M%s_%s_%s" % (table2, j, table2_act, table2_act_alu))
                                m.addConstr(table1_alu_var <= table2_alu_var)

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
        for i in range(table_match_dic[table]):
            match_var = m.getVarByName("%s_M%s" % (table, i))
            action_list = table_act_dic[table] 
            for action in action_list:
                alu_list = action_alu_dic[table][action]
                for alu in alu_list:
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    for j in range(num_of_stages):
                        alu_stage_var = m.getVarByName("%s_M%s_%s_%s_stage%s" % (table, i, action, alu, j))
                        match_var_stage = m.getVarByName("%s_M%s_stage%s" % (table, i, j))
                        # m.addConstr(alu_stage_var <= match_var_stage)
                        m.addConstr((alu_stage_var == 1) >> (match_var_stage == 1))
                        # TODO: change to ILP constraints
                        m.addConstr((alu_stage_var == 1) >> (alu_var == j))
                        m.addConstr((match_var_stage == 1) >> (match_var >= j))

    table_loc_var_vec_transpose = [[table_loc_var_vec[i][j] for i in range(len(table_loc_var_vec))] for j in range(len(table_loc_var_vec[0]))]
    for i in range(len(table_loc_var_vec_transpose)):
        m.addConstr(sum(table_loc_var_vec_transpose[i]) <= num_of_table_per_stage)

    # Use no more than available ALUs per stage
    tmp_state_field_loc_vec = []
    for tmp_field in tmp_fields_def:
        m.addVar(name="%s_beg" % tmp_field) # Beg is the stage number it is written. It is unique because of SSA
        m.addVar(name="%s_end" % tmp_field) # End is >= the stage number it is last read.
        tmp_list = []
        for i in range(num_of_stages):
            tmp_list.append(m.addVar(name="%s_stage%s" % (tmp_field, i), vtype=GRB.BINARY))
        tmp_state_field_loc_vec.append(tmp_list)
    m.update()

    for tmp_field in tmp_fields_def:
        beg_var = m.getVarByName("%s_beg" % tmp_field)
        end_var = m.getVarByName("%s_end" % tmp_field)
        m.addConstr(beg_var >= 0)
        m.addConstr(beg_var <= num_of_stages - 1)
        m.addConstr(end_var >= 0)
        m.addConstr(end_var <= num_of_stages - 1)
        # m.addConstr(beg_var <= end_var - 1)
        for j in range(len(tmp_alu_dic[tmp_field])):
            mem = tmp_alu_dic[tmp_field][j]
            table = mem[0]
            action = mem[1]
            alu = mem[2]
            if j == 0:
                # the ALU that writes tmp fields
                for i in range(table_match_dic[table]):
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    m.addConstr(beg_var == alu_var)
                    m.addConstr(beg_var + 1 <= end_var)
            else:
                # the ALUs that read tmp fields
                for i in range(table_match_dic[table]):
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    m.addConstr(alu_var <= end_var)

    for tmp_field in tmp_fields_def:
        beg_var = m.getVarByName("%s_beg" % tmp_field)
        end_var = m.getVarByName("%s_end" % tmp_field)
        for i in range(num_of_stages):
            # global global_cnt 
            new_var = m.addVar(name='x%s' % global_cnt, vtype=GRB.BINARY)
            # beg <= i < end -> allocate one alu for this tmp field
            stage_var = m.getVarByName("%s_stage%s" % (tmp_field, i))
            m.addGenConstrIndicator(new_var, True, beg_var <= i)
            m.addGenConstrIndicator(new_var, False, beg_var >= i + 1)
            global_cnt += 1
            new_var1 = m.addVar(name='x%s' % global_cnt, vtype=GRB.BINARY)
            m.addGenConstrIndicator(new_var1, True, end_var >= i + 1)
            m.addGenConstrIndicator(new_var1, False, end_var <= i)
            m.addConstr(stage_var == new_var1 * new_var)
            global_cnt += 1

    for state_var in stateful_var_def:
        m.addVar(name="%s_beg" % state_var)
        m.addVar(name="%s_end" % state_var)
        tmp_list = []
        for i in range(num_of_stages):
            tmp_list.append(m.addVar(name="%s_stage%s" % (state_var, i), vtype=GRB.BINARY))
        tmp_state_field_loc_vec.append(tmp_list)
    m.update()
    for state_var in stateful_var_def:
        beg_var = m.getVarByName("%s_beg" % state_var) # Beg is the stage number for stateful ALU
        end_var = m.getVarByName("%s_end" % state_var) # End is >= the stage number it is last read.
        m.addConstr(beg_var >= 0)
        m.addConstr(beg_var <= num_of_stages - 1)
        m.addConstr(end_var >= 0)
        m.addConstr(end_var <= num_of_stages - 1)

        for j in range(len(state_alu_dic[state_var])):
            mem = state_alu_dic[state_var][j]
            table = mem[0]
            action = mem[1]
            alu = mem[2]
            if j == 0:
                for i in range(table_match_dic[table]):
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    m.addConstr(beg_var == alu_var)
                    m.addConstr(beg_var + 1 <= end_var)
            else:
                for i in range(table_match_dic[table]):
                    alu_var = m.getVarByName("%s_M%s_%s_%s" % (table, i, action, alu))
                    m.addConstr(alu_var <= end_var)
        
        for state_var in stateful_var_def:
            beg_var = m.getVarByName("%s_beg" % state_var)
            end_var = m.getVarByName("%s_end" % state_var)
            for i in range(num_of_stages):
                # beg <= i < end -> allocate one alu for this stateful var
                new_var = m.addVar(name='x%s' % global_cnt, vtype=GRB.BINARY)
                stage_var = m.getVarByName("%s_stage%s" % (state_var, i))
                m.addGenConstrIndicator(new_var, True, beg_var <= i)
                m.addGenConstrIndicator(new_var, False, beg_var >= i + 1)
                global_cnt += 1
                new_var1 = m.addVar(name='x%s' % global_cnt, vtype=GRB.BINARY)
                m.addGenConstrIndicator(new_var1, True, end_var >= i + 1)
                m.addGenConstrIndicator(new_var1, False, end_var <= i)
                m.addConstr(stage_var == new_var1 * new_var)
                global_cnt += 1

    m.update()
    if len(tmp_state_field_loc_vec) > 0:
        tmp_state_field_loc_vec_transpose = [[tmp_state_field_loc_vec[i][j] for i in range(len(tmp_state_field_loc_vec))] for j in range(len(tmp_state_field_loc_vec[0]))]
        for i in range(len(tmp_state_field_loc_vec_transpose)):
            m.addConstr(sum(tmp_state_field_loc_vec_transpose[i]) <= num_of_alus_per_stage - num_of_fields)

    '''Start solving the ILP optimization problem'''
    if opt == True:
        m.setObjective(cost, GRB.MINIMIZE)
        print("Solving optimization problem")
    else:
        m.setObjective(1, GRB.MINIMIZE)
        print("Solving satisfiable problem")
    
    m.update()
    # print("-------------num of variable =", len(m.getVars()))
    # sys.exit(0)
    m.optimize()
    if m.status == GRB.OPTIMAL: 
        print("Following is the result we want:*****************\n\n\n")   
        print('Optimal objective: %g (zero index)' % m.objVal)
        # collect all variables that we care about their output
        var_l = []
        for table in table_size_dic:
            for i in range(table_match_dic[table]):
                for j in range(num_of_stages):
                    match_str = "%s_M%s_stage%s" % (table, i, j)
                    var_l.append(match_str)
                action_list = table_act_dic[table] 
                for action in action_list:
                    alu_list = action_alu_dic[table][action]
                    for alu in alu_list:
                        alu_str = "%s_M%s_%s_%s" % (table, i, action, alu)
                        var_l.append(alu_str)
        for tmp_field in tmp_fields_def:
            beg_str = "%s_beg" % tmp_field
            end_str = "%s_end" % tmp_field
            var_l.append(beg_str)
            var_l.append(end_str)
        for v in m.getVars():
            # if v.varName != 'cost' and v.varName.find('stage') == -1:
            if v.varName in var_l or v.varName == 'cost':
                print('%s %g' % (v.varName, v.x))
        print("************************************************")
        # print(m.getJSONSolution())
    else:
        print("Sad")


def main(argv):
    num_of_entries_per_table = int(argv[1])
    num_of_table_per_stage = int(argv[2])
    num_of_stages = int(argv[3])
    # List all info needed for ILP
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1'] # all packet fields in definition
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1'], 'T2':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1, 'T2':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4']},
                        'T2': {'A1' : ['ALU1']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    # alu_dep_dic = {'T1': {'A1': [['ALU1','ALU2']]}, 'T2': {'A1': []}} #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU3','ALU4']]}, 'T2': {'A1': []}}

    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1'],['T2','A1','ALU1']], 
                    'pkt_1':[['T1','A1','ALU2']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU3']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1', 'T2']] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 1: stateful_fw*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4']
    tmp_fields_def = ['tmp_0','tmp_1','tmp_2','tmp_3'] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU2','ALU7'], ['ALU6','ALU3'], ['ALU6','ALU7'],
                                ['ALU3','ALU4'], ['ALU4','ALU5'], ['ALU7','ALU5']]}}
    pkt_alu_dic = {'pkt_3':[['T1','A1','ALU1']], 
                    'pkt_4':[['T1','A1','ALU5']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU2'],['T1','A1','ALU7']],
                    'tmp_1':[['T1','A1','ALU6'],['T1','A1','ALU3'],['T1','A1','ALU7']],
                    'tmp_2':[['T1','A1','ALU7'],['T1','A1','ALU5']],
                    'tmp_3':[['T1','A1','ALU4'],['T1','A1','ALU5']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU3']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 2: blue_increase*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2'] # all packet fields
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0','s1'] # all stateful variables

    table_act_dic = {'T1':['A1']} # key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU2'], ['ALU2','ALU3'], ['ALU3','ALU4']]}}

    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU1']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU3'],['T1','A1','ALU4']]
                    } #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    state_alu_dic = {'s0':[['T1','A1','ALU2'],['T1','A1','ALU3']],
                    's1':[['T1','A1','ALU4']]} #key: packet field in def, val: a list of list of size 3, ['table name', 'action name', 'alu name'], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''

    '''*****************test case 3: marple_new*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1'] # all packet fields
    tmp_fields_def = [] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables
    table_act_dic = {'T1':['A1']} # key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU2']]}}
    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU2']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    state_alu_dic = {'s0':[['T1','A1','ALU1'],['T1','A1','ALU2']]
                    } #key: packet field in def, val: a list of list of size 3, ['table name', 'action name', 'alu name'], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 4: sampling*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1'] # all packet fields
    tmp_fields_def = [] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1']} # key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU2']]}}

    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU2']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {
                    } #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    state_alu_dic = {'s0':[['T1','A1','ALU1'],['T1','A1','ALU2']]} #key: packet field in def, val: a list of list of size 3, ['table name', 'action name', 'alu name'], the first member is the ALU modifies tmp field and the others are ALUs that read from the tmp field
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 5: flowlets*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3']
    tmp_fields_def = ['tmp_0','tmp_1'] # all temporary variables
    stateful_var_def = ['s0', 's1'] # all stateful variables

    table_act_dic = {'T1':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU3'], ['ALU2','ALU3'], ['ALU3','ALU4']]}}
    pkt_alu_dic = {'pkt_3':[['T1','A1','ALU4']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU2'],['T1','A1','ALU3']],
                    'tmp_1':[['T1','A1','ALU3'],['T1','A1','ALU4']]
                    } #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU1'],['T1','A1','ALU3']],
                    's1':[['T1','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 6: rcp*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2']
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0', 's1', 's2'] # all stateful variables

    table_act_dic = {'T1':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU3'], ['ALU1','ALU4']]}}
    pkt_alu_dic = {} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU1'],['T1','A1','ALU3'],['T1','A1','ALU4']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU2']],
                    's1':[['T1','A1','ALU3']],
                    's2':[['T1','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 7: learn_filter*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1']
    tmp_fields_def = ['tmp_0','tmp_1'] # all temporary variables
    stateful_var_def = ['s0', 's1', 's2'] # all stateful variables

    table_act_dic = {'T1':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU4'], ['ALU2','ALU5'], ['ALU3','ALU5'], ['ALU4','ALU6'], ['ALU5','ALU6']]}}
    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU6']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU5'],['T1','A1','ALU6']],
                    'tmp_1':[['T1','A1','ALU4'],['T1','A1','ALU6']]
                    } #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU1'],['T1','A1','ALU4']],
                    's1':[['T1','A1','ALU2'],['T1','A1','ALU5']],
                    's2':[['T1','A1','ALU3'],['T1','A1','ALU5']]
                    } #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 8: marple_tcp*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1']
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0', 's1'] # all stateful variables

    table_act_dic = {'T1':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T1': {'A1': [['ALU1','ALU2'], ['ALU2','ALU3']]}}
    pkt_alu_dic = {} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T1','A1','ALU2'],['T1','A1','ALU3']]
                    } #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU1'],['T1','A1','ALU2']],
                    's1':[['T1','A1','ALU3']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [] #list of list, for each pari [T1, T2], T2 has match dependency on T1
    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 9: ingress_port_mapping + stateful_fw_T /home/xiangyug/benchmarks/switch_p4_benchmarks/test_benchmarks/benchmark1.txt*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6']
    tmp_fields_def = ['tmp_0','tmp1','tmp2','tmp3'] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1'], 'T2':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':288, 'T2':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2']},
                      'T2': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T2': {'A1': [['ALU2','ALU7'], ['ALU6','ALU3'], ['ALU6','ALU7'],
                                ['ALU3','ALU4'], ['ALU4','ALU5'], ['ALU7','ALU5']]}}
    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1']],
                   'pkt_1':[['T1','A1','ALU2']],
                   'pkt_5':[['T2','A1','ALU1']],
                   'pkt_6':[['T2','A1','ALU5']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T2','A1','ALU2'],['T2','A1','ALU7']],
                    'tmp1':[['T2','A1','ALU6'],['T2','A1','ALU3'],['T2','A1','ALU7']],
                    'tmp2':[['T2','A1','ALU7'],['T2','A1','ALU5']],
                    'tmp3':[['T2','A1','ALU4'],['T2','A1','ALU5']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T2','A1','ALU3']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1','T2']] #list of list, for each pari [T1, T2], T2 has match dependency on T1

    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''

    '''*****************test case 10: validate_outer_ipv4_packet + stateful_fw_T /home/xiangyug/benchmarks/switch_p4_benchmarks/test_benchmarks/benchmark2.txt*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6', 'pkt_7', 'pkt_8', 'pkt_9', 'pkt_10', 'pkt_11', 'pkt_12', 'pkt_13']
    tmp_fields_def = ['tmp_0','tmp_1','tmp_2','tmp_3'] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1','A2'], 'T2':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':512, 'T2':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3'], 'A2': ['ALU1','ALU2']},
                      'T2': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T2': {'A1': [['ALU2','ALU7'], ['ALU6','ALU3'], ['ALU6','ALU7'],
                                ['ALU3','ALU4'], ['ALU4','ALU5'], ['ALU7','ALU5']]}}
    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1']],
                   'pkt_1':[['T1','A1','ALU2']],
                   'pkt_3':[['T1','A1','ALU3']],
                   'pkt_5':[['T1','A2','ALU1']],
                   'pkt_6':[['T1','A2','ALU2']],
                   'pkt_12' :[['T2','A1','ALU1']],
                   'pkt_13' :[['T2','A1','ALU5']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T2','A1','ALU2'],['T2','A1','ALU7']],
                    'tmp_1':[['T2','A1','ALU6'],['T2','A1','ALU3'],['T2','A1','ALU7']],
                    'tmp_2':[['T2','A1','ALU7'],['T2','A1','ALU5']],
                    'tmp_3':[['T2','A1','ALU4'],['T2','A1','ALU5']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T2','A1','ALU3'], ['T2','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1','T2']] #list of list, for each pari [T1, T2], T2 has match dependency on T1

    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''

    '''*****************test case 11: ingress_port_mapping + validate_outer_ipv4_packet + stateful_fw_T /home/xiangyug/benchmarks/switch_p4_benchmarks/test_benchmarks/benchmark3.txt*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6', 'pkt_7', 'pkt_8', 'pkt_9', 'pkt_10', 'pkt_11', 'pkt_12', 'pkt_13',
                     'pkt_14', 'pkt_15', 'pkt_16']
    tmp_fields_def = ['tmp_0','tmp_1','tmp_2','tmp_3'] # all temporary variables
    stateful_var_def = ['s0'] # all stateful variables

    table_act_dic = {'T1':['A1'], 'T2':['A1','A2'], 'T3':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':288, 'T2':512, 'T3':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2']},
                      'T2': {'A1' : ['ALU1','ALU2','ALU3'], 'A2': ['ALU1','ALU2']},
                      'T3': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T3': {'A1': [['ALU2','ALU7'], ['ALU6','ALU3'], ['ALU6','ALU7'],
                                ['ALU3','ALU4'], ['ALU4','ALU5'], ['ALU7','ALU5']]}}
    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1']],
                   'pkt_1':[['T1','A1','ALU2']],
                   'pkt_3':[['T2','A1','ALU1']],
                   'pkt_4':[['T2','A1','ALU2']],
                   'pkt_6':[['T2','A1','ALU3']],
                   'pkt_8':[['T2','A2','ALU1']],
                   'pkt_9':[['T2','A2','ALU2']],
                   'pkt_15' :[['T3','A1','ALU1']],
                   'pkt_16' :[['T3','A1','ALU5']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T3','A1','ALU2'],['T3','A1','ALU7']],
                    'tmp_1':[['T3','A1','ALU6'],['T3','A1','ALU3'],['T3','A1','ALU7']],
                    'tmp_2':[['T3','A1','ALU7'],['T3','A1','ALU5']],
                    'tmp_3':[['T3','A1','ALU4'],['T3','A1','ALU5']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T3','A1','ALU3'], ['T3','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1','T3']] #list of list, for each pari [T1, T2], T2 has match dependency on T1

    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''
    '''*****************test case 12: ingress_port_mapping + validate_outer_ipv4_packet + 
                                      stateful_fw_T + blue_increase /home/xiangyug/benchmarks/switch_p4_benchmarks/test_benchmarks/benchmark4.txt*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6', 'pkt_7', 'pkt_8', 'pkt_9', 'pkt_10', 'pkt_11', 'pkt_12', 'pkt_13',
                     'pkt_14', 'pkt_15', 'pkt_16', 'pkt_17', 'pkt_18']

    tmp_fields_def = ['tmp_0','tmp_1','tmp_2','tmp_3', 'tmp_4'] # all temporary variables
    stateful_var_def = ['s0','s1','s2'] # all stateful variables

    table_act_dic = {'T1':['A1'], 'T2':['A1','A2'], 'T3':['A1'], 'T4':['A1']} #key: table name, val: list of actions
    table_size_dic = {'T1':288, 'T2':512, 'T3':1, 'T4':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2']},
                      'T2': {'A1' : ['ALU1','ALU2','ALU3'], 'A2': ['ALU1','ALU2']},
                      'T3': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']},
                      'T4': {'A1' : ['ALU1', 'ALU2', 'ALU3', 'ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {'T3': {'A1': [['ALU2','ALU7'], ['ALU6','ALU3'], ['ALU6','ALU7'],
                                ['ALU3','ALU4'], ['ALU4','ALU5'], ['ALU7','ALU5']]},
                   'T4': {'A1': [['ALU1', 'ALU2'], ['ALU2', 'ALU3'], ['ALU3', 'ALU4']]}}
    pkt_alu_dic = {'pkt_0':[['T1','A1','ALU1']],
                   'pkt_1':[['T1','A1','ALU2']],
                   'pkt_3':[['T2','A1','ALU1']],
                   'pkt_4':[['T2','A1','ALU2']],
                   'pkt_6':[['T2','A1','ALU3']],
                   'pkt_8':[['T2','A2','ALU1']],
                   'pkt_9':[['T2','A2','ALU2']],
                   'pkt_15' :[['T3','A1','ALU1']],
                   'pkt_16' :[['T3','A1','ALU5']],
                   'pkt_17' :[['T4','A1','ALU3']]} #key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {'tmp_0':[['T3','A1','ALU2'],['T3','A1','ALU7']],
                    'tmp_1':[['T3','A1','ALU6'],['T3','A1','ALU3'],['T3','A1','ALU7']],
                    'tmp_2':[['T3','A1','ALU7'],['T3','A1','ALU5']],
                    'tmp_3':[['T3','A1','ALU4'],['T3','A1','ALU5']],
                    'tmp_4':[['T4','A1','ALU3'], ['T4','A1','ALU4']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T3','A1','ALU3'], ['T3','A1','ALU4']],
                     's1':[['T4','A1','ALU2'], ['T4','A1','ALU3']],
                     's2':[['T4','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1','T3'], ['T2','T4']] #list of list, for each pari [T1, T2], T2 has match dependency on T1

    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1 


    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4', 'pkt_5', 'pkt_6']
    tmp_fields_def = []
    stateful_var_def = []
    table_act_dic = {'T1':['A1']}
    table_size_dic = {'T1':1} #key: table name, val: table size
    action_alu_dic = {'T1': {'A1' : ['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6']}}
    alu_dep_dic = {}
    pkt_alu_dic = {'pkt_1':[['T1','A1','ALU1']], 
                'pkt_2':[['T1','A1','ALU2']],
                'pkt_3':[['T1','A1','ALU3']],
                'pkt_4':[['T1','A1','ALU4']],
                'pkt_5':[['T1','A1','ALU5']],
                'pkt_6':[['T1','A1','ALU6']]}
    tmp_alu_dic = {}
    state_alu_dic = {}
    match_dep = []
    action_dep = []
    reverse_dep = []
    successor_dep = []
    '''
    pkt_fields_def = ['pkt_0','pkt_1','pkt_2','pkt_3','pkt_4','pkt_5','pkt_6','pkt_7','pkt_8','pkt_9','pkt_10','pkt_11','pkt_12','pkt_13','pkt_14','pkt_15','pkt_16','pkt_17','pkt_18','pkt_19','pkt_20','pkt_21','pkt_22','pkt_23','pkt_24','pkt_25','pkt_26','pkt_27','pkt_28','pkt_29','pkt_30','pkt_31','pkt_32','pkt_33','pkt_34','pkt_35','pkt_36','pkt_37','pkt_38','pkt_39','pkt_40','pkt_41','pkt_42','pkt_43','pkt_44','pkt_45','pkt_46','pkt_47','pkt_48','pkt_49','pkt_50','pkt_51','pkt_52','pkt_53','pkt_54','pkt_55','pkt_56','pkt_57','pkt_58','pkt_59','pkt_60','pkt_61','pkt_62','pkt_63','pkt_64','pkt_65','pkt_66','pkt_67','pkt_68','pkt_69','pkt_70','pkt_71','pkt_72','pkt_73','pkt_74','pkt_75','pkt_76','pkt_77','pkt_78','pkt_79','pkt_80','pkt_81','pkt_82','pkt_83','pkt_84','pkt_85','pkt_86','pkt_87','pkt_88','pkt_89','pkt_90','pkt_91','pkt_92','pkt_93','pkt_94','pkt_95','pkt_96','pkt_97','pkt_98','pkt_99','pkt_100','pkt_101','pkt_102','pkt_103','pkt_104','pkt_105','pkt_106','pkt_107','pkt_108','pkt_109','pkt_110','pkt_111','pkt_112','pkt_113','pkt_114','pkt_115','pkt_116','pkt_117','pkt_118','pkt_119','pkt_120','pkt_121','pkt_122','pkt_123','pkt_124','pkt_125','pkt_126','pkt_127','pkt_128','pkt_129','pkt_130','pkt_131','pkt_132','pkt_133','pkt_134','pkt_135','pkt_136','pkt_137','pkt_138','pkt_139','pkt_140','pkt_141','pkt_142','pkt_143','pkt_144','pkt_145','pkt_146','pkt_147','pkt_148','pkt_149','pkt_150','pkt_151','pkt_152','pkt_153','pkt_154','pkt_155','pkt_156','pkt_157','pkt_158','pkt_159','pkt_160','pkt_161','pkt_162','pkt_163','pkt_164','pkt_165','pkt_166','pkt_167','pkt_168','pkt_169','pkt_170','pkt_171','pkt_172','pkt_173','pkt_174','pkt_175','pkt_176','pkt_177','pkt_178','pkt_179','pkt_180','pkt_181','pkt_182','pkt_183','pkt_184','pkt_185','pkt_186','pkt_187','pkt_188','pkt_189','pkt_190','pkt_191','pkt_192','pkt_193','pkt_194','pkt_195','pkt_196','pkt_197','pkt_198','pkt_199','pkt_200','pkt_201','pkt_202','pkt_203','pkt_204','pkt_205','pkt_206','pkt_207','pkt_208','pkt_209','pkt_210','pkt_211','pkt_212','pkt_213','pkt_214','pkt_215','pkt_216','pkt_217','pkt_218','pkt_219','pkt_220','pkt_221','pkt_222','pkt_223','pkt_224','pkt_225','pkt_226','pkt_227','pkt_228','pkt_229','pkt_230','pkt_231','pkt_232','pkt_233','pkt_234','pkt_235','pkt_236','pkt_237','pkt_238','pkt_239','pkt_240','pkt_241','pkt_242','pkt_243','pkt_244','pkt_245','pkt_246','pkt_247','pkt_248','pkt_249','pkt_250','pkt_251','pkt_252','pkt_253','pkt_254','pkt_255','pkt_256','pkt_257','pkt_258','pkt_259','pkt_260','pkt_261','pkt_262','pkt_263','pkt_264','pkt_265','pkt_266','pkt_267','pkt_268','pkt_269','pkt_270','pkt_271','pkt_272','pkt_273','pkt_274','pkt_275','pkt_276','pkt_277','pkt_278','pkt_279','pkt_280','pkt_281','pkt_282','pkt_283','pkt_284','pkt_285','pkt_286','pkt_287','pkt_288','pkt_289','pkt_290','pkt_291','pkt_292','pkt_293','pkt_294','pkt_295','pkt_296','pkt_297','pkt_298','pkt_299','pkt_300','pkt_301','pkt_302','pkt_303','pkt_304','pkt_305','pkt_306','pkt_307','pkt_308','pkt_309','pkt_310','pkt_311','pkt_312','pkt_313','pkt_314','pkt_315','pkt_316','pkt_317','pkt_318','pkt_319','pkt_320','pkt_321','pkt_322','pkt_323','pkt_324','pkt_325','pkt_326','pkt_327','pkt_328','pkt_329','pkt_330','pkt_331','pkt_332','pkt_333','pkt_334','pkt_335','pkt_336','pkt_337','pkt_338','pkt_339','pkt_340','pkt_341','pkt_342','pkt_343','pkt_344','pkt_345','pkt_346','pkt_347','pkt_348','pkt_349','pkt_350','pkt_351','pkt_352','pkt_353','pkt_354','pkt_355','pkt_356','pkt_357','pkt_358','pkt_359','pkt_360','pkt_361','pkt_362','pkt_363','pkt_364','pkt_365','pkt_366','pkt_367','pkt_368','pkt_369','pkt_370','pkt_371','pkt_372','pkt_373','pkt_374','pkt_375','pkt_376','pkt_377','pkt_378','pkt_379','pkt_380','pkt_381','pkt_382','pkt_383','pkt_384','pkt_385','pkt_386','pkt_387','pkt_388','pkt_389','pkt_390','pkt_391','pkt_392','pkt_393','pkt_394','pkt_395','pkt_396','pkt_397','pkt_398','pkt_399','pkt_400','pkt_401','pkt_402','pkt_403','pkt_404','pkt_405','pkt_406','pkt_407','pkt_408','pkt_409','pkt_410','pkt_411','pkt_412','pkt_413','pkt_414','pkt_415','pkt_416','pkt_417','pkt_418','pkt_419','pkt_420','pkt_421','pkt_422','pkt_423','pkt_424','pkt_425','pkt_426','pkt_427','pkt_428','pkt_429','pkt_430','pkt_431','pkt_432','pkt_433','pkt_434','pkt_435','pkt_436','pkt_437','pkt_438','pkt_439','pkt_440','pkt_441','pkt_442','pkt_443','pkt_444','pkt_445','pkt_446','pkt_447','pkt_448','pkt_449','pkt_450','pkt_451','pkt_452','pkt_453','pkt_454','pkt_455','pkt_456','pkt_457','pkt_458','pkt_459','pkt_460','pkt_461','pkt_462','pkt_463','pkt_464','pkt_465','pkt_466','pkt_467','pkt_468','pkt_469','pkt_470','pkt_471','pkt_472','pkt_473','pkt_474','pkt_475','pkt_476','pkt_477','pkt_478','pkt_479','pkt_480','pkt_481','pkt_482','pkt_483','pkt_484','pkt_485','pkt_486','pkt_487','pkt_488','pkt_489','pkt_490','pkt_491','pkt_492','pkt_493','pkt_494','pkt_495','pkt_496','pkt_497','pkt_498','pkt_499','pkt_500','pkt_501','pkt_502','pkt_503','pkt_504','pkt_505','pkt_506','pkt_507','pkt_508','pkt_509','pkt_510','pkt_511','pkt_512','pkt_513','pkt_514','pkt_515','pkt_516','pkt_517','pkt_518','pkt_519'] # DONE
    tmp_fields_def = [] # DONE all temporary variables
    stateful_var_def = [] # DONE all stateful variables

    table_act_dic =  {'ingress_port_mapping': ['set_ifindex'], 'ingress_port_properties': ['set_ingress_port_properties'], 'validate_outer_ethernet': ['malformed_outer_ethernet_packet', 'set_valid_outer_unicast_packet_untagged', 'set_valid_outer_unicast_packet_single_tagged', 'set_valid_outer_unicast_packet_double_tagged', 'set_valid_outer_unicast_packet_qinq_tagged', 'set_valid_outer_multicast_packet_untagged', 'set_valid_outer_multicast_packet_single_tagged', 'set_valid_outer_multicast_packet_double_tagged', 'set_valid_outer_multicast_packet_qinq_tagged', 'set_valid_outer_broadcast_packet_untagged', 'set_valid_outer_broadcast_packet_single_tagged', 'set_valid_outer_broadcast_packet_double_tagged', 'set_valid_outer_broadcast_packet_qinq_tagged'], 'validate_outer_ipv4_packet': ['set_valid_outer_ipv4_packet', 'set_malformed_outer_ipv4_packet'], 'validate_outer_ipv6_packet': ['set_valid_outer_ipv6_packet', 'set_malformed_outer_ipv6_packet'], 'validate_mpls_packet': ['set_valid_mpls_label1', 'set_valid_mpls_label2', 'set_valid_mpls_label3'], 'switch_config_params': ['set_config_parameters'], 'port_vlan_mapping': ['set_bd_properties', 'port_vlan_mapping_miss'], 'spanning_tree': ['set_stp_state'], 'ingress_qos_map_dscp': ['set_ingress_tc', 'set_ingress_color', 'set_ingress_tc_and_color'], 'ingress_qos_map_pcp': ['set_ingress_tc', 'set_ingress_color', 'set_ingress_tc_and_color'], 'ipsg': ['on_miss'], 'ipsg_permit_special': ['ipsg_miss'], 'int_sink_update_outer': ['int_sink_update_vxlan_gpe_v4', 'nop'], 'int_source': ['int_set_src', 'int_set_no_src'], 'int_terminate': ['int_sink_gpe', 'int_no_sink'], 'sflow_ing_take_sample': ['nop', 'sflow_ing_pkt_to_cpu'], 'sflow_ingress': ['nop_1', 'sflow_ing_session_enable_0'], 'tunnel_decap_process_inner': ['decap_inner_udp', 'decap_inner_tcp', 'decap_inner_icmp', 'decap_inner_unknown'], 'tunnel_decap_process_outer': ['decap_vxlan_inner_ipv4', 'decap_vxlan_inner_ipv6', 'decap_vxlan_inner_non_ip', 'decap_genv_inner_ipv4', 'decap_genv_inner_ipv6', 'decap_genv_inner_non_ip', 'decap_nvgre_inner_ipv4', 'decap_nvgre_inner_ipv6', 'decap_nvgre_inner_non_ip', 'decap_gre_inner_ipv4', 'decap_gre_inner_ipv6', 'decap_gre_inner_non_ip', 'decap_ip_inner_ipv4', 'decap_ip_inner_ipv6', 'decap_mpls_inner_ipv4_pop1', 'decap_mpls_inner_ipv6_pop1', 'decap_mpls_inner_ethernet_ipv4_pop1', 'decap_mpls_inner_ethernet_ipv6_pop1', 'decap_mpls_inner_ethernet_non_ip_pop1', 'decap_mpls_inner_ipv4_pop2', 'decap_mpls_inner_ipv6_pop2', 'decap_mpls_inner_ethernet_ipv4_pop2', 'decap_mpls_inner_ethernet_ipv6_pop2', 'decap_mpls_inner_ethernet_non_ip_pop2', 'decap_mpls_inner_ipv4_pop3', 'decap_mpls_inner_ipv6_pop3', 'decap_mpls_inner_ethernet_ipv4_pop3', 'decap_mpls_inner_ethernet_ipv6_pop3', 'decap_mpls_inner_ethernet_non_ip_pop3'], 'storm_control': ['nop', 'set_storm_control_meter'], 'validate_packet': ['nop', 'set_unicast', 'set_unicast_and_ipv6_src_is_link_local', 'set_multicast', 'set_multicast_and_ipv6_src_is_link_local', 'set_broadcast', 'set_malformed_packet'], 'ingress_l4_dst_port': ['nop', 'set_ingress_dst_port_range_id'], 'ingress_l4_src_port': ['nop', 'set_ingress_src_port_range_id'], 'dmac': ['nop', 'dmac_hit', 'dmac_multicast_hit', 'dmac_miss', 'dmac_redirect_nexthop', 'dmac_redirect_ecmp', 'dmac_drop'], 'smac': ['nop', 'smac_miss', 'smac_hit'], 'mac_acl': ['nop', 'acl_deny', 'acl_permit', 'acl_redirect_nexthop', 'acl_redirect_ecmp', 'acl_mirror'], 'ip_acl': ['nop', 'acl_deny', 'acl_permit', 'acl_redirect_nexthop', 'acl_redirect_ecmp', 'acl_mirror'], 'ipv6_acl': ['nop', 'acl_deny', 'acl_permit', 'acl_redirect_nexthop', 'acl_redirect_ecmp', 'acl_mirror'], 'rmac': ['rmac_hit', 'rmac_miss'], 'ipv4_racl': ['nop', 'racl_deny', 'racl_permit', 'racl_redirect_nexthop', 'racl_redirect_ecmp'], 'ipv4_urpf': ['on_miss', 'ipv4_urpf_hit'], 'ipv4_urpf_lpm': ['ipv4_urpf_hit', 'urpf_miss'], 'ipv4_fib': ['on_miss', 'fib_hit_nexthop', 'fib_hit_ecmp'], 'ipv4_fib_lpm': ['on_miss', 'fib_hit_nexthop', 'fib_hit_ecmp'], 'ipv6_racl': ['nop', 'racl_deny', 'racl_permit', 'racl_redirect_nexthop', 'racl_redirect_ecmp'], 'ipv6_urpf': ['on_miss', 'ipv6_urpf_hit'], 'ipv6_urpf_lpm': ['ipv6_urpf_hit', 'urpf_miss'], 'ipv6_fib': ['on_miss', 'fib_hit_nexthop', 'fib_hit_ecmp'], 'ipv6_fib_lpm': ['on_miss', 'fib_hit_nexthop', 'fib_hit_ecmp'], 'urpf_bd': ['nop', 'urpf_bd_miss'], 'nat_dst': ['on_miss', 'set_dst_nat_nexthop_index'], 'nat_flow': ['nop', 'set_src_nat_rewrite_index', 'set_dst_nat_nexthop_index', 'set_twice_nat_nexthop_index'], 'nat_src': ['on_miss', 'set_src_nat_rewrite_index'], 'nat_twice': ['on_miss', 'set_twice_nat_nexthop_index'], 'meter_index_0': ['nop_2'], 'compute_ipv4_hashes': ['compute_lkp_ipv4_hash'], 'compute_ipv6_hashes': ['compute_lkp_ipv6_hash'], 'compute_non_ip_hashes': ['compute_lkp_non_ip_hash'], 'compute_other_hashes': ['computed_two_hashes', 'computed_one_hash'], 'meter_action': ['meter_permit_0', 'meter_deny_0'], 'ingress_bd_stats_0': ['update_ingress_bd_stats'], 'acl_stats_0': ['acl_stats_update'], 'storm_control_stats_0': ['nop_3'], 'fwd_result': ['nop', 'set_l2_redirect_action', 'set_fib_redirect_action', 'set_cpu_redirect_action', 'set_acl_redirect_action', 'set_racl_redirect_action', 'set_nat_redirect_action', 'set_multicast_route_action', 'set_multicast_bridge_action', 'set_multicast_flood', 'set_multicast_drop'], 'ecmp_group': ['nop', 'set_ecmp_nexthop_details', 'set_ecmp_nexthop_details_for_post_routed_flood'], 'nexthop': ['nop', 'set_nexthop_details', 'set_nexthop_details_for_post_routed_flood'], 'bd_flood': ['nop', 'set_bd_flood_mc_index'], 'lag_group': ['set_lag_miss', 'set_lag_port', 'set_lag_remote_port'], 'learn_notify': ['nop', 'generate_learn_notify'], 'fabric_lag': ['nop', 'set_fabric_lag_port', 'set_fabric_multicast'], 'traffic_class': ['nop', 'set_icos', 'set_queue', 'set_icos_and_queue'], 'drop_stats_0': ['drop_stats_update'], 'system_acl': ['nop', 'redirect_to_cpu', 'redirect_to_cpu_with_reason', 'copy_to_cpu', 'copy_to_cpu_with_reason', 'drop_packet', 'drop_packet_with_reason', 'negative_mirror'], 'ipv4_multicast_bridge': ['on_miss', 'multicast_bridge_s_g_hit'], 'ipv4_multicast_bridge_star_g': ['nop', 'multicast_bridge_star_g_hit'], 'ipv4_multicast_route': ['on_miss_0', 'multicast_route_s_g_hit_0'], 'ipv4_multicast_route_star_g': ['multicast_route_star_g_miss_0', 'multicast_route_sm_star_g_hit_0', 'multicast_route_bidir_star_g_hit_0'], 'ipv6_multicast_bridge': ['on_miss', 'multicast_bridge_s_g_hit'], 'ipv6_multicast_bridge_star_g': ['nop', 'multicast_bridge_star_g_hit'], 'ipv6_multicast_route': ['on_miss_1', 'multicast_route_s_g_hit_1'], 'ipv6_multicast_route_star_g': ['multicast_route_star_g_miss_1', 'multicast_route_sm_star_g_hit_1', 'multicast_route_bidir_star_g_hit_1']} # DONE
    table_size_dic = {'ingress_port_mapping': 288, 'ingress_port_properties': 288, 'validate_outer_ethernet': 512, 'validate_outer_ipv4_packet': 512, 'validate_outer_ipv6_packet': 512, 'validate_mpls_packet': 512, 'switch_config_params': 1, 'port_vlan_mapping': 4096, 'spanning_tree': 1024, 'ingress_qos_map_dscp': 64, 'ingress_qos_map_pcp': 64, 'ipsg': 1024, 'ipsg_permit_special': 512, 'int_sink_update_outer': 2, 'int_source': 256, 'int_terminate': 256, 'sflow_ing_take_sample': 16, 'sflow_ingress': 512, 'tunnel_decap_process_inner': 1024, 'tunnel_decap_process_outer': 1024, 'storm_control': 512, 'validate_packet': 512, 'ingress_l4_dst_port': 512, 'ingress_l4_src_port': 512, 'dmac': 1024, 'smac': 1024, 'mac_acl': 512, 'ip_acl': 512, 'ipv6_acl': 512, 'rmac': 1024, 'ipv4_racl': 512, 'ipv4_urpf': 1024, 'ipv4_urpf_lpm': 512, 'ipv4_fib': 1024, 'ipv4_fib_lpm': 512, 'ipv6_racl': 512, 'ipv6_urpf': 1024, 'ipv6_urpf_lpm': 512, 'ipv6_fib': 1024, 'ipv6_fib_lpm': 512, 'urpf_bd': 1024, 'nat_dst': 1024, 'nat_flow': 512, 'nat_src': 1024, 'nat_twice': 1024, 'meter_index_0': 1024, 'compute_ipv4_hashes': 1, 'compute_ipv6_hashes': 1, 'compute_non_ip_hashes': 1, 'compute_other_hashes': 1, 'meter_action': 1024, 'ingress_bd_stats_0': 1024, 'acl_stats_0': 1024, 'storm_control_stats_0': 1024, 'fwd_result': 512, 'ecmp_group': 1024, 'nexthop': 1024, 'bd_flood': 1024, 'lag_group': 1024, 'learn_notify': 512, 'fabric_lag': 1, 'traffic_class': 512, 'drop_stats_0': 1024, 'system_acl': 512, 'ipv4_multicast_bridge': 1024, 'ipv4_multicast_bridge_star_g': 1024, 'ipv4_multicast_route': 1024, 'ipv4_multicast_route_star_g': 1024, 'ipv6_multicast_bridge': 1024, 'ipv6_multicast_bridge_star_g': 1024, 'ipv6_multicast_route': 1024, 'ipv6_multicast_route_star_g': 1024} # DONE
    action_alu_dic = {'ingress_port_mapping':{'set_ifindex':['ALU1','ALU2']}, 'ingress_port_properties':{'set_ingress_port_properties':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}, 
'validate_outer_ethernet':{'malformed_outer_ethernet_packet':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10','ALU11','ALU12','ALU13'],
'set_valid_outer_unicast_packet_untagged':['ALU1','ALU2'],
'set_valid_outer_unicast_packet_single_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_unicast_packet_double_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_unicast_packet_qinq_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_multicast_packet_untagged':['ALU1','ALU2'],
'set_valid_outer_multicast_packet_single_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_multicast_packet_double_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_multicast_packet_qinq_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_broadcast_packet_untagged':['ALU1','ALU2'],
'set_valid_outer_broadcast_packet_single_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_broadcast_packet_double_tagged':['ALU1','ALU2','ALU3'],
'set_valid_outer_broadcast_packet_qinq_tagged':['ALU1','ALU2','ALU3']},
'validate_outer_ipv4_packet':{
'set_valid_outer_ipv4_packet':['ALU1','ALU2','ALU3'],
'set_malformed_outer_ipv4_packet':['ALU1','ALU2']}, 
'validate_outer_ipv6_packet':{
    'set_valid_outer_ipv6_packet':['ALU1','ALU2','ALU3'],
    'set_malformed_outer_ipv6_packet':['ALU1','ALU2']}, 
'validate_mpls_packet':{
    'set_valid_mpls_label1':['ALU1','ALU2'],
    'set_valid_mpls_label2':['ALU1','ALU2'],
    'set_valid_mpls_label3':['ALU1','ALU2']}, 
'switch_config_params':{
    'set_config_parameters':['ALU1','ALU2','ALU3','ALU4','ALU5']}, 
'port_vlan_mapping':{
    'set_bd_properties':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10','ALU11','ALU12','ALU13','ALU14','ALU15','ALU16','ALU17','ALU18','ALU19','ALU20','ALU21'],
    'port_vlan_mapping_miss':['ALU1']}, 
'spanning_tree':{'set_stp_state':['ALU1']}, 
'ingress_qos_map_dscp':{
    'set_ingress_tc':['ALU1'],
    'set_ingress_color':['ALU1'],
    'set_ingress_tc_and_color':['ALU1','ALU2']}, 
'ingress_qos_map_pcp':{
    'set_ingress_tc':['ALU1'],
    'set_ingress_color':['ALU1'],
    'set_ingress_tc_and_color':['ALU1','ALU2']}, 
'ipsg':{'on_miss':[]}, 
'ipsg_permit_special':{'ipsg_miss':['ALU1']}, 
'int_sink_update_outer':{
    'int_sink_update_vxlan_gpe_v4':['ALU1','ALU2','ALU3'],
    'nop':[]}, 
'int_source':{
    'int_set_src':['ALU1'],
    'int_set_no_src':['ALU1']}, 
'int_terminate':{
    'int_sink_gpe':['ALU1','ALU2','ALU3'],
    'int_no_sink':['ALU1']}, 
'sflow_ing_take_sample':{
    'nop':[],
    'sflow_ing_pkt_to_cpu':['ALU1']}, 
'sflow_ingress':{
    'nop_1':[],
    'sflow_ing_session_enable_0':['ALU1','ALU2']}, 
'tunnel_decap_process_inner':{
    'decap_inner_udp':['ALU1'],
    'decap_inner_tcp':['ALU1'],
    'decap_inner_icmp':['ALU1'],
    'decap_inner_unknown':[]}, 
'tunnel_decap_process_outer':{
    'decap_vxlan_inner_ipv4':['ALU1','ALU2'],
    'decap_vxlan_inner_ipv6':['ALU1','ALU2'],
    'decap_vxlan_inner_non_ip':['ALU1'],
    'decap_genv_inner_ipv4':['ALU1','ALU2'],
    'decap_genv_inner_ipv6':['ALU1','ALU2'],
    'decap_genv_inner_non_ip':['ALU1'],
    'decap_nvgre_inner_ipv4':['ALU1','ALU2'],
    'decap_nvgre_inner_ipv6':['ALU1','ALU2'],
    'decap_nvgre_inner_non_ip':['ALU1'],
    'decap_gre_inner_ipv4':['ALU1','ALU2'],
    'decap_gre_inner_ipv6':['ALU1','ALU2'],
    'decap_gre_inner_non_ip':['ALU1'],
    'decap_ip_inner_ipv4':['ALU1','ALU2'],
    'decap_ip_inner_ipv6':['ALU1','ALU2'],
    'decap_mpls_inner_ipv4_pop1':['ALU1','ALU2'],
    'decap_mpls_inner_ipv6_pop1':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv4_pop1':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv6_pop1':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_non_ip_pop1':['ALU1'],
    'decap_mpls_inner_ipv4_pop2':['ALU1','ALU2'],
    'decap_mpls_inner_ipv6_pop2':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv4_pop2':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv6_pop2':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_non_ip_pop2':['ALU1'],
    'decap_mpls_inner_ipv4_pop3':['ALU1','ALU2'],
    'decap_mpls_inner_ipv6_pop3':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv4_pop3':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_ipv6_pop3':['ALU1','ALU2'],
    'decap_mpls_inner_ethernet_non_ip_pop3':['ALU1']}, 
'storm_control':{
    'nop':[],
    'set_storm_control_meter':['ALU1']}, 
'validate_packet':{
    'nop':[],
    'set_unicast':['ALU1'],
    'set_unicast_and_ipv6_src_is_link_local':['ALU1','ALU2'],
    'set_multicast':['ALU1','ALU2'],
    'set_multicast_and_ipv6_src_is_link_local':['ALU1','ALU2','ALU3'],
    'set_broadcast':['ALU1','ALU2'],
    'set_malformed_packet':['ALU1','ALU2']}, 
'ingress_l4_dst_port':{
    'nop':[],
    'set_ingress_dst_port_range_id':['ALU1']}, 
'ingress_l4_src_port':{
    'nop':[],
    'set_ingress_src_port_range_id':['ALU1']}, 
'dmac':{
    'nop':[],
    'dmac_hit':['ALU1','ALU2'],
    'dmac_multicast_hit':['ALU1','ALU2'],
    'dmac_miss':['ALU1','ALU2'],
    'dmac_redirect_nexthop':['ALU1','ALU2','ALU3'],
    'dmac_redirect_ecmp':['ALU1','ALU2','ALU3'],
    'dmac_drop':[]}, 
'smac':{
    'nop':[],
    'smac_miss':['ALU1'],
    'smac_hit':['ALU1']}, 
'mac_acl':{
    'nop':[],
    'acl_deny':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8'],
    'acl_permit':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7'],
    'acl_redirect_nexthop':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_redirect_ecmp':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_mirror':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}, 
'ip_acl':{
    'nop':[],
    'acl_deny':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8'],
    'acl_permit':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7'],
    'acl_redirect_nexthop':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_redirect_ecmp':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_mirror':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}, 
'ipv6_acl':{
    'nop':[],
    'acl_deny':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8'],
    'acl_permit':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7'],
    'acl_redirect_nexthop':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_redirect_ecmp':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8','ALU9','ALU10'],
    'acl_mirror':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7']}, 
'rmac':{
    'rmac_hit':['ALU1'],
    'rmac_miss':['ALU1']}, 
'ipv4_racl':{
    'nop':[],
    'racl_deny':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6'],
    'racl_permit':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'racl_redirect_nexthop':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8'],
    'racl_redirect_ecmp':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8']}, 
'ipv4_urpf':{
    'on_miss':[],
    'ipv4_urpf_hit':['ALU1','ALU2','ALU3']}, 
'ipv4_urpf_lpm':{
    'ipv4_urpf_hit':['ALU1','ALU2','ALU3'],
    'urpf_miss':[]}, 
'ipv4_fib':{
    'on_miss':[],
    'fib_hit_nexthop':['ALU1','ALU2','ALU3'],
    'fib_hit_ecmp':['ALU1','ALU2','ALU3']}, 
'ipv4_fib_lpm':{
    'on_miss':[],
    'fib_hit_nexthop':['ALU1','ALU2','ALU3'],
    'fib_hit_ecmp':['ALU1','ALU2','ALU3']}, 
'ipv6_racl':{
    'nop':[],
    'racl_deny':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6'],
    'racl_permit':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'racl_redirect_nexthop':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8'],
    'racl_redirect_ecmp':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6','ALU7','ALU8']}, 
'ipv6_urpf':{
    'on_miss':[],
    'ipv6_urpf_hit':['ALU1','ALU2','ALU3']}, 
'ipv6_urpf_lpm':{
    'ipv6_urpf_hit':['ALU1','ALU2','ALU3'],
    'urpf_miss':[]}, 
'ipv6_fib':{
    'on_miss':[],
    'fib_hit_nexthop':['ALU1','ALU2','ALU3'],
    'fib_hit_ecmp':['ALU1','ALU2','ALU3']}, 
'ipv6_fib_lpm':{
    'on_miss':[],
    'fib_hit_nexthop':['ALU1','ALU2','ALU3'],
    'fib_hit_ecmp':['ALU1','ALU2','ALU3']}, 
'urpf_bd':{
    'nop':[],
    'urpf_bd_miss':['ALU1']}, 
'nat_dst':{
    'on_miss':[],
    'set_dst_nat_nexthop_index':['ALU1','ALU2','ALU3','ALU4']}, 
'nat_flow':{
    'nop':[],
    'set_src_nat_rewrite_index':['ALU1'],
    'set_dst_nat_nexthop_index':['ALU1','ALU2','ALU3','ALU4'],
    'set_twice_nat_nexthop_index':['ALU1','ALU2','ALU3','ALU4']}, 
'nat_src':{
    'on_miss':[],
    'set_src_nat_rewrite_index':['ALU1']}, 
'nat_twice':{
    'on_miss':[],
    'set_twice_nat_nexthop_index':['ALU1','ALU2','ALU3','ALU4']}, 
'meter_index_0':{'nop_2':[]}, 
'compute_ipv4_hashes':{
    'compute_lkp_ipv4_hash':[]}, 
'compute_ipv6_hashes':{
    'compute_lkp_ipv6_hash':[]}, 
'compute_non_ip_hashes':{
    'compute_lkp_non_ip_hash':[]}, 
'compute_other_hashes':{
    'computed_two_hashes':['ALU1','ALU2'],
    'computed_one_hash':['ALU1','ALU2','ALU3']}, 
'meter_action':{
    'meter_permit_0':[],
    'meter_deny_0':[]}, 
'ingress_bd_stats_0':{
    'update_ingress_bd_stats':[]}, 
'acl_stats_0':{'acl_stats_update':[]}, 
'storm_control_stats_0':{'nop_3':[]}, 
'fwd_result':{
    'nop':[],
    'set_l2_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_fib_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6'],
    'set_cpu_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_acl_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_racl_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5','ALU6'],
    'set_nat_redirect_action':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_multicast_route_action':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_multicast_bridge_action':['ALU1','ALU2','ALU3'],
    'set_multicast_flood':['ALU1','ALU2'],
    'set_multicast_drop':['ALU1','ALU2']}, 
'ecmp_group':{
    'nop':[],
    'set_ecmp_nexthop_details':['ALU1','ALU2','ALU3','ALU4','ALU5'],
    'set_ecmp_nexthop_details_for_post_routed_flood':['ALU1','ALU2','ALU3','ALU4','ALU5']}, 
'nexthop':{
    'nop':[],
    'set_nexthop_details':['ALU1','ALU2','ALU3','ALU4'],
    'set_nexthop_details_for_post_routed_flood':['ALU1','ALU2','ALU3','ALU4']}, 
'bd_flood':{
    'nop':[],
    'set_bd_flood_mc_index':['ALU1']}, 
'lag_group':{
    'set_lag_miss':[],
    'set_lag_port':['ALU1'],
    'set_lag_remote_port':['ALU1','ALU2']}, 
'learn_notify':{
    'nop':[],
    'generate_learn_notify':[]}, 
'fabric_lag':{
    'nop':[],
    'set_fabric_lag_port':['ALU1'],
    'set_fabric_multicast':['ALU1']}, 
'traffic_class':{
    'nop':[],
    'set_icos':['ALU1'],
    'set_queue':['ALU1'],
    'set_icos_and_queue':['ALU1','ALU2']}, 
'drop_stats_0':{
    'drop_stats_update':[]}, 
'system_acl':{
    'nop':[],
    'redirect_to_cpu':['ALU1','ALU2','ALU3'],
    'redirect_to_cpu_with_reason':['ALU1','ALU2','ALU3','ALU4'],
    'copy_to_cpu':['ALU1','ALU2'],
    'copy_to_cpu_with_reason':['ALU1','ALU2','ALU3'],
    'drop_packet':[],
    'drop_packet_with_reason':[],
    'negative_mirror':[]}, 
'ipv4_multicast_bridge':{
    'on_miss':[],
    'multicast_bridge_s_g_hit':['ALU1','ALU2']}, 
'ipv4_multicast_bridge_star_g':{
    'nop':[],
    'multicast_bridge_star_g_hit':['ALU1','ALU2']}, 
'ipv4_multicast_route':{
    'on_miss_0':[],
    'multicast_route_s_g_hit_0':['ALU1','ALU2','ALU3','ALU4']}, 
'ipv4_multicast_route_star_g':{
    'multicast_route_star_g_miss_0':['ALU1'],
    'multicast_route_sm_star_g_hit_0':['ALU1','ALU2','ALU3','ALU4'],
    'multicast_route_bidir_star_g_hit_0':['ALU1','ALU2','ALU3','ALU4']}, 
'ipv6_multicast_bridge':{
    'on_miss':[],
    'multicast_bridge_s_g_hit':['ALU1','ALU2']}, 
'ipv6_multicast_bridge_star_g':{
    'nop':[],
    'multicast_bridge_star_g_hit':['ALU1','ALU2']}, 
'ipv6_multicast_route':{
    'on_miss_1':[],
    'multicast_route_s_g_hit_1':['ALU1','ALU2','ALU3','ALU4']}, 
'ipv6_multicast_route_star_g':{
    'multicast_route_star_g_miss_1':['ALU1'],
    'multicast_route_sm_star_g_hit_1':['ALU1','ALU2','ALU3','ALU4'],
    'multicast_route_bidir_star_g_hit_1':['ALU1','ALU2','ALU3','ALU4']}} #key: table name, val: dictionary whose key is action name and whose value is list of alus
    
    #key: table name, val: dictionary whose key is action name and whose value is list of pairs showing dependency among alus
    alu_dep_dic = {} #DONE
    pkt_alu_dic = {} #DONE key: packet field in def, val: a list of list of size 3, [['table name', 'action name', 'alu name']], the corresponding alu modifies the key field
    tmp_alu_dic = {} #DONE key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {} #DONE key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var

    action_dep = [['ipv4_urpf','ipv4_urpf_lpm'],['ipv4_fib','ipv4_fib_lpm'],['ipv6_urpf','ipv6_urpf_lpm'],['ipv6_fib','ipv6_fib_lpm'],['nat_twice','nat_dst'],['nat_dst','nat_src'],['nat_src','nat_flow'],['ingress_port_mapping','switch_config_params'],['ingress_port_mapping','spanning_tree'],['ingress_port_mapping','ingress_qos_map_dscp'],['ingress_port_mapping','ipsg'],['ingress_port_mapping','ingress_qos_map_pcp'],['ingress_port_mapping','int_source'],['ingress_port_mapping','int_terminate'],['ingress_port_mapping','storm_control'],['ingress_port_mapping','meter_index_0'],['ingress_port_mapping','validate_packet'],['ingress_port_mapping','ingress_l4_src_port'],['ingress_port_mapping','compute_ipv4_hashes'],['ingress_port_mapping','compute_ipv6_hashes'],['ingress_port_mapping','compute_non_ip_hashes'],['ingress_port_mapping','smac'],['ingress_port_mapping','dmac'],['ingress_port_mapping','ingress_bd_stats_0'],['ingress_port_mapping','fabric_lag'],['ingress_port_mapping','mac_acl'],['ingress_port_mapping','rmac'],['ingress_port_mapping','ip_acl'],['ingress_port_mapping','ipv6_acl'],['ingress_port_mapping','system_acl'],['ingress_port_properties','ingress_qos_map_dscp'],['ingress_port_properties','ingress_qos_map_pcp'],['ingress_port_properties','ipv4_racl'],['ingress_port_properties','ipv6_racl'],['validate_outer_ethernet','validate_outer_ipv4_packet'],['validate_outer_ethernet','validate_outer_ipv6_packet'],['validate_outer_ethernet','tunnel_decap_process_outer'],['validate_outer_ethernet','validate_packet'],['validate_outer_ethernet','ingress_l4_src_port'],['validate_outer_ethernet','drop_stats_0'],['validate_outer_ipv4_packet','tunnel_decap_process_outer'],['validate_outer_ipv4_packet','validate_packet'],['validate_outer_ipv4_packet','ingress_l4_src_port'],['validate_outer_ipv4_packet','mac_acl'],['validate_outer_ipv4_packet','rmac'],['validate_outer_ipv4_packet','ip_acl'],['validate_outer_ipv4_packet','ipv6_acl'],['validate_outer_ipv4_packet','ipv4_racl'],['validate_outer_ipv4_packet','ipv6_racl'],['validate_outer_ipv4_packet','drop_stats_0'],['validate_outer_ipv4_packet','urpf_bd'],['validate_outer_ipv6_packet','tunnel_decap_process_outer'],['validate_outer_ipv6_packet','validate_packet'],['validate_outer_ipv6_packet','ingress_l4_src_port'],['validate_outer_ipv6_packet','mac_acl'],['validate_outer_ipv6_packet','rmac'],['validate_outer_ipv6_packet','ip_acl'],['validate_outer_ipv6_packet','ipv6_acl'],['validate_outer_ipv6_packet','ipv4_racl'],['validate_outer_ipv6_packet','ipv6_racl'],['validate_outer_ipv6_packet','drop_stats_0'],['validate_outer_ipv6_packet','urpf_bd'],['switch_config_params','dmac'],['switch_config_params','fabric_lag'],['switch_config_params','fwd_result'],['switch_config_params','ecmp_group'],['switch_config_params','nexthop'],['switch_config_params','lag_group'],['port_vlan_mapping','spanning_tree'],['port_vlan_mapping','ingress_qos_map_dscp'],['port_vlan_mapping','ipsg'],['port_vlan_mapping','ingress_qos_map_pcp'],['port_vlan_mapping','int_source'],['port_vlan_mapping','int_terminate'],['port_vlan_mapping','validate_packet'],['port_vlan_mapping','ipv4_racl'],['port_vlan_mapping','ecmp_group'],['port_vlan_mapping','nexthop'],['port_vlan_mapping','ipv6_racl'],['port_vlan_mapping','ipv4_urpf'],['port_vlan_mapping','ipv4_fib'],['port_vlan_mapping','urpf_bd'],['port_vlan_mapping','ipv6_urpf'],['port_vlan_mapping','ipv6_fib'],['port_vlan_mapping','learn_notify'],['ingress_qos_map_dscp','mac_acl'],['ingress_qos_map_dscp','ip_acl'],['ingress_qos_map_dscp','ipv6_acl'],['ingress_qos_map_dscp','ipv4_racl'],['ingress_qos_map_dscp','ipv6_racl'],['ingress_qos_map_pcp','mac_acl'],['ingress_qos_map_pcp','ip_acl'],['ingress_qos_map_pcp','ipv6_acl'],['ingress_qos_map_pcp','ipv4_racl'],['ingress_qos_map_pcp','ipv6_racl'],['int_terminate','sflow_ing_take_sample'],['int_terminate','mac_acl'],['int_terminate','ip_acl'],['int_terminate','ipv6_acl'],['int_sink_update_outer','tunnel_decap_process_outer'],['int_sink_update_outer','tunnel_decap_process_inner'],['sflow_ing_take_sample','mac_acl'],['sflow_ing_take_sample','ip_acl'],['sflow_ing_take_sample','ipv6_acl'],['storm_control','mac_acl'],['storm_control','ip_acl'],['storm_control','ipv6_acl'],['validate_packet','drop_stats_0'],['dmac','ecmp_group'],['dmac','nexthop'],['dmac','bd_flood'],['dmac','lag_group'],['mac_acl','ipv4_racl'],['mac_acl','ipv6_racl'],['ip_acl','ipv4_racl'],['ip_acl','ipv6_racl'],['ipv6_acl','ipv4_racl'],['ipv6_acl','ipv6_racl'],['ipv4_urpf','urpf_bd'],['ipv4_urpf','nat_twice'],['ipv4_urpf_lpm','urpf_bd'],['ipv4_urpf_lpm','nat_twice'],['ipv6_urpf','urpf_bd'],['ipv6_urpf','nat_twice'],['ipv6_urpf_lpm','urpf_bd'],['ipv6_urpf_lpm','nat_twice'],['nat_twice','nat_src'],['nat_twice','nat_flow'],['nat_dst','nat_flow'],['fwd_result','ecmp_group'],['fwd_result','nexthop'],['fwd_result','bd_flood'],['fwd_result','lag_group'],['fwd_result','drop_stats_0'],['ecmp_group','bd_flood'],['ecmp_group','lag_group'],['nexthop','bd_flood'],['nexthop','lag_group'],['bd_flood','fabric_lag'],['lag_group','system_acl'],['traffic_class','system_acl']]
    match_dep = [['int_terminate','int_sink_update_outer'],['sflow_ingress','sflow_ing_take_sample'],['ingress_port_mapping','port_vlan_mapping'],['ingress_port_mapping','sflow_ingress'],['ingress_port_properties','meter_action'],['ingress_port_properties','traffic_class'],['ingress_port_properties','mac_acl'],['ingress_port_properties','ip_acl'],['ingress_port_properties','ipv6_acl'],['ingress_port_properties','system_acl'],['validate_outer_ethernet','ingress_qos_map_pcp'],['validate_outer_ethernet','storm_control'],['validate_outer_ethernet','compute_ipv4_hashes'],['validate_outer_ethernet','compute_ipv6_hashes'],['validate_outer_ethernet','compute_non_ip_hashes'],['validate_outer_ethernet','mac_acl'],['validate_outer_ethernet','fwd_result'],['validate_outer_ethernet','system_acl'],['validate_outer_ethernet','bd_flood'],['validate_outer_ipv4_packet','ingress_qos_map_dscp'],['validate_outer_ipv4_packet','compute_ipv4_hashes'],['validate_outer_ipv4_packet','compute_ipv6_hashes'],['validate_outer_ipv4_packet','compute_non_ip_hashes'],['validate_outer_ipv4_packet','fwd_result'],['validate_outer_ipv4_packet','system_acl'],['validate_outer_ipv6_packet','ingress_qos_map_dscp'],['validate_outer_ipv6_packet','compute_ipv4_hashes'],['validate_outer_ipv6_packet','compute_ipv6_hashes'],['validate_outer_ipv6_packet','compute_non_ip_hashes'],['validate_outer_ipv6_packet','fwd_result'],['validate_outer_ipv6_packet','system_acl'],['switch_config_params','system_acl'],['port_vlan_mapping','smac'],['port_vlan_mapping','dmac'],['port_vlan_mapping','mac_acl'],['port_vlan_mapping','rmac'],['port_vlan_mapping','ip_acl'],['port_vlan_mapping','ipv6_acl'],['port_vlan_mapping','nat_twice'],['port_vlan_mapping','fwd_result'],['port_vlan_mapping','system_acl'],['port_vlan_mapping','nat_dst'],['port_vlan_mapping','nat_src'],['port_vlan_mapping','nat_flow'],['port_vlan_mapping','bd_flood'],['port_vlan_mapping','ipv4_urpf_lpm'],['port_vlan_mapping','ipv4_fib_lpm'],['port_vlan_mapping','ipv6_urpf_lpm'],['port_vlan_mapping','ipv6_fib_lpm'],['spanning_tree','system_acl'],['spanning_tree','learn_notify'],['ingress_qos_map_dscp','meter_action'],['ingress_qos_map_dscp','traffic_class'],['ingress_qos_map_pcp','meter_action'],['ingress_qos_map_pcp','traffic_class'],['ipsg_permit_special','system_acl'],['storm_control','meter_action'],['validate_packet','compute_ipv4_hashes'],['validate_packet','compute_ipv6_hashes'],['validate_packet','compute_non_ip_hashes'],['validate_packet','fwd_result'],['validate_packet','system_acl'],['validate_packet','bd_flood'],['ingress_l4_src_port','ip_acl'],['ingress_l4_src_port','ipv6_acl'],['ingress_l4_src_port','ipv4_racl'],['ingress_l4_src_port','ipv6_racl'],['ingress_l4_dst_port','ip_acl'],['ingress_l4_dst_port','ipv6_acl'],['ingress_l4_dst_port','ipv4_racl'],['ingress_l4_dst_port','ipv6_racl'],['smac','learn_notify'],['dmac','fabric_lag'],['dmac','fwd_result'],['dmac','system_acl'],['mac_acl','meter_action'],['mac_acl','traffic_class'],['mac_acl','fwd_result'],['mac_acl','system_acl'],['ip_acl','meter_action'],['ip_acl','traffic_class'],['ip_acl','fwd_result'],['ip_acl','system_acl'],['ipv6_acl','meter_action'],['ipv6_acl','traffic_class'],['ipv6_acl','fwd_result'],['ipv6_acl','system_acl'],['rmac','fwd_result'],['rmac','system_acl'],['ipv4_racl','meter_action'],['ipv4_racl','traffic_class'],['ipv4_racl','fwd_result'],['ipv4_racl','system_acl'],['ipv4_urpf_lpm','system_acl'],['ipv4_fib','fwd_result'],['ipv4_fib_lpm','fwd_result'],['ipv6_racl','meter_action'],['ipv6_racl','traffic_class'],['ipv6_racl','fwd_result'],['ipv6_racl','system_acl'],['ipv6_urpf_lpm','system_acl'],['ipv6_fib','fwd_result'],['ipv6_fib_lpm','fwd_result'],['urpf_bd','system_acl'],['nat_twice','fwd_result'],['nat_dst','fwd_result'],['nat_flow','fwd_result'],['compute_other_hashes','ecmp_group'],['fwd_result','fabric_lag'],['fwd_result','system_acl'],['ecmp_group','fabric_lag'],['ecmp_group','system_acl'],['nexthop','fabric_lag'],['nexthop','system_acl'],['lag_group','fabric_lag']]
    successor_dep = [['ipsg','ipsg_permit_special']]
    reverse_dep = [['storm_control','validate_packet'],['compute_ipv4_hashes','fwd_result'],['compute_ipv6_hashes','fwd_result'],['compute_non_ip_hashes','fwd_result'],['fabric_lag','system_acl']]


    opt = True
    solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def, 
    table_act_dic, table_size_dic, action_alu_dic, alu_dep_dic,
    pkt_alu_dic, tmp_alu_dic, state_alu_dic,
    match_dep, action_dep, successor_dep, reverse_dep, 
    num_of_entries_per_table, num_of_table_per_stage, num_of_stages, 
    opt)

    # TODO: List all info needed for txt gen
    table_match_dic = {} #key: table name, val: list of packet fields for match
    table_match_val_dic = {} #key: table name, val: list of match value
    alu_content_dic = {} #key: alu name, val: content of this alu



if __name__ == '__main__':
    main(sys.argv)
