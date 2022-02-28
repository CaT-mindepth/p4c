import gurobipy as gp
from gurobipy import GRB

m = gp.Model("ILP")
cost = m.addVar(name='cost', vtype=GRB.INTEGER)
cost1 = m.addVar(name='cost1', vtype=GRB.INTEGER)
cost2 = m.addVar(name='cost2', vtype=GRB.INTEGER)

m.addConstr(cost1 <= cost2)
m.addConstr(cost2 <= cost)
m.addConstr(cost1 <= cost)
m.addConstr(0 <= cost2)
m.addConstr(0 <= cost1)
m.addConstr((cost == 0) >> (cost1 - cost2 >= 2))
m.setObjective(cost, GRB.MINIMIZE)
m.optimize()
print(cost)
print(m)
