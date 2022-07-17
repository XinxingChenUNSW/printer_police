from random import randint
import csv
import time
import numpy as np

# initialise variables
dataGeneratorMatrix = []
dataRowGenerator = 1
windowSize = 11
prevWindowAv =[]
milliPerCount = (1.0000)/(28.3465)
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
            # Calcu late the average of current window (not avaeraging the timeStep)
            windowAverage = np.mean(window[:,1:len(row)], axis = 0)

            timeStep = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][0]

            # Store the average of current
            # window in moving average list
            # insert timestep back into the array
            windowAverage = np.insert(windowAverage,0, timeStep)
            encoderCount = windowAverage[15]
            position = encoderCount*milliPerCount
            print('milliPerCount', milliPerCount)
            print('position',position)
            print(len(windowAverage))
            windowAverage = np.insert(windowAverage,18, position)
            if (len(prevWindowAv) == 0):
              # calculate velocity 
              windowAverage = np.insert(windowAverage,19, 0)
              # calculate acceleration
              windowAverage = np.insert(windowAverage,20, 0)
            else:
              # calculate velocity
              finalDist = position
              finalTime = timeStep
              prevDist = prevWindowAv[18]
              prevTime = prevWindowAv[0]
              velocity = (finalDist-prevDist)/(finalTime-prevTime)
              windowAverage = np.insert(windowAverage,19, velocity)
              # calculate acceleration
              finalVel = velocity
              prevVel = prevWindowAv[19]
              acceleration = (finalVel-prevVel)/(finalTime-prevTime)
              windowAverage = np.insert(windowAverage,20, acceleration)


            with open("dataAverage.csv", 'a') as datafile:
                writer = csv.writer(datafile)
                writer.writerow(windowAverage)
            prevWindowAv = windowAverage
            index+=1

print(dataGeneratorMatrix)
print("All data Read!")