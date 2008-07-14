from uuid import _last_timestamp
import time
from random import choice
from math import *
from threading import Semaphore

from protocol import *
from misc import *
from predictor import *
import statistics


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
		self._connection = connection
		self.stats = statistics.getStats()
		self.currentRun = 0
		self.handlers = []
		self.command = None
		self.runInProgress = False
		
		self._control = (0, 0) # acceleration, rotation
		

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
			commandSent(controlStateTuple)
		"""
		self.handlers.append(handler)

	
	
	
	# forwardControl 
	def clampControl(self, control):
		return (clamp(control[0], -1, 1), clamp(control[1], -2, 2))
	
	def setControl(self, control):
		if not self.runInProgress:
			return
		
		control = self.clampControl(control)
		cmd = "" 
		
		while (self._control != control):
			ds = clamp(control[0] - self._control[0], -1, 1)
			dr = clamp(control[1] - self._control[1], -1, 1)
			cmd += ["b", "", "a"][ds + 1] + ["r", "", "l"][dr + 1] + ";"
			self._control = (self._control[0] + ds, self._control[1] + dr)
		
		if cmd:
			self._connection.sendCommand(cmd)
			self.stats.commandSent(self._control)
			self.dispatchToHandlers("commandSent", self._control)
		else:
			self._connection.sendCommand(";")
		   
			
	def setForwardControl(self, v):
		self.setControl((v, self._control[1]))
		
	def getForwardControl(self):
		return self._control[0]
	
	forwardControl = property(getForwardControl, setForwardControl)

	# turnControl
	def setTurnControl(self, t):
		self.setControl((self._control[0], t))
		
	def getTurnControl(self):
		return self._control[1]
	
	turnControl = property(getTurnControl,setTurnControl)

	# hi-level cmd wrapper
	def cmd(self, command):
		for c in command:
			if c=="a":
				self.forwardControl += 1
			elif c=="b":
				self.forwardControl -= 1
			elif c=="l":
				self.turnControl += 1
			elif c=="r":
				self.turnControl -= 1

	
	# simple hi-level controller implementation
	
	def _rotateTo(self,x,y):
		desiredDir=degrees(atan2(y-self.y,
							     x-self.x))
		dDir = subtractAngles(desiredDir, self.dir)
		
		turnThreshold = self.stats.maxTurn * 0.05 
		hardTurnThreshold = self.stats.maxHardTurn * 0.15 

		if dDir > hardTurnThreshold:
			self.turnControl = 2
		elif dDir> turnThreshold:
			self.turnControl = 1
		elif dDir> -turnThreshold:
			self.turnControl = 0
		elif dDir> -hardTurnThreshold:
			self.turnControl = -1
		else:
			self.turnControl = -2

	def _moveTo(self,x,y):
		self._rotateTo(x,y)
		dirX = cos(radians(self.dir))
		dirY = sin(radians(self.dir))
		
		dot = dirX*(x-self.x)+dirY*(y-self.y)
		
		if dot>0:
			self.forwardControl = 1
		else:
			self.forwardControl = 0
	

#########################
# mainLoop

	def mainLoop(self):
		self._connection.start()
		# to allow connection to startup
		t = time.clock()
		
		sleepTime = 0
		
		while self._connection.state == ConState_Initializing:
			if (time.clock() - t > 20):
				self._connection.close()
				self._connection.join()
				return
			time.sleep(0.002)
			
		while True:
			if self.runInProgress:
				for h in self.handlers:
					if hasattr(h,"idle"):
						h.idle()
			running = self._connection.state == ConState_Running
			
			while self._connection.hasMessage():
				m = self._connection.popMessage()
				self.processMessage(m)
			else:
				time.sleep(0.001)
				sleepTime += 0.001
				
			if not running:
				break
			
		print "run time: %3.2f sleep time: %3.2f" % ((time.clock() - t), sleepTime)
		self._connection.join()


#########################
# message handlers

	def runStart(self,runNumber):	
		"""message handler"""
		print "*"*20, "\nNew Run!\n", "*"*20
		self.commands = []
		self._control = (0, 0)


		               
	def processInitData(self,initData):
		"""message handler"""
		self.initialData = initData
		

	def processTelemetry(self,tele):
		"""message handler"""
		
		self.x = tele.x
		self.y = tele.y
		self.dir = tele.dir
		
		# control
		if self.command!=None:
			if self.command[0] == "rotateTo":
				self._rotateTo(self.command[1],self.command[2])
			elif self.command[0] == "moveTo":
				self._moveTo(self.command[1],self.command[2])
		else:
			# keepalive
			self._connection.sendCommand(";")
			
		

	
	
#########################
# message dispatching
	
	def dispatchToHandlers(self, name, *params):
		for h in self.handlers:
			handler =  getattr(h, name, None) 
			if handler != None:
				handler(*params)

	def processMessage(self, message):
		"""message dispatcher"""
		if isinstance(message, Telemetry):
			if not self.runInProgress:
				self.runInProgress = True
				self.runStart(self.currentRun)
				self.stats.runStart(self.currentRun)
				self.dispatchToHandlers("runStart", self.currentRun)
			
			self.processTelemetry(message)
			self.stats.processTelemetry(message)
			self.dispatchToHandlers("processTelemetry", message)

		elif isinstance(message,Event):
			self.stats.processEvent(message)
			self.dispatchToHandlers("processEvent", message)
			
		elif isinstance(message,EndOfRun):
			self.dispatchToHandlers("runFinish", self.currentRun)
			self.runInProgress = False
			self.currentRun += 1
			
		if isinstance(message, InitData):
			self.processInitData(message)
			self.stats.processInitData(message)
			self.dispatchToHandlers("processInitData", message)
					
