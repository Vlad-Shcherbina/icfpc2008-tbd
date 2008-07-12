#!/usr/bin/python

import socket
import time

host = ""
port = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))

s.listen(1)

conn, addr = s.accept()
print 'Connected by', addr

conn.send("I 10 10 999.9 1 2 1 2 3.3 ;")
x = 0
v = 0
y = 0
angle = 0
for i in range(1):
	t = 0
	time.sleep(0.5)
	for i in range(200):
		dt = 0.02
		time.sleep(dt)
		t += dt
		x += v*dt
		v += dt
		conn.send("T %s a- %s %s %s %s b -220.000 750.000 12.000 m -240.000 812.000 90.0 9.100 ;"%(t*1000,x,y,angle,v))
	conn.send("S 0 ;")
	conn.send("E 0 999.9 ;")
while 1:
    data = conn.recv(1024)
    if not data: 
    	break
#    conn.send(data)


conn.close()

