import sys
import socket
import errno
import re
import new

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
	r"T (?P<timeStamp>%s) (?P<vehicleCtl>[ab\-][Ll\-rR]) "+
	r"(?P<vehicleX>%s) (?P<vehicleY>%s) "+
	r"(?P<vehicleDir>%s) (?P<vehicleSpeed>%s) "+
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
			"timeStamp","vehicleX","vehicleY","vehicleDir","vehicleSpeed"])
		self.timeStamp *= 0.001

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

class Connection(object):
	"""
	This class is responsible for connection with the rover.

	It maintains `messages` field which can be consumed by client 
	from the beginning. But it is better to use `hasMessage` and `popMessage`
	methods.

	`update` have to be called periodically
	"""
	def __init__(self,ip,port):
#		print "Connecting %s:%s..."%(ip,port)
		self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#		self.socket.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

		self.socket.connect((ip,port))
	
		self.socket.setblocking(0)
		self.socket.settimeout(0.005)

		self.buf = ""
		self.messages = []

	def update(self):
		"""
		receive information from rover (if any) and 
		put it into `messages` field
		"""
		try:
			received = self.socket.recv(1024)
			self.buf += received
		except socket.timeout:
			pass
		except socket.error,e:
			if e[0] not in [11,errno.EWOULDBLOCK]:
				raise

		while True:
			m = re.search(";",self.buf)
			if m:
				command = self.buf[:m.end()]
				self.messages.append(eventTypes[command[0]](command))
				self.buf = self.buf[m.end():]
			else:
				return

	def hasMessage(self):
		return len(self.messages) > 0

	def popMessage(self):
		return self.messages.pop(0)

	def sendCommand(self,command):
		"""Send a single command to the rover"""
		assert re.match(r"[ab]?[lr]?;$",command)
		while True:
			try:
				n = self.socket.send(command)
				command = command[n:]
				if command == "":
					break
			except socket.timeout:
				pass
			except socket.error,e:
				if e[0] not in [11,errno.EWOULDBLOCK]:
					raise

	def close(self):
		self.socket.close()
	