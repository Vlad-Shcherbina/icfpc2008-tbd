#!/usr/bin/python
import psyco
psyco.full()

from random import *

from misc import *
from controller import connection,cerebellum,visualize,staticMap,mainLoop
from predictor import *
import predictor
import statistics

##############

keyMapping = { 
	"w":(lambda: cerebellum.cmd("a;")),
	"s":(lambda: cerebellum.cmd("b;")),
	"a":(lambda: cerebellum.cmd("l;")),
	"d":(lambda: cerebellum.cmd("r;")),
	} 

def keyboardHandler(key, x, y):
	if keyMapping.has_key(key):
		keyMapping[key]()
		

def beacons(rover,trace,addTime):
	"""
	returns list of points in trace which look like something to strive to
	"""
	if len(trace) == 1:
		return [trace[0]]
	dists = map(rover.dist,trace)
	dists.append(dists[-2]) # yeah, not dists[-1]
	results = []
	for i in range(1,len(trace)):
		if dists[i-1]>=dists[i] and \
		   dists[i]<dists[i+1]:
			# math: interpolate parabola by three points and minimize it
			t = 0.5*(dists[i-1]-dists[i+1])/(dists[i-1]+dists[i+1]-2*dists[i])
			if i<len(trace)-1:
				dt = 0.5*(trace[i+1].localT-trace[i-1].localT)
			else:
				dt = trace[i].localT-trace[i-1].localT
			t = trace[i].localT + dt*t
			results.append(lerpTrace(t+addTime,trace,firstElem=i))
	if len(results)==0:
		results.append(trace[-1])
	return results

def moveTo(rover,targetX,targetY,targetRadius=5,dt=None):
	if dt is None:
		dt = DEFAULT_DT
	rover = copy(rover)
	commands = []
	curCommand = 0
	trace = []
	n = 0
	while (rover.x-targetX)**2+(rover.y-targetY)**2>targetRadius**2 and n<200:
		command = ControlRecord((0,0),rover.localT)

		desiredDir=degrees(atan2(targetY-rover.y,
							     targetX-rover.x))
		dDir = subtractAngles(desiredDir, rover.dir)

		if dDir>15:
			command.turnControl = 2
		elif dDir>3:
			command.turnControl = 1
		elif dDir>-3:
			command.turnControl = 0
		elif dDir>-15:
			command.turnControl = -1
		else:
			command.turnControl = -2		

		dirX = cos(radians(rover.dir))
		dirY = sin(radians(rover.dir))
		dot = dirX*(targetX-rover.x)+dirY*(targetY-rover.y)
		if dot>0:
			command.forwardControl = 1
		else:
			command.forwardControl = 0
			
		commands.append(command)
		curCommand = roverSimulationStep(rover, dt, commands, curCommand)
		trace.append(copy(rover))
		n += 1

	return trace

class RailController(object):
	def __init__(self):
		pass
	
	# this class have to be registered in cerebellum 
	# AFTER serverMovementPredictor
	 
	def runStart(self,currentRun):
		"""message handler"""
		self.beginning = True
		self.pendingCommands = []
		self.rover = None
		self.beacons = []
		self.targets = []
		self.trace = []
		self.bestTrace = None
	
	def processTelemetry(self,tele):
		"""message handler"""
		# assuming that serverMovementPredictor already
		# received this tele
		self.rover = RoverState(tele,self.rover)
		if self.beginning:
			self.beginning = False
		
		if len(self.trace)==0:
			return
		
		smp = serverMovementPredictor
		
		
		lookAhead = 0.5
		
		actualRover = smp.predict(smp.latency)[-1]
		self.beacons = beacons(actualRover,self.trace,smp.latency+lookAhead)
		
		bestCmds = None
		bestCost = 1e100
		bestPos = None
		self.bestTrace = None
		
		candidates = []
		for fc in range(-1,2):
			for tc in range(-2,3):
				cmds = [
					ControlRecord((fc,tc),tele.localTimeStamp+smp.latency),
					]
				candidates.append(cmds)
		for fc in range(-1,2):
			for tc in range(-2,3):
				cmds = [
					ControlRecord((fc,tc),tele.localTimeStamp+smp.latency),
					ControlRecord((0,0),tele.localTimeStamp+smp.latency+0.05)
					]
				candidates.append(cmds)

		for cmds in candidates:
			tr = predict(actualRover,cmds,lookAhead+smp.latency,dt=0.03)
			pos = tr[-1]
			cost = min(map(pos.penalty,self.beacons))
			if cost<bestCost:
				self.bestTrace = tr
				bestPos = pos
				bestCost = cost
				bestCmds = cmds
		assert bestCmds is not None
		print bestCost,bestCmds
		
		for cmd in bestCmds:
			cmd.time -= smp.latency
		self.pendingCommands = bestCmds
		
		self.processPendingCommands()
		#cerebellum.forwardControl = bestCmds[0].forwardControl
		#cerebellum.turnControl = bestCmds[0].turnControl
		
		#print "%.1f"%actualRover.distToTrace(self.trace)
			
	def commandSent(self,controlState):
		pass
	
	def processPendingCommands(self):
		t = time.clock()
		newCmds = []
		for c in self.pendingCommands:
			if c.time<=t:
				cerebellum.forwardControl = c.forwardControl
				cerebellum.turnControl = c.turnControl
			else:
				newCmds.append(c)
		self.pendingCommands = newCmds
	
	def idle(self):
		self.processPendingCommands()
		#return
	
	def draw(self):
		from visualizer import *	
		glBegin(GL_LINES)
		glColor3f(1,1,0)
		for p in self.trace:
			glVertex2f(p.x,p.y)
		glEnd()

		glBegin(GL_LINES)
		glColor3f(1,1,1)
		if self.bestTrace is not None:
			for p in self.bestTrace:
				glVertex2f(p.x,p.y)
		glEnd()

			
		glBegin(GL_LINES)
		glColor3f(0,1,0)
		for p in serverMovementPredictor.predict(1):
			glVertex2f(p.x,p.y)
		glEnd()
		
		glColor3f(1,0,0)
		for b in self.beacons:
			circle(b.x,b.y,0.5)
			
		glColor3f(1,0,1)
		for t in self.targets:
			circle(t[0],t[1],2)
		
		

	def runFinish(self,currentRun):
		"""message handler"""
		print "rail: run finish"
		#statistics.showFinalStats()		


railController = RailController()
cerebellum.registerMessageHandler(railController)		

def mouseHandler(button,x,y):
	from OpenGL.GLUT import *
	
	if glutGetModifiers() & GLUT_ACTIVE_SHIFT == 0:
		railController.targets = [(x,y)]
		railController.trace = moveTo(railController.rover,x,y,2)
	else:
		railController.targets.append((x,y))
		if len(railController.trace) == 0:
			railController.trace = [railController.rover]
		railController.trace += moveTo(railController.trace[-1],x,y,2)


#pd = PredictionDrawer()
#cerebellum.registerMessageHandler(pd)

if visualize:
	from visualizer import *
	vis = Visualizer(cerebellum, staticMap, keyboardHandler, mouseHandler)
	
	#vis.registerDrawer(pd)
	
	vis.registerDrawer(railController.draw)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()