from misc import *
from math import *
from copy import copy


class PhysicalValues(object):
    def __init__(self):
        self.maxSpeed = 20
        self.accel = 2
        self.brake = 3
        self.turn = 20
        self.hardTurn = 60
        self.rotAccel = 120
        self.drag = 1.0*self.accel/(self.maxSpeed**2)
    def processInitData(self,initData):
        """message handler"""
        self.maxSpeed = initData.maxSpeed
        self.turn = initData.maxTurn
        self.hardTurn = initData.maxHardTurn

        
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
    def setRotSpeed(self,prevTele):
        dt = self.t-prevTele.timeStamp
        if dt>1e-4:
            dDir = subtractAndles(self.dir,prevTele.dir)
            self.rotSpeed = dDir/dt


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