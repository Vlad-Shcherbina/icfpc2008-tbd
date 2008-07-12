from random import choice
from numpy import *
from numpy.linalg import *

from protocol import *


visualize = True

if visualize:
	from visualizer import Visualizer

class MinSQ(object):
	"""Class for minimal square optimization of given constraints"""
	def __init__(self,n):
		self.n = n
		self.a = zeros((n,n))
		self.b = zeros((n,))
	def addConstraint(self,c,d):
		"""Takes constraint of the form c*x=d into account"""
		m = array([[a*b for b in c] for a in c])
		self.a += m
		self.b += c*d
			
	def solve(self):
		try:
			self.x = solve(self.a,self.b)
		except LinAlgError:
			self.x = zeros((self.n,))
			

class Cerebellum(object):
	def __init__(self,connection):
		self.connection = connection

		self.currentRun = 0

		self.initData = None
		self.messages = []


		self.newRun()

		self.minSQ = MinSQ(3)
		self.maxRotSpeed = 0
		self.maxHardRotSpeed = 0

		if visualize:
			self.vis = Visualizer()
			self.vis.start()

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

	def startRun(self,tele):
		self.runInProgress = True
		self.startTime = tele.timeStamp
		self.numTimeStamps = 0
		self.curTime = 0
		               
	def processInitData(self,initData):
		self.initialData = initData
		if visualize:
			self.vis.initData = initData

	def processTelemetry(self,tele):
		if not self.runInProgress:
			self.startRun(tele)
			return 0
		
		self.numTimeStamps += 1
		self.curTime = tele.timeStamp-self.startTime

		self.connection.sendCommand(choice(["a;","b;",";"]))

		if visualize:
			self.vis.telemetry = tele


		if self.prevTele is not None:
			dt = tele.timeStamp-self.prevTele.timeStamp
			dSpeed = tele.vehicleSpeed-self.prevTele.vehicleSpeed
			accelCmd = self.prevTele.vehicleCtl[0]
			if accelCmd=="a":
				coeffs = [dt,0]
			elif accelCmd=="-":
				coeffs = [0,0]
			elif accelCmd=="b":
				coeffs = [0,-dt]
			self.minSQ.addConstraint(
				array(coeffs+[-dt*self.prevTele.vehicleSpeed**2]),
				dSpeed )

			rotCmd = self.prevTele.vehicleCtl[1]

		self.prevTele = tele

	def preprocessMessage(self,message):
		if isinstance(message,InitData):
			self.processInitData(message)
		elif isinstance(message,Telemetry):
			self.processTelemetry(message)
		elif isinstance(message,EndOfRun):
			print "Run ended in %s with score %s"%(message.time,message.score)
			self.currentRun += 1
			if self.currentRun == maxRuns:
				print "the end"
				self.connection.close()
				if visualize:
					self.vis.join(0.01)
				exit(0)
			self.newRun()

	def esteemParams(self):
		self.minSQ.solve()
		self.accel = self.minSQ.x[0]
		self.brake = self.minSQ.x[1]
		self.drag = self.minSQ.x[2]

	def printInfo(self):
		if not self.runInProgress:
			return
		self.esteemParams()
		print "dt",self.curTime/(self.numTimeStamps+1e-6)
		print "accel",self.accel
		print "brake",self.brake
		print "drag",self.drag
