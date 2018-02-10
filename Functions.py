# -*- coding: utf-8 -*-
# Standard Libraries 
import numpy as np
# Import Pulp
from pulp import *
###############################################################################
###############################################################################
#                                  FUNCTIONS                                  #
###############################################################################
###############################################################################
def Plan_LookaheadMIP(H, NumberOfChildren, ChildrenLabels, ChildrenTrTimes,
                      D, S, P,
                      RI_Current, RO_Current,
                      thetas, KO, KI, KPro, KPur,
                      C, Q):
    ###############################################################################
    # Create problem (object)
    prob = LpProblem("Production Plan Optimization", LpMinimize)
    ###############################################################################
    # Define decision variables
    RI_Vars = list()
    UPD_Vars = list()
    RO_Vars = list()
    X_Vars = list()
    U_Vars = list()
    for t in range(H):
        RI_Vars.append(dict())
        UPD_Vars.append(dict())
        for child in ChildrenLabels:
            RI_Vars[t][child] = LpVariable("InputInventory_%s_%s" %(t, child), 0, None, LpInteger)
            if t >= ChildrenTrTimes[child] + 2 and child != -1:
                UPD_Vars[t][child] = LpVariable("UpStreamDemand_%s_%s" %(t, child), 0, None, LpInteger)
            #elif t <= ChildrenTrTimes[child] + 1 and child != -1:
            #    UPD_Vars[t][child] = S[child][t]
            else:
                UPD_Vars[t][child] = 0
        RO_Vars.append(LpVariable("OutputInventory_%s" %t, 0, None, LpInteger))
        X_Vars.append(LpVariable("ProductionDecision_%s" %t, 0, None, LpInteger))
        U_Vars.append(LpVariable("UnmetDemand_%s" %t, 0, None, LpInteger))
    ###############################################################################
    # Define Objective
    ##########################
    # For loop implementation
    temp = []
    for t in range(H):
        temp = temp + thetas[t] * U_Vars[t] + KO * RO_Vars[t] + KPro * X_Vars[t] + \
               lpSum(KI[child] * RI_Vars[t][child] for child in ChildrenLabels) + \
               lpSum(KPur[child] * UPD_Vars[t][child] for child in ChildrenLabels)
    prob += temp
    ##########################
    # lpSum implementation
    #prob += lpSum(thetas[t] * U_Vars[t] + KO * RO_Vars[t] + \
    #              lpSum(KI[child] * RI_Vars[t][child] for child in ChildrenLabels) \
    #              for t  in range(H)), "Objective"
    ###############################################################################
    # Define constraints
    for t in range(H):
        if t == 0:
            RI_Previous = RI_Current
            RO_Previous = RO_Current
        else:
            RI_Previous = RI_Vars[t - 1]
            RO_Previous = RO_Vars[t - 1]
        for child in ChildrenLabels:
            prob += RI_Vars[t][child] - RI_Previous[child] \
                        + Q[child] * X_Vars[t] - UPD_Vars[t][child] \
                        - P[child][t] == 0 # - S[child][t] == 0
        prob += RO_Vars[t] - RO_Previous - X_Vars[t] + D[t] - U_Vars[t] == 0
        prob += U_Vars[t] - D[t] <= 0
    ###############################################################################
    # The problem is solved using our choice of solver (default: PuLP's solver)
    # Built-in Solver
    #prob.solve()
    # CPLEX
    #prob.solve(CPLEX(msg = 0))
    # Gurobi
    prob.solve(GUROBI(msg = 0))
    # Print status of solution
    if LpStatus[prob.status] != 'Optimal':
        print('Optimization Status:', LpStatus[prob.status])
        wait = input('PRESS ENTER TO CONTINUE.\n')
    #print('')
    # Print each of the problem variables is printed with it's resolved optimum value
    #for v in prob.variables():
    #    print(v.name, "=", v.varValue)
    # Print optimized objective function
    #print('\nMinimum UnmetDemand-Penalized Total Inventory Cost:', value(prob.objective))
    #print('')
    # Save data for RETURN
    X_Values = list()
    for var in X_Vars:
        X_Values.append(int(var.varValue))
    In = dict()
    UPD_Values = dict()
    for child in ChildrenLabels:
        In[child] = int(RI_Vars[0][child].varValue)
        UPD_Values[child] = list()
        for t in range(H):
            if child != -1:
                if t >= ChildrenTrTimes[child] + 2:
                    UPD_Values[child].append(int(UPD_Vars[t][child].varValue))
            else:
                UPD_Values[child].append(0)
    #for var in RI_Vars[0]:
    #    In.append(int(var.varValue))
    Out = int(RO_Vars[0].varValue)
    UnMet = list()
    for var in U_Vars:
        UnMet.append(int(var.varValue))
    # Return
    return X_Values, UPD_Values, In, Out, UnMet