#!/usr/bin/python
import psyco
psyco.full()

from random import *

from misc import *
from controller import connection,cerebellum,visualize,staticMap,mainLoop
from predictor import *
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


physicalValues = PhysicalValues()
cerebellum.registerMessageHandler(physicalValues)

class RailController(object):
	def __init__(self):
		pass
	def runStart(self,currentRun):
		"""message handler"""
		self.beginning = True
		self.timeForMessage = 0
	def processTelemetry(self,tele):
		"""message handler"""
		if self.beginning:
			rover = RoverState(tele)
			commands = [(rover.t,"a"),(rover.t+4,"r")]
			self.trace = predict(physicalValues, rover, 
                        dt=0.1, interval=10, commands=commands)
			self.beginning = False
	def draw(self):
		from visualizer import *	
		glBegin(GL_POINTS)
		glColor3f(1,1,0)
		for p in self.trace:
			glVertex3f(p.x,p.y,1)
		glEnd()
	def idle(self):
		"""message handler"""
		if cerebellum.runInProgress:
			if self.timeForMessage<time.clock():
				cerebellum.cmd(choice(["a","b","l","r"]))
				self.timeForMessage = time.clock()+random()*0.5
	def runFinish(self,currentRun):
		"""message handler"""
		print "rail: run finish"
		statistics.showFinalStats()		
		
railController = RailController()
cerebellum.registerMessageHandler(railController)		

if visualize:
	from visualizer import *
#	vis = Visualizer(cerebellum, staticMap, keyboardHandler)
	vis = Visualizer(cerebellum, staticMap)
	
	vis.registerDrawer(PredictorDrawer(cerebellum, physicalValues))
	
	vis.registerDrawer(railController.draw)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()