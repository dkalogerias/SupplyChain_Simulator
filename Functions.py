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
def Plan_LookaheadMIP(H, Hdict, ParentLabels, ChildrenLabels, ChildrenTrTimes, # remove number of children because no use
                      D, P, #D = data from parents (length = horizon), S = data from children, P = projected shipments (length = horizon)
                      RI_Current, RO_Current,
                      thetas, KO, KI, KPro, KPur, Q, NumDiff): # C = Production Cap, Q = Projected demands from children, NumDiff = Number of different parts
    ###############################################################################
    # Create problem (object)
    prob = LpProblem("Production Plan Optimization", LpMinimize)
    ###############################################################################
    # modify Q for leaf suppliers
    if ChildrenLabels[0] == -1:
        Q[-1] = [1, 1, 1]
    ###############################################################################
    # Define decision variables
    # Input inventory: a list of dictionaries whose keys are material types and values are quantities stored at each time point
    RI_Vars = list()
    # upstream demand: a list of dictionaries whose keys are children indices and values are demand to each child at each time point
    UPD_Vars = list()
    # Output inventory: a list of the amount of stored commodities at each time point
    RO_Vars = list()
    # Production decision: a list of the amount of parts to produce at each time point
    X_Vars = list()
    # Unmet demand: a list of dictionaries whose keys are parent labels and values are unmet demand of each of them at each time point
    U_Vars = list()
    #######################SOME HELPFUL DECISION VARIABLES WHICH WE EVENTUALLY DO NOT USE###
    #upstream demand grouped by types of materials supplied from children suppliers
    UPD_Vars_group = list()

    ################################################################################
    # dictDiffParts
    # key = label of parts, val = the children suppliers who supply each part

    dictDiffParts = dict()

    for i in range(NumDiff):
        dictDiffParts[i+1] = []
    for child in Q.keys():
        # Q[child][0] is the label of the part that this child supplier supplies
        dictDiffParts[Q[child][0]].append(child)

    # Construct these decision variables
    for t in range(H):
        RI_Vars.append(dict())
        UPD_Vars.append(dict())

        for part in range(NumDiff):
            RI_Vars[t][part + 1] = LpVariable("InputInventory_%s_%s" %(t, (part + 1)), 0, None)

        for child in ChildrenLabels:
            if t >= ChildrenTrTimes[child] + 2 and child != -1:  # not the leaves
                UPD_Vars[t][child] = LpVariable("UpStreamDemand_%s_%s" % (t, child), 0, None)
            # elif t <= ChildrenTrTimes[child] + 1 and child != -1:
            #    UPD_Vars[t][child] = S[child][t]
            else:
                UPD_Vars[t][child] = 0

        RO_Vars.append(LpVariable("OutputInventory_%s" % t, 0, None))
        X_Vars.append(LpVariable("ProductionDecision_%s" % t, 0, None))
        U_Vars.append(dict())

        for par in ParentLabels:
            if t < Hdict[par]:
                U_Vars[t][par] = LpVariable("UnmetDemand_%s_%s" % (t, par), 0, None)
            else:
                U_Vars[t][par] = 0

    # for i in range(NumDiff):
    #     UPD_Vars_group.append(dict())

    ###############################################################################
    # Define Objective
    ##########################
    # For loop implementation
    temp = []
    for t in range(H):
        # thetas might be different for each parent
        temp = temp + lpSum(thetas[t][par] * U_Vars[t][par] for par in ParentLabels) \
               + KO * RO_Vars[t] + KPro * X_Vars[t] + \
               lpSum(KI[part+1] * RI_Vars[t][part+1] for part in range(NumDiff)) + \
               lpSum(KPur[child] * UPD_Vars[t][child] for child in ChildrenLabels)
    prob += temp
    ##########################
    # lpSum implementation
    #prob += lpSum(thetas[t] * U_Vars[t] + KO * RO_Vars[t] + \
    #              lpSum(KI[child] * RI_Vars[t][child] for child in ChildrenLabels) \
    #              for t  in range(H)), "Objective"
    ###############################################################################
    # Define constraints
    for par in D.keys():
        if len(D[par]) < H:
            for i in range(H - len(D[par])):
                D[par] = np.append(D[par],[0])
    for t in range(H):
        if t == 0:
            RI_Previous = RI_Current
            RO_Previous = RO_Current
        else:
            RI_Previous = RI_Vars[t - 1]
            RO_Previous = RO_Vars[t - 1]
        for part in dictDiffParts.keys():
            prob += RI_Vars[t][part] - RI_Previous[part] \
                    + lpSum(Q[child][1]*Q[child][2]*X_Vars[t] \
                            - UPD_Vars[t][child]  - P[child][t] for child in dictDiffParts[part]) == 0
        # produce = (send to inventory) + (send to parents)
        prob += RO_Vars[t] - RO_Previous - X_Vars[t] + lpSum(D[par][t] - U_Vars[t][par] for par in ParentLabels) == 0
        for par in ParentLabels:
            # send to each parent >= 0 (parents cannot return supplies)
            if t < Hdict[par]:
                prob += U_Vars[t][par] - D[par][t] <= 0
            # if t > Hdict[par] or par == -1:
            #     U_Vars[t][par] == 0
        #need constraint about sum of children in one group = P of the group

        ### add this part #######
        ### has to make sure the ratio matches the chain.txt
        ### and has to deal with the fact that travel times of children who supply the same ting are different
        if ChildrenLabels[0] != -1:
            for part in dictDiffParts:
                partChildren = []
                for child in dictDiffParts[part]:
                    if ChildrenTrTimes[child] <= t - 2:
                        partChildren.append(child)
                for child in partChildren:
                    prob += (UPD_Vars[t][child]+P[child][t])*lpSum(Q[child2][2] for child2 in partChildren) - \
                            Q[child][2]*lpSum(UPD_Vars[t][child2] + P[child2][t] for child2 in partChildren) == 0
        #########################

    ###############################################################################
    # The problem is solved using our choice of solver (default: PuLP's solver)
    # Built-in Solver
    #prob.solve()
    # CPLEX
    prob.solve(CPLEX(msg=0))
    # Gurobi
    #prob.solve(GUROBI(msg = 0))
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
        X_Values.append(var.varValue)

    In = dict()
    UPD_Values = dict()
    for part in range(NumDiff):
        In[part+1] = RI_Vars[0][part+1].varValue
    for child in ChildrenLabels:
        UPD_Values[child] = list()
        for t in range(H):
            if child != -1:
                if t >= ChildrenTrTimes[child] + 2:
                    UPD_Values[child].append(UPD_Vars[t][child].varValue)
            else:
                UPD_Values[child].append(0)
    #for var in RI_Vars[0]:
    #    In.append(int(var.varValue))
    Out = RO_Vars[0].varValue
    UnMet = dict()
    for par in ParentLabels:
        UnMet[par] = list()
        for t in range(H):
            if t < Hdict[par]:
                UnMet[par].append(U_Vars[t][par].varValue)
            else:
                UnMet[par].append(U_Vars[t][par])
    # Return
    # X_Values is a list of produced quantity over time horizon
    # UPD_Values is a dictionary whose keys are children and values are upstream demand over time horizon
    # In is a stored quantity in the input inventory, it's a dictionary whose keys are different product parts
    # Out is a stored quantity in the output inventory. It's just a single number.
    # Unmet is a dictionary whose keys are parents and values are unmet demand

    return X_Values, UPD_Values, In, Out, UnMet
#print('done this')