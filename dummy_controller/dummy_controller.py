#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap

##############

cerebellum.registerMessageHandler(TestHandler())

#cerebellum.command = ("moveTo",0,0)

if visualize:
    from visualizer import Visualizer
    vis = Visualizer(cerebellum, staticMap)
    vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()