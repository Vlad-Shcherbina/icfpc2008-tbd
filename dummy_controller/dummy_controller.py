#!/usr/bin/python

visualize = True

import time

from protocol import *
from cerebellum import Cerebellum
from visualizer import Visualizer
from static_map import StaticMap

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

#cereb.registerMessageHandler(TestHandler())

staticMap = StaticMap()
cereb.registerMessageHandler(staticMap)

if visualize:
	vis = Visualizer()
	vis.cerebellum = cereb
	vis.staticMap = staticMap
	cereb.registerMessageHandler(vis)
	vis.start()




conn.start()
cereb.mainLoop()
	
