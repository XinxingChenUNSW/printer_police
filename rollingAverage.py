from random import randint
import csv
import time
import numpy as np

# initialise variables
dataGeneratorMatrix = []
dataRowGenerator = 1
windowSize = 11
# The number of moving averages you have found
index = 0
with open("test.csv", "r") as readfile:
    reader = csv.reader(readfile)
    for row in reader:
        time.sleep(0.01)
        # remove white spaces from test data and convert string to float
        row = list(map(float, row[0].split()))
        # write float numbers to file for plotting
        with open("testNumbers.csv", 'a') as dataRawfile:
            writer = csv.writer(dataRawfile)
            writer.writerow(row)

        # append row to dataGeneratorMatrix
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

print("All data Read!")