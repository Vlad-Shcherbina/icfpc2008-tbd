from protocol import *

NODE_MAX_OBJECTS = 5

clearance={"b":0.5,"c":0.1}
# clearance for boulder is 0.5, because if we touch it, we bounce
# clearance for crate is 0 (because rover center is considered),
# and 0.1 is added for safety

def radius(o):
	return o.radius+clearance[o.kind]


def rectCircleIntersection(x1,y1,x2,y2,x,y,r):
	"""Returns 
	0 if no intersection, 
	1 if objects intersect,
	2 if circle covers rect completely
	"""
	# point in rectangle closest to circle center
	cx = max(min(x,x2),x1)
	cy = max(min(y,y2),y1)
	if (cx-x)*(cx-x)+(cy-y)*(cy-y) > r*r:
		return 0
	# farthest
	if x+x > x1+x2:
		fx = x1
	else:
		fx = x2
	if y+y > y1+y2:
		fy = y1
	else:
		fy = y2
	if (fx-x)*(fx-x)+(fy-y)*(fy-y) < r*r:
		return 2
	else:
		return 1


class Node(object):
	"""
	Fields:
		x1,y1,x2,y2
		objects
		covered:Bool
		parent
		childs[] or None if leaf
		verticalSplit (if false, then split is horisontal)
	If node is covered, then objects is a list of a single element
	"""
	def __init__(self,x1,y1,x2,y2,objects):
		self.x1 = x1
		self.y1 = y1
		self.x2 = x2
		self.y2 = y2
		self.objects = []
		self.covered = False
		self.childs = None
		for o in objects:
			self.addObject(o)
	def addObject(self,o):
		if self.covered:
			return
		intersection = rectCircleIntersection(
			self.x1,self.y1,self.x2,self.y2,
			o.x,o.y,radius(o))
		if intersection == 0:
			return
		if intersection == 2:
			self.covered = True
			self.objects = [o]
			self.childs = None
			return
		if self.childs is None:
			self.objects.append(o)
			if len(self.objects)>NODE_MAX_OBJECTS \
				and max(self.x2-self.x1,self.y2-self.y1)>1:
				self.subdivide()
		else:
			for c in self.childs:
				c.addObject(o)
	def subdivide(self):
		if self.x2-self.x1>self.y2-self.y1:
			xs = [self.x1,0.5*(self.x1+self.x2),self.x2]
			ys = [self.y1,self.y2]
			self.verticalSplit = True
		else:
			xs = [self.x1,self.x2]
			ys = [self.y1,0.5*(self.y1+self.y2),self.y2]
			self.verticalSplit = False
		self.childs = []
		for i in range(len(xs)-1):
			for j in range(len(ys)-1):
				child = Node(xs[i],ys[j],xs[i+1],ys[j+1],self.objects)
				child.parent = self
				self.childs.append(child)
#		self.objects = None
	def __str__(self):
		return "Node (%s,%s)-(%s,%s)"%(self.x1,self.y1,self.x2,self.y2)
	def draw(self):
		from visualizer import *		
		if self.childs is not None:
			for c in self.childs:
				c.draw()
			return
		glPushMatrix()
		glColor3f(0,0,1)
		glTranslatef(0.5*(self.x1+self.x2),0.5*(self.y1+self.y2),0)
		glScalef(0.5*(self.x2-self.x1),0.5*(self.y2-self.y1),1)
		circle(0,0,1)
		glBegin(GL_LINE_LOOP)
		glVertex2f(-1,-1)
		glVertex2f( 1,-1)
		glVertex2f( 1, 1)
		glVertex2f(-1, 1)
		glEnd()
		glPopMatrix()
		for obj in self.objects:
			glColor3f(0,1,1)
			circle(obj.x+0.2,obj.y,obj.radius)
	def calc_all_objects(self):
		if self.childs is None:
			return self.objects
		else:
			rt = []
			for child in self.childs:
				rt += child.calc_all_objects()
			return rt


class StaticMap(object):
	def __init__(self):
		self.staticObjects = []
		self.objectsHash = {}
		self.tree = None

	def processInitData(self,initData):
		self.dx = initData.dx
		self.dy = initData.dy
		if self.tree == None:
			self.tree = Node(-0.5*self.dx,-0.5*self.dy,
							  0.5*self.dx, 0.5*self.dy,[])
			self.tree.parent = None
			self.curNode = self.tree

	def processTelemetry(self,tele):
		"""message handler"""
		for o in tele.objects:
			if isinstance(o,StaticObject):
				if not self.objectsHash.has_key(o):
					self.staticObjects.append(o)
					self.objectsHash[o] = True
					self.tree.addObject(o)
					self.curNode = self.tree

	def intersect(self,x,y):
		"""Returns None or one of the objects intersected"""
		node = self.curNode
		while (x<node.x1 or x>node.x2 or
				y<node.y1 or y>node.y2) and \
			node.parent is not None:
			node = node.parent
		while node.childs is not None:
			if node.verticalSplit:
				if x+x<node.x1+node.x2:
					node = node.childs[0]
				else:
					node = node.childs[1]
			else:
				if y+y<node.y1+node.y2:
					node = node.childs[0]
				else:
					node = node.childs[1]
		self.curNode = node
		for o in node.objects:
			dist2 = (o.x-x)*(o.x-x)+(o.y-y)*(o.y-y)
			minDist = radius(o)
			if dist2 <= minDist*minDist:
				return o
		return None
	def drawer(self):
		from visualizer import *
#		for obj in self.staticObjects:
		for obj in self.tree.calc_all_objects():
			if obj.kind=="c":
				glColor3f(1,0,0)
			elif obj.kind=="b":
				glColor3f(1,1,1)
			circle(obj.x,obj.y,obj.radius,segments = 20)

		if self.tree: self.tree.draw()
	

#	for o in node.objects:
#		staticObject(o)
