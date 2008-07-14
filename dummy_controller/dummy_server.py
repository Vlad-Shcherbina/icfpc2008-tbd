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


framePeriod = 0.1

mapSize = 80
timeLimit = 60
objCount = 0

accel = 3
brake = 2
drag = 0.02

rotAccel = 100
maxTurn = 50
maxHardTurn = 100


conn.send("I %s %s %s 0.5 3 %s %s %s ;" %
			(mapSize,mapSize,timeLimit*1000,
			 math.sqrt(accel/drag),maxTurn,maxHardTurn) )


objs="".join([
	"b %s %s %s "%((random()-0.5)*mapSize,(random()-0.5)*mapSize,random()*5)
	for i in range(00)])

x = -20
y = 6
v = 0
angle = 30
data = ""
acc = 0
rot = 0
rotSpeed = 0
t = 0

prevTime = 0

def timeStep():
	global x,y,v,angle,acc,rot,rotSpeed,t,data,prevTime
	dt = time.clock()-prevTime
	prevTime += dt
	while True:
		m = re.match(r"[ab]?[lr]?;",data)
		if m is None:
			break
		data = data[m.end():]
		command = m.group()
		print command,
		if command.find("a") != -1 and acc<1:
			acc += 1
		elif command.find("b") != -1 and acc>-1:
			acc -= 1
		
		if command.find("r") != -1 and rot<2:
			rot += 1
		elif command.find("l") != -1 and rot>-2:
			rot -= 1
			
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
	if v<0:
		v = 0


def optSend():
	global lastSendTime
	global objs
	ctl = "b-a"[acc+1]+"Ll-rR"[rot+2]
	print ctl
	if lastSendTime+framePeriod<time.clock():
		conn.send(
				  "T %s %s %s %s %s %s "%(t*1000,ctl,x,y,angle,v) +
						objs +
			";")
		lastSendTime = time.clock()
	objs = ""
	

######### main loop
for i in range(1):
	t = 0
	time.sleep(0.1)
	 
	startTime = time.clock()
	prevTime = time.clock()
	lastSendTime = 0
	while time.clock()<startTime+timeLimit:
		optSend()
		try:
			data += conn.recv(1024)
			time.sleep(0.01)
			timeStep()
			optSend()
		except socket.timeout:
			pass
		except socket.error,e:
			if e[0] not in [11,errno.EWOULDBLOCK]:
				raise

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

