#!/usr/bin/python
import psyco
psyco.full()

import time
from random import *
import os

from misc import *
from controller import connection,cerebellum,visualize,mainLoop,staticMap
from statistics import delaysToGraph


##############


class Stater(object):
	def __init__(self,cereb):
		self.telemetryIntervals = []
		self.delays = [[] for i in range(10)]
		self.cereb = cereb
		
	def runStart(self,runNumber):
		"""message handler"""
		self.state = 0
		self.sendDelayIndex = 0
		self.maxSendDelayIndex = 10 
		self.sendDelayStep = 0.01
    	
	def idle(self):
		"""message handler"""
		if self.cereb.runInProgress:
			if self.state == 2 and \
				time.clock()>self.timeToSend:
				self.sendTime = time.clock()
				self.cereb.forwardControl = 1
				self.state = 1
				
    
 	def processTelemetry(self,tele):
		"""message handler"""
		if hasattr(self,"prevTime"):
			self.telemetryIntervals.append(
				time.clock()-self.prevTime)
		self.prevTime = time.clock()

		if self.state == 0:
			if tele.ctl == "--":
				sendDelay = self.sendDelayStep*self.sendDelayIndex
				self.timeToSend = time.clock()+sendDelay 
				self.state = 2
		elif self.state == 1:
			if tele.ctl != "--":
				self.delays[self.sendDelayIndex].\
					append(time.clock()-self.sendTime)
				self.sendDelayIndex = \
					(self.sendDelayIndex+1) % self.maxSendDelayIndex
				self.cereb.forwardControl = 0
				self.state = 0
				
	def runFinish(self,runNumber):
		"""message handler"""
		
		fout = open("log/stats.html","wt")
		fout.write("<html><body></body></html>")
		fout.write("telemetry intervals: <br/> <img src='%s'/> <hr/>"%
				   delaysToGraph(self.telemetryIntervals))
		
		for i in range(self.maxSendDelayIndex):
			fout.write("reaction if we send %0.2fs after tele: <br/>"%
					    (self.sendDelayStep*i)+
						"<img src='%s'/> <br>"%
						delaysToGraph(self.delays[i],height=50))
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