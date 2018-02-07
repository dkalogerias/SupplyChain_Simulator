# -*- coding: utf-8 -*-
# Standard Libraries  
import numpy as np
import time as time
import datetime as dt
import matplotlib.pyplot as mp
import copy as cp
# Custom Libraries
from dataPrep import *
from SupplierClasses import Supplier, LocalShipment
###############################################################################
print('\n===============================================')
print()
# Specify the Supplier Horizon (later, make this user input)
H = 13
# Specify the total chain time (also user input, later)
T = 365
print('Supplier Horizon Length (Days): ', H)
print('Total Supply Chain Operation (Days): ', T)
print()
# Import Supply Chain data from file Chain.txt (provided)
# Also, perform data preparation
SupplierDict, maxLagTotal = dataPrep(H)
# Initialize header files for PilotView
# Top level parameter file
SCParFile = open('PilotView/SupplyChainParameters.pf','w')
SCParFile.write(''.join(['Void\n',
                         'Locations.pf\n',
                         dt.datetime.now().strftime('%B %d %Y %I:%M %p'), '\n',
                         str(T * 24), '\n',
                         str(24 * 60), '\n',
                         'PartFlow PartFlow_Header.pf PartFlow_Data.pf', '\n',
                         'InputInventory InputInventory_Header.pf InputInventory_Data.pf', '\n',
                         ]))
SCParFile.close()
# PartFlow header file
PartFlowHeaderFile = open('PilotView/PartFlow_Header.pf','w')
PartFlowHeaderFile.write('From To TIME Duration FLOW')
PartFlowHeaderFile.close()
# InputInventory header file
PartFlowHeaderFile = open('PilotView/InputInventory_Header.pf','w')
PartFlowHeaderFile.write('From To TIME Duration FLOW')
PartFlowHeaderFile.close()
###############################################################################
#                      Ready to execute the main Loop                         #
###############################################################################
# Create an empty list for parts
PartList = list()
# Initialize extended plan
RootPlan = np.zeros((T + H))
# Fixed Root Plan
# This should be given
RootPlan[0: T] = np.ones((T))
# Auxiliary end of plan; All zeros
RootPlan[T: ] = 0
# Start Simulation
print('\nSimulation Started...')
# At each time step
start = time.time() # Also start measuring total time
PartFlowFile = open('PilotView/PartFlow_Data.pf','w') # Create and open file (for PilotView)
InputInventoryFile = open('PilotView/InputInventory_Data.pf','w') # Create and open file (for PilotView)
for t in range(T):
    startDay = time.time() # Also start measuring Supplier update time PER day
    print('============================================')
    print('Day', t)
    # Update shipment list for EACH supplier
    for ID, value in SupplierDict.items():
        if SupplierDict[ID].NumberOfChildren != 0:
            # Iterate in a COPY of the current ShipmentList  
            for shipment in SupplierDict[ID].ShipmentList[:]:
                # Update shipment in ShipmentList of current Supplier
                shipment.LocalShipmentUpdate(SupplierDict[ID])
    # Produce Parts (and "PRIVATELY" update attributes) for EACH Supplier
    for ID, value in SupplierDict.items(): # This should be able to be performed in parallel
        #print('Day', t, '/ Updating Suppler ID:', int(ID))
        # Get label of parent to current Supplier
        TheParent = SupplierDict[ID].ParentLabel
        # Get the plans from all children to current Supplier
        tempSpec = dict()
        # ALSO: Compute TOTAL input inventory for current Supplier (with no children)
        tempTotalInv = 0
        if SupplierDict[ID].NumberOfChildren != 0:
            for child in SupplierDict[ID].ChildrenLabels:
                tempSpec[child] = SupplierDict[child].DownStream_Info_PRE
                tempTotalInv += SupplierDict[ID].InputInventory[child]
            # ALSO: Write InputInventoryFile for current Supplier (for PilotView)
            InputInventoryFile.write(' '.join([str(int(SupplierDict[ID].Label)), \
                                         str(int(SupplierDict[ID].Label)), \
                                         str(24 * 60 * t), str(24 * 60), \
                                         str(int(tempTotalInv)), '\n']))
        # Produce parts for today and update Supplier
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        SupplierDict[ID].ProduceParts(SupplierDict[TheParent] if TheParent != -1 else -1,
            DataFromChildren = tempSpec,
            DataFromParent = SupplierDict[TheParent].UpStream_Info_PRE[ID] if TheParent != -1 else RootPlan[t : t + H])
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
    # Update PRE variables with POST variables
    for ID, value in SupplierDict.items():
        SupplierDict[ID].DownStream_Info_PRE = cp.deepcopy(SupplierDict[ID].DownStream_Info_POST)
        SupplierDict[ID].UpStream_Info_PRE = cp.deepcopy(SupplierDict[ID].UpStream_Info_POST)
        # Write PartFlowFile for current Supplier (for PilotView)
        if SupplierDict[ID].NumberOfChildren != 0:
            # Initialize dictionary for keeping the flow of each child
            childrenFlows = dict(zip(SupplierDict[ID].ChildrenLabels, \
                                     np.zeros((SupplierDict[ID].NumberOfChildren)))) 
            # Iterate in a COPY of the current ShipmentList
            # For each shipment in ShipmentList, record its flow 
            for shipment in SupplierDict[ID].ShipmentList:
                childrenFlows[shipment.From] += shipment.Size # Update Flow
            # Write PartFlowFile (for PilotView)
            for child in SupplierDict[ID].ChildrenLabels:
                if childrenFlows[child] >= 1:
                    PartFlowFile.write(' '.join([str(int(child)), \
                                                 str(int(SupplierDict[ID].Label)), \
                                                 str(24 * 60 * t), str(24 * 60), \
                                                 str(int(childrenFlows[child])), '\n']))          
    endDay = time.time() # End measuring Supplier update time PER day
    print('Time Elapsed (Suppliers Updating):', round(endDay - startDay, 2), 'sec.')
    #wait = input('PRESS ENTER TO CONTINUE.\n')
# endfor
PartFlowFile.close()
InputInventoryFile.close()
end = time.time() # End measuring total time
print('\n... Done.')
print('===============================================')
print('Time Elapsed (total):', round(end - start, 2), 'sec.')
###############################################################################