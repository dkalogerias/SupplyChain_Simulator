# -*- coding: utf-8 -*-
# Standard Libraries 
import numpy as np
from geopy.distance import vincenty # For computing distances from Geo-Coordinates
# Custom Libraries
from SupplierClasses import Supplier
###############################################################################
def dataPrep(H):
    print('========== Data Import & Preparation ==========')
    print('- Getting Supply Chain Structure from File...')
    # Open sypply chain file: Chain.txt...
    ChainFile = open("Chain.txt","r")
    # Create an EMPTY DICTIONARY of Suppliers...
    SupplierDict = dict()
    # Fill the dictionary of Suppliers...
    # For each line in the file...
    for line in ChainFile:
        # If Line is empty, continue...
        if len(line.strip()) == 0:
            continue
        # Save attributes for each Supplier...
        attList = np.array(line.split(',')).astype(np.float)
        # Case: Most upstream Suppliers (no Children)
        if attList[4] == -1:
            #----------------------Parameters---------------------#
            # Thetas (tunable)
            thetas = 5 * np.random.rand(H)
            # Stock Cost per Unit
            #KO = 5 * np.random.rand(1)
            ΚΟ = .01
            # Input cost per unit per part
            #KI = dict(zip([-1], 3 * np.random.rand(1))) 
            KI = dict(zip([-1], [.01] )) 
            #------------------End of Parameters------------------#
            # Construct Supplier...
            SupplierDict[attList[0]] = Supplier(attList[0], attList[1], attList[2],
                                                attList[3], -7, [-1], dict(zip([-1], [0])), 0, -1,
                                                dict(zip([-1], [0])), dict(zip([-1], [1000000])), 0, 8000,
                                                np.zeros((H)), np.zeros((H)), -1, np.zeros((H)), -1,
                                                -1, -1, 0, list(),
                                                thetas, KI, KO)
        # Case: Rest of suppliers
        elif attList[4] > 0:
            # Extract children labels...
            childList = attList[4: :2]
            # Extract children part demands...
            demandList = attList[5: :2]
            # Initialize DICTIONARIES PER CHILD...
            # To be filled with travel times for each child
            spec = dict(zip(childList, np.zeros((len(childList)))))
            # Initial input inventory
            spec3 = dict(zip(childList, 100 * np.ones((len(childList)))))
            # DownStream_Info_PRE
            spec4_PRE = np.zeros((H))
            # DownStream_Info_PRE
            spec5_PRE = dict(zip(childList, np.zeros((len(childList), H))))
            # DownStream_Info_POST
            spec4_POST = np.zeros((H))
            # UpStream_Info_POST
            spec5_POST = dict(zip(childList, np.zeros((len(childList), H))))
            # Total UnMet demand
            spec6 = dict(zip(childList, np.zeros((len(childList)))))
            #----------------------Parameters---------------------#
            # Thetas (tunable)
            thetas = 5 * np.random.rand(H)
            # Stock Cost per Unit
            #KO = 0.5 * np.random.rand(1)
            KO = .01
            # Input cost per unit per part
            #KI = dict(zip(childList, 0.5 * np.random.rand(len(childList)))) 
            KI = dict(zip(childList, (.01/len(childList)) * np.ones((len(childList)))))                
            #------------------End of Parameters------------------#
            if attList[3] == -1: localCapacity = 4
            else: localCapacity = 8000
            # Construct Supplier
            SupplierDict[attList[0]] = Supplier(attList[0], attList[1], attList[2], 
                                                attList[3], -7, childList, spec, len(childList), -1,
                                                dict(zip(childList, demandList)), spec3, 0, localCapacity,
                                                np.zeros((H)), spec4_PRE, spec5_PRE, spec4_POST, spec5_POST,
                                                spec6, -1, 0, list(),
                                                thetas, KI, KO)
        # If this happens the code is flawed!
        else:
            print('Logical Error! Check Code!')
    ChainFile.close()
    # endfor
    print('... Done.')
    print('')
    print('- Update Travel Times for All Suppliers...')
    # Update travel times for both parents and children, for each supplier...
    for ID, value in SupplierDict.items():
        # Exclude parentless Suppliers (root)...
        if SupplierDict[ID].ParentLabel != -1:
            # Extract lat and long of Parent...
            ParLat = SupplierDict[SupplierDict[ID].ParentLabel].Lat
            ParLong = SupplierDict[SupplierDict[ID].ParentLabel].Long
            # Compute distance of Supplier and its Parent in km...
            # This uses *geopy*; has to be installed first...
            dist = vincenty((SupplierDict[ID].Lat, SupplierDict[ID].Long), (ParLat, ParLong)).km
            ##############################################
            # This calculates travel times, ASSUMING an average speed of "speed" in km/h...
            # Use custom code if needed for the computation of "ttime" below...
            speed = 150;
            ttime = (dist / speed) / 24
            ttime = np.ceil(ttime)
            ##############################################
            # Update Parent travel time for current Supplier...
            SupplierDict[ID].ParentTrTime = ttime
        # Exclude childrenless Suppliers (leafs)...
        if SupplierDict[ID].NumberOfChildren != 0:
            # For each of the Suppliers children, DO...
            for child in SupplierDict[ID].ChildrenLabels:
                # Extract lat and long of Parent...
                ChildLat = SupplierDict[child].Lat
                ChildLong = SupplierDict[child].Long
                # Compute distance of Supplier and its Parent in km...
                # This uses *geopy*; has to be installed first...
                dist = vincenty((SupplierDict[ID].Lat, SupplierDict[ID].Long), (ChildLat, ChildLong)).km
                ##############################################
                # This calculates travel times, ASSUMING an average speed of "speed" in km/h...
                # Use custom code if needed for the computation of "ttime" below...
                speed = 150;
                ttime = (dist / speed) / 24
                ttime = np.ceil(ttime)
                ##############################################
                # Update Parent travel time for current Supplier...
                SupplierDict[ID].ChildrenTrTimes[child] = ttime
    # endfor
    print('... Done.')
    print('')
    print('- Determine Supplier Horizons...')
    # (Re)Set correct local horizon for each supplier,
    # based on the total travel time to Root.
    # Also: Find depth of each supplier in the chain
    # Also: Write location file for PilotView
    # Also: fix the thetas for each supplier, using correct horizon (temporary)
    # -------------------------------------------------------------------------
    # NOTE: +1 day for arrival overhead
    #       +1 day for day passing
    LocFile = open('PilotView/Locations.pf','w') # Createe and open file (for PilotView)
    maxLagTotal = 0 # Ininitialize variable for maximum total travel lag
    for ID, value in SupplierDict.items():
        # Assign initial horizon value (correct for Root)
        SupplierDict[ID].Horizon = H
        # Assign initial tree depth (by the way)
        SupplierDict[ID].treeDepth = 0
        # Ininitialize variable for LOCAL total travel lag
        TotalLag = 0
        # If not at Root, update horizon recursively following the path to the Root
        # Rule: H = H_parent - (TrTime_parent + 1) - 1
        if SupplierDict[ID].ParentLabel != -1:
            # Initialize Supplier ID
            LocalID = ID
            while True:
                # Update tree depth
                SupplierDict[ID].treeDepth += 1
                # Get parent travel time from current Supplier (on the part to Root)
                LocalParentTrTime = SupplierDict[LocalID].ParentTrTime
                # Update LOCAL total travel lag
                TotalLag += LocalParentTrTime
                # Update Supplier horizon
                #SupplierDict[ID].Horizon -= LocalParentTrTime + 2
                SupplierDict[ID].Horizon -= LocalParentTrTime
                # Update Supplier ID with the parent's ID
                LocalID = SupplierDict[LocalID].ParentLabel
                # Check if updated Supplier ID is the Root; if yes, then BREAK
                if SupplierDict[LocalID].ParentLabel == -1: break
        # Update Supplier's DownStream_Info and UpStream_Info to reflect the new horizon
        SupplierDict[ID].DownStream_Info_PRE = np.zeros((int(SupplierDict[ID].Horizon)))
        SupplierDict[ID].DownStream_Info_POST = np.zeros((int(SupplierDict[ID].Horizon)))
        if SupplierDict[ID].NumberOfChildren != 0:
            for child in SupplierDict[ID].ChildrenLabels:
                childHorizon = int(SupplierDict[ID].Horizon \
                                - SupplierDict[ID].ChildrenTrTimes[child] - 2) # NOTE: -2 
                SupplierDict[ID].UpStream_Info_PRE[child] = np.zeros((childHorizon))
                SupplierDict[ID].UpStream_Info_POST[child] = np.zeros((childHorizon))
        # Update maximum total travel lag
        maxLagTotal = max(maxLagTotal, TotalLag)
        # BY THE WAY, fix thetas (tunable)!!!
        #SupplierDict[ID].thetas = 5 * np.random.rand(int(SupplierDict[ID].Horizon))
        # Put the initial value 1 to all thetas, for all Suppliers
        SupplierDict[ID].thetas = 1 * np.ones((int(SupplierDict[ID].Horizon)))
        # Exponentially decreasing thetas, for all Suppliers
        #SupplierDict[ID].thetas = 5 * np.exp(-4 * np.linspace(0, 5, int(SupplierDict[ID].Horizon)))
        # Write location file for PilotView
        LocFile.write(' '.join([str(int(SupplierDict[ID].Label)), \
                                str(SupplierDict[ID].Lat), \
                                str(-SupplierDict[ID].Long), \
                                str(SupplierDict[ID].treeDepth), '\n']))
    # endfor
    LocFile.close()
    print('... Done.')
    print('===============================================')
    return SupplierDict, maxLagTotal