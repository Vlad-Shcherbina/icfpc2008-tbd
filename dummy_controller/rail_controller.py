#!/usr/bin/python
import psyco
psyco.full()

from random import *

from misc import *
from controller import connection,cerebellum,visualize,staticMap,mainLoop
from predictor import *
import predictor
import statistics
from pathfinders import *

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


class Rail(object):
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
		self.trace = []
		self.bestTrace = None
		
	def setRail(self,trace):
		self.trace = trace
		self.pendingCommands = []
	
	def processTelemetry(self,tele):
		"""message handler"""
		# assuming that serverMovementPredictor already
		# received this tele
		self.rover = RoverState(tele,self.rover)
		if self.beginning:
			self.beginning = False
		
		#return
	
		if len(self.trace)==0:
			return
		
		smp = serverMovementPredictor
		
		
		lookAhead = 0.1
		
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

		glColor3f(1,0,0)
		for b in self.beacons:
			circle(b.x,b.y,0.5)

	def runFinish(self,currentRun):
		"""message handler"""
		print "rail: run finish"
		#statistics.showFinalStats()		


class WayPointController(object):
	def __init__(self,rail,pathFinder):
		self.rail = rail
		self.pathFinder = pathFinder
	
	def runStart(self,currentRun):
		self.wayPoints = []
		
	def mouseHandler(self,button,x,y):
		from OpenGL.GLUT import *
	
		if glutGetModifiers() & GLUT_ACTIVE_SHIFT == 0:
			start = self.rail.rover
			self.wayPoints = []
			self.rail.setRail([])
		else:
			if len(rail.trace) == 0:
				start = rail.rover
			else:
				start = rail.trace[-1]
		path = self.pathFinder(start,x,y)
		if len(path)>0:
			self.wayPoints.append((x,y))
			rail.setRail(self.rail.trace + path)
	
	def draw(self):
		glColor3f(1,0,1)
		for w in self.wayPoints:
			circle(w[0],w[1],2)


rail = Rail()
cerebellum.registerMessageHandler(rail)

wpController = WayPointController(rail,moveTo)
cerebellum.registerMessageHandler(wpController)		

#pd = PredictionDrawer()
#cerebellum.registerMessageHandler(pd)

if visualize:
	from visualizer import *
	vis = Visualizer(cerebellum, staticMap, 
					 keyboardHandler, wpController.mouseHandler)
	
	#vis.registerDrawer(pd)
	
	vis.registerDrawer(rail.draw)
	vis.registerDrawer(wpController.draw)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()