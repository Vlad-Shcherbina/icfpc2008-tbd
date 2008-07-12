from protocol import *

class StaticMap(object):
	def __init__(self):
		self.staticObjects = []

	def processInitData(self,initData):
		self.dx = initData.dx
		self.dy = initData.dy

	def processTelemetry(self,tele):
		"""message handler"""
		for o in tele.objects:
			if isinstance(o,StaticObject):
				if o not in self.staticObjects:
					print "static object added"
					self.staticObjects.append(o)

