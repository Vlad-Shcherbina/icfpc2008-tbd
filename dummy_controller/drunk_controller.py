#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap
from static_map import StaticMap
from predictor import *
from neuroactivity.drunkygohome import DrunkyGoHome
##############

cerebellum.registerMessageHandler(TestHandler())

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

physicalValues = PhysicalValues()
cerebellum.registerMessageHandler(physicalValues)


cerebellum.registerMessageHandler(DrunkyGoHome(cerebellum, staticMap))

#cerebellum.command = ("moveTo",0,0)

if visualize:
	from visualizer import *

	vis = Visualizer(cerebellum, staticMap)
	
	vis.registerDrawer(PredictorDrawer(cerebellum, physicalValues))
	
	vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()