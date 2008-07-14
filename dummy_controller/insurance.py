from predictor import *

class Insurance(object):
	"""
	This message handler have to be registered in cerebellum AFTER
	high-level logic
	"""
	def __init__(self):
		pass
	def runStart(self,currentRun):
		"""message handler"""
		self.rover = None

	def processTelemetry(self,tele):
		"""message handler"""
		# assuming that serverMovementPredictor already
		# received this tele
		self.rover = RoverState(tele,self.rover)
		self.predictedTrace = []

	def draw(self):
		from visualizer import *	
		glBegin(GL_LINES)
		glColor3f(1,0,0)
		for p in self.predictedTrace:
			glVertex2f(p.x,p.y)
		glEnd()