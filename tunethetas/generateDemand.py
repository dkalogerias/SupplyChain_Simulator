import numpy as np
T = 60
H = 13
RootPlan = np.zeros((T + H))
RootPlan[0: T] = np.random.randint(10, size = T)
RootPlan[T: ] = 0
demandfile = open("rootDemand.txt", 'w')
for i in RootPlan:
    demandfile.write(str(i) + "\n")
demandfile.close()