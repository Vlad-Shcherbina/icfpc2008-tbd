from math import *
from copy import copy
import time

from misc import *

DEFAULT_DT = 0.15

# TODO: replace it with estimate
DEFAULT_LATENCY = 0.05

class PredictionDrawer(object):
	
	def __init__(self):
		pass

	def runStart(self,tele):
		self.rover = None

	def processTelemetry(self,tele):
		self.rover = RoverState(tele,self.rover)

	def __call__(self):
		from visualizer import *
		trace = predict(self.rover,
						commands=[],
						interval=5)
		glBegin(GL_POINTS)
		glColor3f(1,1,0)
		for p in trace:
			glVertex3f(p.x,p.y,1)
		glEnd()


class PhysicalValues(object):
    """
    This class is responsible for estimation of all simulation parameters
    """
    def __init__(self):
        self.maxSpeed = 0
        self.accel = 2
        self.brake = 3
        self.turn = 20
        self.hardTurn = 60
        self.rotAccel = 123.4 # this is initial value, it is used specifically
        self.drag = 0
        
        #initialize esteems
        self.abdSQ = MinSQ(3) # for accel, brake and drag
        self.adSQ = MinSQ(2) # for accel and drag

        self.esteemParams()
                
    def processInitData(self,initData):
        """message handler"""
        self.maxSpeed = initData.maxSpeed
        self.turn = initData.maxTurn
        self.hardTurn = initData.maxHardTurn
        
    def runStart(self,runNumber):
        self.hist = []
        
    def processEvent(self,event):
        """message handler"""
        if event.tag=="B":
            self.hist = []
        
    def processTelemetry(self,tele):
        """message handler"""
        if len(self.hist)>0:
            state = RoverState(tele,self.hist[-1])
        else:
        	state = RoverState(tele)
        self.hist.append(state)
        self.hist = self.hist[-7:] # keep last seven states
        
        if len(self.hist) >= 2:
            dt = self.hist[-1].serverT-self.hist[-2].serverT

            forwardControl = self.hist[-2].forwardControl

            # form constraint of the form of the motion equation
            # dv = dt*accel - dt*drag*speed*speed
            speed = 0.5*(self.hist[-1].speed+self.hist[-2].speed) 
            dSpeed = self.hist[-1].speed-self.hist[-2].speed
            if forwardControl==1:
                self.abdSQ.addConstraint(
                    array([dt,0,-dt*speed**2]),dSpeed)
                self.adSQ.addConstraint(
                    array([dt,-dt*speed**2]),dSpeed)
            elif forwardControl==0:
                self.abdSQ.addConstraint(
                    array([0,0,-dt*speed**2]),dSpeed)
                self.adSQ.addConstraint(
                    array([0,-dt*speed**2]),dSpeed)
            elif forwardControl==-1:
                if self.brake>1e-6:
                    w = min(dt,speed/self.brake)
                else:
                    w = dt
                self.abdSQ.addConstraint(
                    array([0,-w,-dt*speed**2]),dSpeed)

        self.esteemParams()

        if len(self.hist) >= 3:
            # calculate angular acceleration
            
            #if there were turn commands in recent history (say, five states)
            if any([self.hist[-2].turnControl != s.turnControl 
                   for s in self.hist[-7:-2]]):
                dt2 = self.hist[-1].serverT-self.hist[-3].serverT
                if dt2>1e-4:
                    curRotAccel = (self.hist[-1].rotSpeed-self.hist[-2].rotSpeed)/\
                                  (0.5*dt2)
                    curRotAccel = abs(curRotAccel)
                    if self.rotAccel == 123.4 or curRotAccel>self.rotAccel:
                        # 120 - initial value, it can be overriden.
                        # increase no more than 10 percents a time
                        # to reduce damage from fluctuations
                        self.rotAccel = min(curRotAccel,self.rotAccel*1.10)

            
    def esteemParams(self):
        if self.abdSQ.solve():
            self.accel = self.abdSQ.x[0]
            self.brake = self.abdSQ.x[1]
            self.drag = self.abdSQ.x[2]
        elif self.adSQ.solve():
            self.accel = self.adSQ.x[0]
            self.brake = 0
            self.drag = self.adSQ.x[1]
            
        self.typicalSpeed = max(0.5*self.maxSpeed,0.01)
        self.typicalAccel = max(0.5*(self.accel+self.brake),0.01)
        self.typicalRotSpeed = max(0.5*(self.turn+self.hardTurn),0.01)
        #self.printInfo()
        
    def printInfo(self):
        print "Physical values estimates:"
        print "  accel",self.accel
        print "  brake",self.brake
        print "  drag",self.drag
        print "  rotAccel",self.rotAccel

physicalValues = PhysicalValues()


class ControlRecord():
	__slots__=("time", "forwardControl", "turnControl")
	def __init__(self,controlTuple,t = None):
		if t is None:
			self.time = time.clock()
		else:
			self.time = t
		self.forwardControl,self.turnControl = controlTuple
	def __repr__(self):
		return "'%s%s'@%.3f"%(
			"b-a"[self.forwardControl+1],
			"Rr-lL"[self.turnControl+2],
			self.time
			)
			

class ServerMovementPredictor(object):
	"""
	Keeps commands that are sent but not executed by server because of latency
	"""
	def __init__(self):
		pass
		
	def runStart(self,currentRun):
		self.controls = []
		self.rover = None
	
	def commandSent(self,controlTuple):
		t = time.clock()
		#clean up sent commands
		while len(self.controls)>0 and self.controls[0].time < t-self.latency:
			self.controls.pop(0)
			
		self.controls.append(ControlRecord(controlTuple))
		#print self.controls

	def processTelemetry(self,tele):
		self.rover = RoverState(tele,self.rover)

	def getLatency(self):
		# TODO - add estimation here!!!!!!
		return DEFAULT_LATENCY
	latency = property(getLatency)
	
	def predict(self,interval):
		commands = []
		for c in self.controls:
			cmd = copy(c)
			cmd.time += self.latency
			commands.append(cmd)
		return predict(self.rover,commands,interval)
        
serverMovementPredictor = ServerMovementPredictor()
        

class RoverState(object):
    """
    Represents telemetry data, but without objects
    """
    __slots__ = (
        "serverT","localT",
        "x","y","dir","speed","rotSpeed","forwardControl","turnControl")
    
    def __init__(self,tele=None,prevState = None):
    	# prev state is used to determine rotSpeed
    	if tele is None:
    		return
        self.serverT = tele.timeStamp # only for parameter estimation
        self.localT = tele.localTimeStamp
        self.x = tele.x
        self.y = tele.y
        self.dir = tele.dir
        self.speed = tele.speed
        self.forwardControl = {"b":-1,"-":0,"a":1}[tele.ctl[0]]
        self.turnControl = {"R":-2,"r":-1,"-":0,"l":1,"L":2}[tele.ctl[1]]
        
        if prevState is None:
        	self.rotSpeed = 0
        else:
            dt = self.serverT-prevState.serverT
            if dt>1e-4:
                dDir = subtractAngles(self.dir,prevState.dir)
                self.rotSpeed = dDir/dt
            else:
                self.rotSpeed = prevState.rotSpeed
    
    def lerp(self,another,t):
    	# it should be optimized if required
        for slot in RoverState.__slots__:
           setattr(self,slot,(1-t)*getattr(self,slot)+t*getattr(another,slot))

    def dist(self,another): 
        return \
            sqrt((self.x-another.x)**2+abs(self.y-another.y)**2)
            
    def penalty(self,another):
        return \
            (sqrt((self.x-another.x)**2+abs(self.y-another.y)**2)/\
                physicalValues.typicalSpeed)**3 +\
            abs(self.speed-another.speed)/\
                physicalValues.typicalAccel+\
            abs(subtractAngles(self.dir,another.dir))/\
                physicalValues.typicalRotSpeed

def roverSimulationStep(rover,dt,commands=None,firstCommand=0):
    phys = physicalValues
    
    if commands is not None:
        #update controls
        while firstCommand<len(commands) and \
        	  commands[firstCommand].time < rover.localT:
            rover.forwardControl = commands[firstCommand].forwardControl
            rover.turnControl = commands[firstCommand].turnControl
            firstCommand += 1
            
        while firstCommand<len(commands) and \
              commands[firstCommand].time < rover.localT+dt:
            partialDt = commands[firstCommand].time-rover.localT
            roverSimulationStep(rover,partialDt) # recursion deep is 1
            dt -= partialDt
            rover.forwardControl = commands[firstCommand].forwardControl
            rover.turnControl = commands[firstCommand].turnControl
            firstCommand += 1
            
            
    #update speed
    accel = [-phys.brake,0,phys.accel][rover.forwardControl+1]
    rover.speed += dt*accel
    dragDelta = -rover.speed
    maxDragDelta = dt*rover.speed*rover.speed*phys.drag
    dragDelta = max(min(dragDelta,maxDragDelta),-maxDragDelta)
    rover.speed += dragDelta
    rover.speed = max(rover.speed,0)
    rover.speed = min(rover.speed,phys.maxSpeed)
    
    desiredRotSpeed = \
        [-phys.hardTurn,-phys.turn,0,phys.turn,phys.hardTurn] \
        [rover.turnControl+2]
    rotSpeedDelta = subtractAngles(desiredRotSpeed,rover.rotSpeed)
    rotSpeedDelta = \
        max(min(rotSpeedDelta,dt*phys.rotAccel),-dt*phys.rotAccel)
    rover.rotSpeed += rotSpeedDelta
        
    #update position and direction
    rover.x += dt*rover.speed*cos(radians(rover.dir))
    rover.y += dt*rover.speed*sin(radians(rover.dir))
    rover.dir += dt*rover.rotSpeed
    rover.dir = subtractAngles(rover.dir,0)

    rover.localT += dt
    rover.serverT +=dt
    
    return firstCommand

def predict(rover,commands,interval,dt=None):
    """
    Constructs the trace of the rover.
    
    Commands is list of control records
    
    Returns list of roverStates
    """
    finishTime = rover.localT+interval
    if dt is None:
        n = max(ceil(interval/DEFAULT_DT),1)
        dt = interval/n
    else:
        n = max(ceil(interval/dt),1)
        
    res = []
    cur = 0
    intervalSimulated = 0
    for i in range(n):
        rover = copy(rover)
        if intervalSimulated+dt>interval:
        	dt = interval-intervalSimulated
        cur=roverSimulationStep(rover,dt,commands,cur)
        res.append(rover)
        intervalSimulated += dt
        
    return res

def lerpTrace(time,trace,firstElem=0):
	assert firstElem < len(trace)
	while firstElem < len(trace) and trace[firstElem].localT<time:
		firstElem += 1
	if firstElem > len(trace)-2:
		return trace[-1]
	dt = trace[firstElem+1].localT-trace[firstElem].localT 
	if dt<1e-3:
		return trace[-1]
	res = copy(trace[firstElem])
	res.lerp(trace[firstElem+1],(time-trace[firstElem].localT)/dt)
	return res 