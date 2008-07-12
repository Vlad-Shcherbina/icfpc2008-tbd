import sys
import socket
import errno
import re
import new
from threading import Thread, Semaphore

maxRuns = 1
messages = []

################
# parsing tools

floatRE = r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?"
initRE = re.compile((
	r"I (?P<dx>%s) (?P<dy>%s) (?P<timeLimit>%s) "+
	r"(?P<minSensor>%s) (?P<maxSensor>%s) "+
	r"(?P<maxSpeed>%s) (?P<maxTurn>%s) (?P<maxHardTurn>%s) ;$" ) % \
	(floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,floatRE,) )
telemetryRE = re.compile((
	r"T (?P<timeStamp>%s) (?P<ctl>[ab\-][Ll\-rR]) "+
	r"(?P<x>%s) (?P<y>%s) "+
	r"(?P<dir>%s) (?P<speed>%s) "+
	r"(?P<objects>.*);$") % \
	(floatRE,floatRE,floatRE,floatRE,floatRE,) )
staticObjectRE = re.compile(
	r"(?P<kind>[bch]) (?P<x>%s) (?P<y>%s) (?P<radius>%s) " % \
	(floatRE,floatRE,floatRE,) )
martianRE = re.compile(
	r"m (?P<x>%s) (?P<y>%s) (?P<dir>%s) (?P<speed>%s) " % \
	(floatRE,floatRE,floatRE,floatRE,))
eventRE = re.compile(
	r"(?P<tag>[BCKS]) (?P<timeStamp>%s) ;$"%floatRE )
endOfRunRE = re.compile(
	r"E (?P<time>%s) (?P<score>%s) ;$"%(floatRE,floatRE,) )

def convertFloats(obj,fields):
	for f in fields:
		setattr(obj,f,float(getattr(obj,f)))

class InitData(object):
	"""
	Fields:
		dx,dy
		timeLimit,
		minSensor,maxSensor,
		maxSpeed,maxTurn,maxHardTurn
	"""
	def __init__(self,command):
		m = initRE.match(command)
		assert m
		self.__dict__ = m.groupdict()
		convertFloats(self,[
			"dx","dy","timeLimit",
			"minSensor","maxSensor",
			"maxSpeed","maxTurn","maxHardTurn"])
		self.timeLimit *= 0.001


class StaticObject(object):
	"""
	Fields:
		x,y,radius
	"""
	def __eq__(self,other):
		if not isinstance(other,StaticObject):
			return False
		eps=1e-6
		return self.kind==other.kind and \
			abs(self.x-other.x)<eps and \
			abs(self.y-other.y)<eps and \
			abs(self.radius-other.radius)<eps

	def __repr__(self):
		return "Object"+repr(self.__dict__)

class Martian(object):
	"""
	Fields:
		x,y,dir,speed
	"""
	def __repr__(self):
		return "Martian"+repr(self.__dict__)

class Telemetry(object):
	"""
	Fields:
		timeStamp,
		vehicleCtl,
		vehicleX,vehicleY,
		vehicleDir,VehicleSpeed,
		objects

	`objects` is array of static objects and martians
	"""
	def __init__(self,command):
		m = telemetryRE.match(command)
		assert m
		self.__dict__ = m.groupdict()
		objs = m.groupdict()["objects"]
		pos = 0
		self.objects = []
		while pos != len(objs):
			if objs[pos] == "m":
				obj = Martian()
				m = martianRE.match(objs,pos)
				assert m
				obj.__dict__ = m.groupdict()
				convertFloats(obj,["x","y","dir","speed"])
				self.objects.append(obj)
			else:
				obj = StaticObject()
				m = staticObjectRE.match(objs,pos)
				assert m
				obj.__dict__ = m.groupdict()
				convertFloats(obj,["x","y","radius"])
				self.objects.append(obj)
			pos = m.end()

		convertFloats(self,[
			"timeStamp","x","y","dir","speed"])
		self.timeStamp *= 0.001 # it was given in milliseconds


class Event(object):
	"""
	Fields:
		timeStamp
	"""
	def __init__(self,command):
		m = eventRE.match(command)
		assert m
		self.__dict__ = m.groupdict()
		convertFloats(self,["timeStamp"])
		self.timeStamp *= 0.001

class EndOfRun(object):
	"""
	Fields:
		time,score
	"""
	def __init__(self,command):
		m = endOfRunRE.match(command)
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

class Connection(Thread):
	"""
	This class is responsible for connection with the rover.

	It maintains `messages` field which can be consumed by client 
	from the beginning. But it is better to use `hasMessage` and `popMessage`
	methods.

	`update` have to be called periodically
	"""
	def __init__(self,ip,port):
		Thread.__init__(self)
#		print "Connecting %s:%s..."%(ip,port)
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#		self.socket.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

		self.socket.connect((ip,port))
	
		self.socket.setblocking(1)
#		self.socket.settimeout(0.005)

		self.buf = ""
		self.messages = []
		self.running = False
		self.lock = Semaphore()

	def run(self):
		"""
		receive information from rover (if any) and 
		put it into `messages` field
		"""
		self.running = True
		try:
			while self.running:
				received = self.socket.recv(1024)
				if len(received) == 0: # socket closed
					self.running = False
					continue
				self.buf += received
				m = re.search(";",self.buf)
				while m:
					command = self.buf[:m.end()]
#					print '[DEBUG] adding message'
					self.addMessage(eventTypes[command[0]](command))
					self.buf = self.buf[m.end():]
					m = re.search(";",self.buf)
#		except socket.timeout,e:
#			print 'DEBUG: socket timeout'
#			self.running = False
#			pass
		except socket.error,e:
			print 'DEBUG: socket closed'
			self.running = False
			
	def stopRun(self):
		self.running = False
		self.socket.close()
		
	def isRunning(self):
		return self.running
		
	def addMessage(self, message):
		self.lock.acquire(True)
		self.messages.append(message)
		self.lock.release()

	def hasMessage(self):
		self.lock.acquire(True)
		rt = len(self.messages) > 0
		self.lock.release()
		return rt

	def popMessage(self):
		self.lock.acquire(True)
		rt = self.messages.pop(0)
		self.lock.release()
		return rt

	def sendCommand(self,command):
		"""Send a single command to the rover"""
		if command=="":
			return
		assert re.match(r"([ab]?[lr]?;)+$",command)
		self.socket.sendall(command)

	def close(self):
		self.socket.close()
	