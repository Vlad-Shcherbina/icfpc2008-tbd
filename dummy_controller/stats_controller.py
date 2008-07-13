#!/usr/bin/python
import psyco
psyco.full()

import time
from random import randrange
import os

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap


##############

def delaysToGraph(delays,seconds=1):
	steps = 100
	freqs = [0 for i in range(steps)]
	for d in delays:
		f = int(d*steps/seconds)
		if f<steps:
			freqs[f] += 1
	
	freqs = ",".join([str(int(100*f/(1e-2+max(freqs)))) for f in freqs])
	marks = "|".join(map(str,range(seconds+1)))
	
	res = "http://chart.apis.google.com/chart?" +\
		"cht=lc&chd=t:%s&chs=300x100&chl=%s"%(freqs,marks)
	return res
	

class Stater(object):
	def __init__(self,cereb):
		self.telemetryIntervals = []
		self.delays = []
		self.cereb = cereb
		
	def runStart(self,runNumber):
		"""message handler"""
		self.state = 0
    	
	def processTelemetry(self,tele):
		"""message handler"""
		if hasattr(self,"prevTime"):
			self.telemetryIntervals.append(
				time.clock()-self.prevTime)
		self.prevTime = time.clock()

		if self.state == 0:
			if tele.ctl == "--":
				self.sendTime = time.clock()
				self.cereb.forwardControl = 1
				self.state = 1
		elif self.state == 1:
			if tele.ctl != "--":
				self.delays.append(time.clock()-self.sendTime)
				self.cereb.forwardControl = 0
				self.state = 0
				
	def runFinish(self,runNumber):
		"""message handler"""
		
		fout = open("log/stats.html","wt")
		fout.write("<html><body></body></html>")
		fout.write("telemetry intervals: <br/> <img src='%s'/> <hr/>"%
				   delaysToGraph(self.telemetryIntervals))
		fout.write("full latency: <br/> <img src='%s'/> <hr/>"%
				   delaysToGraph(self.delays))
		fout.close()
		os.system("start log\\stats.html")

cerebellum.registerMessageHandler(TestHandler())

stater = Stater(cerebellum)
cerebellum.registerMessageHandler(stater)

if visualize:
	from visualizer import Visualizer
	vis = Visualizer(cerebellum, staticMap)
	vis.start()
	
mainLoop()

if visualize:
	vis.terminate = True
	vis.join()