import math
from numpy import *

import cerebellum

from protocol import *
from misc import *

class DrunkyGoHome(object):
	"""
	Higher Neuroactivity handler
	Drunky man going home
	"""

	def __init__(self, cerebellum, physicalValues, staticmap):
	    self.change = 0
	    self.physicalValues = physicalValues
	    self.cerebellum = cerebellum
	    self.objectcloud = []
	    self.underAttack = False
	
	def directcmd(self, c):
		self.cerebellum.connection.sendCommand(c)

	def processInitData(self, initData):
		self.initData = initData


	def runStart(self,runNumber):
		self.directcmd("a;a;a;")
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
		
		# slowdown because of steering
		maxSpeed = maxSpeed - (maxSpeed/2*(140-self.physicalValues.rotAccel)/140)
		
		#
		# Approaching base - slowdown man!
		if self.tele.x**2 + self.tele.y**2 < (maxSpeed*2)**2:
		    maxSpeed /= 4
		if not self.underAttack:
			if self.tele.x**2 + self.tele.y**2 < (maxSpeed)**2:
				maxSpeed /= 2
		
		if self.tele.speed < maxSpeed:
			self.directcmd("a;")
		else:
			self.directcmd("b;")


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
					self.directcmd("l;")
			else:
				if self.ifTurningLeft():
					self.directcmd("r;")
			return

		#
		# Fix direction
		if directionDiff > 0:
			if self.ifDirectionTooWrong(directionDiff) or not self.ifTurningRight():
				self.directcmd("r;")
		else:
			if self.ifDirectionTooWrong(directionDiff) or not self.ifTurningLeft():
				self.directcmd("l;")			


	def fillObjectCloud(self, obj):
		if isinstance(obj, StaticObject) and obj.kind == 'h':
			return None
		
		if isinstance(obj, Martian):
			objRadius = 10 # warn on martians
		else:
			objRadius = obj.radius

		relx = obj.x - self.tele.x
		rely = obj.y - self.tele.y

		objectAngle = math.degrees(math.atan2(rely, relx))
		#to local rover coorinates: forward is UP is 90
		mA = subtractAngles(90 + objectAngle, self.tele.dir)
		
		#mA = math.radians(mA)
		#turnMatrix = matrix([ [math.cos(mA), -math.sin(mA)], [math.sin(mA), math.cos(mA)] ])		
		#result = (turnMatrix * matrix([[relx],[rely]])).tolist()[0]

		visualAngle = 90
		if relx != 0 and rely != 0:
			visualAngle = math.degrees(math.asin(objRadius/math.sqrt(relx**2+rely**2)))
		
		return (mA, objectAngle, visualAngle, obj)
		 
	def martianAttack(self):
		log("================ martianAttack!")		
		if self.ifTurningLeft():
			self.directcmd("a;r;r;");
		elif self.ifTurningRight():
			self.directcmd("a;l;l;");
		else: # panic!
			self.directcmd("l;l;l;l;a;a;a;a;");

	def processTelemetry(self, tele):

		self.tele = tele

		print "pos: %f %f %f speed: %f ctl:%s" % (tele.x, tele.y, tele.dir, tele.speed, tele.ctl)
		

		self.objectcloud = []
		for obj in self.tele.objects:
			self.objectcloud.append(self.fillObjectCloud(obj) )
		
		self.underAttack = False

		for c in self.objectcloud:
			if isinstance(c[3], Martian):
				if (50 < c[0] < 130):
					self.underAttack = True
					self.martianAttack()
				# haste!
				if (-130 < c[0] < -50):
					self.directcmd("a;")
			if isinstance(c[3], StaticObject):
				if (60 < c[0] < 90) and c[2] > 10:
					log("lllllllllll StaticObject")
					self.directcmd("l;")
				if (90 < c[0] < 120) and c[2] > 10:
					log("rrrrrrrrrrr StaticObject")
					self.directcmd("r;")
		
				
		self.thinkOnSpeed()

		#print this.objectcloud
		
		if not self.underAttack:
			self.thinkOnHomeDirection()

		pass

