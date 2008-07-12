#!/usr/bin/python

import socket
import time
import re
import errno
import random

host = ""
port = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))

s.listen(1)

conn, addr = s.accept()
print 'Connected by', addr

conn.settimeout(0.005)


conn.send("I 10 10 999.9 1 2 1 2 3.3 ;")
x = 0
v = 0
y = 0
angle = 0
data = ""
accel = 0
drug = 0.1
for i in range(1):
	t = 0
	time.sleep(0.5)
	for i in range(200):
		try:
			data += conn.recv(1024)
		except socket.timeout:
			pass
		except socket.error,e:
			if e[0] not in [11,errno.EWOULDBLOCK]:
				raise
		while True:
			m = re.match(r"[ab]?[lr]?;",data)
			if m is None:
				break
			data = data[m.end():]
			command = m.group()
			print command,
			if command == "a;" and accel<1:
				accel += 1
			elif command == "b;" and accel>-1:
				accel -= 1

		ctl = "b-a"[accel+1]+"-"
		conn.send(
			"T %s %s %s %s %s %s "%(t*1000,ctl,x,y,angle,v) +
			"b -220.000 750.000 12.000 " +
			"m -240.000 812.000 90.0 9.100 ;")
		dt = 0.02
		time.sleep(dt)
		t += dt
		x += v*dt
		v += dt*(accel - drug*v*v + random.random()*0.001)

	conn.send("S 0 ;")
	conn.send("E 0 999.9 ;")

while True:
	try:
		data += conn.recv(1024)
	except socket.timeout:
		break
	except socket.error,e:
		if e[0] not in [11,errno.EWOULDBLOCK]:
			raise


conn.close()

