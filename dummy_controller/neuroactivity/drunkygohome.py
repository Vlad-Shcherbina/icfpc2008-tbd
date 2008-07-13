import math
import cerebellum

def reverse(angle):
	"""
	Reverses the angle direction 180 degrees, keeping it with in -180/180 range
	"""
	angle += 180
	if angle > 180: angle -= 360
	return angle


class DrunkyGoHome(object):
	"""
	Higher Neuroactivity handler
	Drunky man going home
	"""

	def __init__(self, cerebellum):
	    self.change = 0
	    self.cerebellum = cerebellum
	
	def processInitData(self, initData):
		self.initData = initData
		print initData.__dict__
#	def runStart(self,runNumber):
#		print "run %s started"%runNumber
#	def processEvent(self,event):
#		pass
#	def runFinish(self,runNumber):
#		print "run %s finished"%runNumber

		
	def setCerebellum(self, cerebellum):
		self.cerebellum = cerebellum
	
	def ifTurningRight(self):
	    print "right: %d" % (self.tele.ctl[1] == 'r' or self.tele.ctl[1] == 'R')
	    return self.tele.ctl[1] == 'r' or self.tele.ctl[1] == 'R'

	def ifTurningLeft(self):
	    return self.tele.ctl[1] == 'l' or self.tele.ctl[1] == 'L'

	def processTelemetry(self, tele):

		self.tele = tele

		print "pos: %f %f %f speed: %f ctl:%s" % (tele.x, tele.y, tele.dir, tele.speed, tele.ctl)
		
		maxSpeed = self.initData.maxSpeed

		#
		# Approaching base - slowdown man!
		if tele.x**2+tele.y**2 < (tele.speed*2)**2:
		    maxSpeed /= 4
		
		if tele.speed < maxSpeed:
			self.cerebellum.cmd("a;")
		else:
			self.cerebellum.cmd("b;")

		
		
		angle = 0

		if (tele.x != 0):
			angle = math.degrees(math.atan2(tele.y, tele.x))
			
			angle = reverse(angle)
			
			dDir = cerebellum.subtractAngles(tele.dir, angle)
			print "angle: %f %f" % (angle, dDir)        
		
		
		if dDir > 0:
			if not self.ifTurningRight(): self.cerebellum.cmd("r;")
		else:
			if not self.ifTurningLeft(): self.cerebellum.cmd("l;")

		#if self.change < 1:
			#self.cerebellum.send("r;")
			#self.change += 1
			

		pass


