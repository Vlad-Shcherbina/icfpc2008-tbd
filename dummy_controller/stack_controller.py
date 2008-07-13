#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from static_map import StaticMap
from simple_stack_logic import SimpleStackLogic
from controller import connection,cerebellum,visualize,mainLoop

##############

cerebellum.registerMessageHandler(TestHandler())

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

logic = SimpleStackLogic(cerebellum,staticMap)
cerebellum.registerMessageHandler(logic)

if visualize:
	from visualizer import Visualizer
	vis = Visualizer(cerebellum, staticMap)
	vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()