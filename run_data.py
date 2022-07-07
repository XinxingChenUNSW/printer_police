from random import randint
import csv
import time
import numpy as np
from typing import List
import math
from itertools import chain
from matplotlib import style
import matplotlib.pyplot as plt
import matplotlib.animation as animation
style.use("fivethirtyeight")

fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(20, 15))
#axs = list(chain(*axs))
plot_names = ["Load Cell 1", "Load cell 2", "Gyro 1", "Gyro 2", "Accelerometer 1", "Accelerometer 2", "Encoder"]
ax_colours = [['r', 'b'], ['r', 'b','g'],['r','b','g'],['r', 'b','g'],['r','b','g'],['r']]
ax_labels = [['L1', 'L2'], 
            ['Rotation X', 'Rotation Y', 'Rotation Z'],
            ['Rotation X', 'Rotation Y', 'Rotation Z'],
            ['Magnitude Z', 'Magnitude Y', 'Magnitude Z'],
            ['Magnitude Z', 'Magnitude Y', 'Magnitude Z'],
            ['Count']]

plot_y_lims = [[0, 1],
              [0, 1],
              [0, 1],
              [0, 1],
              [0, 1],
              [0, 1]]
def rollingAverage(data):
  # initialise variables
  dataGeneratorMatrix = []
  dataRowGenerator = 1
  windowSize = 11
  # The number of moving averages you have found
  index = 0

  for row in data:
    
    row = list(map(float, row[0].split()))
    with open("testNumbers.csv", 'a') as dataRawfile:
      writer = csv.writer(dataRawfile)
      writer.writerow(row)

    dataGeneratorMatrix.append(row)
    dataRowGenerator = dataRowGenerator + 1
    # for every valid data with required window size compute moving average
    if (index < len(dataGeneratorMatrix) - windowSize + 1):

        # Store elements from i to i+window_size
        # in list to get the current window
        window = np.array(dataGeneratorMatrix[index : index  + windowSize])
        # Calculate the average of current window (not avaeraging the timeStep)
        windowAverage = np.mean(window[:,1:len(row)], axis = 0)

        timeStep = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][0]

        # Store the average of current
        # window in moving average list
        # insert timestep back into the array
        windowAverage = np.insert(windowAverage,0, timeStep)

        with open("dataAverage.csv", 'a') as datafile:
            writer = csv.writer(datafile)
            writer.writerow(windowAverage)
        index+=1

  print("All data Read from run_data!")

def animate(i):
  dataAverage = np.loadtxt(open("dataAverage.csv", "rb"), delimiter=",").astype("float")
  dataRaw = np.loadtxt(open("testNumbers.csv", "rb"), delimiter=",").astype("float")

  # time steps should be the same across files
  timestep = dataRaw[-310:, 0]
  timestep_avg = dataRaw[-310,0]
  
  # loadcell 1 data
  y_lc1_avg = dataAverage[-310:, 1]
  y_lc1_raw= dataRaw[-310:, 1]

  # loadcell 2 data
  y_lc2_avg = dataAverage[-310:, 2]
  y_lc2_raw= dataRaw[-310:, 2]

  # Accelorometer 1 data
  acc_x_avg = dataAverage[-310:, 3]
  acc_x_raw = dataRaw[-310:, 3]
  acc_y_avg = dataAverage[-310:, 4]
  acc_y_raw = dataRaw[-310:, 4]
  acc_z_avg = dataAverage[-310:, 5]
  acc_z_raw = dataAverage[-310:, 5]
  
  axs[0].clear()
  axs[0].plot(timestep, y_lc1_avg, timestep,y_lc1_raw)

  axs[1].clear()
  axs[1].plot(timestep, y_lc2_avg, timestep,y_lc2_raw)

  axs[2].clear()
  axs[2].plot(timestep, acc_x_avg, timestep,acc_x_raw, timestep,acc_y_avg, timestep, acc_y_raw)


def plotData():
  
  # reading the file
  with open("test.csv", "r") as readfile:
    reader = csv.reader(readfile)
    rollingAverage(reader)
    
  ani = animation.FuncAnimation(fig, animate, interval = 30)
  plt.show(block=False)
  exit = input("Press Enter to stop: ")
  while (exit != ""):
      exit = input("Press Enter to stop: ")
  

plotData()