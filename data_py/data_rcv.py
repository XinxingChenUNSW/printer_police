import socket

s = socket.socket()

s.bind(('172.20.10.2', 5000))
s.listen(0)

print(s.getsockname())

while True:
    client, addr = s.accept()

    while True:
        content = client.recv(32)
        if len(content) == 0:
            break
        else:
            print(content)
            pass

    # client.send(bytes('{\"accel\",\"gyro\",\"time\":1}', "utf-8"))
    print("Closing connection")
    client.close()