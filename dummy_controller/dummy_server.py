#!/usr/bin/python

import socket
import time
import re
import errno
from random import *
import math

host = ""
port = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))

s.listen(1)

conn, addr = s.accept()
print 'Connected by', addr

conn.settimeout(0.1)


accel = 2
brake = 2
drag = 0.1

rotAccel = 150
maxTurn = 50
maxHardTurn = 100

mapSize = 30

conn.send("I %s %s 999.9 0.5 3 %s %s %s ;" %
			(mapSize,mapSize,math.sqrt(accel/drag),maxTurn,maxHardTurn) )


objs="".join([
	"b %s %s %s "%((random()-0.5)*mapSize,(random()-0.5)*mapSize,random()*5)
	for i in range(20)])


x = 5
y = 6
v = 0
angle = 30
data = ""
acc = 0
rot = 0
rotSpeed = 0
prevTime = time.clock()
for i in range(1):
	t = 0
	time.sleep(0.1)
	for i in range(1000):
		try:
			data += conn.recv(1024)
			time.sleep(0.001)
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
#			print command,
			if command.find("a") != -1 and acc<1:
				acc += 1
			elif command.find("b") != -1 and acc>-1:
				acc -= 1

			if command.find("r") != -1 and rot<2:
				rot += 1
			elif command.find("l") != -1 and rot>-2:
				rot -= 1

		ctl = "b-a"[acc+1]+"Ll-rR"[rot+2]

		print ctl
		conn.send(
			"T %s %s %s %s %s %s "%(t*1000,ctl,x,y,angle,v) +
			"b -4.000 7.000 1.000 " +
			"b -1.000 5.000 1.000 " +
			objs +
			"m -2.000 8.000 90.0 9.100 ;")

		objs = ""
		time.sleep(0.01+random()*0.005)
		dt = time.clock()-prevTime
		prevTime += dt
		t += dt
		x += math.cos(math.radians(angle))*v*dt
		y += math.sin(math.radians(angle))*v*dt

		desiredRotSpeed = \
			[maxHardTurn,maxTurn,0,-maxTurn,-maxHardTurn][rot+2]
		if rotSpeed<desiredRotSpeed:
			rotSpeed += dt*rotAccel
		if rotSpeed>desiredRotSpeed:
			rotSpeed -= dt*rotAccel
		angle += rotSpeed*dt

		v += dt*([-brake,0,accel][acc+1] - drag*v*v + random()*0.001)

	conn.send("S 0 ;")
	conn.send("E 0 999.9 ;")

while True:
	try:
		data += conn.recv(1024)
		time.sleep(0.01)
	except socket.timeout:
		break
	except socket.error,e:
		if e[0] not in [11,errno.EWOULDBLOCK]:
			raise
		break


conn.close()

