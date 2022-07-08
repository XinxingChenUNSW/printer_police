import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import matplotlib.animation as animation
from matplotlib import style
import numpy as np


style.use("fivethirtyeight")

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)

def animate(i):
    # print(i)
    # index = int(i)
    dataAverage = np.loadtxt(open("dataAverage.csv", "rb"), delimiter=",").astype("float")
    dataRaw = np.loadtxt(open("testNumbers.csv", "rb"), delimiter=",").astype("float")
    x = dataAverage[-310:, 0]
    y = dataAverage[-310:, 1]
    x2 = dataRaw[-310:, 0]
    y2 = dataRaw[-310:, 1]

    ax1.clear()
    ax1.plot(x2, y2, x,y)

def bar(pos):
    pos = slider_position.pos
    ax1.axis([pos,pos+10,-1,1])
    Plot.canvas.draw_idle()
    slider_position.on_changed(bar)
    plt.show()

ani = animation.FuncAnimation(fig, animate, interval = 1)
# plt.tight_layout()
plt.show(block=False)

exit = input("Press Enter to stop: ")
while (exit != ""):
    exit = input("Press Enter to stop: ")