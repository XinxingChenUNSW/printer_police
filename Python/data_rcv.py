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

        self.show()       

'''
WiFi data gathering process
'''
def wifi_process(s: socket, rolling_a_q: Queue, enable_wifi_q: Queue) -> None:
    # Define start and stop bytes
    start_bytes = "START".encode('utf-8')

    #size of sensor data from load cells, imus and encoder
    enable_wifi = True

    while True:
        client, addr = s.accept()
        prev = time.time()
        # TODO: Keep track of bytes thrown away
        stored_bytes = bytearray()
        if not enable_wifi_q.empty():
            enable_wifi = enable_wifi_q.get()

        while enable_wifi:
            if not enable_wifi_q.empty():
                enable_wifi = enable_wifi_q.get()

            # Read data, in a buffer double the size of the data structure
            content = client.recv(128)
            if len(content) == 0:
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

timestamps: List[int] = []
plot_data: List[List[float]] = None
curr_t = 0
count = 0

'''
Animation callback function for updating plot data
''' 
def animate(frame, plot_q, lines, axs):
    # data = np.loadtxt(open("data.csv", "rb"), delimiter=",").astype("float")
    global timestamps, plot_data


    if plot_data is None:
        plot_data = [[] for _ in range(lines_to_plot)]

    if plot_q.empty():
        return lines

    # Grab all data points currently in the data queue for plotting
    while not plot_q.empty():
        data = plot_q.get()
        
        timestamps.append(data[0])

        for i in range(len(plot_data)):
            plot_data[i].append(data[i + 1])

    # Select the last 100 data points to plot (Abstract into variable)
    if len(timestamps) > 300:
        timestamps = timestamps[-300:]
        for i in range(len(plot_data)):
            plot_data[i] = plot_data[i][-300:]

    # Reset X axes limits for all plots
    for ax in axs:
        ax.set_xlim([timestamps[0], timestamps[-1]])

    # Set data for each line
    for i in range(len(plot_data)):
        lines[i].set_data(timestamps, plot_data[i])

    # Code for plotting data
    # data = data_q.get()
    # x = data[-300:, 0]
    # y = data[-300:, 1]
    # ax1.clear()
    # ax1.plot(ids, y)

    return lines

def start(event, enable_wifi_q):
    enable_wifi_q.put(True)

def stop(event, enable_wifi_q):
    enable_wifi_q.put(False)

def export_csv(event, enable_wifi_q, enable_csv_q):
    enable_wifi_q.put(False)
    enable_csv_q.put(True)

'''
Plotting function
'''
def run_plot(plot_q: Queue, processes: list, enable_wifi_q: Queue, enable_csv_q: Queue):
    style.use("fivethirtyeight")
    
    
    # fig = plt.figure()
    # ax1 = fig.add_subplot(1,1,1)
    # Plot two cols, n/2 rows
    fig, axs = plt.subplots(nrows=math.ceil(num_plots/2), ncols=2, figsize=(20, 15))

    start_button_axes = plt.axes([0.2, 0.95, 0.2, 0.05])
    start_button = Button(start_button_axes, 'Start Live Plotting')
    start_button.on_clicked(lambda x: start(x, enable_wifi_q))
    stop_button_axes = plt.axes([0.5, 0.95, 0.2, 0.05])
    stop_button = Button(stop_button_axes, 'Stop Live Plotting')
    stop_button.on_clicked(lambda x: stop(x, enable_wifi_q))
    csv_button_axes = plt.axes([0.8, 0.95, 0.2, 0.05])
    csv_button = Button(csv_button_axes, 'Export to CSV')
    csv_button.on_clicked(lambda x: export_csv(x, enable_wifi_q, enable_csv_q))



    # Flatten axes for easier use
    axs = list(chain(*axs))

    lines = []
    pos = 0

    # Configure axes and lines
    for ax in axs:
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
            lines.append(ax_line)

        # Axis plotting parameters
        ax.legend(loc="upper left")
        ax.set_ylim(plot_y_lims[pos])
        ax.grid()

        pos += 1

    # TODO: Blit TRUE
    ani = animation.FuncAnimation(fig, animate, fargs=(plot_q,lines,axs), interval = 1, blit=True)

    # Set as blockinng for now, close the program by closing the plot window
    # plt.show(block=False)
    # plt.show(block=True)

    window = ScrollableWindow(fig)
    
    exit = input("Press Enter to stop: ")
    while (exit != ""):
        exit = input("Press Enter to stop: ")

    # Kill all processes when program is finished
    for process in processes:
        process.terminate()


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

    run_plot(plot_q, processes, enable_wifi_q, enable_csv_q)


if __name__ == "__main__":
    main()