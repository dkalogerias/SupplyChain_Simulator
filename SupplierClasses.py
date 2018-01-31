# -*- coding: utf-8 -*-
# Standard Libraries 
import numpy as np
# Custom Libraries
from Functions import Plan_LookaheadMIP
###############################################################################
# Definition of "Supplier" class
class Supplier:
    # Constructor...
    def __init__(self, Label, Lat, Long,
                 ParentLabel, ParentTrTime, ChildrenLabels, ChildrenTrTimes, NumberOfChildren, treeDepth,
                 ProductDemands, InputInventory, OutputInventory, ProdCap,
                 ProductionPlan, DownStream_Info_PRE, UpStream_Info_PRE, DownStream_Info_POST, UpStream_Info_POST,
                 ProdFailure, Horizon, CurrentUnMet, ShipmentList,
                 thetas, KI, KO): # Last line: Parameters
        self.Label = Label
        self.Lat = Lat
        self.Long = Long
        self.ParentLabel = ParentLabel
        self.ParentTrTime = ParentTrTime
        self.ChildrenLabels = ChildrenLabels
        self.ChildrenTrTimes = ChildrenTrTimes
        self.NumberOfChildren = NumberOfChildren
        self.treeDepth = treeDepth # Supplier's depth in the supply chain (tree)
        self.ProductDemands = ProductDemands # Upstream part demands PER produced part
        self.InputInventory = InputInventory
        self.OutputInventory = OutputInventory
        self.ProdCap = ProdCap # DIFFERENT among suppliers; has to be given in Chain.txt (ultimately)
        self.ProductionPlan = ProductionPlan # PROJECTED Production plan at each day
        self.DownStream_Info_PRE = DownStream_Info_PRE # PRE (t-1): Information to be sent downstream
        self.UpStream_Info_PRE = UpStream_Info_PRE # PRE (t-1):Information to be sent upstream
        self.DownStream_Info_POST = DownStream_Info_POST # POST (t): Information to be sent downstream
        self.UpStream_Info_POST = UpStream_Info_POST # POST (t): Information to be sent upstream
        self.ProdFailure = ProdFailure # Total UnMet demand PER Child (from Day 0)
        self.Horizon = Horizon # Local optimization horizon
        self.CurrentUnMet = CurrentUnMet # Current Unmet Demand
        self.ShipmentList = ShipmentList # Current shipments which have NOT stored in inventory YET
        self.thetas = thetas # Thetas (tunable)
        self.KI = KI # Input cost per unit per part
        self.KO = KO # Stock Cost per Unit
    ##########################################
    # Methods
    # Private method for updating the attributes of a Supplier
    def _SupplierUpdate(self, DataFromChildren, DataFromParent):
        """
        DataFromChildream: DICTIONARY of FORECASTS from ALL UpStream suppliers
        ...................Of size NumberOfChildren x H_c (H_c: Horizon for child c)
        DataFromParent: FORECAST from DownStream supplier
        ................Array of size 1 x (self.Horizon - 2)
        BOTH are TRAVEL TIME ADJUSTED!
        """
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Project inventories by projecting shipments
        if self.NumberOfChildren != 0:
            ProjectedShipments = dict(zip(self.ChildrenLabels, \
                                    np.zeros((self.NumberOfChildren, int(self.Horizon)))))
            # For each part in the list of shipments to the current supplier
            for part in self.ShipmentList:
                # Get where part comes from
                childFrom = part.From
                # Get current day counter of the part
                partCounter = part.DayCounter
                # If this counter is less than self.Horizon,
                # then the part will arrive at the current Supplier on time.
                # Recall that this counter cannot be smaller than zero;
                # otherwise, the part has already arrived AND added to the
                # inventory of the current supplier (+1 day)
                # (and has been removed from the ShipmentList)
                if int(partCounter) <= int(self.Horizon) - 1:
                    # If the part will arrive, increase the
                    # corresponding ProjectedShipments entry by 1 
                    ProjectedShipments[childFrom][int(partCounter) + 1] += 1
        else:
            ProjectedShipments = dict(zip(self.ChildrenLabels, np.zeros((1, int(self.Horizon)))))
        #----------------------------------------------------------------------#
        #print('')
        #for child in self.ChildrenLabels:
        #    print(ProjectedShipments[child])
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
        ExtDataFromParent = list(DataFromParent)
        ExtDataFromParent.append(DataFromParent[-1])
        ExtDataFromParent.append(DataFromParent[-1])       
        # Solve the MIP now!
        X_Values, UpStreamDemand, In, Out, Unmet = \
        Plan_LookaheadMIP(int(self.Horizon), self.NumberOfChildren, self.ChildrenLabels, self.ChildrenTrTimes,
                          ExtDataFromParent[0 : int(self.Horizon)], ExtDataFromChildren, ProjectedShipments,
                          self.InputInventory, self.OutputInventory,
                          self.thetas, self.KO, self.KI,
                          self.ProdCap, self.ProductDemands)
        # Update Supplier's Variables
        self.ProductionPlan = X_Values
        for child in self.ChildrenLabels:
            self.InputInventory[child] = In[child]
        self.OutputInventory = Out
        self.CurrentUnMet = Unmet[0]
        # DeBug
        #print('Demand From DownStream:', list(DataFromParent))
        #print('ProductionPlan:', self.ProductionPlan)
        #----------------------------------------------------------------------#
        #----------------------------------------------------------------------#
        # Generate DownStream_Info
        #self.DownStream_Info_POST = self.ProductionPlan
        # MET Demand
        for t in range(int(self.Horizon)): 
            self.DownStream_Info_POST[t] = ExtDataFromParent[t] - Unmet[t]
        #----------------------------------------------------------------------#
        # Generate UpStream_Info (this is given as downstream information to EACH child Supplier)
        if self.NumberOfChildren != 0:
            # For each of the Suppliers children, DO
            for child in self.ChildrenLabels:
                index = int(self.ChildrenTrTimes[child])
                self.UpStream_Info_POST[child] =  self.ProductDemands[child] * \
                                                np.array(UpStreamDemand[child]).astype(np.int)          
    ##########################################
    # Produce Parts for TODAY
    def ProduceParts(self, Parent, DataFromChildren, DataFromParent):
        # Update Supplier
        self._SupplierUpdate(DataFromChildren, DataFromParent)
        # Actual Production for Today
        # Today's MET Demand
        MetDemandToday = int(DataFromParent[0] - self.CurrentUnMet)
        # Create a list for all produced parts
        Produced = list()
        # Produce parts one-by-one
        # No Worries: No need to update inventories.
        # This is taken care by the MIP (see above)
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        #print('Met Demand Today:', MetDemandToday)
        #print('Demand from DownStream:', DataFromParent)
        #print('Plan:', self.ProductionPlan)
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        for item in range(MetDemandToday):
            # Add part to parent's list of shipments
            # Also update total unmet demand (from time 0)
            if self.ParentLabel != -1:
                Parent.ShipmentList.append(LocalPart(self.Label, self.ParentTrTime))
                Parent.ProdFailure[self.Label] += self.CurrentUnMet
###############################################################################
# Definition of "Part" class     
class LocalPart:
    # Constructor
    def __init__(self, From, DayCounter):
        self.From = From                 # This should be a label       
        self.DayCounter = DayCounter # Day counter until arrival to destination
    ##########################################
    # Methods        
    def LocalPartUpdate(self, Supplier):
        # CAREFUL: +1 day After arrival!
        self.DayCounter -= 1
        if self.DayCounter == -1:
            Supplier.InputInventory[self.From] += 1
            Supplier.ShipmentList.remove(self)          
###############################################################################