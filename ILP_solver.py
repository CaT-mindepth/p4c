import z3
import sys

def main(argv):
    """main program."""
    if len(argv) >= 3:
        print("Usage: python3 " + argv[0] + " <ILP filename>(optional)")
    z3_slv = z3.Optimize()
    # Input file containing variables and constraints
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
    # cost is our objective func
    cost = z3.Int("cost")
    if len(argv) == 2:
        filename = argv[1]
    else:
        filename = "/tmp/ILP.txt"
    f = open(filename,"r")
    
    var_list = [] 
    while 1:
        l = f.readline()
        if l == "Variables:\n":
            while 1:
                l = f.readline()
                if l == "Constraints:\n":
                    break
                # remove /n from this string
                l = l[:-1]
                var_list.append(l)
                # Ref website:https://www.programiz.com/python-programming/methods/built-in/exec
                exec(l+'=z3.Int(\'%s\')'%l)
        elif l:           
            # Ref website: 
            z3_slv.add(eval(l))
        else:
            break
    for v in var_list:
        z3_slv.add(eval("cost >= " + v))
    h = z3_slv.minimize(cost)
    print(z3_slv.check())
    print(z3_slv.lower(h))
    print(z3_slv.model())

if __name__ == "__main__":
    main(sys.argv)
