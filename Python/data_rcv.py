from cgitb import enable
import socket
import csv
from struct import unpack
from multiprocessing import Queue, Process
from itertools import chain

import datetime

import time
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.widgets import Slider, Button
import numpy as np

from typing import List
import math

import time
import numpy as np

from rollingAverage import rolling_average

# TODO: Abstract these into a configuration file, these values can be set and changed from there.
# Data Configurations
BLITTING = True
num_bytes = [1,2,3,3,3,3,1]
data_type = ['i','f','f','f','f','f','i']

lines_to_plot = 15
num_plots = len(num_bytes) - 1

plot_names = ["Load Cell", "Gyro 1", "Gyro 2", "IMU 1", "IMU 2", "Encoder"]
ax_colours = [['r', 'b'], ['r', 'b','g'],['r','b','g'],['r', 'b','g'],['r','b','g'],['r']]
ax_labels = [['L1', 'L2'], 
             ['Rotation X', 'Rotation Y', 'Rotation Z'],
             ['Rotation X', 'Rotation Y', 'Rotation Z'],
             ['Magnitude Z', 'Magnitude Y', 'Magnitude Z'],
             ['Magnitude Z', 'Magnitude Y', 'Magnitude Z'],
             ['Count']]

plot_y_lims = [[-50, 50],
               [-50, 50],
               [-50, 50],
               [-50, 50],
               [-50, 50],
               [-10000, -5000]]

#Class for scrollable UI
class ScrollableWindow(QtWidgets.QMainWindow):
    def __init__(self, fig):
        self.qapp = QtWidgets.QApplication.instance()

        QtWidgets.QMainWindow.__init__(self)
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)
        self.widget.setLayout(QtWidgets.QVBoxLayout())
        self.widget.layout().setContentsMargins(0,0,0,0)
        self.widget.layout().setSpacing(0)

        self.fig = fig
        self.canvas = FigureCanvas(self.fig)
        self.canvas.draw()
        self.scroll = QtWidgets.QScrollArea(self.widget)
        self.scroll.setWidget(self.canvas)

        self.nav = NavigationToolbar(self.canvas, self.widget)
        self.widget.layout().addWidget(self.nav)
        self.widget.layout().addWidget(self.scroll)

        self.setWindowTitle('Live Plotting Monitoring')
        self.showMaximized()       

'''
WiFi data gathering process
'''
def wifi_process(s: socket, rolling_a_q: Queue, enable_wifi_q: Queue) -> None:
    # Define start and stop bytes
    start_bytes = "START".encode('utf-8')
    #size of sensor data from load cells, imus and encoder
    enable_wifi = False

    while True:
        client, addr = s.accept()
        prev = time.time()
        # TODO: Keep track of bytes thrown away
        stored_bytes = bytearray()

        while True:
            if not enable_wifi_q.empty():
                enable_wifi = enable_wifi_q.get()

            # Read data, in a buffer double the size of the data structure
            # Need to read data regardless of whether WiFi is enabled.
            # This ensures WiFi buffer doesn't fill up, and we get new data when enabling WiFi
            content = client.recv(128)

            if enable_wifi:
                
                if len(content) == 0:
                    print("DED")
                    break

                curr_t = time.time()
                # print(curr_t - prev)
                prev = curr_t

                curr_ptr = -1

                # Find start bytes
                for i in range(70):
                    if content[i:i+len(start_bytes)] == start_bytes:

                        curr_ptr = i + len(start_bytes)
                        break

                if curr_ptr == -1:
                    continue

                data_row = []
                full_packet_found = True

                # Unpack each struct attribute
                for idx, size in enumerate(num_bytes):
                    if not full_packet_found:
                        break
                    # Loop through each float / integer and unpack them
                    for _ in range(size):
                        # Partial data detected that is not the full data packet
                        if curr_ptr + 4 > len(content):
                            full_packet_found = False
                            break
                        val = unpack(data_type[idx], content[curr_ptr: curr_ptr + 4])[0]
                        data_row.append(val)
                        curr_ptr += 4

                if full_packet_found:
                    rolling_a_q.put(data_row)
                    # csv_q.put(data_row)

        print("Closing connection")
        client.close()


'''
CSV writing process
'''
def csv_process(csv_q: Queue, enable_csv_q: Queue):
    f = open('data_out.csv', 'w')
    writer = csv.writer(f)
    enable_csv = False

    while True:
        if not enable_csv_q.empty():
            enable_csv = enable_csv_q.get()
        while enable_csv:
            if not csv_q.empty():
                data = csv_q.get()
                # flat_data = chain(*data)
                writer.writerow(data)
            else:
                enable_csv = False

'''
Connect to wifi
'''
def connectWifi():
    # Set up socket
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print("Getting WiFi Details...")
    local_ip = input("Enter IPV4 address: ")
    port = int(input("Enter port number: "))

    s.bind((local_ip, port))
    s.listen(0)

    print(s.getsockname())

    return s

# TODO: Make UI look better for button and slider
#       Abstract some of the functionality like setting up buttons and getting lines out
class PlotAnimation:
    '''
    PlotAnimation __init__ function
    Inputs: plot_q: Queue for gathering plotting data
            enable_wifi_q: Queue for commanding WiFi to start and stop
            enable_csv_q: Queue for commanding CSV to start and stop
    '''
    def __init__(self, plot_q: Queue, enable_wifi_q: Queue, enable_csv_q: Queue):
        self.timestamps: List[int] = []
        self.plot_data: List[List[float]] = None
        self.curr_t = 0
        self.count = 0

        self.setup_figure()
        self.setup_ui(plot_q, enable_wifi_q, enable_csv_q)

        # TODO: Blit TRUE
        self.ani = animation.FuncAnimation(self.fig, self.animate, fargs=(plot_q,), interval = 1, blit=BLITTING)

        self.window = ScrollableWindow(self.fig)

        exit = input("Press Enter to stop: ")
        while (exit != ""):
            exit = input("Press Enter to stop: ")

    '''
    Setup figure, axes, and lines
    '''
    def setup_figure(self):
        self.fig, self.axs = plt.subplots(nrows=math.ceil(num_plots/2), ncols=2, figsize=(20, 15))

        # Flatten axes for easier use
        self.axs = list(chain(*self.axs))

        self.lines = []
        pos = 0

        # Configure axes and lines
        for ax in self.axs:
            # Disable non-used axes
            if pos >= num_plots:
                ax.set_axis_off()
                continue

            ax.set_title(plot_names[pos])
            
            # Assign lines to each axes for plotting data
            for i in range(num_bytes[pos + 1]):
                ax_line, = ax.plot([], [],
                                lw=1,
                                color=ax_colours[pos][i],
                                label=ax_labels[pos][i])
                self.lines.append(ax_line)

            # Axis plotting parameters
            ax.legend(loc="upper left")
            ax.set_ylim(plot_y_lims[pos])
            ax.grid()

            pos += 1

    '''
    Setup user interactive features such as sliders and buttons
    '''
    def setup_ui(self, plot_q, enable_wifi_q, enable_csv_q):
        start_button_axes = plt.axes([0.2, 0.95, 0.2, 0.05])
        self.start_button = Button(start_button_axes, 'Start Live Plotting')
        self.start_button.on_clicked(lambda x: self.start(x, enable_wifi_q, plot_q))
        stop_button_axes = plt.axes([0.5, 0.95, 0.2, 0.05])
        self.stop_button = Button(stop_button_axes, 'Stop Live Plotting')
        self.stop_button.on_clicked(lambda x: self.stop(x, enable_wifi_q))
        csv_button_axes = plt.axes([0.8, 0.95, 0.2, 0.05])
        self.csv_button = Button(csv_button_axes, 'Export to CSV')
        self.csv_button.on_clicked(lambda x: self.export_csv(x, enable_wifi_q, enable_csv_q))

        self.plot_slider_ax = plt.axes([0.25, 0.025, 0.5, 0.03])
        self.plot_slider = Slider(self.plot_slider_ax, 'Overall', 0.0, 1.0, 1.0)
        self.plot_slider.on_changed(self.update)

        self.showall_ax = plt.axes([0.8, 0.025, 0.1, 0.04])
        self.display_button = Button(self.showall_ax, 'Display All', color='gold',
                        hovercolor='skyblue')
        self.display_button.on_clicked(self.show_all)

        self.plot_slider_ax.set_visible(False)
        self.showall_ax.set_visible(False)

    '''
    Updating a single frame of the plot, depending on BLITTING
    '''
    def update_frame(self):
        if BLITTING:
            # TODO: Test if this canvas.blit works on windows machine
            self.fig.canvas.draw_idle()
            # for ax in self.axs:
            #     self.fig.canvas.blit(ax.bbox)
        else:
            self.fig.canvas.draw_idle()

    '''
    Animation callback function for updating plot data
    ''' 
    def animate(self, frame, plot_q):
        # data = np.loadtxt(open("data.csv", "rb"), delimiter=",").astype("float")
        if self.plot_data is None:
            self.plot_data = [[] for _ in range(lines_to_plot)]

        plot_frame = [[] for _ in range(lines_to_plot)]

        if plot_q.empty():
            return self.lines 

        # Grab all data points currently in the data queue for plotting
        while not plot_q.empty():
            data = plot_q.get()
            
            self.timestamps.append(data[0])

            for i in range(len(self.plot_data)):
                self.plot_data[i].append(data[i + 1])

        # Select the last 300 data points to plot (Abstract into variable)
        if len(self.timestamps) > 300:
            time_frame = self.timestamps[-300:]
            for i in range(len(self.plot_data)):
                plot_frame[i] = self.plot_data[i][-300:]
        else:
            time_frame = self.timestamps
            plot_frame = self.plot_data

        # Reset X axes limits for all plots
        for ax in self.axs:
            ax.set_xlim([time_frame[0], time_frame[-1]])

        # Set data for each line
        for i in range(len(plot_frame)):
            self.lines[i].set_data(time_frame, plot_frame[i])
            self.lines[i]

        

        return self.lines

    '''
    Slider update callback
    Updates the range for each plot depending on position of overall slider
    '''
    def update(self, val):
        # Find left and right indices for our plot range,
        # depending on slider value
        if len(self.timestamps) <= 300:
            left = 0
            right = len(self.timestamps)
        else:
            left = (int)(val * (len(self.timestamps) - 300))
            right = left + 300

        time_frame = self.timestamps[left:right]

        # Update plot x limits and data stored in the lines
        for ax in self.axs:
            ax.set_xlim([time_frame[0], time_frame[-1]])

        self.update_frame()

    '''
    Show all data points for every plot
    '''
    def show_all(self, event):
        for ax in self.axs:
            ax.set_xlim([self.timestamps[0], self.timestamps[-1]])

        self.update_frame()
        
    '''
    Start button callback
    Resumes WiFi, plot animation, and disables slider axes
    '''
    def start(self, event, enable_wifi_q, plot_q):
        enable_wifi_q.put(True)
        self.timestamps = []
        self.plot_data = None

        # Empty Queue of any remaining items
        while not plot_q.empty():
            plot_q.get()

        # Draw an empty frame to allow blitting to resume
        for i in range(lines_to_plot):
            self.lines[i].set_data([], [])
        self.update_frame()

        self.ani.resume()
        self.plot_slider_ax.set_visible(False)
        self.showall_ax.set_visible(False)

    '''
    Stop button callback
    Pauses WiFi, plot animation, and enables slider axes
    '''
    def stop(self, event, enable_wifi_q):
        enable_wifi_q.put(False)
        self.ani.pause()
        self.plot_slider_ax.set_visible(True)
        self.showall_ax.set_visible(True)

        for i in range(len(self.plot_data)):
            self.lines[i].set_data(self.timestamps, self.plot_data[i])

        self.show_all(None)

    '''
    Export csv button callback
    Commands csv process to write to csv, and stops the plot
    '''
    def export_csv(self, event, enable_wifi_q, enable_csv_q):
        enable_csv_q.put(True)
        self.stop(None, enable_wifi_q)


'''
Main functionn
'''
def main():
    # Connect to wifi before starting other processes
    s = connectWifi()

    # Setup multiprocessing communication Queues
    plot_q = Queue()
    rolling_a_q = Queue()
    csv_q = Queue()
    enable_wifi_q = Queue()
    enable_csv_q = Queue() 

    wifi_p = Process(target=wifi_process, args=(s, rolling_a_q, enable_wifi_q))
    csv_p = Process(target=csv_process, args=(csv_q, enable_csv_q))
    processing_p = Process(target=rolling_average, args=(rolling_a_q, csv_q, plot_q))

    # Start Processes
    wifi_p.start()
    csv_p.start()
    processing_p.start()

    processes = [wifi_p, csv_p, processing_p]

    # Run our plot
    pa = PlotAnimation(plot_q, enable_wifi_q, enable_csv_q)

    # Kill all processes when program is finished
    for process in processes:
        process.terminate()


if __name__ == "__main__":
    main()