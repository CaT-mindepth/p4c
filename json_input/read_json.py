import sys

import math

import json

import gurobipy as gp
from gurobipy import GRB

num_of_entries_per_table = 256
num_of_alus_per_stage = 64
num_of_table_per_stage = 8
num_of_stages = 12
global_cnt = 0


def solve_ILP(table_match_dic, match_action_unit_dic, alu_dependency_dic, table_dependency_dic, must_allocate_alu, alu_peer_list):
    # get all match variables
    match_component_list = match_action_unit_dic.keys()

    match_component_var = []
    alu_components_list = []

    alu_dic = {} # key: alu name, val: which stage it is allocated
    not_alu_dic = {} # key: alu name, val: which stage it is allocated

    for mem in match_action_unit_dic:
        for alu in match_action_unit_dic[mem]:
            if alu not in alu_components_list:
                alu_components_list.append(alu)
    print(alu_components_list)
    alu_components_var = []

    # Create a new model
    m = gp.Model("ILP")
    
    # Add variables
    for var in match_component_list:
        match_component_var.append(m.addVar(name="%s" % var, vtype=GRB.INTEGER))
    for var in alu_components_list:
        alu_components_var.append(m.addVar(name="%s" % var, vtype=GRB.INTEGER))
    
    # Add objective function variable
    cost = m.addVar(name='cost', vtype=GRB.INTEGER)

    # Add prelimianry constraints >=0
    for var in match_component_var:
        m.addConstr(var >= 0)
        m.addConstr(cost >= var)
    for var in alu_components_var:
        m.addConstr(var >= 0)
        m.addConstr(cost >= var)

    '''it is necessary to update model before later processing
    ref: https://support.gurobi.com/hc/en-us/community/posts/360059768191-GurobiError-No-variable-names-available-to-index
    '''
    m.update()

    # Add ALU level dependency
    for mem in alu_dependency_dic:
        dependent_alu_l = alu_dependency_dic[mem]
        for alu in dependent_alu_l:
            v1 = m.getVarByName("%s" % mem)
            v2 = m.getVarByName("%s" % alu)
            # Gurobi does not support "a < b" and so we replace it by "a <= b - 1"
            m.addConstr(v1 <= v2 - 1)

    # Add table level dependency
    for table1 in table_dependency_dic:
        for table2 in table_dependency_dic[table1]:
            for m_table1 in table_match_dic[table1]:
                for alu_table1 in match_action_unit_dic[m_table1]:
                    for m_table2 in table_match_dic[table2]:
                        for alu_table2 in match_action_unit_dic[m_table2]:
                            v1 = m.getVarByName("%s" % alu_table1)
                            v2 = m.getVarByName("%s" % alu_table2)
                            m.addConstr(v1 <= v2 - 1)
    # Add alu allocation constraints TODO figure out when two ALU can merge into one
    alu_loc_var_vec = [] # for each alu, it has 12 variables
    for var in alu_components_list:
        tmp_list = []
        for i in range(num_of_stages):
            tmp_list.append(m.addVar(name="%s_stage_%s" % (var, i),vtype=GRB.BINARY))
        if var in must_allocate_alu:
            alu_dic[var] = tmp_list
        else:
            not_alu_dic[var] = tmp_list
        alu_loc_var_vec.append(tmp_list)
    # print("not_alu_dic:", not_alu_dic)
    # print("alu_dic:", alu_dic)
    # ALU must be allocated to one place
    for var in alu_dic:
        m.addConstr(sum(alu_dic[var]) == 1)
    # Add sequence between all alus in alu_peer_list
    for mem in alu_peer_list:
        for i in range(1, len(mem)):
            v1 = m.getVarByName("%s" % mem[i - 1])
            v2 = m.getVarByName("%s" % mem[i])
            m.addConstr(v1 <= v2)
            # print("v2 =", v2)
            # print("mem[i] =", mem[i])

            global global_cnt
            new_var = m.addVar(name='x%s' % global_cnt, vtype=GRB.INTEGER)
            global_cnt += 1
            m.update()
            m.addGenConstrIndicator(new_var, True, v2 - v1 == 0)
            m.addConstr((new_var == 1) >> (sum(not_alu_dic[mem[i]]) == 0))
            m.addConstr((new_var == 0) >> (sum(not_alu_dic[mem[i]]) == 1))
            # m.addConstr((sum(not_alu_dic[mem[i]]) == 1) >> (v2 >= v1 + 1))
            # if mem[i] in not_alu_dic:
            #     m.addConstr(sum(not_alu_dic[mem[i]]) == 1)

    alu_loc_var_vec_transpose = [[alu_loc_var_vec[i][j] for i in range(len(alu_loc_var_vec))] for j in range(len(alu_loc_var_vec[0]))]
    for i in range(len(alu_loc_var_vec_transpose)):
        m.addConstr(sum(alu_loc_var_vec_transpose[i]) <= num_of_alus_per_stage)

    # Match allocation constraints
    match_loc_var_vec = []
    for var in match_component_list:
        tmp_list = []
        for i in range(num_of_stages):
            tmp_list.append(m.addVar(name="%s_stage_%s" % (var, i),vtype=GRB.BINARY))
        match_loc_var_vec.append(tmp_list)
    m.update()
    
    for alu in alu_components_list:
        for mem in match_action_unit_dic:
            if alu in match_action_unit_dic[mem]:
                alu_v = m.getVarByName("%s" % alu)
                mem_v = m.getVarByName("%s" % mem)
                for i in range(num_of_stages):
                    v1 = m.getVarByName("%s_stage_%s" % (alu, i))
                    v2 = m.getVarByName("%s_stage_%s" % (mem, i))
                    m.addConstr((v1 == 1) >> (v2 == 1))
                    m.addConstr((v1 == 1) >> (alu_v == i))
                    m.addConstr((v2 == 1) >> (mem_v >= i))
    for i in range(len(match_loc_var_vec)):
        m.addConstr(sum(match_loc_var_vec[i]) >= 1)
    # guarantee # of tables per stage is smaller than num_of_table_per_stage
    match_loc_var_vec_transpose = [[match_loc_var_vec[i][j] for i in range(len(match_loc_var_vec))] for j in range(len(match_loc_var_vec[0]))]
    for i in range(len(match_loc_var_vec_transpose)):
        m.addConstr(sum(match_loc_var_vec_transpose[i]) <= num_of_table_per_stage)


    m.setObjective(cost, GRB.MINIMIZE)
    m.optimize()
    # output the model solution
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


'''generate a dictionary showing the relation between table name and match components'''
def gen_table_match(table_info_list):
    ret_dic = {}
    for mem in table_info_list:
        table_name = mem["name"]
        match_size = mem["size"]
        match_component = math.ceil(match_size / num_of_entries_per_table)
        ret_dic[table_name] = []
        for i in range(match_component):
            ret_dic[table_name].append(table_name+"_M"+str(i))
    return ret_dic

'''generate a dictionary showing the table dependency'''
def get_tbl_dependency(table_dep_list):
    ret_dic = {}
    for mem in table_dep_list:
        key_table = mem[0]
        dep_table = mem[1]
        if key_table not in ret_dic:
            ret_dic[key_table] = [dep_table]
        else:
            ret_dic[key_table].append(dep_table)
    return ret_dic

'''generate a dictionary showing which match entry has which ALUs'''
def gen_match_action(table_info_list, table_match_dic):
    ret_dic = {}
    for mem in table_info_list:
        table_name = mem["name"]
        alu_number = mem["alu_num"]
        for match_component in table_match_dic[table_name]:
            ret_dic[match_component] = []
            for i in range(alu_number):
                ret_dic[match_component].append(match_component+"_ALU_"+str(i))
    return ret_dic

'''generate a dictionary showing which ALU is dependent on which ALUs'''
def gen_alu_dep(table_info_list, table_match_dic, match_action_unit_dic):
    ret_dic = {}
    for mem in table_info_list:
        table_name = mem["name"]
        alu_dep_list = mem["alu_dep"]
        for dep_l in alu_dep_list:
            alu1 = dep_l[0]
            alu2 = dep_l[1]
            for match_component in table_match_dic[table_name]:
                alu1_name = match_component + "_ALU_" + str(alu1)
                alu2_name = match_component + "_ALU_" + str(alu2)
                assert alu1_name in match_action_unit_dic[match_component], "wrong alu"
                assert alu2_name in match_action_unit_dic[match_component], "wrong alu"
                if alu1_name not in ret_dic:
                    ret_dic[alu1_name] = []
                ret_dic[alu1_name].append(alu2_name)
    return ret_dic

def gen_peer_alu(table_match_dic, match_action_unit_dic):
    ret_l = []
    for table in table_match_dic:
        if len(table_match_dic[table]) > 1:
            num_of_alu = len(match_action_unit_dic[table_match_dic[table][0]])
            for j in range(num_of_alu):
                tmp_l = []
                for i in range(len(table_match_dic[table])):
                    tmp_l.append(table_match_dic[table][i]+"_ALU_"+str(j))
                ret_l.append(tmp_l)
    return ret_l

def main(argv):
    filename = 'table_info.json'
    f = open(filename, 'r')
    contents = f.read()
    # collect the information in json file
    table_info = json.loads(contents)
    # Generate variables
    # TODO: get table information from table_info["tables"]
    table_match_dic = {} # key: table name; value: list of match part
    table_match_dic = gen_table_match(table_info["tables"])
    print("table_match_dic =", table_match_dic)

    match_action_unit_dic = {} # key: match name; value: list of ALUs
    match_action_unit_dic = gen_match_action(table_info["tables"], table_match_dic)
    print("match_action_unit_dic =", match_action_unit_dic)

    alu_dependency_dic = {} # key: alu name; value: list of ALUs dependent on the key
    alu_dependency_dic = gen_alu_dep(table_info["tables"], table_match_dic, match_action_unit_dic,)
    print("alu_dependency_dic =", alu_dependency_dic)

    table_dependency_dic = {} # key: table name; value: list of tables dependent on the key
    # Generate table dependency dic focus on table_info['table_dep']
    table_dependency_dic = get_tbl_dependency(table_info['table_dep'])
    print("table_dependency_dic =", table_dependency_dic)
    
    alu_peer_list = []
    alu_peer_list = gen_peer_alu(table_match_dic, match_action_unit_dic)
    print("alu_peer_list =", alu_peer_list)

    must_allocate_alu = []
    must_allocate_match = []
    for mem in table_match_dic:
        must_allocate_match.append(table_match_dic[mem][0])
    for mem in must_allocate_match:
        for alu in match_action_unit_dic[mem]:
            must_allocate_alu.append(alu)
    print("must_allocate_alu =", must_allocate_alu)
    solve_ILP(table_match_dic, match_action_unit_dic, alu_dependency_dic, table_dependency_dic, must_allocate_alu, alu_peer_list)
if __name__ == '__main__':
    main(sys.argv)