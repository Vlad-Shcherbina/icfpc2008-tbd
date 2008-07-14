import time
import sys
import socket
import errno
import re
import new
from threading import Thread, Semaphore

def slotsToDict(object):
	d = {}
	for attr in object.__class__.__slots__:
		d[attr] = getattr(object, attr)
	return d;
		
################
# objects

class StaticObject(object):
	__slots__ = ("kind", "x", "y", "radius")
	
	def __eq__(self,other):
		if not isinstance(other,StaticObject):
			return False
		return self.kind==other.kind and \
			self.x==other.x and \
			self.y==other.y and \
			self.radius==other.radius

	def __hash__(self):
		return  hash(self.kind) + \
				113*hash(self.x+self.y*.91234+self.radius*3.1415)

	def __repr__(self):
		return "Object" + repr(slotsToDict(self))

class Martian(object):
	__slots__ = ("x", "y", "dir", "speed")
	
	def __repr__(self):
		return "Martian" + repr(slotsToDict(self))

################
# events

class InitData(object):
	__slots__ = (
		"dx", "dy",
		"timeLimit",
		"minSensor","maxSensor",
		"maxSpeed", "maxTurn", "maxHardTurn")

	def __init__(self, command):
		slots = self.__class__.__slots__
		for i, s in enumerate(command[1:-1]):
			setattr(self, slots[i], float(s))
		self.timeLimit *= 0.001


class Telemetry(object):
	__slots__ = (
		"timeStamp", 
		"ctl",
		"x", "y",
		"dir", "speed",
		"objects",
		"localTimeStamp",
		"moreMessagesWaiting")
	
	def __init__(self, command):
		self.localTimeStamp = time.clock()
		
		slots = self.__class__.__slots__
		
		pos = 1 
		for s in slots[:-3]: #skip objects, localTimeStamp and moreMessagesWaiting
			if s != "ctl":
				setattr(self, s, float(command[pos]))
			else:
				self.ctl = command[pos]
			pos += 1

		self.timeStamp *= 0.001
		
		objs = []
		
		while True:
			if command[pos] == "m":
				obj = Martian()
				pos += 1
				for s in obj.__class__.__slots__:
					setattr(obj, s, float(command[pos]))
					pos += 1
				objs.append(obj)
			elif command[pos] == ";":
				break
			else:
				obj = StaticObject()
				obj.kind = command[pos]
				pos += 1
				for s in obj.__class__.__slots__[1:]:
					setattr(obj, s, float(command[pos]))
					pos += 1
				
				if obj.kind != "h":
					objs.append(obj)
					
		self.objects = objs



class Event(object):
	__slots__ = ("localTimeStamp", "tag", "timeStamp")  
	def __init__(self, command):
		self.localTimeStamp = time.clock()
		self.tag = command[0]
		self.timeStamp = float(command[1]) * 0.001
		

class EndOfRun(object):
	__slots__ = ("time", "score")  
	
	def __init__(self, command):
		self.time = float(command[1])
		self.score = float(command[2])
		
		

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
# networking

ConState_Initializing = 0
ConState_Running = 1
ConState_Closed = 2 

messageBufferSize = 128

class Connection(Thread):
	"""
	This class is responsible for connection with the rover.

	It maintains `messages` field which can be consumed by client 
	from the beginning. But it is better to use `hasMessage` and `popMessage`
	methods.

	`update` have to be called periodically
	"""
	
	__slots__ = ("socket", "state", "abortRequested", "buf", 
				 "conparams", "messageBuffer", "writePtr", "readPtr")
	#"messages", "lock"  
	
	def __init__(self, ip, port):
		Thread.__init__(self)
		
		self.conparams = (ip, port)
		self.socket = None
		self.state = ConState_Initializing
		self.abortRequested = False

		self.buf = ""
#		self.messages = []
#		self.lock = Semaphore()

		self.writePtr = 0
		self.readPtr = 0
		self.messageBuffer = [None for i in range(messageBufferSize)]
		
	def run(self):
		"""
		receive information from rover (if any) and 
		put it into `messages` field
		"""
		try:
			self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 
			try: self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
			except:
				print "setsockopt failed!!!"
				pass
			self.socket.setblocking(1)
			self.socket.connect(self.conparams)
			
			self.state = ConState_Running
			while not self.abortRequested:
				try:
					received = self.socket.recv(1024)
				except socket.error,e:
					print 'protocol.py: DEBUG: socket error on receive'
					break;
				
				if len(received) == 0: # socket closed
					break
				
				self.buf += received
				m = re.search(";",self.buf)
				while m:
					command = self.buf[:m.end()]
					self.addMessage(eventTypes[command[0]](command.split()))
					self.buf = self.buf[m.end():]
					m = re.search(";",self.buf)
					
			print "protocol.py: thread normally terminated"
		finally:
			self.state = ConState_Closed
			if self.socket != None:
				self.socket.close()
			
		
	def addMessage(self, message):
		self.messageBuffer[self.writePtr] = message

		tmp = self.writePtr + 1
		if tmp >= messageBufferSize:
			tmp = 0
		
		if tmp != self.readPtr:
			self.writePtr = tmp
		else:
			# we have a congestion. but we won't dump core!
			print "WARNING! Message buffer congestion!"
			
#		self.lock.acquire(True)
#		self.messages.append(message)
#		self.lock.release()
		

	def hasMessage(self):
		return self.writePtr != self.readPtr
	
#		self.lock.acquire(True)
#		rt = len(self.messages) > 0
#		self.lock.release()
#		return rt


	def popMessage(self):
		"""
		Returns None if there is no messages in queue
		"""
		
		if self.writePtr == self.readPtr:
			return None
		
		msg = self.messageBuffer[self.readPtr]
		self.messageBuffer[self.readPtr] = None #we don't want messages lying around
		
		tmp = self.readPtr + 1
		if tmp >= messageBufferSize:
			tmp = 0
		self.readPtr = tmp
		
		return msg
		
#		self.lock.acquire(True)
#		rt = self.messages.pop(0)
#		self.lock.release()
#		return rt


	def sendCommand(self,command):
		"""Send a single command to the rover"""
		if command=="":
			return
		assert re.match(r"([ab]?[lr]?;)+$",command)
		
		if self.state != ConState_Running:
			return
		
		try:
			self.socket.sendall(command)
		except:
			print "proto: [DEBUG] socket error on send"
			pass

	def close(self):
		self.abortRequested = True
