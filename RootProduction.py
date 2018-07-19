import numpy as np
import matplotlib.pyplot as plt
InputPlan = open("PilotView/InputInventory_Data.pf","r")
OutputPlan = open("PilotView/OutputInventory_Data.pf","r")
ProdPlan = open("PilotView/ProdPlan_Data.pf","r")
ChainFile = open("Chain.txt","r")
ChainLines = list(ChainFile)
RootLabel = ChainLines[0].split(',')[0]
print(RootLabel)
InputLines = list(InputPlan)
OutputLines = list(OutputPlan)
ProdLines = list(ProdPlan)
T = 40
InputData = [[] for i in range(T)]
OutputData = np.zeros(T)
ProdData = np.zeros(T)
for fullline in InputLines:
    line = fullline.split()
    if line[0] == RootLabel:
        InputData[int(int(line[2])/int(line[3]))].append(float(line[4]))
print("##### Input Inventory Data #####")
print(InputData)
for fullline in OutputLines:
    line = fullline.split()
    if line[0] == RootLabel:
        OutputData[int(int(line[1])/int(line[2]))] = float(line[3])
print("##### Output Inventory Data #####")
print(OutputData)
for fullline in ProdLines:
    line = fullline.split()
    if line[0] == RootLabel:
        ProdData[int(int(line[1])/int(line[2]))] = float(line[3])
print("##### Production Plan #####")
print(ProdData)
RootPlan = open("PilotView/RootPlan_Data.pf","r")
RootLines = list(RootPlan)
RootData = np.zeros(T)
index = 0
for fullline in RootLines:
    line = fullline.split()
    subline = line[0].split()
    RootData[index] = int(subline[0])
    index = index + 1
    if index >= T:
        break
print('##### Root Plan #####')
print(RootData)
plot1, = plt.plot(range(T), RootData)
plot2, = plt.plot(range(T), ProdData)
plt.legend([plot1,plot2],["original plan", "actual production"])
plt.title("Root's production")
plt.xlabel("time")
plt.ylabel("quantity")
plt.savefig("RootProduction1.png")
