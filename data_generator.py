from random import randint
import csv
import time
import numpy as np

with open("dataRaw.csv", "w+") as datafile:
    pass

with open("dataAverage.csv", "w+") as datafile:
    pass

dataGenerator = [0.0]*5
movingAverage = [0.0]*5
dataGeneratorMatrix = []
movingAverageMatrix = []
dataRowGenerator = 1
movingAverageRow = 1
windowSize = 11
index = 0

while(True):
    time.sleep(0.01)
    dataGenerator = [dataGenerator[0]+0.1, 0.0, 0.0, 0.0, 0.0]

    for i in range(1, len(dataGenerator)):
        dataGenerator[i] += 0.1 * randint(-10, 10)

    with open("dataRaw.csv", 'a') as dataRawfile:
        writer = csv.writer(dataRawfile)
        writer.writerow(dataGenerator)

    dataGeneratorMatrix.append(dataGenerator)

    dataRowGenerator = dataRowGenerator + 1

    if (index < len(dataGeneratorMatrix) - windowSize + 1):
        # Store elements from i to i+window_size
        # in list to get the current window

        window = np.array(dataGeneratorMatrix[index : index  + windowSize])
    
        # Calculate the average of current window
        windowAverage = np.mean(window[:,1:5], axis = 0)

        timeStep = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][0]

        # Store the average of current
        # window in moving average list
        windowAverage = np.insert(windowAverage,0, timeStep)

        with open("dataAverage.csv", 'a') as datafile:
            writer = csv.writer(datafile)
            writer.writerow(windowAverage)
        index+=1

print(dataGeneratorMatrix)

