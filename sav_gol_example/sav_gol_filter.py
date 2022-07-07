import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from matplotlib.widgets import Slider
# creating the updating function 
def update(val):
  current_val = int(win_len.val)
  new_y = savgol_filter(y, current_val,2)
  p.set_ydata(new_y)
  fig.canvas.draw() # redraw figure



# generating a noisy signal 
x = np.linspace(0, 2*np.pi, 100)   # x array
y = np.sin(x) + np.cos(x) + np.random.random(100)


# applying the Savitzky Golay filter
# first argument, out array
# second argument is the window size which is the number of points to average (window length should be higher then the poly number)
# third argument is the polynomial function you want to use to fit your graph 
y_filtered = savgol_filter(y, 99, 2)


# plot normalling 
fig = plt.figure()
ax = fig.subplots()
p = ax.plot(x, y, '-*')
p, = ax.plot(x, y_filtered, 'g')
plt.subplots_adjust(bottom=0.25)

# defining the slider
ax_slider = plt.axes([0.25, 0.1,0.65,0.03]) # xposition, yposition, width and height of the slider
# properties of the slider
win_len = Slider(ax_slider,'Window length', valmin=3, valmax=99, valinit=99, valstep=2)

win_len.on_changed(update)

# ax.plot(x, y)
plt.show()
