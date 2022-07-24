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
    threshold_percent = 0.15 # a percentage of the currently tracked mean that the new data must be within to affect the rolling average
    outlier_damp = 0.9
    prevWindowAv =[]
    milliPerCount = (1.0000)/(28.3465)
    # The number of moving averages you have found
    index = 0
    # threshold flag
    first_run = True
    
    while True:

        # with open("test.csv", "r") as readfile:
        #     reader = csv.reader(readfile)
        #     for row in reader:
        while not rolling_a_q.empty():
            # grab a row of data 
            row = rolling_a_q.get()
            if (first_run == True):
                threshold_flags = [False] * (len(row)-1)
                tracked_mean = [00.00] * (len(row)-1)
                data_out = [00.00] * (len(row)-1)
                first_run = False
                # temp = np.array([])   
            # time.sleep(0.01)
            # # remove white spaces from test data and convert string to float
            # row = list(map(float, row[0].split()))
            # # write float numbers to file for plotting
            # with open("testNumbers.csv", 'a') as dataRawfile:
            #     writer = csv.writer(dataRawfile)
            #     writer.writerow(row)

            # append row to dataGeneratorMatrix to keep track of data
            dataGeneratorMatrix.append(row)
            # increment the index that keeps track of dataGeneratorMatrix
            dataRowGenerator = dataRowGenerator + 1

            # for every valid data with required window size compute moving average
            if (index < len(dataGeneratorMatrix) - windowSize + 1): 

                # Store elements from i to i+window_size
                # in list to get the current window for every data point
                # grabs the last windowSize (11 for example) samples 

                window = np.array(dataGeneratorMatrix[index : index  + windowSize])
                for data_idx in range(threshold_flags):
                    if (threshold_flags[data_idx] == False):
                        # dont threshold
                        # compute average
                        data_out[data_idx] = np.mean(window[:, data_idx+1], axis = 0)
                        # store this average
                        tracked_mean[data_idx] = data_out[data_idx]
                        # allow threshold flag, change if targeting certain data for thresholding
                        threshold_flags[data_idx] = True
                    else:
                        # if latest data is OUTSIDE threshold
                        if (abs(dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][data_idx+1] - tracked_mean[data_idx]) > threshold_percent*tracked_mean[data_idx]):
                            # simply set the data output to the value outside threshold
                            data_out[data_idx] = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][data_idx+1]
                            # UNUSED
                            # however, we cant just ignore the value since it might be valid, 
                            # so apply a weighting to reduce the impact on the tracked mean
                            # temp = np.append(temp, window[:, data_idx+1], axis = 1)
                            # temp = temp[-1, data_idx]*outlier_damp
                            # simply store the mean with the outlier so it allows the rolling average to still respond to consistent outlier data
                            tracked_mean[data_idx] = np.mean(window[:, data_idx+1], axis = 0)

                        else:
                            # compute average
                            data_out[data_idx] = np.mean(window[:, data_idx+1], axis = 0)
                            # store this average
                            tracked_mean[data_idx] = data_out[data_idx]
                            # allow threshold flag, change if targeting certain data for thresholding
                            threshold_flags[data_idx] = True
                
                # if (threshold_flag == False):
                #     # dont threshold because either:
                #     #                       - theres no currently tracked average because we just started
                #     #                       - the tracked_mean was reset and so no threshold 
                #     windowAverage = np.mean(window[:,1:len(row)], axis = 0)
                #     tracked_mean = windowAverage
                # else: # check data if we need to threshold and also check if tracked_mean must be reset
                #     # threshold means if the latest data point is too far off from 
                #     # the previous mean, output the raw data as valid data
                #     if (window[-1,1:len(row)] - tracked_mean)
                # # Calculate the average of current window (not avaeraging the timeStep)
                # windowAverage = np.mean(window[:,1:len(row)], axis = 0)

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

                # timeStep = dataGeneratorMatrix[dataRowGenerator - (windowSize - 1)][0]
                timeStep = dataGeneratorMatrix[-1][0]

                windowAverage = np.insert(tracked_mean, 0, timeStep)
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