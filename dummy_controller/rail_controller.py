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


class RailController(object):
	def __init__(self):
		pass
	
	def runStart(self,currentRun):
		"""message handler"""
		self.beginning = True
	
	def processTelemetry(self,tele):
		"""message handler"""
		if self.beginning:
			rover = RoverState(tele)
			commands = []
			self.trace = predict(
				rover,
				commands=commands,
				interval=10,dt=0.15)
			self.beginning = False
			
	def commandSent(self,controlState):
		print controlState
	
	def draw(self):
		from visualizer import *	
		glBegin(GL_POINTS)
		glColor3f(1,1,0)
		for p in self.trace:
			glVertex3f(p.x,p.y,1)
		glEnd()

	def runFinish(self,currentRun):
		"""message handler"""
		print "rail: run finish"
		statistics.showFinalStats()		
		
railController = RailController()
cerebellum.registerMessageHandler(railController)		

pd = PredictionDrawer()
cerebellum.registerMessageHandler(pd)

if visualize:
	from visualizer import *
	vis = Visualizer(cerebellum, staticMap, keyboardHandler)
	
	vis.registerDrawer(pd)
	
	vis.registerDrawer(railController.draw)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()