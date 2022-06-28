from random import randint
import csv
import time

with open("data.csv", "w+") as datafile:
    pass

data = [0.0] * 5
while(True):
    time.sleep(0.01)
    with open("data.csv", 'a') as datafile:
        writer = csv.writer(datafile)
        writer.writerow(data)
    data[0] += 0.01
    for i in range(1, len(data)):
        data[i] += 0.1 * randint(-10, 10)
