import sys
from z3 import *

def gen_and_solve_ILP(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, alu_dep_dic, table_list):
    # Get the match and alu list
    z3_match_list = [Int('%s_M' % t) for t in table_list]
    z3_alu_list = [Int('%s_A_%s' % (t, i)) for t in table_list for i in range(1, int(alu_dic[t]) + 1)]

    total_stage = 12
    # z3_alu_loc_vec is a list of 0/1 which specifies which stage this ALU is at
    z3_alu_loc_vec = [[Bool('%s_A_%s_stage_%s' % (t, i, k)) for k in range(total_stage)] for t in table_list for i in range(1, int(alu_dic[t]) + 1)]
    z3_alu_loc_vec_transpose = [[z3_alu_loc_vec[i][j] for i in range(len(z3_alu_loc_vec))] for j in range(len(z3_alu_loc_vec[0]))]
    # print(z3_alu_loc_vec)
    # print(z3_alu_loc_vec_transpose)
    # sys.exit(1)

    # Constraint 1: Match happens before any action 
    match_then_action_c = [(Int('%s_M' % t) <= Int('%s_A_%s' % (t, i))) for t in table_list for i in range(1, int(alu_dic[t]) + 1)]

    # Constraint 2: All stage numbers cannot be greater than total available stage
    # TODO: set the total available stage as the parameter
    # For now, we just assume the total available stages is 12
    match_stage_c = [And(match_s >= 0, match_s < total_stage) for match_s in z3_match_list]
    alu_stage_c = [And(alu_s >= 0, alu_s < total_stage) for alu_s in z3_alu_list]

    # TODO: set the total number of available ALUs per stage to be a parameter
    # For now, we just assume the total available ALUs per stage is 2
    avail_alu = 200

    # Constraint 3: alu-level dependency
    alu_level_c = []
    for key in alu_dep_dic:
        for pair in alu_dep_dic[key]:
            alu_level_c.append((Int('%s_A_%s' % (key, pair[0])) < Int('%s_A_%s' % (key, pair[1]))))

    # Constraint 4: An ALU must be allocated to one and exactly one block
    alu_pos_rel_c1 = [Implies(z3_alu_list[i] == k,
                         z3_alu_loc_vec[i][k] == True) 
                for k in range(total_stage) for i in range(len(z3_alu_list))]
    alu_pos_rel_c2 = [Implies(z3_alu_loc_vec[i][k] == True,
                         z3_alu_list[i] == k)
                for k in range(total_stage) for i in range(len(z3_alu_list))]
    # alu_pos_val_c = [And(z3_alu_loc_vec[i][j] >= 0) for i in range(len(z3_alu_loc_vec)) for j in range(len(z3_alu_loc_vec[0]))]
    # alu_row_sum_c = [Sum(z3_alu_loc_vec[i]) == 1 for i in range(len(z3_alu_loc_vec))]
    alu_col_sum_c = [Sum([If(z3_alu_loc_vec_transpose[i][j], 1, 0) for j in range(len(z3_alu_loc_vec_transpose[0]))]) <= avail_alu for i in range(len(z3_alu_loc_vec_transpose))]

    # Constraint 5: set a variable cost which is our objective function whose value is >= to any other vars
    cost = Int('cost')
    cost_with_match_c = [(cost >= m_v) for m_v in z3_match_list]
    cost_with_alu_c = [(cost >= alu_v) for alu_v in z3_alu_list]

    # Constraint 6: constraints for match, action, successor and reverse dep
    match_dep_c = []
    for ele in match_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(1, int(alu_dic[t1]) + 1):
            match_dep_c.append((Int('%s_A_%s' % (t1, i)) < Int('%s_M' % t2)))
    action_dep_c = []
    for ele in action_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(1, int(alu_dic[t1]) + 1):
            for j in range(1, int(alu_dic[t2]) + 1):
                action_dep_c.append((Int('%s_A_%s' % (t1, i)) < Int('%s_A_%s' % (t2, j))))
    successor_dep_c = []
    reverse_dep_c = []

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
            alu_pos_rel_c1 + alu_pos_rel_c2 + alu_col_sum_c +
            cost_with_match_c + cost_with_alu_c + 
            match_dep_c + action_dep_c + successor_dep_c + reverse_dep_c)
    h = opt.minimize(cost)
    print(opt.check())
    print(opt.model())
    # Output the obective function's value Ref:https://www.cs.tau.ac.il/~msagiv/courses/asv/z3py/guide-examples.htm
    print('objective function cost = %s' % opt.model()[cost])
    # TODO: output the layout of ALU grid

def main(argv):
    """main program."""
    """Format: python3 ILP_constrain.py <filename>"""
    if len(argv) != 2:
        print("Usage: python3 " + argv[0] + " <Dep+Act filename>")
        sys.exit(1)
    filename = argv[1]
    f = open(filename, "r")
    table_list = []
    match_dep = []
    action_dep = []
    successor_dep = []
    reverse_dep = []
    alu_dic = {} # key: table name; val: total number of alus
    alu_dep_dic = {} # key: table name; val: list of alu dep
    while 1:
        line = f.readline()
        if line: 
            # Remove the last '\n'
            line = line[:-1]
            print(line)
            if line == "Table Info:":
                # Get Table Info
                while 1:
                    line = f.readline()
                    line = line[:-1]
                    if line == "Dep Info:":
                        break
                    table_list.append(line)
            # Get Dep Info
            while 1:
                line = f.readline()
                line = line[:-1]
                if line == "Action Info:":
                    break
                sen_list = line.split()
                # Format: T1 has Match dependency relationship with T2
                table1 = sen_list[0]
                table2 = sen_list[-1]
                dep_type = sen_list[2]
                if dep_type == 'Match':
                    match_dep.append([table1, table2])
                elif dep_type == 'Action':
                    action_dep.append([table1, table2])
                elif dep_type == 'Successor':
                    successor_dep.append([table1, table2])
                else:
                    assert dep_type == 'Reverse', "Unrecongnizable dependency type"
                    reverse_dep.append([table1, table2])
            # Get Act Info
            while 1:
                line = f.readline()
                if line:
                    # Format: T1:5,(1,2),(1,3),(2,4),(3,5)
                    line = line[:-1]
                    table_name = line.split(':')[0]
                    line = line.split(':')[1]
                    print("line = ", line)
                    alu_num = line.split(';')[0]
                    alu_dic[table_name] = alu_num
                    # No alu-level dep if there is only one alu
                    if line.split(';')[1] == '':
                        continue
                    alu_dep_list = line.split(';')
                    for i in range(1, len(alu_dep_list)):
                        pair = alu_dep_list[i]
                        # pair is in the format: (1,2)
                        pair = pair[1:]
                        pair = pair[:-1]
                        node1 = pair.split(',')[0]
                        node2 = pair.split(',')[1]
                        if alu_dep_dic.get(table_name) == None:
                            alu_dep_dic[table_name] = []
                        alu_dep_dic[table_name].append([node1, node2])
                else:
                    break
        else:
            break
    print("alu_dic = ", alu_dic)
    # Example output: alu_dic =  {'T1': '5'}
    print("alu_dep_dic = ", alu_dep_dic)
    # Example output: alu_dep_dic =  {'T1': [['1', '2'], ['1', '3'], ['2', '4'], ['3', '5']]
    print("table_list = ", table_list)
    # Generate ILP input with format 
    gen_and_solve_ILP(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, alu_dep_dic, table_list)

if __name__ == "__main__":
        main(sys.argv)
