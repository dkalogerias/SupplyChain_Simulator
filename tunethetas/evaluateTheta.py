import matplotlib.pyplot as plt
### retrieve the label of root node
ChainFile = open("Chain.txt","r")
ChainLines = list(ChainFile)
RootLabel = int(ChainLines[0].split(',')[0])

### specify time horizon
T = 60
CostList = [line.split(' ') for line in open("PilotView/costdatafiles/Cost_Data_tune.txt").read().splitlines()]
CostDict = dict()
CostRoot = dict()
Cost6253 = dict()
Cost2735 = dict()
Cost11192 = dict()
for line in CostList:
    if int(line[1]) == (int(line[2])*(T-1)):
        if float(line[4]) in CostDict:
            CostDict[float(line[4])] = CostDict[float(line[4])] + float(line[3])
        else:
            CostDict[float(line[4])] = 0
    if int(line[1]) == (int(line[2])*(T-1)) and int(line[0]) ==  RootLabel:
        CostRoot[float(line[4])] = float(line[3])
    elif int(line[1]) == (int(line[2])*(T-1)) and int(line[0]) ==  6253:
        Cost6253[float(line[4])] = float(line[3])
    elif int(line[1]) == (int(line[2])*(T-1)) and int(line[0]) ==  2735:
        Cost2735[float(line[4])] = float(line[3])
    elif int(line[1]) == (int(line[2]) * (T - 1)) and int(line[0]) == 11192:
        Cost11192[float(line[4])] = float(line[3])
    else:
        pass

x = []
y1 = []
y2 = []
y3 = []
y4 = []
y5 = []
for key in sorted(CostDict.keys()):
    print("%s: %s" % (key, CostDict[key]))
    x.append(key)
    y1.append(CostDict[key])
    print("%s: %s" % (key, CostRoot[key]))
    y2.append(CostRoot[key])
    print("%s: %s" % (key, Cost6253[key]))
    y3.append(Cost6253[key])
    print("%s: %s" % (key, Cost2735[key]))
    y4.append(Cost2735[key])
    print("%s: %s" % (key, Cost11192[key]))
    y5.append(Cost11192[key])


plt.figure(1)
# ax1 = plt.subplot2grid(shape=(2,6), loc=(0,0), colspan=2)
# ax2 = plt.subplot2grid((2,6), (0,2), colspan=2)
# ax3 = plt.subplot2grid((2,6), (0,4), colspan=2)
# ax4 = plt.subplot2grid((2,6), (1,1), colspan=2)
# ax5 = plt.subplot2grid((2,6), (1,3), colspan=2)

ax1 = plt.subplot2grid(shape=(2,2), loc=(0,0))
ax2 = plt.subplot2grid((2,2), (0,1))
ax3 = plt.subplot2grid((2,2), (1,0))
ax4 = plt.subplot2grid((2,2), (1,1))

ax1.set_xlabel('theta')
ax1.plot(x, y1)
ax1.set_title('Cost of the entire supply chain')

ax2.set_xlabel('theta')
ax2.plot(x, y2)
ax2.set_title('Cost at the root supplier')

ax3.set_xlabel('theta')
ax3.plot(x, y3)
ax3.set_title('Cost at the supplier #6253')

ax4.set_xlabel('theta')
ax4.plot(x, y4)
ax4.set_title('Cost at the supplier #2735')

plt.show()







