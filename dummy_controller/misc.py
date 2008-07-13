from numpy import *
from numpy.linalg import *

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
            return True
        except LinAlgError:
            return False

def subtractAngles(a,b):
    res = a-b
    while res < -180:
        res += 360
    while res > 180:
        res -= 360
    return res

def reverse(angle):
	"""
	Reverses the angle direction 180 degrees, keeping it with in -180/180 range
	"""
	angle += 180
	if angle > 180: angle -= 360
	return angle

def lerp(a, b, q):
    return a * (1 - q) + b * q

class FOFilter(object):
    def __init__(self, quotient, value = 0.0):
        self.quotient = quotient
        self.value = value
    
    def next(self, value):
        self.value = lerp(self.value, value, self.quotient)
    
    def __str__(self):
        return str(self.value)

class TestHandler(object):
    def processInitData(self,initData):
        print "init data"
    def runStart(self,runNumber):
        print "run %s started"%runNumber
    def processTelemetry(self,tele):
        pass
#        print "tele"
    def processEvent(self,event):
        print "event",event.tag
#        print "event"
    def runFinish(self,runNumber):
        print "run %s finished"%runNumber

def addMethod(*classes):
    """Adds decorated method to given classes
    
    Usage:
    @addMethod(class1,...)
    def newMethod(self,...):
        ...
        @
    """
    def t(m):
        for c in classes:
            setattr(c,m.__name__,m)
        return m
    return t
