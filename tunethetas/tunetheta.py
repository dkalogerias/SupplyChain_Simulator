# -*- coding: utf-8 -*-
# Standard Libraries
import numpy as np
import time as time
import datetime as dt
import matplotlib.pyplot as mp
import copy as cp
# Custom Libraries
from dataPrep import *
from SupplierClasses import *
from multiprocessing import Pool
###############################################################################
print('\n===============================================')
print()
# Specify the Supplier Horizon (later, make this user input)
H = 13
# Specify the total chain time (also user input, later)
T = 60
print('Supplier Horizon Length (Days): ', H)
print('Total Supply Chain Operation (Days): ', T)
print()
# Import Supply Chain data from file Chain.txt (provided)
# Also, perform data preparation
SupplierDict, maxLagTotal = dataPrep(H)
dictpenalties = dict()
for supplier in SupplierDict:
    dictpenalties[supplier] = SupplierDict[supplier].Penalty

# Initialize header files for PilotView

###############################################################################
#                      Ready to execute the main Loop                         #
###############################################################################
# Create an empty list for parts
PartList = list()
# Initialize extended plan
RootPlan = np.zeros((T + H))
# Fixed Root Plan
demandFile = open("rootDemand.txt", 'r')
demandFile = list(demandFile)
for i in range(len(demandFile)):
    line = demandFile[i].split('\n')
    RootPlan[i] = int(float(line[0]))
# This should be given
print(RootPlan)
RootPlanFile = open('PilotView/RootPlan_Data_tune.pf', 'w')
for i in range(T+H):
    RootPlanFile.write(' '.join([str(int(RootPlan[i])), '\n']))
RootPlanFile.close()
# Start Simulation
print('\nSimulation Started...')
# At each time step
start = time.time() # Also start measuring total time

def tunetheta(theta):
    SupplierDict, maxLagTotal = dataPrep(H)
    for supplier in SupplierDict:
        SupplierDict[supplier].Penalty = dictpenalties[supplier]
        SupplierDict[supplier].theta = theta


    filename = 'PilotView/Cost_Data_tune_' + str(theta)+ '.txt'
    CostFile = open(filename, 'w')
    filename = 'PilotView/OutputInventory_Data_tune_' + str(theta) + '.txt'
    OutputInventoryFile = open(filename, 'w')
    filename = 'PilotView/PartFlow_Data_tune_' + str(theta) + '.txt'
    PartFlowFile = open(filename, 'w')
    filename = 'PilotView/InputInventory_Data_tune_' + str(theta) + '.txt'
    InputInventoryFile = open(filename, 'w')
    filename = 'PilotView/ProdPlan_Data_tune_' + str(theta) + '.txt'
    ProdPlanFile = open(filename, 'w')

    for t in range(T):
        startDay = time.time() # Also start measuring Supplier update time PER day
        print('============================================')
        print('Day', t, ' theta ', theta)
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
            TheParents = SupplierDict[ID].ParentLabels
            # Get the plans from all children to current Supplier
            dataFromChildren = dict()
            # ALSO: Compute TOTAL input inventory for current Supplier (with no children)
            tempTotalInv = 0
            if SupplierDict[ID].NumberOfChildren != 0:
                for child in SupplierDict[ID].ChildrenLabels:
                    dataFromChildren[child] = SupplierDict[child].DownStream_Info_PRE[ID]
                    #length of each of this is self.Horizon - child's travel time
            else:
                dataFromChildren[-1] = np.zeros(SupplierDict[ID].Horizon)

            for diffPart in range(SupplierDict[ID].NumberOfDiffParts):
                tempTotalInv += SupplierDict[ID].InputInventory[diffPart+1]
                InputInventoryFile.write(' '.join(
                    [str(int(SupplierDict[ID].Label)), str(diffPart + 1), str(24 * 60 * t), str(24 * 60), str(round(tempTotalInv, 2)), str(theta),
                     '\n']))
                # ALSO: Write InputInventoryFile for current Supplier (for PilotView)

            # Produce parts for today and update Supplier
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
            # construct input variables for the ProduceParts function
            if TheParents[0] != -1:
                listParentSuppliers = dict()
                dataFromParents = dict()
                for par in TheParents:
                    listParentSuppliers[par] = SupplierDict[par]
                    dataFromParents[par] = SupplierDict[par].UpStream_Info_PRE[ID]
                SupplierDict[ID].ProduceParts(listParentSuppliers, dataFromChildren, dataFromParents)

            else:
                dataFromParents = dict()
                dataFromParents[-1] = RootPlan[t:t+H]
                SupplierDict[ID].ProduceParts([-1], dataFromChildren, dataFromParents)
            CostFile.write(' '.join([str(int(SupplierDict[ID].Label)), str(24 * 60 * t), str(24 * 60), str(round(SupplierDict[ID].cost, 2)), str(theta), '\n']))

            # SupplierDict[ID].ProduceParts(SupplierDict[TheParent] if TheParent != -1 else -1,
            #     DataFromChildren = tempSpec,
            #     DataFromParent = SupplierDict[TheParent].UpStream_Info_PRE[ID] if TheParent != -1 else RootPlan[t : t + H])
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
                                                     str(int(childrenFlows[child])), str(theta), '\n']))

                OutputInventoryFile.write(' '.join([str(int(ID)),
                                                    str(24 * 60 * t), str(24 * 60),
                                                    str(round(SupplierDict[ID].OutputInventory, 2)), str(theta), '\n']))
                ProdPlanFile.write(' '.join([str(int(ID)), str(24 * 60 * t), str(24 * 60),
                                             str(round(SupplierDict[ID].ProductionPlan[0], 2)), str(theta), '\n']))

        endDay = time.time() # End measuring Supplier update time PER day
        print('Time Elapsed (Suppliers Updating):', round(endDay - startDay, 2), 'sec.')
        print('Thetas that we are testing: ', theta)
    CostFile.close()
    PartFlowFile.close()
    InputInventoryFile.close()
    OutputInventoryFile.close()
    ProdPlanFile.close()
    #if t>= 111: wait = input('PRESS ENTER TO CONTINUE.\n')
# endfor

#################################################################
#                          Tune Thetas                          #
#################################################################
listtheta = np.arange(0.5,1.6,0.1)
listtheta = np.append(listtheta, 2)
filenames_PartFlow = []
filenames_InputInventory = []
filenames_OutputInventory = []
filenames_ProdPlan = []
filenames_Cost = []

for theta in listtheta:
    filenames_PartFlow.append('PilotView/PartFlow_Data_tune_' + str(theta) + '.txt')
    filenames_InputInventory.append('PilotView/InputInventory_Data_tune_' + str(theta) + '.txt')
    filenames_OutputInventory.append('PilotView/OutputInventory_Data_tune_' + str(theta) + '.txt')
    filenames_ProdPlan.append('PilotView/ProdPlan_Data_tune_' + str(theta) + '.txt')
    filenames_Cost.append('PilotView/Cost_Data_tune_' + str(theta) + '.txt')

if __name__ == '__main__':
    with Pool(processes=16) as pool:
        result = pool.map(tunetheta, listtheta)


end = time.time() # End measuring total time
print('\n... Done.')
print('===============================================')
print('Time Elapsed (total):', round(end - start, 2), 'sec.')

############ combine text file ################################################
PartFlowFile = open('PilotView/PartFlow_Data_tune.txt','w') # Create and open file (for PilotView)
InputInventoryFile = open('PilotView/InputInventory_Data_tune.txt','w') # Create and open file (for PilotView)
OutputInventoryFile = open('PilotView/OutputInventory_Data_tune.txt','w')
ProdPlanFile = open('PilotView/ProdPlan_Data_tune.txt','w')
CostFile = open('PilotView/Cost_Data_tune.txt','w')

for fname in filenames_PartFlow:
    with open(fname) as infile:
        for line in infile:
            PartFlowFile.write(line)
for fname in filenames_InputInventory:
    with open(fname) as infile:
        for line in infile:
            InputInventoryFile.write(line)
for fname in filenames_OutputInventory:
    with open(fname) as infile:
        for line in infile:
            OutputInventoryFile.write(line)
for fname in filenames_ProdPlan:
    with open(fname) as infile:
        for line in infile:
            ProdPlanFile.write(line)
for fname in filenames_Cost:
    with open(fname) as infile:
        for line in infile:
            CostFile.write(line)

PartFlowFile.close()
InputInventoryFile.close()
OutputInventoryFile.close()
ProdPlanFile.close()
CostFile.close()

###############################################################################
# Here I use KO = 2 for root , else 4
# with some zero entries, day 0 takes 120 secs and from day 1 onwards each day takes about 300 secs
# with only nonzeros, day 0 takes 19 secs, day 1 takes 21 secs, day 2 takes 32 secs, day 3 takes 41 secs
