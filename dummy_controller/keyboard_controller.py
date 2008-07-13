#!/usr/bin/python
import sys

import psyco
psyco.full()

visualize = eval(open("visualize.config").readline())

import time

from protocol import *
from cerebellum import Cerebellum
from static_map import StaticMap
from simple_stack_logic import SimpleStackLogic

from visualizer import Visualizer


class TestHandler(object):
	def processInitData(self,initData):
		pass
	def runStart(self,runNumber):
		print "run %s started"%runNumber
	def processTelemetry(self,tele):
		pass
	def processEvent(self,event):
		pass
	def runFinish(self,runNumber):
		print "run %s finished"%runNumber

##################
# main
if len(sys.argv) != 3:
	print "specify ip and port"
	exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])

conn = Connection(ip, port)
cereb = Cerebellum(conn)

staticMap = StaticMap()
cereb.registerMessageHandler(staticMap)

keyMapping = { 
	"w":(lambda: conn.sendCommand("a;")),
	"s":(lambda: conn.sendCommand("b;")),
	"a":(lambda: conn.sendCommand("l;")),
	"d":(lambda: conn.sendCommand("r;")),
	} 

def keyboardHandler(key, x, y):
	if keyMapping.has_key(key):
		keyMapping[key]()
	

vis = Visualizer(cereb, staticMap, keyboardHandler)
vis.start()


conn.start()
cereb.mainLoop()
sys.exit(0)

