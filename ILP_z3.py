import sys

from z3 import *
import math

num_of_entries_per_table = 256
num_of_alus_per_stage = 5
num_of_table_per_stage = 8
num_of_stages = 5

def gen_and_solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def,
                        table_act_dic, table_size_dic, action_alu_dic,
                        alu_dep_dic, 
                        pkt_alu_dic, tmp_alu_dic, state_alu_dic,
                        match_dep, action_dep, reverse_dep):
    # Get the place where we need to newly allocate the alus
    used_alu = len(pkt_fields_def)
    tmp_alu = []
    for tmp_field in tmp_fields_def:
        curr_list = []
        for i in range(num_of_stages):
            curr_list.append(Int('%s_stage%s' % (tmp_field, i)))
        tmp_alu.append(curr_list)
    for state_var in stateful_var_def:
        curr_list = []
        for i in range(num_of_stages):
            curr_list.append(Int('%s_stage%s' % (state_var, i)))
        tmp_alu.append(curr_list)
    print(tmp_alu)
    sys.exit(0)
    # Get the match and alu list
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
    # print(z3_table_loc_vec)
    '''
    # z3_alu_loc_vec is a list of 0/1 which specifies which stage this ALU is at
    z3_alu_loc_vec = [[Int('%s_A_%s_stage_%s' % (t, i, k)) for k in range(total_stage)] for t in table_list for i in range(1, int(alu_dic[t]) + 1)]
    z3_alu_loc_vec_transpose = [[z3_alu_loc_vec[i][j] for i in range(len(z3_alu_loc_vec))] for j in range(len(z3_alu_loc_vec[0]))]
    # print(z3_alu_loc_vec)
    # print(z3_alu_loc_vec_transpose)
    # sys.exit(1)
    '''
    # Constraint 1: Match happens before any action (DONE)
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
                    alu_level_c.append(And(Int('%s_M%s_%s_%s' % (table, i, action, alu1)) < Int('%s_M%s_%s_%s' % (table, i, action, alu2))))
    print(alu_level_c)
    sys.exit(0)

    # Constraint 4: No use more tables than available per stage (DONE)
    num_table_c = []
    for i in range(len(z3_table_loc_vec)):
        num_table_c.append(Sum(z3_table_loc_vec[i]) <= num_of_table_per_stage)
        for j in range(len(z3_table_loc_vec[i])):
            num_table_c.append(And(z3_table_loc_vec[i][j] >= 0, z3_table_loc_vec[i][j] <= 1))

    # Constraint 4: An ALU must be allocated to one and exactly one block
    alu_pos_rel_c = []
    for i in range(len(z3_alu_list)):
        for k in range(total_stage):
            alu_pos_rel_c.append(Implies(z3_alu_list[i] == k, z3_alu_loc_vec[i][k] == 1))

    alu_pos_val_c = [(z3_alu_loc_vec[i][j] >= 0) for i in range(len(z3_alu_loc_vec)) for j in range(len(z3_alu_loc_vec[0]))]
    alu_row_sum_c = [Sum(z3_alu_loc_vec[i]) == 1 for i in range(len(z3_alu_loc_vec))]
    alu_col_sum_c = [Sum(z3_alu_loc_vec_transpose[i]) <= avail_alu for i in range(len(z3_alu_loc_vec_transpose))]

    # Constraint 5: set a variable cost which is our objective function whose value is >= to any other vars (DONE)
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
    opt = Optimize()
    opt.add(match_then_action_c + 
            match_stage_c + alu_stage_c +
            alu_level_c + 
            alu_pos_rel_c + alu_pos_val_c + alu_row_sum_c + alu_col_sum_c +
            cost_with_match_c + cost_with_alu_c + 
            table_dep_c)
    h = opt.minimize(cost)
    print(opt.check())
    print(opt.model())
    # Output the obective function's value Ref:https://www.cs.tau.ac.il/~msagiv/courses/asv/z3py/guide-examples.htm
    print('objective function cost = %s' % opt.model()[cost])
    # TODO: output the layout of ALU grid

def main(argv):
    """main program."""
    pkt_fields_def = ['pkt_0', 'pkt_1', 'pkt_2'] # all packet fields
    tmp_fields_def = ['tmp_0'] # all temporary variables
    stateful_var_def = ['s0','s1'] # all stateful variables

    table_act_dic = {'T1':['A1']} # key: table name, val: list of actions
    table_size_dic = {'T1':257} #key: table name, val: table size
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
    
    gen_and_solve_ILP(pkt_fields_def, tmp_fields_def, stateful_var_def,
                        table_act_dic, table_size_dic, action_alu_dic,
                        alu_dep_dic, 
                        pkt_alu_dic, tmp_alu_dic, state_alu_dic,
                        match_dep, action_dep, reverse_dep)

if __name__ == "__main__":
        main(sys.argv)
