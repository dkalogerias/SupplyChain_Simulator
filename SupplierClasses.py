# -*- coding: utf-8 -*-
# Standard Libraries 
import numpy as np
import copy as cp
from pulp import *
# Custom Libraries
from Functions import *
###############################################################################\
def Plan_LookaheadMIP(H, ParentLabels, ChildrenLabels, ChildrenTrTimes, # remove number of children because no use
                      D, P, #D = data from parents (length = horizon), S = data from children, P = projected shipments (length = horizon)
                      RI_Current, RO_Current,
                      thetas, KO, KI, KPro, KPur, Q, NumDiff): # C = Production Cap, Q = Projected demands from children, NumDiff = Number of different parts
    ###############################################################################
    # Create problem (object)
    prob = LpProblem("Production Plan Optimization", LpMinimize)
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
    for child in Q:
        # Q[child][0] is the label of the part that this child supplier supplies
        dictDiffParts[Q[child][0]].append(child)

    # Construct these decision variables
    for t in range(H):
        RI_Vars.append(dict())
        UPD_Vars.append(dict())

        for part in range(NumDiff):
            RI_Vars[t][part + 1] = LpVariable("InputInventory_%s_%s" %(t, (part + 1)), 0, None, LpInteger)

        for child in ChildrenLabels:
            if t >= ChildrenTrTimes[child] + 2 and child != -1:  # not the leaves
                UPD_Vars[t][child] = LpVariable("UpStreamDemand_%s_%s" % (t, child), 0, None, LpInteger)
            # elif t <= ChildrenTrTimes[child] + 1 and child != -1:
            #    UPD_Vars[t][child] = S[child][t]
            else:
                UPD_Vars[t][child] = 0

        RO_Vars.append(LpVariable("OutputInventory_%s" % t, 0, None, LpInteger))
        X_Vars.append(LpVariable("ProductionDecision_%s" % t, 0, None, LpInteger))
        U_Vars.append(dict())

        for par in ParentLabels:
            U_Vars[t][par] = LpVariable("UnmetDemand_%s_%s" % (t, par), 0, None, LpInteger)

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
               lpSum(KI[part] * RI_Vars[t][part+1] for part in range(NumDiff)) + \
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
        for part in dictDiffParts:
            prob += RI_Vars[t][part] - RI_Previous[part] \
                    + lpSum(Q[child][1]*Q[child][2]*X_Vars[t] \
                            - UPD_Vars[t][child]  - P[child][t] for child in dictDiffParts[part]) == 0
        # produce = (send to inventory) + (send to parents)
        prob += RO_Vars[t] - RO_Previous - X_Vars[t] + lpSum(D[par][t] - U_Vars[t][par] for par in ParentLabels) == 0
        for par in ParentLabels:
            # send to each parent >= 0 (parents cannot return supplies)
            prob += U_Vars[t][par] - D[par][t] <= 0
        #need constraint about sum of children in one group = P of the group

        ### add this part #######
        ### has to make sure the ratio matches the chain.txt
        ### and has to deal with the fact that travel times of children who supply the same ting are different
        for part in dictDiffParts:
            partChildren = []
            for child in dictDiffParts[part]:
                if ChildrenTrTimes[child] <= t - 2:
                    partChildren.append(child)
            for child in partChildren:
                prob += (UPD_Vars[t][child]/lpSum(UPD_Vars[t][child2] for child2 in partChildren)) \
                        - (Q[child][2]/lpSum(Q[child2][2] for child2 in partChildren)) == 0
        #########################

    ###############################################################################
    # The problem is solved using our choice of solver (default: PuLP's solver)
    # Built-in Solver
    #prob.solve()
    # CPLEX
    prob.solve(CPLEX(msg = 0))
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
        X_Values.append(int(var.varValue))
    In = dict()
    UPD_Values = dict()
    for part in range(NumDiff):
        In[part] = int(RI_Vars[0][part].varValue)
    for child in ChildrenLabels:
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
    UnMet = dict()
    for par in ParentLabels:
        UnMet[par] = list()
        for t in range(H):
            UnMet[par].append(U_Vars[t][par])
    # Return
    # X_Values is a list of produced quantity over time horizon
    # UPD_Values is a dictionary whose keys are children and values are upstream demand over time horizon
    # In is a stored quantity in the input inventory, it's a dictionary whose keys are different product parts
    # Out is a stored quantity in the output inventory. It's just a single number.
    # Unmet is a dictionary whose keys are parents and values are unmet demand
    return X_Values, UPD_Values, In, Out, UnMet
###############################################################################
# Definition of "Supplier" class
class Supplier:
    # Constructor...
    def __init__(self, Label, Lat, Long,
                 ParentLabels, ParentTrTimes, NumberOfParents, ChildrenLabels, ChildrenTrTimes, NumberOfChildren, treeDepth,
                 ProductDemands, NumberOfDiffParts,InputInventory, OutputInventory, ProdCap,
                 ProductionPlan, DownStream_Info_PRE, UpStream_Info_PRE, DownStream_Info_POST, UpStream_Info_POST,
                 ProdFailure, Horizon, CurrentUnMet, ShipmentList,
                 thetas, KI, KO, KPro, KPur): # Last line: Parameters
        self.Label = Label
        self.Lat = Lat
        self.Long = Long
        self.ParentLabels = ParentLabels
        self.ParentTrTime = ParentTrTimes
        self.ChildrenLabels = ChildrenLabels
        self.ChildrenTrTimes = ChildrenTrTimes
        self.NumberOfChildren = NumberOfChildren
        self.treeDepth = treeDepth # Supplier's depth in the supply chain (tree)
        self.ProductDemands = ProductDemands # Upstream part demands PER produced part
        # It is a dictionary whose key is the node index and value is a lsi of 3: group number, fraction and demand quantity
        # ###### added variables #####################################################
        self.NumberOfParents = NumberOfParents
        self.NumberOfDiffParts = NumberOfDiffParts # the number of different parts demanded from the children/upstream supppliers
        # ############################################################################
        self.InputInventory = InputInventory # dictionary whose keys are different parts (different types of input supplies)
        self.OutputInventory = OutputInventory # a number
        self.ProdCap = ProdCap # DIFFERENT among suppliers; has to be given in Chain.txt (ultimately)
        self.ProductionPlan = ProductionPlan # PROJECTED Production plan at each day
        self.DownStream_Info_PRE = DownStream_Info_PRE # PRE (t-1): Information to be sent downstream
        self.UpStream_Info_PRE = UpStream_Info_PRE # PRE (t-1):Information to be sent upstream
        self.DownStream_Info_POST = DownStream_Info_POST # POST (t): Information to be sent downstream
        self.UpStream_Info_POST = UpStream_Info_POST # POST (t): Information to be sent upstream
        self.ProdFailure = ProdFailure # Total UnMet demand PER Child (from Day 0)
        self.Horizon = Horizon # Local optimization horizon
        self.CurrentUnMet = CurrentUnMet # Current Unmet Demand from its children
        self.ShipmentList = ShipmentList # Current shipments from children which have NOT been stored in inventory YET
        self.thetas = thetas # Thetas (tunable)
        self.KI = KI # Input cost per unit per part
        self.KO = KO # Stock Cost per unit
        self.KPro = KPro # Production cost per unit
        self.KPur = KPur # Purchase Cost per unit per part
    ##########################################
    # Methods
    # Private method for updating the attributes of a Supplier
    def _SupplierUpdate(self, DataFromChildren, DataFromParent):
        """
        DataFromChildren: DICTIONARY of FORECASTS from ALL UpStream suppliers
        ...................Of size NumberOfChildren x H_c (H_c: Horizon for child c)
        (This is basically the upstream suppliers' forecast of how much we, the current node, wants.
        So, it's also how much they are supplying to us. Thus, we will store this into projected shipments.)
        DataFromParent: FORECAST from DownStream supplier
        ................Array of size number of parents x (self.Horizon - 2)
        BOTH are TRAVEL TIME ADJUSTED!
        """
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Project inventories by projecting shipments
        if self.NumberOfChildren != 0:
            ProjectedShipments = dict(zip(self.ChildrenLabels, \
                                    np.zeros((self.NumberOfChildren, int(self.Horizon)))))
            # For each part in the list of shipments to the current supplier
            for shipment in self.ShipmentList:
                # Get where part comes from
                childFrom = shipment.From
                # Get current day counter of the part
                shipmentCounter = shipment.DayCounter
                # If this counter is less than self.Horizon,
                # then the part will arrive at the current Supplier on time.
                # Recall that this counter cannot be smaller than zero;
                # otherwise, the part has already arrived AND added to the
                # inventory of the current supplier (+1 day)
                # (and has been removed from the ShipmentList)
                if int(shipmentCounter) <= int(self.Horizon) - 1:
                    # If the part will arrive, increase the
                    # corresponding ProjectedShipments entry by 1 
                    ProjectedShipments[childFrom][int(shipmentCounter) + 1] += shipment.Size
        else:
            # the leaf nodes have no supply
            ProjectedShipments = dict(zip(self.ChildrenLabels, np.zeros((1, int(self.Horizon)))))
        #----------------------------------------------------------------------#
        # Extended data from children
        if self.NumberOfChildren != 0:
            ExtDataFromChildren = dict(zip(self.ChildrenLabels, \
                                     np.zeros((self.NumberOfChildren, int(self.Horizon)))))
            # Append with zeros "in the beginning"
            for child in self.ChildrenLabels:
                ExtDataFromChildren[child][0 : int(self.ChildrenTrTimes[child])] = 0
                ExtDataFromChildren[child][int(self.ChildrenTrTimes[child]) : ]  = \
                                                                    DataFromChildren[child]
        else:
            ExtDataFromChildren = dict(zip(self.ChildrenLabels, np.zeros((1, int(self.Horizon)))))
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Extend data from parent!
        # Append with "data", "in the end" (heuristic)
        ExtDataFromParent = DataFromParent
        for par in ExtDataFromParent:
            ExtDataFromParent[par].append(DataFromParent[par][-1])
            ExtDataFromParent[par].append(DataFromParent[par][-1])
        # Solve the MIP now!
        X_Values, UpStreamDemand, In, Out, Unmet = \
        Plan_LookaheadMIP(int(self.Horizon), self.ParentLabels, self.ChildrenLabels,
                          self.ChildrenTrTimes, ExtDataFromParent[0 : int(self.Horizon)],
                          ProjectedShipments, self.InputInventory, self.OutputInventory,
                          self.thetas, self.KO, self.KI, self.KPro, self.KPur,
                          self.ProductDemands, self.NumberOfDiffParts)
        # ## comments about output
        # X_Values is a list with length = H
        # UpStreamDemand is a dict whose key = child index and val = upstream demand with length = horizon_child - 2
        # In = a dict of input inventory
        # Out = amount/size of output inventory
        # Unmet = a dict whose key = parent and val = list of unmet demand with length = time horizon
        # Update Supplier's Variables
        self.ProductionPlan = X_Values
        tempII = cp.deepcopy(self.InputInventory)
        for part in range(self.NumberOfDiffParts):
            self.InputInventory[part+1] = In[part+1]
        # for child in self.ChildrenLabels:
        #     self.InputInventory[child] = In[child]
        self.OutputInventory = Out
        self.CurrentUnMet = dict()
        for par in self.ParentLabels:
            self.CurrentUnMet[par] = Unmet[par][0]
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Generate DownStream_Info
        #self.DownStream_Info_POST = self.ProductionPlan
        # MET Demand
        # self.DownStream_Info_POST = np.zeros((int(self.Horizon)))
        self.DownStream_Info_POST = dict()
        for par in self.ParentLabels:
            self.DownStream_Info_POST[par] = list()
            for t in range(int(self.Horizon)):
                self.DownStream_Intfo_POST[par].append(ExtDataFromParent[par][t] - Unmet[par][t])
        #----------------------------------------------------------------------#
        # Generate UpStream_Info (this is given as downstream information to EACH child Supplier)
        if self.NumberOfChildren != 0:
            self.UpStream_Info_POST = dict(zip(self.ChildrenLabels, \
                                       np.zeros((self.NumberOfChildren, int(self.Horizon)))))
            # For each of the Suppliers children, DO
            for child in self.ChildrenLabels: 
                self.UpStream_Info_POST[child] = np.array(UpStreamDemand[child]).astype(np.int)
        #----------------------------------------------------------------------#
        # DeBug
        #if self.CurrentUnMet > 0: print(self.treeDepth, int(self.Label), int(self.ParentLabel))
        if self.Label == 8576:
            print('')
            print('Label:', self.Label)
            print('Parent:', self.ParentLabels)
            print('Demand From DownStream:', list(DataFromParent))
            print('ProductionPlan:', self.ProductionPlan)
            print('MET:', self.DownStream_Info_POST)
            print('UnMet:', Unmet)
            #print('Input Inventory (AFTER):' , self.InputInventory)
            print('')
            for part in range(self.NumberOfDiffParts):
                print('Input Inventory (BEFORE):', tempII[part])
                print('Input Inventory (AFTER):', self.InputInventory[part])
            for child in self.ChildrenLabels:
                print(child)
                #print('Travel Time:', self.ChildrenTrTimes[child])
                print('Projected:', ProjectedShipments[child])
                print('Info Communicated Upstream:', self.UpStream_Info_POST[child])
                #print(self.ProductDemands[child])
                #print('')
            print('OUT:', self.OutputInventory)
            #wait = input('PRESS ENTER TO CONTINUE.\n')
        #----------------------------------------------------------------------#       
    ##########################################
    # Produce Parts for TODAY
    def ProduceParts(self, DataFromChildren, DataFromParent):
        # Update Supplier
        self._SupplierUpdate(DataFromChildren, DataFromParent)
        # Actual Production for Today
        # Today's MET Demand
        MetDemandToday = dict()
        if self.ParentLabels != [-1]:
            for par in self.ParentLabels:
                MetDemandToday[par] = int(DataFromParent[par][0] - self.CurrentUnMet[par])
                par.ProdFailure[self.label] += self.CurrentUnMet[par]
                if MetDemandToday[par] > 0:
                    par.ShipmentList.append(LocalShipment(self.Label, par, self.ParentTrTime[par], MetDemandToday[par]))
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        # Produce Shipment!
        # No Worries: No need to update inventories.
        # This is taken care by the MIP (see above)
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        #print('Met Demand Today:', MetDemandToday)
        #print('Demand from DownStream:', DataFromParent)
        #print('Plan:', self.ProductionPlan)
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
###############################################################################
# Definition of LocalShipment class     
class LocalShipment:
    # Constructor
    def __init__(self, From, To, DayCounter, Size):
        self.From = From                 # This should be a label
        self.To = To
        self.DayCounter = DayCounter     # Day counter until arrival to destination
        self.Size = Size # Number of parts in the shipment
    ##########################################
    # Methods        
    def LocalShipmentUpdate(self, Supplier):
        # CAREFUL: +1 day After arrival!
        # This Supplier is the parent supplier that this shipment is being shipped to
        self.DayCounter -= 1
        if self.DayCounter == -1:
            Supplier.InputInventory[Supplier.ProductDemands[self.From][0]] += self.Size
            Supplier.ShipmentList.remove(self)
###############################################################################