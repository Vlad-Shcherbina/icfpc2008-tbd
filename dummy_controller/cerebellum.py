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
		self.connection = connection
		self.currentRun = 0
		self.handlers = []
		self.command = None
		self.runInProgress = False
		

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

	def _cmd(self,command):
		self.connection.sendCommand(command)
#		self.commandHistory.cmd(command)
		
	def setForwardControl(self,v):
		v = max(min(v,1),-1)
		self._cmd("a;"*(v-self._forwardControl)+"b;"*(self._forwardControl-v))
		self._forwardControl = v
	def getForwardControl(self):
		return self._forwardControl
	forwardControl = property(getForwardControl,setForwardControl)

	def setTurnControl(self,t):
		t = max(min(t,2),-2)
		self._cmd("l;"*(t-self._turnControl)+"r;"*(self._turnControl-t))
		self._turnControl = t
	def getTurnControl(self):
		return self._turnControl
	turnControl = property(getTurnControl,setTurnControl)

	def cmd(self,command):
		for c in command:
			if c=="a":
				self.forwardControl += 1
			elif c=="b":
				self.forwardControl -= 1
			elif c=="l":
				self.turnControl += 1
			elif c=="r":
				self.turnControl -= 1

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
	

#########################
# mainLoop

	def mainLoop(self):
		self.connection.start()
		# to allow connection to startup
		t = time.clock()
		
		sleepTime = 0
		
		while self.connection.state == ConState_Initializing:
			if (time.clock() - t > 20):
				self.connection.close()
				self.connection.join()
				return
			time.sleep(0.002)
			
		while True:
			for h in self.handlers:
				if hasattr(h,"idle"):
					h.idle()
			running = self.connection.state == ConState_Running
			
			while self.connection.hasMessage():
				m = self.connection.popMessage()
				self.processMessage(m)
			else:
				time.sleep(0.002)
				sleepTime += 0.002
				
			if not running:
				break
			
		print "run time: %3.2f sleep time: %3.2f" % ((time.clock() - t), sleepTime)
		self.connection.join()


#########################
# message handlers

	def runStart(self,runNumber):	
		"""message handler"""
		print "*"*20, "\nNew Run!\n", "*"*20
		self.teles = []
		self.numTeles = 0
		self.commands = []
		self._forwardControl = 0
		self._turnControl = 0


		               
	def processInitData(self,initData):
		"""message handler"""
		self.initialData = initData
		

	def processTelemetry(self,tele):
		"""message handler"""

		#kinda keepalive
		self.connection.sendCommand(";")

		# control
		if self.command!=None and len(self.teles)>=2:
			if self.command[0] == "rotateTo":
				self._rotateTo(self.command[1],self.command[2])
			elif self.command[0] == "moveTo":
				self._moveTo(self.command[1],self.command[2])
		
		
		self.teles.append(tele)
		self.teles = self.teles[-3:] # keep last three tele's
		# so teles[-1] is current tele,
		#    teles[-2] is previous one and so on
		
		self.numTeles += 1

	
	
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
				statistics.runStart(self.currentRun)
				self.dispatchToHandlers("runStart", self.currentRun)
			
			self.processTelemetry(message)
			statistics.processTelemetry(message)
			self.dispatchToHandlers("processTelemetry", message)

		elif isinstance(message,Event):
			statistics.processEvent(message)
			self.dispatchToHandlers("processEvent", message)
			
		elif isinstance(message,EndOfRun):
			self.dispatchToHandlers("runFinish", self.currentRun)
			self.runInProgress = False
			self.currentRun += 1
			
		if isinstance(message, InitData):
			self.processInitData(message)
			statistics.processInitData(message)
			self.dispatchToHandlers("processInitData", message)
					
