import gurobipy as gp
from gurobipy import GRB

global_cnt = 0

m = gp.Model("ILP")
cost = m.addVar(name='cost', vtype=GRB.INTEGER)
cost1 = m.addVar(name='cost1', vtype=GRB.INTEGER)
cost2 = m.addVar(name='cost2', vtype=GRB.INTEGER)

m.addConstr(cost >= cost1)
m.addConstr(cost >= cost2)

m.addConstr(cost1 <= cost2)
m.addConstr(cost1 == 1)
m.addConstr(cost2 == 10)
tmp_l = []
for i in range(12):
    tmp_l.append(m.addVar(name="stage_%s" % i,vtype=GRB.BINARY))

m.update()
# new_var = m.addVar(name='x%s' % global_cnt, vtype=GRB.INTEGER)
# m.addGenConstrIndicator(new_var, True, cost1 <= 5)
# m.addGenConstrIndicator(new_var, False, cost1 >= 6)
for i in range(12):
    new_var = m.addVar(name='x%s' % global_cnt, vtype=GRB.INTEGER)
    global_cnt += 1
    stage_var = m.getVarByName("stage_%s" % i)
    m.addGenConstrIndicator(new_var, True, cost1 <= i)
    m.addGenConstrIndicator(new_var, False, cost1 >= i + 1)
    new_var1 = m.addVar(name='x%s' % global_cnt, vtype=GRB.INTEGER)
    m.addGenConstrIndicator(new_var1, True, cost2 >= i)
    m.addGenConstrIndicator(new_var1, False, cost2 <= i - 1)
    m.addConstr(stage_var == new_var1 * new_var)

m.setObjective(cost, GRB.MINIMIZE)
m.optimize()
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
# print(m)
