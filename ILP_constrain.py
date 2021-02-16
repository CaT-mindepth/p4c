import sys

def generate_ILP_input(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, table_list):
    '''
    Format input:
    ---------------
    Variables:
    x
    y
    z
    Constraints:
    x > 10
    y == x + 2
    z <= 20
    ---------------
    '''
    output_str = ""
    # Generate Variables:
    output_str += "Variables:\n"
    # Generate Match part
    for t in table_list:
        output_str += t + "_M\n"
    # Generate Action part
    # TODO: support multiple actions
    # TODO: consider the case where match is spread into multiple stages
    for key in alu_dic:
        print(key)
        stage = -1
        for alu in alu_dic[key]:
            stage += 1
            for i in range(int(alu)):
                output_str += key + "_A_" + str(stage) + "_" + str(i) + "\n"
    # Generate common constraints for match and action (Match < Action)
    output_str += "Constraints:\n"
    for key in alu_dic:
        stage = -1
        for alu in alu_dic[key]:
            stage += 1
            for i in range(int(alu)):
                alu_name = key + "_A_" + str(stage) + "_" + str(i)
                match_name = key + "_M";
                output_str += match_name + " <= " + alu_name + "\n"
                output_str += match_name + " >= 0\n"
    # Generate constraints for dep:
    for ele in match_dep:
        t1 = ele[0]
        t2 = ele[1]
        stage = -1
        for alu in alu_dic[t1]:
            stage += 1
            for i in range(int(alu)):
                output_str += t1 + "_A_" + str(stage) + "_" + str(i) + " < " + t2 + "_M\n"
    # TODO: other kinds of dep
    # Generate constraints within actions
    for key in alu_dic:
        stage = 0
        if len(alu_dic[key]) == 1:
            continue
        else:
            for i in range(len(alu_dic[key]) - 1):
                # Gen pre_alu_list
                pre_alu_list = []
                for j in range(int(alu_dic[key][i])):
                    pre_alu_list.append(key + "_A_" + str(stage + i) + "_" + str(j))
                # Gen aft_alu_list
                aft_alu_list = []
                for j in range(int(alu_dic[key][i + 1])):
                    aft_alu_list.append(key + "_A_" + str(stage + i + 1) + "_" + str(j))
                for pre_alu in pre_alu_list:
                    for aft_alu in aft_alu_list:
                        output_str += pre_alu + " <= " + aft_alu + "\n"
    return output_str

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
    alu_dic = {} # key: table name; val: alu per stage
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
                    # Format: T1:1,2
                    line = line[:-1]
                    table_name = line.split(':')[0]
                    line = line.split(':')[1]
                    alu_num_list = line.split(',')
                    alu_dic[table_name] = alu_num_list
                else:
                    break
        else:
            break
    print("match_dep = ", match_dep)
    print("alu_dic = ", alu_dic)
    print("table_list = ", table_list)
    # Generate ILP input with format
    str_gen = generate_ILP_input(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, table_list)
    print("str_gen = ", str_gen)
if __name__ == "__main__":
        main(sys.argv)
