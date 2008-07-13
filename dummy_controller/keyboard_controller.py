#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from static_map import StaticMap
from controller import connection,cerebellum,visualize,mainLoop

##############

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

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
	from visualizer import Visualizer
	vis = Visualizer(cerebellum, staticMap, keyboardHandler)
	vis.start()

mainLoop()

if visualize:
	vis.terminate = True
	vis.join()