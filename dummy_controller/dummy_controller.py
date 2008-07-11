import sys
import socket
import re
import new


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

class InitData(object):
	def __init__(self,command):
		m = re.match(initRE,command)
		assert m
		self.__dict__ = m.groupdict()


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
				print repr(objs)
				obj = Martian()
				m = re.match(martianRE,objs)
				assert m
				obj.__dict__ = m.groupdict()
				self.objects.append(obj)
			else:
				obj = StaticObject()
				m = re.match(staticObjectRE,objs)
				assert m
				obj.__dict__ = m.groupdict()
				self.objects.append(obj)
			objs = objs[m.end():]

class Event(object):
	def __init__(self,command):
		m = re.match(eventRE,command)
		assert m
		self.__dict__ = m.groupdict()

class EnfOfRun(object):
	def __init__(self,command):
		m = re.match(endOfRunRE,command)
		assert m
		self.__dict__ = m.groupdict()

eventTypes = {
	"I": InitData,
	"T": Telemetry,
	"B": Event,
	"C": Event,
	"K": Event,
	"S": Event,
	"E": EnfOfRun,
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
	s.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

	s.connect((ip,port))
	
	s.settimeout(0)

	buf = ""
	messages = []


def update():
	global buf
	try:
		buf += s.recv(1024)
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

		

##################3
# main

initConnection()

while True:
	if messages!= []:
		print messages[0]
	messages = messages[1:]
	update()
	


#print InitData(i).__dict__
#print Telemetry(t).__dict__


#s.close()
