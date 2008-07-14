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
	    self._right = 0
	    self._accel = 0
	
	def directcmdx(self, c):
		print "--", c
		self.cerebellum.connection.sendCommand(c)
		#self.cerebellum.cmd(c)

	def processInitData(self, initData):
		self.initData = initData


	def runStart(self,runNumber):
		self.directcmdx("a;a;a;")
#	def processEvent(self,event):
#		pass
#	def runFinish(self,runNumber):
#		print "run %s finished"%runNumber

		
	def left(self, c = 1):
		self._right -= c;
	def right(self, c = 1):
		self._right += c;
	def accel(self, c = 1):
		self._accel += c;
	def br(self, c = 1):
		self._accel -= c;


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
			self.accel()
		else:
			self.br()


	def thinkOnHomeDirection(self):
		#
		# Fixing angle
		#

		angle = math.degrees(math.atan2(self.tele.y, self.tele.x))
		
		angle = reverse(angle)
		
		directionDiff = subtractAngles(self.tele.dir, angle)
		#print "angle: %f %f" % (angle, directionDiff)
    	
		#
		# Restore direction
		#if abs(directionDiff) < 10:
		#	return

#			if directionDiff > 0:
#				if self.ifTurningRight():
#					self.left()
#			else:
#				if self.ifTurningLeft():
#					self.right()
#			return

		#
		# Fix direction
		if directionDiff > 10:
			self.right()
		elif directionDiff < -10:
			self.left()			


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
		    self.accel()
		    self.right(3)
		elif self.ifTurningRight():
		    self.accel()
		    self.left(3)
		else: # panic!
		    self.accel(4)
		    self.left(6)

	def processTelemetry(self, tele):

		self.tele = tele

		print "speed: %f ctl:%s" % (tele.speed, tele.ctl)		
		self._right = 0
		self._accel = 0


		
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
					self.accel()
			if isinstance(c[3], StaticObject) and c[3].kind != 'h':
				if (60 < c[0] < 90) and c[2] > 10:
					log("lllllllllll StaticObject")
					self.left(2)
				if (90 < c[0] < 120) and c[2] > 10:
					log("rrrrrrrrrrr StaticObject")
					self.right(2)
				#crater
				if (60 < c[0] < 120) and c[2] > 30 and c[3].kind == 'c':
					log("bbbbbbbbbbb Crater")
					self.br(1)
		
				
		self.thinkOnSpeed()

		#print this.objectcloud
		
		if not self.underAttack:
			self.thinkOnHomeDirection()

		
		if self.tele.ctl[0] == 'a':
			self._accel -= 1
		
		if self.tele.ctl[0] == 'b':
			self._accel += 1
		if self.tele.ctl[1] == 'l':
			self._right += 1
		if self.tele.ctl[1] == 'L':
			self._right += 2
		if self.tele.ctl[1] == 'r':
			self._right -= 1
		if self.tele.ctl[1] == 'R':
			self._right -= 2
		
		if (self._right > 0):
		    self.directcmdx("r;" * abs(self._right))
		if (self._right < 0):
		    self.directcmdx("l;" * abs(self._right))
		if (self._accel > 0):
		    self.directcmdx("a;" * abs(self._accel))
		if (self._accel < 0):
		    self.directcmdx("b;" * abs(self._accel))

		pass

