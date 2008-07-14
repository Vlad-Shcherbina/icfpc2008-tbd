import math
import cerebellum

from protocol import *
from misc import *

class DrunkyGoHome(object):
	"""
	Higher Neuroactivity handler
	Drunky man going home
	"""

	def __init__(self, cerebellum, staticmap):
	    self.change = 0
	    self.cerebellum = cerebellum
	
	def processInitData(self, initData):
		self.initData = initData

#	def runStart(self,runNumber):
#		print "run %s started"%runNumber
#	def processEvent(self,event):
#		pass
#	def runFinish(self,runNumber):
#		print "run %s finished"%runNumber

		
	def setCerebellum(self, cerebellum):
		self.cerebellum = cerebellum
	
	def ifTurningRight(self):
	    return self.tele.ctl[1] == 'r' or self.tele.ctl[1] == 'R'

	def ifTurningLeft(self):
	    return self.tele.ctl[1] == 'l' or self.tele.ctl[1] == 'L'

	def ifDirectionTooWrong(self, directionDiff):
		return abs(directionDiff) > 90



	def thinkOnSpeed(self):

		maxSpeed = self.initData.maxSpeed
		#
		# Approaching base - slowdown man!
		if self.tele.x**2 + self.tele.y**2 < (self.tele.speed*2)**2:
		    maxSpeed /= 4
		
		if self.tele.speed < maxSpeed:
			self.cerebellum.cmd("a;")
		else:
			self.cerebellum.cmd("b;")


	def thinkOnHomeDirection(self):
		#
		# Fixing angle
		#

		angle = math.degrees(math.atan2(self.tele.y, self.tele.x))
		
		angle = reverse(angle)
		
		directionDiff = subtractAngles(self.tele.dir, angle)
		print "angle: %f %f" % (angle, directionDiff)
    	
		#
		# Restore direction
		if abs(directionDiff) < 10:
			if directionDiff > 0:
				if self.ifTurningRight():
					self.cerebellum.cmd("l;")
			else:
				if self.ifTurningLeft():
					self.cerebellum.cmd("r;")
			return

		#
		# Fix direction
		if directionDiff > 0:
			if self.ifDirectionTooWrong(directionDiff) or not self.ifTurningRight():
				self.cerebellum.cmd("r;")
		else:
			if self.ifDirectionTooWrong(directionDiff) or not self.ifTurningLeft():
				self.cerebellum.cmd("l;")			


	def processTelemetry(self, tele):

		self.tele = tele

		print "pos: %f %f %f speed: %f ctl:%s" % (tele.x, tele.y, tele.dir, tele.speed, tele.ctl)
		
		self.thinkOnSpeed()
		
		
		for o in self.tele.objects:
			if isinstance(o, StaticObject) and o.kind != 'h':
				#print o
				pass
		
		self.thinkOnHomeDirection()

		pass

