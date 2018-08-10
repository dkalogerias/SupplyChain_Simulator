import numpy as np
T = 30
H = 13
asd = np.zeros((T+H))
file = open("rootDemand.txt", 'r')
file = list(file)
print(len(file))
for i in range(len(file)):
    line = file[i].split('\n')
    print(line[0])