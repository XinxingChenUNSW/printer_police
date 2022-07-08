import socket
import csv
from struct import unpack
from multiprocessing import Queue, Process
from itertools import chain

import datetime

import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.widgets import Slider
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

'''
WiFi data gathering process
'''
def wifi_process(s: socket, rolling_a_q: Queue) -> None:
    # Define start and stop bytes
    start_bytes = "START".encode('utf-8')

    #size of sensor data from load cells, imus and encoder
    

    while True:
        client, addr = s.accept()
        prev = time.time()
        # TODO: Keep track of bytes thrown away
        stored_bytes = bytearray()

        while True:
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
def csv_process(csv_q: Queue):
    f = open('data_out.csv', 'w')
    writer = csv.writer(f)

    while True:
        if not csv_q.empty():
            data = csv_q.get()
            # flat_data = chain(*data)
            writer.writerow(data)

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

'''
Plotting function
'''
def run_plot(plot_q: Queue, processes: list):
    style.use("fivethirtyeight")
    
    
    # fig = plt.figure()
    # ax1 = fig.add_subplot(1,1,1)
    # Plot two cols, n/2 rows
    fig, axs = plt.subplots(nrows=math.ceil(num_plots/2), ncols=2, figsize=(20, 15))
    # TODO: Make this plot scrolling or smaller so we can observe all the data

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
    ani = animation.FuncAnimation(fig, animate, fargs=(plot_q,lines,axs), interval = 1, blit=False)

    # Set as blockinng for now, close the program by closing the plot window
    # plt.show(block=False)
    plt.show(block=True)

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

    wifi_p = Process(target=wifi_process, args=(s, rolling_a_q))
    csv_p = Process(target=csv_process, args=(csv_q,))
    processing_p = Process(target=rolling_average, args=(rolling_a_q, csv_q, plot_q))


    # Start Processes
    wifi_p.start()
    csv_p.start()
    processing_p.start()

    processes = [wifi_p, csv_p, processing_p]

    run_plot(plot_q, processes)


if __name__ == "__main__":
    main()