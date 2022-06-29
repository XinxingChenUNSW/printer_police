import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np


style.use("fivethirtyeight")

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animate(i):
    data = np.loadtxt(open("data.csv", "rb"), delimiter=",").astype("float")
    x = data[-300:, 0]
    y = data[-300:, 1]
    ax1.clear()
    ax1.plot(x, y)

ani = animation.FuncAnimation(fig, animate, interval = 30)
plt.show(block=False)

exit = input("Press Enter to stop: ")
while (exit != ""):
    exit = input("Press Enter to stop: ")