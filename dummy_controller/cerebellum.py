from uuid import _last_timestamp
import time
from random import choice
from numpy import *
from numpy.linalg import *
from math import *

from protocol import *

maxRuns = 6


class MinSQ(object):
	"""Class for minimal square optimization of given constraints"""
	def __init__(self,n):
		self.n = n
		self.a = zeros((n,n))
		self.b = zeros((n,))
	def addConstraint(self,c,d):
		"""Takes constraint of the form c*x=d into account"""
		m = array([[a*b for b in c] for a in c])
		self.a += m
		self.b += c*d
			
	def solve(self):
		try:
			self.x = solve(self.a,self.b)
		except LinAlgError:
			self.x = zeros((self.n,))
			

def subtractAngles(a,b):
	res = a-b
	while res < -180:
		res += 360
	while res > 180:
		res -= 360
	return res

def lerp(a, b, q):
	return a * (1 - q) + b * q

class FOFilter(object):
	def __init__(self, quotient, value = 0.0):
		self.quotient = quotient
		self.value = value
	
	def next(self, value):
		self.value = lerp(self.value, value, self.quotient)
	
	def __str__(self):
		return str(self.value)

#class RotationPredictor(object):
#	def __init__(self,dir,rotSpeed):
#		self.dir = dir
#		self.rotSpeed = rotSpeed

class Cerebellum(object):
	"""
	Cerebellum is responsible for movement parameters (such as drag) estimation
	It is also intended to provide
		`rotateTo`
		`moveTo`
	operations.

	It also dispatches information to higher layers.
	"""
	def __init__(self,connection):
		self.connection = connection

		self.currentRun = 0
		self.messages = []
		self.newRun()

		self.handlers = []
		self.registerMessageHandler(self)

		#initialize esteems
		self.minSQ = MinSQ(3)
		self.rotAccel = 720
		self.latency = 0.02 # TODO: estimate it correctly

		self.command = None
		
		self.clockOffset = None
		self.avgReceptionLatency = None
		

	def registerMessageHandler(self,handler):
		"""
		handler is an object with following methods 
		(but not necessarily all of them):
			processInitData(initData)
			runStart(runNumber)
			processTelemetry(tele)
			processEvent(event)
			runFinish()
		"""
		self.handlers.append(handler)

	def update(self):
		while self.connection.hasMessage():
			m = self.connection.popMessage()
			self.processMessage(m)
			self.messages.append(m)

	def cmd(self,command):
		self.connection.sendCommand(command)

	def setForwardControl(self,v):
		self.cmd("a;"*(v-self._forwardControl)+"b;"*(self._forwardControl-v))
		self._forwardControl = v
	def getForwardControl(self):
		return self._forwardControl
	forwardControl = property(getForwardControl,setForwardControl)

	def setTurnControl(self,t):
		self.cmd("l;"*(t-self._turnControl)+"r;"*(self._turnControl-t))
		self._turnControl = t
	def getTurnControl(self):
		return self._turnControl
	turnControl = property(getTurnControl,setTurnControl)

	def _rotateTo(self,x,y):
		desiredDir=degrees(atan2(y-self.teles[-1].y,
							     x-self.teles[-1].x))
		dDir = subtractAngles(desiredDir,self.teles[-1].dir)

		if dDir>15:
			self.turnControl = 2
		elif dDir>3:
			self.turnControl = 1
		elif dDir>-3:
			self.turnControl = 0
		elif dDir>-15:
			self.turnControl = -1
		else:
			self.turnControl = -2

	def _moveTo(self,x,y):
		self._rotateTo(x,y)
		dirX = cos(radians(self.teles[-1].dir))
		dirY = sin(radians(self.teles[-1].dir))
		dot = dirX*(x-self.teles[-1].x)+dirY*(y-self.teles[-1].y)
		if dot>0:
			self.forwardControl = choice([1]*8+[0]+[-1])
		else:
			self.forwardControl = choice([0]*8+[1]+[-1])

	def mainLoop(self):
		while self.connection.isRunning():
			self.update()
			if self.command!=None and len(self.teles)>=2:
				if self.command[0] == "rotateTo":
					self._rotateTo(self.command[1],self.command[2])
				elif self.command[0] == "moveTo":
					self._moveTo(self.command[1],self.command[2])
			time.sleep(0.01)

	def newRun(self):
		self.runInProgress = False
		self.accel = None
		self.teles = []
		self.numTeles = 0
		self.clockOffset = None
		print "*"*20, "\nNew Run!\n", "*"*20

	def runStart(self,runNumber):	
		"""message handler"""
		self._forwardControl = 0
		self._turnControl = 0

		self.numTimeStamps = 0
		self.curTime = 0
		               
	def processInitData(self,initData):
		"""message handler"""
		self.initialData = initData
		self.clockOffset = None #reset clock
		

	def processTelemetry(self,tele):
		"""message handler"""
		
		#update reception latency
		if self.clockOffset == None:
			self.clockOffset = FOFilter(0.0, time.clock() - tele.timeStamp);
			self.avgReceptionLatency = FOFilter(0.1, 0.0)
		else:
			clock = time.clock()
			newOffset =  clock - tele.timeStamp
			diff = self.clockOffset.value - newOffset 
#			print "%6.3f %6.3f %6.3f" % (clock, self.clockOffset.value, diff)
			self.avgReceptionLatency.next(abs(diff))
			self.clockOffset.next(newOffset)
			
		
		self.teles.append(tele)
		self.teles = self.teles[-3:] # keep last three tele's
		# so teles[-1] is current tele,
		#    teles[-2] is previous one and so on
		
		self.numTeles += 1
		if self.numTeles%20 == 0:
			self.printInfo()

#		self.cmd(choice(["al;","al;","br;",]))
		
		if len(self.teles) >= 2:
			dt = tele.timeStamp-self.teles[-2].timeStamp

			accelCmd = self.teles[-2].ctl[0]
			rotCmd = self.teles[-2].ctl[1]

			# form constraint of the form of the motion equation
			# dv = dt*accel - dt*drag*speed*speed
			dSpeed = tele.speed-self.teles[-2].speed
			if accelCmd=="a":
				coeffs = [dt,0]
			elif accelCmd=="-":
				coeffs = [0,0]
			elif accelCmd=="b":
				coeffs = [0,-dt]
			self.minSQ.addConstraint(
				array(coeffs+[-dt*self.teles[-2].speed**2]),
				dSpeed )

		if len(self.teles) >= 3:
			# calculate angular acceleration
			rotSpeed = \
				subtractAngles(tele.dir,self.teles[-2].dir)/ \
				(dt+1e-6)
			self.rotSpeed = rotSpeed
			prevDt=self.teles[-2].timeStamp-self.teles[-3].timeStamp
			prevRotSpeed = subtractAngles(
							self.teles[-2].dir,
							self.teles[-3].dir)/(prevDt+1e-6)
			if dt+prevDt>1e-8:
				curRotAccel = (rotSpeed-prevRotSpeed)/(dt+prevDt)*2
				if self.rotAccel==720: # initial value
					self.rotAccel = curRotAccel
				else:
					self.rotAccel = max(self.rotAccel,abs(curRotAccel))



	def processMessage(self,message):
		"""message dispatcher"""
		if isinstance(message,InitData):
			for h in self.handlers:
				if hasattr(h,"processInitData"):
					h.processInitData(message)

		elif isinstance(message,Telemetry):
			if not self.runInProgress:
				self.runInProgress = True
				for h in self.handlers:
					if hasattr(h,"runStart"):
						h.runStart(self.currentRun)
			for h in self.handlers:
				if hasattr(h,"processTelemetry"):
					h.processTelemetry(message)

		elif isinstance(message,Event):
			for h in self.handlers:
				if hasattr(h,"processEvent"):
					h.processEvent(message)

		elif isinstance(message,EndOfRun):
			for h in self.handlers:
				if hasattr(h,"runFinish"):
					h.runFinish(self.currentRun)
			self.currentRun += 1
			if self.currentRun == maxRuns:
				print "the end"
				self.connection.close()
				exit(0)
			self.newRun()

	def esteemParams(self):
		self.minSQ.solve()
		self.accel = self.minSQ.x[0]
		self.brake = self.minSQ.x[1]
		self.drag = self.minSQ.x[2]

	def printInfo(self):
		if not self.runInProgress:
			return
		self.esteemParams()
		print "Estimates:"
		print "  accel",self.accel
		print "  brake",self.brake
		print "  drag",self.drag
		print "  rotAccel",self.rotAccel
		print "  receptionLatency",self.avgReceptionLatency
