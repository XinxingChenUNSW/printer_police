import socket
import csv
from struct import unpack

# Set up socket
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(('172.20.10.2', 5000))
s.listen(0)

print(s.getsockname())

# Define start and stop bytes
start_bytes = "START".encode('utf-8')
stop_bytes = "DOVIC".encode('utf-8')

num_bytes = [2, 12, 1]
data_type = ['f', 'f', 'i']

# load_cell_bytes = 2
# imu_bytes = 12
# encoder_bytes = 1

total_size = 5

# Csv writer
f = open('data_out.csv', 'w')
writer = csv.writer(f)

while True:
    client, addr = s.accept()
    print("Connected to client, writing to csv...")

    while True:
        content = client.recv()

        if len(content) == 0:
            break

        curr_ptr = -1

        # Find start bytes
        for i in range(26):
            if content[i:i+len(start_bytes)] == start_bytes:
                
                curr_ptr = i + len(start_bytes)
                break
        
        if curr_ptr == -1:
            continue

        data_row = []

        for size, idx in enumerate(num_bytes):
            byteSize = size * 4
            val = unpack(data_type[idx], content[curr_ptr: curr_ptr + byteSize])
            data_row.append(val)
            curr_ptr += byteSize

        # Decode bytes
        # for _ in range(total_size):
        #     val = unpack('f', content[curr_ptr: curr_ptr+4])[0]
        #     data_row.append(val)
        #     curr_ptr += 4
        print(data_row)
        # writer.writerow(data_row)

    print("Closing connection")
    client.close()