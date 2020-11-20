import z3

z3_slv = z3.Solver()
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
filename = "/tmp/ILP.txt"
f = open(filename,"r")


while 1:
    l = f.readline()
    if l == "Variables:\n":
        while 1:
            l = f.readline()
            if l == "Constraints:\n":
                break
            # remove /n from this string
            l = l[:-1]
            # Ref website:https://www.programiz.com/python-programming/methods/built-in/exec
            exec(l+'=z3.Int(\'%s\')'%l)
    elif l:           
        # Ref website: 
        z3_slv.add(eval(l))
    else:
        break
print(z3_slv.check())
print(z3_slv.model())
