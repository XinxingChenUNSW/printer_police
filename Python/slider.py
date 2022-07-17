# Import libraries using import keyword
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Setting Plot and Axis variables as subplots()
# function returns tuple(fig, ax)
Plot, Axis = plt.subplots()

# Adjust the bottom size according to the
# requirement of the user
plt.subplots_adjust(bottom=0.25)

# Set the x and y axis to some dummy data
dataAverage = np.loadtxt(open("dataAverage.csv", "rb"), delimiter=",").astype("float")
t = dataAverage[:,0]
s = dataAverage[:,20]

print('t', t)
print('s', s)

# plot the x and y using plot function
Axis.clear()
Axis.plot(t, s)

yAxis = Axis.get_ylim()

# Choose the Slider color
slider_color = 'White'

# Set the axis and slider position in the plot
axis_position = plt.axes([0.2, 0.1, 0.65, 0.03],
						facecolor = slider_color)
slider_position = Slider(axis_position,
						'Pos', dataAverage[0][0], dataAverage[-1][0])
print(dataAverage[0][0])
print(dataAverage[-1][0])

# update() function to change the graph when the
# slider is in use
def update(val):
    pos = slider_position.val
    #Axis.set_xlim(pos, pos+10)
    mini = slider_position.valmin
    maxi = slider_position.valmax
    print(mini)
    print(maxi)
    Axis.axis([mini, pos, yAxis[0], yAxis[1]])
    Plot.canvas.draw_idle()

# update function called using on_changed() function
slider_position.on_changed(update)

# Display the plot
plt.show()