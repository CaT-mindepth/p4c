import sys
import random

def main(argv):
    # check argv length
    """main program"""
    """Format: python3 ILP_Info_gen.py <Table num>"""
    if len(argv) != 2:
        print("Usage: python3 ILP_Info_gen.py <Table num>")
        sys.exit(1)
    table_num = int(argv[1])
    output_str = "Table Info:\n"
    for i in range(1, table_num + 1):
        output_str += "T" + str(i) + "\n"
    output_str += "Dep Info:\n"

    # random num = 0 is match dep
    # random num = 1 is action dep
    # others no dep
    for i in range(1, table_num):
        dep_rand = random.randint(0,9)
        t1 = "T" + str(i)
        t2 = "T" + str(i + 1)
        if dep_rand == 0:
            output_str += t1 + " has Match dependency relationship with " + t2 + "\n"
        elif dep_rand == 1:
            output_str += t1 + " has Action dependency relationship with " + t2 + "\n"

    output_str += "Action Info:\n"
    # alu_num is from [1, 10]
    # posibility that a pair has dependency is 0.1 
    # TODO: make them into parameter
    # Format: T2:5;(1,2);(1,3);(2,4);(3,5)
    for i in range(1, table_num + 1):
        output_str += "T" + str(i) + ":"
        alu_num = random.randint(1,10)
        output_str += str(alu_num) + ";"
        add_flag = 0
        for j in range(1, alu_num + 1):
            for k in range(j + 1, alu_num + 1):
                alu_dep_rand = random.randint(0,9)
                if alu_dep_rand == 0:
                    output_str += "(" + str(j) + "," + str(k) + ");"
                    add_flag = 1
        if output_str[-1] == ";" and add_flag == 1:
            output_str = output_str[:-1]
            output_str += "\n"
        elif i != table_num:
            output_str += "\n"
    print(output_str)

if __name__ == "__main__":
    main(sys.argv)
