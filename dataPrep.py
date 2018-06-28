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
    # Open sypply chain file: Chain.txt
    ChainFile = open("Chain.txt","r")
    # Create an EMPTY DICTIONARY of Suppliers
    SupplierDict = dict()
    # Fill the dictionary of Suppliers
    # For each line in the file
    GlobalCap = 80000 # Use for "debug"
    # list of unique IDs
    uniqueID = []
    for line in ChainFile:
        # If Line is empty, continue
        if len(line.strip()) == 0:
            continue
        # Save attributes for each Supplier
        attList = np.array(line.split(',')).astype(np.float)
        uniqueID.append(attList[0])
        # Case: Most upstream Suppliers (no Children)
        # update: we check the last entry instead since there might be more than one parent
        if attList[-1] == -1:
            parentList = attList[3:-1]
            parentTrTimeDict = dict(zip(parentList,np.zeros(len(parentList))))
            #----------------------Parameters---------------------#
            # Thetas (tunable)
            thetas = []
            for t in range(H):
                thetas.append(dict(zip(parentList, 5*np.random.rand(len(parentList)))))
            # Stock Cost per Unit
            # KO = 5 * np.random.rand(1)
            KO = 0.0008
            # Input cost per unit per part
            #KI = dict(zip([-1], 3 * np.random.rand(1))) 
            KI = dict(zip([-1], [.0001] ))
            # Production cost per unit
            KPro = .001
            # Purchase Cost per unit per part 
            KPur = dict(zip([-1], [.001] )) 
            #------------------End of Parameters------------------#
            # Construct Supplier...
            SupplierDict[attList[0]] = Supplier(attList[0], attList[1], attList[2], # Label, Lat, Long
                                                # ParentLabels, ParentTrTimes, NumberOfParents,
                                                # ChildrenLabels, ChildrenTrTimes,
                                                parentList, parentTrTimeDict, len(parentList), [-1], dict(zip([-1], [0])),
                                                # NumberOfChildren, tree depth, ProductDemands, NumberOfDiffParts
                                                0, -1, dict(zip([-1], [[0,0,0]])), 1,
                                                # InputInventory, OutputInventory, ProdCap
                                                dict(zip([-1], [10000000])), 0, GlobalCap,
                                                # ProductionPlan, Downstream_Info_PRE,
                                                np.zeros((H)), dict(zip(parentList, np.zeros([len(parentList), H]))),
                                                # Upstream_Info_PRE, Downstream_Info_POST
                                                dict(zip([-1], [0])), dict(zip(parentList, np.zeros([len(parentList), H]))),
                                                # Upstream_Info_POST, ProdFailure, Horizon, CurrentUnmet, ShipmentList
                                                dict(zip([-1], [0])), dict(zip([-1],[0])), -1, dict(zip([-1], [0])), list(),
                                                # thetas, KI, KO, KPro, KPur
                                                thetas, KI, KO, KPro, KPur)
        # Case: Rest of suppliers
        elif attList[-1] > 0:
            # Extract parent labels...
            firstchild_index = 0
            for i in range(4, len(attList)):
                if attList[i] >= 0 and attList[i] <= 1:
                    firstchild_index = i-1
                    break
            parentList = attList[3:firstchild_index] #the root node would have this be -1
            parentTrTimeDict = dict(zip(parentList, np.zeros(len(parentList))))
            # Extract children labels...
            childList = []
            # Extract children part demands...
            demandList = []
            groupList = []
            fracList = []
            current = firstchild_index
            currentgroup = 1
            while current < len(attList):
                a = attList[firstchild_index]
                b = attList[firstchild_index + 1]
                if b <= 1:
                    childList.append(a)
                    fracList.append(b)
                    groupList.append(currentgroup)
                    current = current + 2
                else:
                    demandList.append(a)
                    current = current + 1
                    currentgroup = currentgroup + 1
            demandList.append(attList[current])
            fullDemandList = np.zeros(len(childList))
            for i in range(len(childList)):
                fullDemandList[i] = demandList[groupList[i]]
            NumberOfDiffParts = groupList[-1]
            # Initialize DICTIONARIES PER CHILD...
            demandDict = dict(zip(childList, np.transpose([groupList, fullDemandList, fracList])))
            # demandDict: key = child index, value = [group number, demand of the whole group, fraction in the group]
            # To be filled with travel times for each child
            spec = dict(zip(childList, np.zeros((len(childList)))))
            # Initial input inventory: key = diff parts
            spec3 = dict(zip([(i+1) for i in range(NumberOfDiffParts)], 0 * np.ones(NumberOfDiffParts)))
            # DownStream_Info_PRE
            spec4_PRE = dict(zip(parentList, np.zeros((len(parentList), H))))
            # UpStream_Info_PRE
            spec5_PRE = dict(zip(childList, np.zeros((len(childList), H))))
            # DownStream_Info_POST
            spec4_POST = dict(zip(parentList, np.zeros((len(parentList), H))))
            # UpStream_Info_POST
            spec5_POST = dict(zip(childList, np.zeros((len(childList), H))))
            # Total UnMet demand
            spec6 = dict(zip(childList, np.zeros((len(childList)))))
            # ----------------------Parameters---------------------#
            # Thetas (tunable)
            thetas = []
            if attList[3] == -1:
                thetas = [-1]
            else:
                for t in range(H):
                    thetas.append(dict(zip(parentList, 5 * np.random.rand(len(parentList)))))

            # Stock Cost per Unit
            # KO = 0.5 * np.random.rand(1)
            KO = 0.0008
            # Input cost per unit per part
            KI = dict(zip(childList, (0.0001/len(childList)) * np.ones((len(childList))))) 
            # Production cost per unit
            KPro = 0.001
            # Purchase Cost per unit per part 
            KPur = dict(zip(childList, (0.001/len(childList)) * np.ones((len(childList)))))               
            # ------------------End of Parameters------------------
            if attList[3] == [-1]:
                localCapacity = GlobalCap
            else:
                localCapacity = GlobalCap
            # Construct Supplier
            SupplierDict[attList[0]] = Supplier(attList[0], attList[1], attList[2], 
                                                parentList, parentTrTimeDict, len(parentList), childList, spec,
                                                len(childList), -1, demandDict, NumberOfDiffParts,
                                                spec3, 0, localCapacity,
                                                np.zeros((H)), spec4_PRE,
                                                spec5_PRE, spec4_POST,
                                                spec5_POST, spec6, -1, 0, list(),
                                                thetas, KI, KO, KPro, KPur)
        # If this happens the code is flawed!
        else:
            print('Logical Error! Check Code!')
    ChainFile.close()
    # endfor
    print('... Done.')
    print('')
    print('- Update Travel Times for All Suppliers...')
    # Update travel times for both parents and children, for each supplier
    for ID, value in SupplierDict.items():
        # Exclude parentless Suppliers (root)
        if SupplierDict[ID].ParentLabels != [-1]:
            # Extract parents list
            parents = SupplierDict[ID].ParentLabels
            # Extract lat and long of Parent
            for par in parents:
                ParLat = SupplierDict[par].Lat
                ParLong = SupplierDict[par].Long
                # Compute distance of Supplier and its Parent in km
                # This uses *geopy*; has to be installed first
                dist = vincenty((SupplierDict[ID].Lat, SupplierDict[ID].Long), (ParLat, ParLong)).km
                ##############################################
                # This calculates travel times, ASSUMING an average speed of "speed" in km/h
                # Use custom code if needed for the computation of "ttime" below
                speed = 150
                ttime = (dist / speed) / 24
                ttime = np.ceil(ttime)
                ##############################################
                # Update Parent travel time for current Supplier
                SupplierDict[ID].ParentTrTime[par] = ttime
        # Exclude childrenless Suppliers (leafs)
        if SupplierDict[ID].NumberOfChildren != 0:
            # For each of the Suppliers children, DO
            for child in SupplierDict[ID].ChildrenLabels:
                # Extract lat and long of Parent
                ChildLat = SupplierDict[child].Lat
                ChildLong = SupplierDict[child].Long
                # Compute distance of Supplier and its Parent in km
                # This uses *geopy*; has to be installed first
                dist = vincenty((SupplierDict[ID].Lat, SupplierDict[ID].Long), (ChildLat, ChildLong)).km
                ##############################################
                # This calculates travel times, ASSUMING an average speed of "speed" in km/h
                # Use custom code if needed for the computation of "ttime" below
                speed = 150
                ttime = (dist / speed) / 24
                ttime = np.ceil(ttime)
                ##############################################
                # Update Parent travel time for current Supplier
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
    LocFile = open('PilotView/Locations.pf','w') # Create and open file (for PilotView)
    maxLagTotal = 0 # Initialize variable for maximum total travel lag

    # determine supplier horizons
    for ID in uniqueID:
        if SupplierDict[ID].ParentLabels == [-1]:
            # this is the root supplier
            SupplierDict[ID].Horizon = H
        else:
            # each supplier's horizon = the horizon - each travel time
            listHorizon = np.subtract([SupplierDict[parID].Horizon for parID in SupplierDict[ID].ParentLabels],
                                      SupplierDict[ID].ParentTrTime)
            SupplierDict[ID].Horizon = max(listHorizon)
        # Update Supplier's DownStream_Info to reflect the new horizon
        SupplierDict[ID].DownStream_Info_PRE = dict(zip(SupplierDict[ID].ParentLabels,
                                                        np.zeros((len(SupplierDict[ID].ParentLabels),
                                                                  SupplierDict[ID].Horizon))))
        SupplierDict[ID].DownStream_Info_POST = dict(zip(SupplierDict[ID].ParentLabels,
                                                        np.zeros((len(SupplierDict[ID].ParentLabels),
                                                                  SupplierDict[ID].Horizon))))
    # Update Supplier's UpStream_Info to reflect the new horizon
    for ID in uniqueID:
        if SupplierDict[ID].NumberOfChildren != 0:
            for child in SupplierDict[ID].ChildrenLabels:
                childHorizon = int(SupplierDict[ID].Horizon - SupplierDict[ID].ChildrenTrTimes[child])
                SupplierDict[ID].UpStream_Info_POST[child] = np.zeros(childHorizon)

    # determine tree depths
    for ID in uniqueID:
        if SupplierDict[ID].ParentLabels == [-1]:
            SupplierDict[ID].treeDepth = 0
        else:
            firstparID = SupplierDict[ID].ParentLabels[0]
            # its parents must be given their tree depths already since we go in order of the Chain.txt
            SupplierDict[ID].treeDepth = SupplierDict[firstparID].treeDepth + 1

    # compute total lag and max total lag
    dictTimeLag = dict()
    maxLagTotal = 0
    for ID in uniqueID:
        if SupplierDict[ID].ParentLabels == [-1]:
            dictTimeLag[ID] = 0
        else:
            dictTimeLag[ID] = max([dictTimeLag[par] + SupplierDict[ID].ParentTrTime[par] for par in SupplierDict[ID].ParentLabels])
            if dictTimeLag[ID] > maxLagTotal:
                maxLagTotal = dictTimeLag[ID]

    # fix thetas
    for ID in uniqueID:
        # BY THE WAY, fix thetas (tunable)!!!
        #SupplierDict[ID].thetas = 5 * np.random.rand(int(SupplierDict[ID].Horizon))
        # Put the initial value 1 to all thetas, for all Suppliers
        for t in range(SupplierDict[ID].Horizon):
            SupplierDict[ID].thetas[t] = dict(zip(SupplierDict[ID].ParentLabels, np.ones(SupplierDict[ID].NumberOfParents)))
        # Exponentially decreasing thetas, for all Suppliers
        #SupplierDict[ID].thetas = 5 * np.exp(-4 * np.linspace(0, 1, int(SupplierDict[ID].Horizon)))
        # Write location file for PilotView
        LocFile.write(' '.join([str(int(SupplierDict[ID].Label)),
                                str(SupplierDict[ID].Lat),
                                str(-SupplierDict[ID].Long),
                                str(SupplierDict[ID].treeDepth), '\n']))
    # endfor
    LocFile.close()
    print('... Done.')
    print('===============================================')
    return SupplierDict, maxLagTotal