import sys
import filterpy as fp
import matplotlib.pyplot as plt
import numpy as np
import csv

# formats the csv data as numpy arrays of type np.float64
def format_np(list_):
    list_ = np.array(list_,dtype=object)                         # convert raw laser data to numpy array
    list_ = list_.astype(np.float64)                # cast to numpy.float64
    return list_

# open both files
f_test = open('test1.csv', 'r')
f_laser = open('Laser_test1.csv', 'r')
# read as csv
csv_test = csv.reader(f_test, delimiter=' ')
csv_laser = csv.reader(f_laser)
# convert and store in list
list_test = list(csv_test)
list_laser = list(csv_laser)                        # line 24 always has headers, data from line 25 onwards

# supress printing in scientific notation
np.set_printoptions(suppress=True)

# cleaning the data
# test
for row in list_test:
    row.pop()

print(list_test[0])
list_test = np.array(list_test[0:-1])
print(list_test)
# temp = np.array(list_test[0])
# temp = temp.astype(np.float64)
# laser
laser_headings = list_laser[24]                     # in case we need the headings of the laser data
print(list_laser[26])
list_laser = format_np(list_laser[25:])             # grab the raw data from the laser data files and clean it


# plotting
plt.figure()
plt.plot(list_laser[:,0],list_laser[:,1])
plt.show()

f_test.close()
f_laser.close()