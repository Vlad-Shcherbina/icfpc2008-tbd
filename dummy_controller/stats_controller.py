#!/usr/bin/python
import psyco
psyco.full()

import time
from random import randrange
import os

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap


##############

def delaysToGraph(delays):
	scale = 5
	xs = ",".join([str(int(300*d/scale)) for d in delays])
	ys = ",".join([str(randrange(100)) for d in delays])
	marks = "|".join(map(str,range(scale+1)))
	res = "http://chart.apis.google.com/chart?" +\
		"cht=s&chd=t:%s|%s&chs=300x100&chl=%s"%(xs,ys,marks)
	return res
	

class Stater(object):
	def __init__(self,cereb):
		self.delays = []
		self.cereb = cereb
		
	def runStart(self,runNumber):
		"""message handler"""
		self.state = 0
    	
	def processTelemetry(self,tele):
		"""message handler"""
		if self.state == 0:
			if tele.ctl == "--":
				self.startTime = time.clock()
				self.cereb.forwardControl = 1
				self.state = 1
		elif self.state == 1:
			if tele.ctl != "--":
				self.delays.append(time.clock()-self.startTime)
				self.cereb.forwardControl = 0
				self.state = 0
				
	def runFinish(self,runNumber):
		"""message handler"""
		print "run finished!"
		print len(self.delays)
		s = delaysToGraph(self.delays)
		
		fout = open("log/stats.html","wt")
		fout.write("<html><body><img src='%s'/></body></html>"%s)
		fout.close()
		#os.system("start log\\stats.html")

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