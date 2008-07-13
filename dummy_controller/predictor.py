from misc import *
from math import *
from copy import copy


class PhysicalValues(object):
    """
    This class is responsible for estimation of all simulation parameters
    """
    def __init__(self):
        self.maxSpeed = 0
        self.accel = 1
        self.brake = 1
        self.turn = 20
        self.hardTurn = 60
        self.rotAccel = 120 # this is initial value, it is used specifically
        self.drag = 0
        
        #initialize esteems
        self.abdSQ = MinSQ(3) # for accel, brake and drag
        self.adSQ = MinSQ(2) # for accel and drag
                
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
        self.hist.append(RoverState(tele))
        self.hist = self.hist[-7:] # keep last seven states
        
        if len(self.hist) >= 2:
            self.hist[-1].setRotSpeed(self.hist[-2])
            
            dt = self.hist[-1].t-self.hist[-2].t

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
                dt2 = self.hist[-1].t-self.hist[-3].t
                if dt2>1e-4:
                    curRotAccel = (self.hist[-1].rotSpeed-self.hist[-2].rotSpeed)/\
                                  (0.5*dt2)
                    curRotAccel = abs(curRotAccel)
                    if self.rotAccel == 120 or curRotAccel>self.rotAccel:
                        # 120 - initial value, it can be overriden
                        
                        # increase no more than 10 percents a time
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
            
        self.printInfo()
        
    def printInfo(self):
        print "Physical values estimates:"
        print "  accel",self.accel
        print "  brake",self.brake
        print "  drag",self.drag
        print "  rotAccel",self.rotAccel
        
class RoverState(object):
    def __init__(self,tele):
        self.t = tele.timeStamp
        self.x = tele.x
        self.y = tele.y
        self.dir = tele.dir
        self.speed = tele.speed
        self.forwardControl = {"b":-1,"-":0,"a":1}[tele.ctl[0]]
        self.turnControl = {"R":-2,"r":-1,"-":0,"l":1,"L":2}[tele.ctl[1]]   
        self.rotSpeed = 0
    def setRotSpeed(self,prevState):
        dt = self.t-prevState.t
        if dt>1e-4:
            dDir = subtractAngles(self.dir,prevState.dir)
            self.rotSpeed = dDir/dt
        else:
            self.rotSpeed = prevState.rotSpeed


def predict(phys,roverState,commands,dt,interval):
    """
    Constructs the trace of the rover.
    
    phys is PhysicalValues object
    Commands is list of the form [(time,cmd),...]
    
    Returns list of roverStates
    """
    rover = copy(roverState)
    finishTime = rover.t+interval
    res = []
    cur = 0
    while rover.t < finishTime:
        #update controls
        while cur<len(commands) and commands[cur][0]<rover.t:
            for c in commands.cur[1]:
                if c=="a":
                    if rover.forwardControl<1:
                        rover.forwardControl += 1
                elif c=="b":
                    if rover.forwardControl>-1:
                        rover.forwardControl -= 1
                elif c=="l":
                    if rover.turnControl<2:
                        rover.turnControl += 1
                elif c=="r":
                    if rover.turnControl>-2:
                        rover.turnControl += 1
            cur += 1
            
        #update speed
        accel = [-phys.brake,0,phys.accel][rover.forwardControl+1]
        rover.speed += dt*accel
        dragDelta = -rover.speed
        maxDragDelta = dt*rover.speed*rover.speed*phys.drag
        dragDelta = max(min(dragDelta,maxDragDelta),-maxDragDelta)
        rover.speed += dragDelta
        rover.speed = max(rover.speed,0)
        
        #rover.speed = min(rover.speed,phys.maxSpeed)
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

        rover.t += dt
        
        res.append(copy(rover))
        
    return res