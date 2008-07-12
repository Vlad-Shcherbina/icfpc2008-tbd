#!/usr/bin/python
import sys

import psyco
psyco.full()


#visualize = True
visualize = eval(open("visualize.config").readline())


import time

from protocol import *
from cerebellum import Cerebellum
from static_map import StaticMap
from simple_stack_logic import SimpleStackLogic

if visualize:
	from visualizer import Visualizer

class TestHandler(object):
	def processInitData(self,initData):
		pass
#		print "init data"
	def runStart(self,runNumber):
		print "run %s started"%runNumber
	def processTelemetry(self,tele):
		pass
#		print "tele"
	def processEvent(self,event):
		pass
#		print "event"
	def runFinish(self,runNumber):
		print "run %s finished"%runNumber


##################
# main

if len(sys.argv) != 3:
	print "specify ip and port"
	exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])

conn = Connection(ip,port)
cereb = Cerebellum(conn)
cereb.command = ("moveTo",0,0)


#cereb.registerMessageHandler(TestHandler())

staticMap = StaticMap()
cereb.registerMessageHandler(staticMap)

logic = SimpleStackLogic(cereb, map)
cereb.registerMessageHandler(logic)

if visualize:
	vis = Visualizer()
	vis.cerebellum = cereb
	vis.staticMap = staticMap
	cereb.registerMessageHandler(vis)
	vis.start()




conn.start()
cereb.mainLoop()
sys.exit(0)