#!/usr/bin/python

import psyco
psyco.full()

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap
from static_map import StaticMap
from predictor import *
from neuroactivity import drunkygohome
##############

cerebellum.registerMessageHandler(TestHandler())

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

physicalValues = PhysicalValues()
cerebellum.registerMessageHandler(physicalValues)

drunky = drunkygohome.DrunkyGoHome(cerebellum, physicalValues, staticMap)
cerebellum.registerMessageHandler(drunky)

pred = PredictionDrawer()
cerebellum.registerMessageHandler(pred)

#cerebellum.command = ("moveTo",0,0)

if visualize:
	from visualizer import *
	from neuroactivity import drunky_vis

	vis = Visualizer(cerebellum, staticMap)

	vis.registerDrawer(pred)
	
	vis.registerDrawer(drunky_vis.createDrawer(drunky))
	
	vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()