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
	if len(results)<0:
		results.append(trace[-1])
	return results

class RailController(object):
	def __init__(self):
		pass
	
	# this class have to be registered in cerebellum 
	# AFTER serverMovementPredictor
	 
	def runStart(self,currentRun):
		"""message handler"""
		self.rover = None
		self.beginning = True
	
	def processTelemetry(self,tele):
		"""message handler"""
		# assuming that serverMovementPredictor already
		# received this tele
		self.rover = RoverState(tele,self.rover)
		if self.beginning:
			commands = [
				ControlRecord((1,0),self.rover.localT+1),
				ControlRecord((1,-1),self.rover.localT+3),
				ControlRecord((1,2),self.rover.localT+5),
				ControlRecord((0,0),self.rover.localT+8),
				]
			self.trace = predict(
				self.rover,
				commands=commands,
				interval=10,dt=0.051)
			self.beginning = False
		
		smp = serverMovementPredictor
		
		
		lookAhead = 0.1
		
		actualRover = smp.predict(smp.latency)[-1]
		self.beacons = beacons(actualRover,self.trace,smp.latency+lookAhead)
		
		bestCmds = None
		bestCost = 1e100
		bestPos = None
		
		candidates = []
		for fc in range(-1,2):
			for tc in range(-2,3):
				cmds = [
					ControlRecord((fc,tc),tele.localTimeStamp+smp.latency)]
				candidates.append(cmds)

		for cmds in candidates:
			pos = predict(actualRover,cmds,lookAhead+smp.latency)[-1]
			cost = min(map(pos.penalty,self.beacons))
			if cost<bestCost:
				bestPos = pos
				bestCost = cost
				bestCmds = cmds
		assert bestCmds is not None
		print bestCost,bestCmds
		
		cerebellum.forwardControl = bestCmds[0].forwardControl
		cerebellum.turnControl = bestCmds[0].turnControl
				
		#print "%.1f"%actualRover.distToTrace(self.trace)
		
		
			
	def commandSent(self,controlState):
		pass
	
	def draw(self):
		from visualizer import *	
		glBegin(GL_LINES)
		glColor3f(1,1,0)
		for p in self.trace:
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
		
		

	def runFinish(self,currentRun):
		"""message handler"""
		print "rail: run finish"
		#statistics.showFinalStats()		
		
railController = RailController()
cerebellum.registerMessageHandler(railController)		

#pd = PredictionDrawer()
#cerebellum.registerMessageHandler(pd)

if visualize:
	from visualizer import *
	vis = Visualizer(cerebellum, staticMap, keyboardHandler)
	
	#vis.registerDrawer(pd)
	
	vis.registerDrawer(railController.draw)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()