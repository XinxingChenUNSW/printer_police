import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np


style.use("fivethirtyeight")

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)
dataAverage = np.loadtxt(open("dataAverage.csv", "rb"), delimiter=",").astype("float")
ax1.plot(dataAverage[:,0], dataAverage[:,1])
plt.show()



