from protocol import *
from static_map import *
from math import *

def calc_hit(x1, y1, x2, y2, px, py, R, r, g):
    """
    calculates the math magic for an obstacle (px,py) with the radius R over 
    the segment ((x1,y1),(x2,y2)).
    r - rover radius
    g - preferred avoidance distance (safe distance to pass by an obstacle)
    returns:
     - None when the point's height does not hit the segment
     - distance till the point of an obstacle hit and coordinates of 
     recommended avoidance point otherwise
    """
    a2 = (x2-px)**2 + (y2-py)**2
    b2 = (x1-x2)**2 + (y1-y2)**2
    c2 = (x1-px)**2 + (y1-py)**2
    b = sqrt(b2)
    c = sqrt(c2)
    cosalpha = (b2 + c2 - a2) / (2 * b * c) 
    # b != 0 because then we reached the target; c != 0 because then we died 
    if (cosalpha < 0.0): 
        return None # does not hit
    assert cosalpha <= 1.01
    assert cosalpha >= -1.01
    l = c * cosalpha
    if l > b: 
        return None # does not hit
    sinalpha2 = 1.0 - cosalpha**2
    if sinalpha2 < 0: sinalpha2 = 0
    sinalpha = sqrt(sinalpha2)
    assert sinalpha <= 1.01
    assert sinalpha >= -1.01
    h = abs(c * sinalpha)
    if h > R: 
        return None # does not hit
    hx = x1 + ((x2 - x1) * l) / b;
    hy = y1 + ((y2 - y1) * l) / b;
    if h == 0:
        ox = px + ((y2 - y1) * (R + g + r)) / b;
        oy = py + ((x1 - x2) * (R + g + r)) / b;
        d = l - sqrt(R**2 - h**2)
    else:
        ox = px + ((hx - px) * (R + g + r)) / h;
        oy = py + ((hy - py) * (R + g + r)) / h;
        d = l - sqrt(R**2 - h**2)
    return (d, ox, oy)

class SimpleStackLogic(object):
    def __init__(self, cere, mymap):
        self.cere = cere
        self.mymap = mymap
        self.resetTargets()
        
    def resetTargets(self):
        self.targets = [(0,0)]

    def processInitData(self,initData):
        self.dx = initData.dx
        self.dy = initData.dy

    def runStart(self,runNumber):    
        self.resetTargets()

    def processTelemetry(self,tele):
        """message handler"""
        x1 = tele.x
        y1 = tele.y
        if len(self.targets) == 0: 
            return
        self.checkReached(x1, y1)
        if len(self.targets) == 0: 
            return
        x2, y2 = self.targets[0]
        d_min = None
        ox_min = None
        oy_min = None
        for o in self.mymap.staticObjects:
            rslt = calc_hit(x1, y1, x2, y2, o.x, o.y, o.radius, 0.5, 0.1)
            if rslt is not None:
                d, ox, oy = rslt
                if (d_min is None) or (d < d_min):
                    d_min = d
                    ox_min = ox
                    oy_min = oy
        if d_min is not None:
            # we found an obstacle to avoid
            self.addTarget(ox_min, oy_min)
        x2, y2 = self.targets[0]
        self.cere.command = ("moveTo",x2,y2)
        
    def processEvent(self, event):
        """We should reset targets stack after bounce"""
        if event.tag == 'B':
            self.resetTargets()
            
    def addTarget(self, x, y):
        self.targets.insert(0, (x,y))
    
    def checkReached(self, x, y):
        tx, ty = self.targets[0]
        if sqrt((tx-x)**2 + (ty-y)**2) < 1: # less than 1
            self.targets.pop(0)
                    
    