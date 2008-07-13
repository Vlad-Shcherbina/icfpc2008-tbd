#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from controller import connection,cerebellum,visualize,staticMap,mainLoop
from predictor import *

##############

keyMapping = { 
	"w":(lambda: connection.sendCommand("a;")),
	"s":(lambda: connection.sendCommand("b;")),
	"a":(lambda: connection.sendCommand("l;")),
	"d":(lambda: connection.sendCommand("r;")),
	} 

def keyboardHandler(key, x, y):
	if keyMapping.has_key(key):
		keyMapping[key]()



if visualize:
	from visualizer import *
	vis = Visualizer(cerebellum, staticMap, keyboardHandler)
	
	def predictionDrawer():
		phys = PhysicalValues()
		rover = RoverState(cerebellum.teles[-1])
		commands = []
		trace = predict(phys,rover,commands,0.1,5)
		glBegin(GL_POINTS)
		glColor3f(1,1,0)
		for p in trace:
			glVertex3f(p.x,p.y,1)
		glEnd()
		
	vis.registerDrawer(predictionDrawer)
	
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()