from uuid import _last_timestamp
import time
from random import choice
from math import *

from protocol import *
from misc import *

maxRuns = 6


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
		self.prepairForNewRun()

		self.handlers = []
		self.registerMessageHandler(self)

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
			idle()
			runFinish()
		"""
		self.handlers.append(handler)

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
		self.connection.start()
		# to allow connection to startup
		time.sleep(0.5)
		while self.connection.running:
			time.sleep(0.002)
			for h in self.handlers:
				if hasattr(h,"idle"):
					h.idle()
			running = self.connection.isRunning()
			while self.connection.hasMessage():
				m = self.connection.popMessage()
				self.processMessage(m)
				#self.messages.append(m) # memory leak was here I think
			if not running:
				break
		self.connection.join()

	def prepairForNewRun(self):
		"""
		As problem document states, at this moment we have at least 1 second 
		before run start. But... everybody lies
		"""
		self.runInProgress = False
		self.accel = None
		self.teles = []
		self.numTeles = 0
		self.clockOffset = None

	def runStart(self,runNumber):	
		"""message handler"""
		print "*"*20, "\nNew Run!\n", "*"*20
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

		# control
		if self.command!=None and len(self.teles)>=2:
			if self.command[0] == "rotateTo":
				self._rotateTo(self.command[1],self.command[2])
			elif self.command[0] == "moveTo":
				self._moveTo(self.command[1],self.command[2])
		
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
		

	def processMessage(self,message):
		"""message dispatcher"""
		if isinstance(message,InitData):
			for h in self.handlers:
				try: h.processInitData(message)
				except: pass
		elif isinstance(message,Telemetry):
			if not self.runInProgress:
				self.runInProgress = True
				for h in self.handlers:
					try: h.runStart(self.currentRun)
					except: pass
			for h in self.handlers:
				h.processTelemetry(message)

		elif isinstance(message,Event):
			for h in self.handlers:
				try: h.processEvent(message)
				except: pass

		elif isinstance(message,EndOfRun):
			for h in self.handlers:
				try: h.runFinish(self.currentRun)
				except: pass

			self.currentRun += 1
			if self.currentRun == maxRuns:
				print "maxRuns reached"
				self.connection.close()
				return
			self.prepairForNewRun()

	def printInfo(self):
		if not self.runInProgress:
			return
		print "Estimates:"
		print "  receptionLatency",self.avgReceptionLatency        
