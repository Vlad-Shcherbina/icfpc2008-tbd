from uuid import _last_timestamp
import time
from random import choice
from math import *
from threading import Semaphore

from protocol import *
from misc import *
from predictor import *
import statistics

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
		self.prepareForNewRun()

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

	def prepareForNewRun(self):
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
		self.commands = []
		self._forwardControl = 0
		self._turnControl = 0

		self.numTimeStamps = 0
		self.curTime = 0
		
#		self.commandHistory = CommandHistory()
		               
	def processInitData(self,initData):
		"""message handler"""
		self.initialData = initData
		self.clockOffset = None #reset clock
		

	def processTelemetry(self,tele):
		"""message handler"""

		self.connection.sendCommand(";")

		self.timeMinusTimeStamp = time.clock()-tele.timeStamp
		
		# clean up commands
						
#		self.commandHistory.processTelemetry(tele)
#		print self.commands
		
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
				if hasattr(h, "processInitData"): 
					h.processInitData(message)
		elif isinstance(message,Telemetry):
			if not self.runInProgress:
				self.runInProgress = True
				for h in self.handlers:
					if hasattr(h, "runStart"): 
						h.runStart(self.currentRun)
			for h in self.handlers:
				if hasattr(h, "processTelemetry"):
					h.processTelemetry(message)

		elif isinstance(message,Event):
			for h in self.handlers:
				if hasattr(h, "processEvent"): 
					h.processEvent(message)

		elif isinstance(message,EndOfRun):
			for h in self.handlers:
				if hasattr(h, "runFinish"): 
					h.runFinish(self.currentRun)

			self.currentRun += 1
			if self.currentRun == maxRuns:
				print "maxRuns reached"
				self.connection.close()
				return
			self.prepareForNewRun()

	def printInfo(self):
		return
		if not self.runInProgress:
			return
		print "Estimates:"
		print "  receptionLatency",self.avgReceptionLatency        

class CommandHistory(object):
	def __init__(self):
		self.commands = []
		self.prev = None
		self.semaphore = Semaphore()
		
	def cmd(self,command):
		self.semaphore.acquire()
		for c in command:
			if c in "ablr":
				self.commands.append([time.clock(),c,"current"])
		print self.commands
		self.semaphore.release()
		
	def processTelemetry(self,tele):
		cur = RoverState(tele)
		if self.prev is not None:
			t=time.clock()
			#self.semaphore.acquire()
			def popCommand(command):
				for i in range(len(self.commands)):
					if self.commands[i][1] == command and \
						self.commands[i][2] != "annihilated":
						cmd = self.commands.pop(i)
#						print cmd
						if cmd[2] == "current":
							# command was processed in closed tele
							statistics.goodLatency(t-cmd[0])
						elif cmd[2] == "outdated":
							# was not
							statistics.badLatency(t-cmd[0])
						else:
							assert False
						return
				for i in range(len(self.commands)):
					if self.commands[i][1] == command and \
						self.commands[i][2] == "annihilated":
						cmd = self.commands.pop(i)
						return
				assert False
				
			for i in range(cur.forwardControl-self.prev.forwardControl):
				popCommand("a")
			for i in range(self.prev.forwardControl-cur.forwardControl):
				popCommand("b")
			for i in range(cur.turnControl-self.prev.turnControl):
				popCommand("l")
			for i in range(self.prev.turnControl-cur.turnControl):
				popCommand("r")
				
			statusChange = {
				"current":"outdated",
				"outdated":"outdated",
				"annihilated":"annihilated"}
			for c in self.commands:
				if c[2]=="current":
					c[2]="outdated" 

			# annihilate outdated pairs
			def findPair(pos,neg,annihilated):
				posIndex = None
				negIndex = None
				for i in range(len(self.commands)):
					if posIndex is None and \
						self.commands[i][1]==pos and \
						(self.commands[i][2]=="annihilated")==annihilated:
						posIndex = i
					if negIndex is None and \
						self.commands[i][1]==neg and \
						(self.commands[i][2]=="annihilated")==annihilated:
						negIndex = i
				if posIndex is not None and negIndex is not None:
					return (posIndex,negIndex)
				else:
					return None
			for pos,neg in [("a","b"),("l","r")]:
				pair = findPair(pos,neg,annihilated=False)
				if pair is not None:
					self.commands[pair[0]][2]="annihilated"
					self.commands[pair[1]][2]="annihilated"
				pair = findPair(pos,neg,annihilated=True)
				if pair is not None:
					if self.commands[pair[0]][0]<t-1 and\
						self.commands[pair[1]][0]<t-1:
						self.commands.pop(max(pair))
						self.commands.pop(min(pair))
			#self.semaphore.release()
		self.prev = cur
