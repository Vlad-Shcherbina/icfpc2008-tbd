#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from static_map import StaticMap
from controller import connection,cerebellum,visualize,mainLoop

##############

cerebellum.registerMessageHandler(TestHandler())

#cerebellum.command = ("moveTo",0,0)

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

if visualize:
    from visualizer import Visualizer
    vis = Visualizer(cerebellum, staticMap)
    vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()