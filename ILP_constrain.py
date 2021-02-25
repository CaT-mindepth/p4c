import sys

def generate_ILP_input(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, alu_dep_dic, table_list):
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
        for i in range(1, int(alu_dic[key]) + 1):
            output_str += key + "_A_" + str(i) + "\n"
    # Generate common constraints for match and action (Match < Action)
    output_str += "Constraints:\n"
    for key in alu_dic:
        for i in range(1, int(alu_dic[key]) + 1):
            alu_name = key + "_A_" + str(i)
            match_name = key + "_M";
            output_str += match_name + " <= " + alu_name + "\n"
            output_str += match_name + " >= 0\n"
    # Generate constraints for dep:
    for ele in match_dep:
        t1 = ele[0]
        t2 = ele[1]
        for i in range(1, int(alu_dic[t1]) + 1):
            output_str += t1 + "_A_" + str(i) + " < " + t2 + "_M\n"
    for ele in action_dep:
        t1 = ele[0]
        t2 = ele[1]
        t1_alu = []
        for i in range(1, int(alu_dic[t1]) + 1):
            t1_alu.append(t1 + "_A_" + str(i))
        t2_alu = []
        for i in range(1, int(alu_dic[t2]) + 1):
            t2_alu.append(t2 + "_A_" + str(i))
        for alu1 in t1_alu:
            for alu2 in t2_alu:
                output_str += alu1 + " < " + alu2 + "\n"
    # TODO: other kinds of dep

    # Generate constraints within actions
    for key in alu_dep_dic:
        # alu_dep_dic =  {'T1': [{'1', '2'}, {'1', '3'}, {'2', '4'}, {'5', '3'}]}
        for pair in alu_dep_dic[key]:
            node1 = pair[0]
            node2 = pair[1]
            alu1 = key + '_A_' + node1
            alu2 = key + '_A_' + node2
            output_str += alu1 + ' < ' + alu2 + '\n'
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
    print("match_dep = ", match_dep)
    print("alu_dic = ", alu_dic)
    # Example output: alu_dic =  {'T1': '5'}
    print("alu_dep_dic = ", alu_dep_dic)
    # Example output: alu_dep_dic =  {'T1': [['1', '2'], ['1', '3'], ['2', '4'], ['3', '5']]
    print("table_list = ", table_list)
    # Generate ILP input with format
    str_gen = generate_ILP_input(match_dep, action_dep, successor_dep, reverse_dep, alu_dic, alu_dep_dic, table_list)
    f = open("/tmp/ILP.txt", "w")
    f.write(str_gen)
    f.close()
    print("str_gen = ", str_gen)
if __name__ == "__main__":
        main(sys.argv)
