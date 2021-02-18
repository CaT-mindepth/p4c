import sys
import random

def main(argv):
    # TODO: check argv length
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
    # length is from [1, 10]
    # width is from [1,5]
    # TODO: make them into parameter
    for i in range(1, table_num + 1):
        stage = random.randint(1, 10)
        output_str += "T" + str(i) + ":"
        for j in range(stage):
            alu_num = random.randint(1,5)
            output_str += str(alu_num)
            if j == stage - 1:
                output_str += "\n"
            else:
                output_str += ","
    print(output_str)

if __name__ == "__main__":
    main(sys.argv)
