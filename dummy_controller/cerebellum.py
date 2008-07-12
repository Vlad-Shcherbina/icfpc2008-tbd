from protocol import *

class Cerebellum(object):
	def __init__(self,connection):
		self.connection = connection

		self.currentRun = 0

		self.initialData = None
		self.messages = []

		self.newRun()
	

	def update(self):
		self.connection.update()
		while self.connection.hasMessage():
			m = self.connection.popMessage()
			self.preprocessMessage(m)
			self.messages.append(m)

	def newRun(self):
		print "run",self.currentRun
		self.runInProgress = False
		self.prevTele = None
		self.accel = None

	def processTelemetry(self,tele):
		self.runInProgress = True
		self.connection.sendCommand("a;")
		if self.prevTele is not None:
			dt = tele.timeStamp-self.prevTele.timeStamp
			if self.prevTele.vehicleCtl[0]=="a" and dt>1e-6:
				self.accel = \
					(tele.vehicleSpeed-self.prevTele.vehicleSpeed)/dt
				print self.accel
		self.prevTele = tele

	def preprocessMessage(self,message):
		if isinstance(message,InitData):
			self.initialData = message
		elif isinstance(message,Telemetry):
			self.processTelemetry(message)
		elif isinstance(message,EndOfRun):
			print "Run ended in %s with score %s"%(message.time,message.score)
			self.currentRun += 1
			if self.currentRun == maxRuns:
				print "the end"
				conn.close()
				exit(0)
			self.newRun()

	def printInfo(self):
		if not self.runInProgress:
			return
		print "accel = ",self.accel
