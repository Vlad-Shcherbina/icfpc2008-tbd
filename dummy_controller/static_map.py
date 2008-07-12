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

	def intersectionObjects(self,x,y,
			clearance={"b":0.5,"c":0.1,"h":0.5}):
		# clearance for boulder is 0.5, because if we touch it, we bounce
		# silimal reason determines clearance for home
		# clearance for crate is 0 (because rover center is considered),
		# and 0.1 is added for safety
		res = []
		for o in self.staticObjects:
			dist2 = (o.x-x)*(o.x-x)+(o.y-y)*(o.y-y)
			minDist = clearance[o.kind]+o.radius
			if dist2 <= minDist*minDist:
				res.append(o)
		return res
