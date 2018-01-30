# -*- coding: utf-8 -*-
# Matlab Like...  
import numpy as np
# Import Pulp...
from pulp import *
###############################################################################
# Inputs
NumberOfChildren = 4
# Horizon
H = 20
# Initial Input Inventory
RI_Current = np.ceil(5 * np.random.rand(NumberOfChildren)).astype(int)
# Initial Output Inventory
RO_Current = np.ceil(5 * np.random.rand(1)).astype(int)
# Thetas (tunable)
thetas = 5 * np.random.rand(H)
# Stock Cost per Unit
KO = 5 * np.random.rand(1)
# Input cost per unit per part
KI = 3 * np.random.rand(NumberOfChildren)
# Capacity (assume same for all days)
C = 10
# Quantities
Q = np.ceil(3 * np.random.rand(NumberOfChildren)).astype(int)
# Demand from DOWNSTREAM
#D = np.ceil(5 * np.random.rand(H)).astype(int)
D = np.zeros((H))
# Parts from UPSTREAM
S = np.ceil(10 * np.random.rand(NumberOfChildren, H)).astype(int)
S[:, 0:2] = 0
# Plot to get an idea...
print('\n===========================================================\n')
#print('Current RI:\n', RI_Current)
#print('Current RO:\n', RO_Current)
#print('Thetas:\n', thetas)
#print('Stock Cost per Unit (KO):\n', KO)
#print('Input Cost per Unit (per Part):\n', KI)
#print('Demand from Downstream:\n', D)
#print('Per Day Production Capacity:\n', C)
#print('Part Quantities Required per Product:\n', Q)
#print('Parts from Ustream:\n', S)
#print('')
###############################################################################
# Create problem (object)
prob = LpProblem("Production Plan Optimization", LpMinimize)
###############################################################################
# Define decision variables
RI_Vars = list()
RO_Vars = list()
X_Vars = list()
U_Vars = list()
for t in range(H):
    RI_Vars.append(list())
    for p in range(NumberOfChildren):
        RI_Vars[t].append(LpVariable("InputInventory_%s_%s" %(t, p), 0, None, LpInteger))
    RO_Vars.append(LpVariable("OutputInventory_%s" %t, 0, None, LpInteger))
    X_Vars.append(LpVariable("ProductionDecision_%s" %t, 0, C, LpInteger))
    U_Vars.append(LpVariable("UnmetDemand_%s" %t, 0, None, LpInteger))
###############################################################################
# Define Objective
##########################
# For Loop Implementation
#temp = []
#for t in range(H):
#    temp = temp + thetas[t] * U_Vars[t] + KO * RO_Vars[t] + \
#           lpSum(KI[p] * RI_Vars[t][p] for p in range(NumberOfChildren))
#prob += temp
##########################
# lpSum implementation
prob += lpSum(thetas[t] * U_Vars[t] + KO * RO_Vars[t] + \
              lpSum(KI[p] * RI_Vars[t][p] for p in range(NumberOfChildren)) \
              for t  in range(H)), "Objective"
###############################################################################
# Define Constraints
for t in range(H):
    if t == 0:
        RI_Previous = RI_Current
        RO_Previous = RO_Current
    else:
        RI_Previous = RI_Vars[t - 1]
        RO_Previous = RO_Vars[t - 1]
    for p in range(NumberOfChildren):
        prob += RI_Vars[t][p] - RI_Previous[p] +  Q[p] * X_Vars[t] - S[p, t] == 0
    prob += RO_Vars[t] - RO_Previous - X_Vars[t] + D[t] - U_Vars[t] == 0
    prob += U_Vars[t] - D[t] <= 0
###############################################################################
# The problem is solved using PuLP's choice of Solver
prob.solve(CPLEX(msg = 0))
#prob.solve(GUROBI(msg = 0))
# Alternatively
#GUROBI(msg=0).solve(prob)
# The status of the solution is printed to the screen
print("Status:", LpStatus[prob.status])
# Each of the variables is printed with it's resolved optimum value
#for v in prob.variables():
#    print(v.name, "=", v.varValue)
# The optimised objective function value is printed to the screen
print('\nMinimum UnmetDemand-Penalized Total Inventory Cost:', value(prob.objective))
print('')
# Save Data for RETURN
X_Values = list()
for var in X_Vars:
    X_Values.append(int(var.varValue))
In = list()
for var in RI_Vars[0]:
    In.append(int(var.varValue))
Out = int(RO_Vars[0].varValue)
UnMet = int(U_Vars[0].varValue)

print(D)

print(X_Values)
print(In)
print(Out)
print(UnMet)

print(list(RI_Current))

print('\n===========================================================')


#for var in RI_Vars:
    #print(var)

