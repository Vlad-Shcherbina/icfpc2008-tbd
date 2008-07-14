from protocol import *
from static_map import *
from math import *

def sort(x1, y1, x2, y2):
    if x1 < x2:
        min_x = x1
        max_x = x2
    else:
        min_x = x2
        max_x = x1
    if y1 < y2:
        min_y = y1
        max_y = y2
    else:
        min_y = y2
        max_y = y1
    return min_x, min_y, max_x, max_y

def _getObjects(node, min_x, min_y, max_x, max_y):
    """selects smallest subnode of a static map tree containing both points and returns its objects.
    returns None if node does not contain given points or an array of objects otherwise.
    WARNING: The coords data must be sorted!"""
    n_min_x, n_min_y, n_max_x, n_max_y = sort(node.x1, node.y1, node.x2, node.y2)
    if min_x >= n_min_x and max_x <= n_max_x and min_y >= n_min_y and max_y <= n_max_y:
        # this node contains our objects
        childs = node.childs
        if childs is None:
            return node.objects
        else:
            for child in childs:
                objects = _getObjects(child, min_x, min_y, max_x, max_y)
                if not (objects is None):
                    return objects
            return node.calc_all_objects()
    else:
        return None 

def getObjects(node, x1, y1, x2, y2):
    """selects smallest subnode of a static map tree containing both points and returns its objects.
    returns None if node does not contain given points or an array of objects otherwise."""
    min_x, min_y, max_x, max_y = sort(x1, y1, x2, y2)
#    return node.calc_all_objects()
    return _getObjects(node, min_x, min_y, max_x, max_y)

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
    if l > b and a2 < R**2: 
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
        dx = ((y2 - y1) * (R + g + r)) / b
        dy = ((x1 - x2) * (R + g + r)) / b
        ox1 = px + dx
        oy1 = py + dy
        ox2 = px - dx
        oy2 = py - dy
    else:
        dx = ((hx - px) * (R + g + r)) / h
        dy = ((hy - py) * (R + g + r)) / h
        ox1 = px + dx
        oy1 = py + dy
        ox2 = px - dx
        oy2 = py - dy
    d = l - sqrt(R**2 - h**2)
    return (d, ox1, oy1, ox2, oy2) # distance till collision, preferred avoidance point, alternative avoidance point

def calcTargetsChainAvoidance(vx, vy, ox, oy, d, prev, objects):
    """ recursively checks if the given avoidance point hits other objects 
    and calculates the coords to avoid it by going to the same side as the given ox, oy proposes
    if no collision is expected, returns None """
    for o in objects:
        if ((ox - o.x)**2 + (oy - o.y)**2) <= o.radius**2:
            rslt = calc_hit(vx, vy, ox, oy, o.x, o.y, o.radius, 0.5, 0.5)
            if rslt is not None:
                new_d, new_ox, new_oy, new_alt_ox, new_alt_oy = rslt
                if (prev.x - new_ox)**2 + (prev.y - new_oy)**2 <= prev.radius**2:
                    new_ox = new_alt_ox
                    new_oy = new_alt_oy
                new_rslt = calcTargetsChainAvoidance(vx, by, new_ox, new_oy, o, objects)
                if new_rslt is None: return (o, new_d, new_ox, new_oy)
                else: return new_rslt
    return None

def calcCollision(vx, vy, tx, ty, objects):
    """vehicle x, vehicle y, target x, target y, list of objects"""
    d_min = None  # distance to the nearest collision 
    obj = None    # collision-causing object 
    ox_min = None # x of the recommended avoidance point
    oy_min = None # y of the recommended avoidance point
    alt_ox_min = None
    alt_oy_min = None
    for o in objects:
        rslt = calc_hit(vx, vy, tx, ty, o.x, o.y, o.radius, 0.5, 0.5)
        if rslt is not None:
            d, ox, oy, alt_ox, alt_oy = rslt
            if (d_min is None) or (d < d_min):
                d_min = d
                ox_min = ox
                oy_min = oy
                alt_ox_min = alt_ox
                alt_oy_min = alt_oy
                obj = o
    # todo: check that we did not hit more objects by this waypoint
    if obj is not None:
        o1 = None
        o2 = None
        for o in objects:
            if o1 is None and((ox_min - o.x)**2 + (oy_min - o.y)**2) <= o.radius**2:
                o1 = o
            elif o2 is None and((alt_ox_min - o.x)**2 + (alt_oy_min - o.y)**2) <= o.radius**2:
                o2 = o
            # for ease, we only suppose there is one colliding object only, otherwise we die 
        if o1 is None:
            return obj, d_min, ox_min, oy_min
        elif o2 is None:
            return obj, d_min, alt_ox_min, alt_oy_min
        else: # fuck...
            o1, new_d1, new_ox1, new_oy1 = calcTargetsChainAvoidance(vx, vy, ox_min, oy_min, d, o1, objects)
            o2, new_d2, new_ox2, new_oy2 = calcTargetsChainAvoidance(vx, vy, alt_ox_min, alt_oy_min, d, o2, objects)
            if new_d1 < new_d2:
                return o1, new_d1, new_ox1, new_oy1
            else:
                return o2, new_d2, new_ox2, new_oy2
    return obj, d_min, ox_min, oy_min

class SimpleStackLogic(object):
    def __init__(self, cere, mymap):
        self.cere = cere
        self.mymap = mymap
        self.resetTargets()
        
    def resetTargets(self):
        self.targets = [(None, 0,0)]

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
        try:
            if  tele.moreMessagesWaiting:
                print 'stack logic: skipping frame'
                return
        except AttributeError,e:
            print "!!! --- " + str(tele)
            print e
        curr_o, x2, y2 = self.targets[0]
        d_min = None  # distance to the nearest collision 
        obj = None    # collision-causing object 
        ox_min = None # x of the recommended avoidance point
        oy_min = None # y of the recommended avoidance point
        tree = self.mymap.tree
        if tree is None:
            staticObjects = self.mymap.staticObjects
        else:
            staticObjects = getObjects(tree, x1, y1, x2, y2)
            if staticObjects is None: staticObjects = self.mymap.staticObjects
        obj, d_min, ox_min, oy_min = calcCollision(x1, y1, x2, y2, staticObjects)
        if d_min is not None:
            # we found an obstacle to avoid
            self.addTarget(obj, ox_min, oy_min)
        else: # TODO: estimate if our current target is sane
            self.dropRedunantTargets(x1, y1)
        o, x2, y2 = self.targets[0]
        self.cere.command = ("moveTo",x2,y2)
        
    def dropRedunantTargets(self, x1, y1):
        if len(self.targets) > 1:
            curr_o, x2, y2 = self.targets[0]
            tree = self.mymap.tree
            next_object, next_x, next_y = self.targets[1]
            if tree is None:
                staticObjects = self.mymap.staticObjects
            else:
                staticObjects = getObjects(tree, x1, y1, next_x, next_y)
            n_coll_obj, n_d_min, n_ox_min, n_oy_min = calcCollision(x1, y1, next_x, next_y, staticObjects)
            if curr_o != n_coll_obj:
                print 'DROP target'
                self.dropNearestTarget()
                self.dropRedunantTargets(x1, y1)
        
        
        
    def processEvent(self, event):
        """We should reset targets stack after bounce"""
        if event.tag == 'B':
            self.resetTargets()
            
    def addTarget(self, o, x, y):
        self.targets.insert(0, (o, x,y))
    
    def dropNearestTarget(self):
        self.targets.pop(0)
    
    def checkReached(self, x, y):
        o, tx, ty = self.targets[0]
        if sqrt((tx-x)**2 + (ty-y)**2) < 1: # less than 1
            self.dropNearestTarget()
                    
    