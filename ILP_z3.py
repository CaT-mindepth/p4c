import sys

from z3 import *
import math

num_of_entries_per_table = 256
num_of_alus_per_stage = 64
num_of_table_per_stage = 8
num_of_stages = 5

# TODO: replace binary ints by bool variables and use cardinality constraints instead of sum
# TODO: collect math.ceil(float(table_size_dic[t]) / num_of_entries_per_table) into a dictionary

def gen_and_solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def,
                        table_act_dic, table_size_dic, action_alu_dic,
                        alu_dep_dic, 
                        pkt_alu_dic, tmp_alu_dic, state_alu_dic,
                        match_dep, action_dep, reverse_dep,
                        optimization):
    # Get the place where we need to newly allocate the alus
    used_alu = len(pkt_fields_def)
    
    z3_match_list = [Int('%s_M%s' % (t, i)) for t in table_size_dic for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table))]
    z3_alu_list = [Int('%s_M%s_%s_%s' % (t, i, action, alu)) for t in table_size_dic for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table))
    for action in table_act_dic[t] for alu in action_alu_dic[t][action]]
    # print(z3_match_list)
    # print(z3_alu_list)
    
    z3_table_loc_vec = []
    for j in range(num_of_stages):
        curr_list = []
        for t in table_size_dic:
            for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
                curr_list.append(Int('%s_M%s_stage%s' % (t, i, j)))
        z3_table_loc_vec.append(curr_list)
    print(z3_table_loc_vec)
    
    z3_alu_loc_vec = []
    for t in table_size_dic:
        for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
            for action in table_act_dic[t]:
                for alu in action_alu_dic[t][action]:
                    curr_list = []
                    for j in range(num_of_stages):
                        curr_list.append(Int('%s_M%s_%s_%s_stage%s' % (t, i, action, alu, j)))
                    z3_alu_loc_vec.append(curr_list)
    # print(z3_alu_loc_vec)
    
    # Constraint 0: all binary variable should be either 0 or 1
    binary_c = []
    for mem in z3_table_loc_vec:
        for v in mem:
            binary_c.append(And(v >= 0, v <= 1))
    for mem in z3_alu_loc_vec:
        for v in mem:
            binary_c.append(And(v >= 0, v <= 1))

    # Constraint 1: Match happens before any alus belonging to that table (DONE)
    match_then_action_c = []
    for table in alu_dep_dic:
        for i in range(math.ceil(float(table_size_dic[table]) / num_of_entries_per_table)):
            for action in table_act_dic[table]:
                for alu in action_alu_dic[table][action]:
                    for stage in range(num_of_stages):
                        match_then_action_c.append(Implies(Int('%s_M%s_%s_%s' % (table, i, action, alu)) == stage, Int('%s_M%s' % (table, i)) >= stage))
                        match_then_action_c.append(Implies(Int('%s_M%s_%s_%s' % (table, i, action, alu)) == stage, Int('%s_M%s_stage%s' % (table, i, stage)) == 1))
    # print(match_then_action_c)

    # Constraint 2: All stage numbers cannot be greater than total available stage (DONE)
    match_stage_c = [And(match_s >= 0, match_s < num_of_stages) for match_s in z3_match_list]
    alu_stage_c = [And(alu_s >= 0, alu_s < num_of_stages) for alu_s in z3_alu_list]

    # Constraint 3: alu-level dependency (DONE)
    alu_level_c = []
    for table in alu_dep_dic:
        for i in range(math.ceil(float(table_size_dic[table]) / num_of_entries_per_table)):
            for action in table_act_dic[table]:
                for pair in alu_dep_dic[table][action]:
                    alu1 = pair[0]
                    alu2 = pair[1]
                    alu_level_c.append(Int('%s_M%s_%s_%s' % (table, i, action, alu1)) < Int('%s_M%s_%s_%s' % (table, i, action, alu2)))
    # print(alu_level_c)

    # Constraint 4: No use more tables than available per stage (DONE)
    num_table_c = []
    for i in range(len(z3_table_loc_vec)):
        num_table_c.append(Sum(z3_table_loc_vec[i]) <= num_of_table_per_stage)
        for j in range(len(z3_table_loc_vec[i])):
            num_table_c.append(And(z3_table_loc_vec[i][j] >= 0, z3_table_loc_vec[i][j] <= 1))

    # Constraint 5: An ALU must be allocated to one and exactly one stage (DONE)
    alu_pos_rel_c = []
    for mem in z3_alu_loc_vec:
        alu_pos_rel_c.append(Sum(mem) == 1)
    for t in table_size_dic:
        for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
            for action in table_act_dic[t]:
                for alu in action_alu_dic[t][action]:
                    for j in range(num_of_stages):
                        alu_pos_rel_c.append(Implies(Int('%s_M%s_%s_%s_stage%s' % (t, i, action, alu, j))==1, Int('%s_M%s_%s_%s' % (t, i, action, alu))==j ))
                        alu_pos_rel_c.append(Implies(Int('%s_M%s_%s_%s' % (t, i, action, alu))==j, Int('%s_M%s_%s_%s_stage%s' % (t, i, action, alu, j))==1))
    # print(alu_pos_rel_c)

    tmp_state_field_loc_vec = []
    # Create beg and end for tmp and stateful
    for tmp_field in tmp_fields_def:
        tmp_l = []
        for i in range(num_of_stages):
            tmp_l.append(Int('%s_stage%s' % (tmp_field, i)))
        tmp_state_field_loc_vec.append(tmp_l)
        curr_beg = Int('%s_beg' % tmp_field)
        curr_end = Int('%s_end' % tmp_field)
        alu_pos_rel_c.append(And(curr_beg >= 0, curr_beg < num_of_stages, curr_end >= 0, curr_end < num_of_stages))
        for j in range(len(tmp_alu_dic[tmp_field])):
            mem = tmp_alu_dic[tmp_field][j]
            table = mem[0]
            action = mem[1]
            alu = mem[2]
            if j == 0:
                for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
                    alu_pos_rel_c.append(curr_beg == Int('%s_M%s_%s_%s' % (table, i, action, alu)))
                    alu_pos_rel_c.append(curr_beg + 1 <= curr_end)
            else:
                for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
                    alu_pos_rel_c.append(curr_end >= Int('%s_M%s_%s_%s' % (table, i, action, alu)))

    for tmp_field in tmp_fields_def:
        for i in range(num_of_stages):
            alu_pos_rel_c.append( If(
                And(Int('%s_beg' % tmp_field) <= i, i < Int('%s_end' % tmp_field)), Int('%s_stage%s' % (tmp_field, i)) == 1, Int('%s_stage%s' % (tmp_field, i)) == 0
                ))

    for state_var in stateful_var_def:
        tmp_l = []
        for i in range(num_of_stages):
            tmp_l.append(Int('%s_stage%s' % (state_var, i)))
        tmp_state_field_loc_vec.append(tmp_l)
        curr_beg = Int('%s_beg' % state_var)
        curr_end = Int('%s_end' % state_var)
        alu_pos_rel_c.append(And(curr_beg >= 0, curr_beg < num_of_stages, curr_end >= 0, curr_end < num_of_stages))
        for j in range(len(state_alu_dic[state_var])):
            mem = state_alu_dic[state_var][j]
            table = mem[0]
            action = mem[1]
            alu = mem[2]
            if j == 0:
                for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
                    alu_pos_rel_c.append(curr_beg == Int('%s_M%s_%s_%s' % (table, i, action, alu)))
                    alu_pos_rel_c.append(curr_beg + 1 <= curr_end)
            else:
                for i in range(math.ceil(float(table_size_dic[t]) / num_of_entries_per_table)):
                    alu_pos_rel_c.append(curr_end >= Int('%s_M%s_%s_%s' % (table, i, action, alu)))
    for state_var in stateful_var_def:
        for i in range(num_of_stages):
            alu_pos_rel_c.append( If(
                And(Int('%s_beg' % state_var) <= i, i < Int('%s_end' % state_var)), Int('%s_stage%s' % (state_var, i)) == 1, Int('%s_stage%s' % (state_var, i)) == 0
                ))

    for mem in tmp_state_field_loc_vec:
        for v in mem:
            binary_c.append(And(v >= 0, v <= 1))

    tmp_state_field_loc_vec_transpose = [[tmp_state_field_loc_vec[i][j] for i in range(len(tmp_state_field_loc_vec))] for j in range(len(tmp_state_field_loc_vec[0]))]
    for i in range(len(tmp_state_field_loc_vec_transpose)):
        alu_pos_rel_c.append(Sum(tmp_state_field_loc_vec_transpose[i]) <= (num_of_alus_per_stage - used_alu) )

    # Constraint 6: set a variable cost which is our objective function whose value is >= to any other vars (DONE)
    cost = Int('cost')
    cost_with_match_c = [And(cost >= m_v) for m_v in z3_match_list]
    cost_with_alu_c = [And(cost >= alu_v) for alu_v in z3_alu_list]

    # Constraint 6: table-level constraints for match, action, and reverse dep (DONE)
    table_dep_c = []
    for ele in match_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(math.ceil(float(table_size_dic[t1]) / num_of_entries_per_table)):
            for j in range(math.ceil(float(table_size_dic[t2]) / num_of_entries_per_table)):
                for act1 in table_act_dic[t1]:
                    for act2 in table_act_dic[t2]:
                        for alu1 in action_alu_dic[t1][act1]:
                            for alu2 in action_alu_dic[t2][act2]:
                                table_dep_c.append(And(Int('%s_M%s_%s_%s' % (t1, i, act1, alu1)) < Int('%s_M%s_%s_%s' % (t2, j, act2, alu2))))
    for ele in action_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(math.ceil(float(table_size_dic[t1]) / num_of_entries_per_table)):
            for j in range(math.ceil(float(table_size_dic[t2]) / num_of_entries_per_table)):
                for act1 in table_act_dic[t1]:
                    for act2 in table_act_dic[t2]:
                        for alu1 in action_alu_dic[t1][act1]:
                            for alu2 in action_alu_dic[t2][act2]:
                                table_dep_c.append(And(Int('%s_M%s_%s_%s' % (t1, i, act1, alu1)) < Int('%s_M%s_%s_%s' % (t2, j, act2, alu2))))
    for ele in reverse_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(math.ceil(float(table_size_dic[t1]) / num_of_entries_per_table)):
            for j in range(math.ceil(float(table_size_dic[t2]) / num_of_entries_per_table)):
                for act1 in table_act_dic[t1]:
                    for act2 in table_act_dic[t2]:
                        for alu1 in action_alu_dic[t1][act1]:
                            for alu2 in action_alu_dic[t2][act2]:
                                table_dep_c.append(And(Int('%s_M%s_%s_%s' % (t1, i, act1, alu1)) <= Int('%s_M%s_%s_%s' % (t2, j, act2, alu2))))

    # print("z3_match_list = ", z3_match_list)
    # print("z3_alu_list = ", z3_alu_list)
    # print("match_then_action_c", match_then_action_c)
    # print("alu_pos_rel_c", alu_pos_rel_c)
    # print("cost_with_alu_c = ", cost_with_alu_c)
    # print('alu_level_c =', alu_level_c)
    # print('match_dep_c = ', match_dep_c)
    # print('action_dep_c = ', action_dep_c)
    # print('cost_with_alu_c = ', cost_with_alu_c)
    print("Come here------------------------")
    set_option("parallel.enable", True)
    if optimization:
        opt = Optimize()
        # TODO: add a constraint as soon as we finish building one
        opt.add(binary_c +
            match_then_action_c + 
            match_stage_c + alu_stage_c +
            alu_level_c + 
            num_table_c + 
            alu_pos_rel_c + 
            cost_with_match_c + cost_with_alu_c +
            table_dep_c)
        opt.minimize(cost)
        print("Solving Optimization problem")
        if opt.check() == sat:
            print("Achieve a solution")
            for v in opt.model():
                if str(v).find('stage') == -1:
                    print(v, '=' ,opt.model()[v])
        else:
            print("No solution")
        
        # Output the obective function's value Ref:https://www.cs.tau.ac.il/~msagiv/courses/asv/z3py/guide-examples.htm
        print('objective function cost = %s (zero index)' % opt.model()[cost])
    else:
        print("Solving SAT problem")
        s = Solver()
        s.add(binary_c +
            match_then_action_c + 
            match_stage_c + alu_stage_c +
            alu_level_c + 
            num_table_c + 
            alu_pos_rel_c + 
            cost_with_match_c + cost_with_alu_c +
            table_dep_c)
        if s.check() == sat:
            print("Achieve a solution")
            for v in s.model():
                if str(v).find('stage') == -1:
                    print(v, '=', s.model()[v])
        else:
            print("No solution")
    
    # TODO: output the layout of ALU grid

def main(argv):
    """main program."""
    '''*****************test case 1: stateful_fw*****************'''
    '''
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2', 'pkt_3', 'pkt_4']
    tmp_fields_def = ['tmp_0','tmp1','tmp2','tmp3'] # all temporary variables
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
                    'tmp1':[['T1','A1','ALU6'],['T1','A1','ALU3'],['T1','A1','ALU7']],
                    'tmp2':[['T1','A1','ALU7'],['T1','A1','ALU5']],
                    'tmp3':[['T1','A1','ALU4'],['T1','A1','ALU5']]} #key: tmp packet fields, val: a list of list of size 3, [['table name', 'action name', 'alu name']]
    state_alu_dic = {'s0':[['T1','A1','ALU3'],['T1','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
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
    state_alu_dic = {'s0':[['T2','A1','ALU3'], ['T2','A1','ALU4']]} #key: packet field in def, val: a list of size 3, ['table name', 'action name', 'alu name'], the corresponding alu modifies the key stateful var
    match_dep = [['T1','T2']] #list of list, for each pari [T1, T2], T2 has match dependency on T1

    action_dep = [] #list of list, for each pari [T1, T2], T2 has action dependency on T1
    reverse_dep = [] #list of list, for each pari [T1, T2], T2 has reverse dependency on T1
    '''

    '''*****************test case 10: validate_outer_ipv4_packet + stateful_fw_T /home/xiangyug/benchmarks/switch_p4_benchmarks/test_benchmarks/benchmark2.txt*****************'''
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



    optimization = True
    gen_and_solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def,
                        table_act_dic, table_size_dic, action_alu_dic,
                        alu_dep_dic, 
                        pkt_alu_dic, tmp_alu_dic, state_alu_dic,
                        match_dep, action_dep, reverse_dep,
                        optimization)

if __name__ == "__main__":
        main(sys.argv)
