#!/usr/bin/python

import sys
import socket
import re
import new

maxRuns = 5


################
# parsing tools

floatRE = r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?"
initRE = (
	r"I (?P<dx>%s) (?P<dy>%s) (?P<timeLimit>%s) "+
	r"(?P<minSensor>%s) (?P<maxSensor>%s) "+
	r"(?P<maxSpeed>%s) (?P<maxTurn>%s) (?P<maxHardTurn>%s) ;$" ) % \
	(floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,)
telemetryRE = (
	r"T (?P<timeStamp>%s) (?P<vehicleCtl>[ab\-][Ll\-rR]) "+
	r"(?P<vehicleX>%s) (?P<vehicleY>%s) "+
	r"(?P<vehicleDir>%s) (?P<vehicleSpeed>%s) "+
	r"(?P<objects>.*);$") % \
	(floatRE,floatRE,floatRE,floatRE,floatRE,)
staticObjectRE = r"(?P<kind>[bch]) (?P<x>%s) (?P<y>%s) (?P<radius>%s) " % \
	(floatRE,floatRE,floatRE,)
martianRE = r"m (?P<x>%s) (?P<y>%s) (?P<dir>%s) (?P<speed>%s) " % \
	(floatRE,floatRE,floatRE,floatRE,)
eventRE = r"(?P<tag>[BCKS]) (?P<timeStamp>%s) ;$"%floatRE
endOfRunRE = r"E (?P<time>%s) (?P<score>%s) ;$"%(floatRE,floatRE,)

def convertFloats(obj,fields):
	for f in fields:
		setattr(obj,f,float(getattr(obj,f)))

class InitData(object):
	def __init__(self,command):
		m = re.match(initRE,command)
		assert m
		self.__dict__ = m.groupdict()
		convertFloats(self,[
			"dx","dy","timeLimit",
			"minSensor","maxSensor",
			"maxSpeed","maxTurn","maxHardTurn"])


class StaticObject(object):
	pass

class Martian(object):
	pass

class Telemetry(object):
	def __init__(self,command):
		m = re.match(telemetryRE,command)
		assert m
		self.__dict__ = m.groupdict()
		objs = m.groupdict()["objects"]
		self.objects = []
		while objs!="":
			if objs[0] == "m":
				obj = Martian()
				m = re.match(martianRE,objs)
				assert m
				obj.__dict__ = m.groupdict()
				convertFloats(obj,["x","y","dir","speed"])
				self.objects.append(obj)
			else:
				obj = StaticObject()
				m = re.match(staticObjectRE,objs)
				assert m
				obj.__dict__ = m.groupdict()
				convertFloats(obj,["x","y","radius"])
				self.objects.append(obj)
			objs = objs[m.end():]

		convertFloats(self,[
			"timeStamp","vehicleX","vehicleY","vehicleDir","vehicleSpeed"])

class Event(object):
	def __init__(self,command):
		m = re.match(eventRE,command)
		assert m
		self.__dict__ = m.groupdict()
		convertFloats(self,["timeStamp"])

class EndOfRun(object):
	def __init__(self,command):
		m = re.match(endOfRunRE,command)
		assert m
		self.__dict__ = m.groupdict()
		convertFloats(self,[
			"time","score"])

eventTypes = {
	"I": InitData,
	"T": Telemetry,
	"B": Event,
	"C": Event,
	"K": Event,
	"S": Event,
	"E": EndOfRun,
}

###########
# networking tools

def initConnection():
	global s
	global buf
	global messages

	if len(sys.argv) != 3:
		print "specify ip and port"
		exit(1)

	ip = sys.argv[1]
	port = int(sys.argv[2])

	print "Connecting %s:%s..."%(ip,port)
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#	s.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

	s.connect((ip,port))
	
	s.settimeout(0)

	buf = ""
	messages = []


def update():
	global buf
	try:
		received = s.recv(1024)
		buf += received

	except socket.timeout:
		pass
	while True:
		m = re.search(";",buf)
		if m:
			command = buf[:m.end()]
			messages.append(eventTypes[command[0]](command))
			buf = buf[m.end():]
		else:
			return

def sendCommand(command):
	while True:
		n = s.send(command)
		command = command[n:]
		if command == "":
			break


##################3
# main

initConnection()

currentRun = 0

while True:
	while messages != []:
		message = messages.pop(0)
		# message handling routine
#		print message.__dict__
		if isinstance(message,InitData):
			print "Run N%s started"%currentRun
			sendCommand(";")
		elif isinstance(message,EndOfRun):
			print "Run ended with score",message.score
			currentRun += 1
			if currentRun == maxRuns:
				print "the end"
				s.close()
				exit(0)
	update()
	
