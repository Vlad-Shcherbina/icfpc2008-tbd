#!/usr/bin/python
import psyco
psyco.full()

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap
from neuroactivity.drunkygohome import DrunkyGoHome
##############

cerebellum.registerMessageHandler(TestHandler())

if False:
	cerebellum.registerMessageHandler(DrunkyGoHome(cerebellum))

#cerebellum.command = ("moveTo",0,0)

if visualize:
    from visualizer import Visualizer
    vis = Visualizer(cerebellum, staticMap)
    vis.start()

mainLoop()

if visualize:
    vis.terminate = True
    vis.join()