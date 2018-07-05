# -*- coding: utf-8 -*-
# Standard Libraries 
import numpy as np
import copy as cp
from pulp import *
# Custom Libraries
from Functions import *
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
        self.ProductionPlan = ProductionPlan # PROJECTED Production plan at each day (This is a number list of length H)
        self.DownStream_Info_PRE = DownStream_Info_PRE # PRE (t-1): Information to be sent downstream
        self.UpStream_Info_PRE = UpStream_Info_PRE # PRE (t-1):Information to be sent upstream
        self.DownStream_Info_POST = DownStream_Info_POST # POST (t): Information to be sent downstream
        self.UpStream_Info_POST = UpStream_Info_POST # POST (t): Information to be sent upstream
        self.ProdFailure = ProdFailure # Total UnMet demand PER Child (from Day 0) (one number per child)
        self.Horizon = Horizon # Local optimization horizon
        self.CurrentUnMet = CurrentUnMet # Current Unmet Demand of its parents2
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
                # if len(ExtDataFromChildren[child][int(self.ChildrenTrTimes[child]) : ]) != len(DataFromChildren[child]):
                #     print("LengthError")
                #     print(self.Label)
                #     print(child)
                #     print(DataFromChildren[child])
                #     print(len(ExtDataFromChildren[child]))
                #     print(self.ChildrenTrTimes[child])
                #     print(ExtDataFromChildren[child][int(self.ChildrenTrTimes[child]) : ])
                ExtDataFromChildren[child][0 : int(self.ChildrenTrTimes[child])] = 0
                ExtDataFromChildren[child][int(self.ChildrenTrTimes[child]) : ]  = \
                                                                    DataFromChildren[child][0:int(self.Horizon - self.ChildrenTrTimes[child])]
        else:
            ExtDataFromChildren = dict(zip(self.ChildrenLabels, np.zeros((1, int(self.Horizon)))))
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Extend data from parent!
        # Append with "data", "in the end" (heuristic)
        ExtDataFromParent = DataFromParent
        for par in ExtDataFromParent.keys():
            ExtDataFromParent[par] = np.append(ExtDataFromParent[par], [DataFromParent[par][-1]])
            ExtDataFromParent[par] = np.append(ExtDataFromParent[par], [DataFromParent[par][-1]])
            #np.concatenate([ExtDataFromParent[par], [DataFromParent[par][-1]]])
            #np.concatenate([ExtDataFromParent[par], [DataFromParent[par][-1]]])
            #ExtDataFromParent[par].append(DataFromParent[par][-1])
            #ExtDataFromParent[par].append(DataFromParent[par][-1])
        # Solve the MIP now!

        X_Values, UpStreamDemand, In, Out, Unmet = \
        Plan_LookaheadMIP(int(self.Horizon), self.ParentLabels, self.ChildrenLabels,
                          self.ChildrenTrTimes, ExtDataFromParent, #[0:int(self.Horizon)]
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
                self.DownStream_Info_POST[par].append(ExtDataFromParent[par][t] - Unmet[par][t])
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
    def ProduceParts(self, Parents, DataFromChildren, DataFromParent):
        # the input Parents is a list of supplier objects that are parents of the current node
        # Update Supplier
        self._SupplierUpdate(DataFromChildren, DataFromParent)
        # Actual Production for Today
        # Today's MET Demand
        MetDemandToday = dict()
        if self.ParentLabels[0] != -1:
            for parentIndex in Parents.keys():
                parent = Parents[parentIndex]
                MetDemandToday[parent.Label] = int(DataFromParent[parent.Label][0] - self.CurrentUnMet[parent.Label])
                parent.ProdFailure[self.Label] += self.CurrentUnMet[parent.Label]
                if MetDemandToday[parent.Label] > 0:
                    parent.ShipmentList.append(LocalShipment(self.Label, parent.Label, self.ParentTrTime[parent.Label], MetDemandToday[parent.Label]))
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
        print('hey')
        # CAREFUL: +1 day After arrival!
        # This Supplier is the parent supplier that this shipment is being shipped to
        self.DayCounter -= 1
        if self.DayCounter == -1:
            Supplier.InputInventory[Supplier.ProductDemands[self.From][0]] += self.Size
            Supplier.ShipmentList.remove(self)
###############################################################################