# -*- coding: utf-8 -*-
# Standard Libraries  
import numpy as np
import time as time
import matplotlib.pyplot as mp
# Custom Libraries
from dataPrep import *
from SupplierClasses import Supplier, LocalPart
###############################################################################
print('\n===============================================')
print()
# Specify the Supplier Horizon (later, make this user input)
H = 30
# Specify the total chain time (also user input, later)
T = 40
print('Supplier Horizon Length (Days): ', H)
print('Total Supply Chain Operation (Days): ', T)
print()
# Import Supply Chain data from file Chain.txt (provided)
# Also, perform data preparation
SupplierDict, maxLagTotal = dataPrep(H)
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
for t in range(T):
    startDay = time.time() # Also start measuring Supplier update time PER day
    print('============================================')
    print('Day', t + 1)
    # Update shipment list for EACH supplier
    for ID, value in SupplierDict.items():   
        for part in SupplierDict[ID].ShipmentList[:]:
            part.LocalPartUpdate(SupplierDict[ID])
    # Produce Parts (and "PRIVATELY" update attributes) for EACH Supplier
    for ID, value in SupplierDict.items(): # This should be able to be performed in parallel
        #print('Day', t + 1, '/ Updating Suppler ID:', int(ID))
        # Get label of parent to current Supplier
        TheParent = SupplierDict[ID].ParentLabel
        # Get the plans from all children to current Supplier
        tempSpec = dict()
        if SupplierDict[ID].NumberOfChildren != 0:
            for child in SupplierDict[ID].ChildrenLabels:
                tempSpec[child] = SupplierDict[child].DownStream_Info_PRE
        # Produce parts for today and update Supplier
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        SupplierDict[ID].ProduceParts(SupplierDict[TheParent] if TheParent != -1 else -1,
            DataFromChildren = tempSpec,
            DataFromParent = SupplierDict[TheParent].UpStream_Info_PRE[ID] if TheParent != -1 else RootPlan[t : t + H])
        #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
    # Update PRE variables with POST variables
    for ID, value in SupplierDict.items():
        SupplierDict[ID].DownStream_Info_PRE = SupplierDict[ID].DownStream_Info_POST
        SupplierDict[ID].UpStream_Info_PRE = SupplierDict[ID].UpStream_Info_POST
    endDay = time.time() # End measuring Supplier update time PER day
    print('Time Elapsed (Suppliers Updating):', round(endDay - startDay, 2), 'sec.')
    #wait = input('PRESS ENTER TO CONTINUE.\n')
# endfor
end = time.time() # End measuring total time
print('\n... Done.')
print('===============================================')
print('Time Elapsed (total):', round(end - start, 2), 'sec.')
###############################################################################