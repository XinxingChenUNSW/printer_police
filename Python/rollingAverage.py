from random import randint
import csv
import time
import numpy as np
from multiprocessing import Queue

'''
Input: Gyro values as List[float]: (gyro_x, gyro_y, gyro_z)
Output: Corrected gyro
'''
def gyroCorrection(gyro_in):
    # TODO: Implement this
    gyro_out = gyro_in
    return gyro_out


'''
Input: Accelerometer values as List[float]: (accel_x, accel_y, accel_z)
Output: Corrected Accelerometer
'''
def accelCorrection(accel_in):
    # TODO: Implement this
    accel_out = accel_in
    return accel_out

# TODO: make dataGeneratorMatrix to window size
def rolling_average(rolling_a_q: Queue, csv_queue: Queue, plot_queue: Queue):

    # initialise variables
    dataGeneratorMatrix = []
    dataRowGenerator = 1
    windowSize = 11
    prevWindowAv =[]
    milliPerCount = (1.0000)/(28.3465)
    # The number of moving averages you have found
    index = 0

    while True:

        # with open("test.csv", "r") as readfile:
        #     reader = csv.reader(readfile)
        #     for row in reader:
        while not rolling_a_q.empty():
            row = rolling_a_q.get()
            # time.sleep(0.01)
            # # remove white spaces from test data and convert string to float
            # row = list(map(float, row[0].split()))
            # # write float numbers to file for plotting
            # with open("testNumbers.csv", 'a') as dataRawfile:
            #     writer = csv.writer(dataRawfile)
            #     writer.writerow(row)

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

                # timeStep = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][0]
                timeStep = dataGeneratorMatrix[-1][0]

                # Store the average of current
                # window in moving average list
                # insert timestep back into the array
                # loads = windowAverage[0:2]
                # gyro1 = gyroCorrection(windowAverage[2:5])
                # gyro2 = gyroCorrection(windowAverage[5:8])
                # acc1 = accelCorrection(windowAverage[8:11])
                # acc2 = accelCorrection(windowAverage[11:14])
                # print(loads)
                # windowAverage = [timeStep] + loads + gyro1 + gyro2 + acc1 + acc2 + windowAverage[14:]

                windowAverage = np.insert(windowAverage,0, timeStep)
                encoderCount = windowAverage[-1]
                position = encoderCount*milliPerCount
                windowAverage = np.insert(windowAverage,len(windowAverage), position)
                if (len(prevWindowAv) == 0):
                    # calculate velocity 
                    windowAverage = np.insert(windowAverage,len(windowAverage), 0)
                    # calculate acceleration
                    windowAverage = np.insert(windowAverage,len(windowAverage), 0)
                else:
                # calculate velocity
                    finalDist = position
                    finalTime = timeStep
                    prevDist = prevWindowAv[len(windowAverage) - 1]
                    prevTime = prevWindowAv[0]
                    velocity = (finalDist-prevDist)/(finalTime-prevTime)
                    windowAverage = np.insert(windowAverage,len(windowAverage), velocity)
                    # calculate acceleration
                    finalVel = velocity
                    prevVel = prevWindowAv[len(windowAverage) - 1]
                    acceleration = (finalVel-prevVel)/(finalTime-prevTime)
                    windowAverage = np.insert(windowAverage,len(windowAverage), acceleration)
                # with open("dataAverage.csv", 'a') as datafile:
                #     writer = csv.writer(datafile)
                #     writer.writerow(windowAverage)


                csv_queue.put(windowAverage)
                plot_queue.put(windowAverage)
                prevWindowAv = windowAverage

                index+=1

    print("All data Read!")