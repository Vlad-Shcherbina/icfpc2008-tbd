import psyco
psyco.full()

from threading import Thread	
import sys
from math import *
from random import *
import time

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from protocol import *
from predictor import *


name = 'suka glut'

def circle(x,y,r,segments=50):
	glBegin(GL_LINE_LOOP)
	for i in range(segments):
		a = 2*3.1415/segments*i
		glVertex2f(x+r*cos(a),y+r*sin(a))
	glEnd()

				
def base():
	glColor3f(0,1,0)
	circle(0,0,5)
	for i in range(1,5):
		circle(0,0,i)
			
def martian(martian):
	glPushMatrix()
	glTranslatef(martian.x,martian.y,0)
	glColor3f(1,0,0)
	glutSolidSphere(0.4,20,10)
	glTranslatef(
		0.4*cos(radians(martian.dir)),
		0.4*sin(radians(martian.dir)),
		0)
	glutSolidSphere(0.2,20,10)
	glPopMatrix()

def staticObject(obj,highlight=False):
	if obj.kind=="h":
		glColor3f(0,1,0)
	elif obj.kind=="c":
		glColor3f(1,0,0)
	elif obj.kind=="b":
		glColor3f(1,1,1)
	circle(obj.x,obj.y,obj.radius,segments = 20)
	if highlight:
		for i in range(1,5):
			circle(obj.x,obj.y,obj.radius*i/5,segments=10)

def drawNode(node):
	if node.childs is not None:
		for c in node.childs:
			drawNode(c)
		return
	glPushMatrix()
	glColor3f(0,0,1)
	glTranslatef(0.5*(node.x1+node.x2),0.5*(node.y1+node.y2),0)
	glScalef(0.5*(node.x2-node.x1),0.5*(node.y2-node.y1),1)
#	circle(0,0,1)
	glBegin(GL_LINE_LOOP)
	glVertex2f(-1,-1)
	glVertex2f( 1,-1)
	glVertex2f( 1, 1)
	glVertex2f(-1, 1)
	glEnd()
	glPopMatrix()
#	for o in node.objects:
#		staticObject(o)

class Visualizer(Thread):
	def __init__(self, cerebellum, staticMap, keyHandler = None):
		Thread.__init__(self)
		self.terminate = False
		
		self.cerebellum = cerebellum
		self.staticMap = staticMap
		self.keyHandler = keyHandler
		
		cerebellum.registerMessageHandler(self)
		

	def run(self):
		glutInit([])
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		glutInitWindowSize(800,800)
		self.window = glutCreateWindow(name)
		glEnable(GL_DEPTH_TEST)

		glClearColor(0.,0.,0.,1.)
		glutDisplayFunc(self.display)
		glutIdleFunc(self._idle)
		if (self.keyHandler):
			glutKeyboardFunc(self.keyHandler)

		glutMainLoop()
		
	def _idle(self):
		# because it is not a message handler
		if self.terminate:
			if self.window:
				glutDestroyWindow(self.window)
				self.window = None
			return
			#exit()
		time.sleep(0.01)
		glutPostRedisplay()

	def processInitData(self,initData):
		"""message handler"""
		self.initData = initData

	def processTelemetry(self,tele):
		"""message handler"""
		self.tele = tele

	def rover(self):
		t = self.tele
		d = self.initData
		glPushMatrix()
		glTranslatef(t.x,t.y,0)
		glColor3f(1,1,1)
		glutSolidSphere(0.5,20,10)

		glRotatef(t.dir,0,0,1)
		longAxis = (d.maxSensor+d.minSensor)*0.5
		shortAxis = sqrt(d.maxSensor*d.minSensor)
		glTranslatef((d.maxSensor-d.minSensor)*0.5,0,-5)
		glScalef(longAxis,shortAxis,0.001)
		glColor3f(0.5,0.5,0.5)
		glScalef(1,1,0.001)
		circle(0,0,1)

		glPopMatrix()
		
		phys = PhysicalValues()
		rover = RoverState(self.tele)
		commands = []
		trace = predict(phys,rover,commands,0.1,5)
		glBegin(GL_POINTS)
		glColor3f(1,1,0)
		for p in trace:
			glVertex3f(p.x,p.y,1)
		glEnd()
		
	def testIntersection(self):
		for t in range(2): 
			for i in range(-10,10):
				for j in range(-10,10):
					x = self.tele.x + i
					y = self.tele.y + j
					x += (random()-0.5)*1
					y += (random()-0.5)*1
					#if random()<0.999:
					#	continue
					if self.staticMap.intersect(x,y):
						glColor3f(1,1,0)
					else:
						glColor3f(0,1,1)
					circle(x,y,0.1,5)

	def display(self):
		if not hasattr(self,"initData") or\
			not hasattr(self,"tele") or\
			not self.cerebellum.runInProgress: 
			return

		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(-self.initData.dx*0.5,
				self.initData.dx*0.5,
				-self.initData.dy*0.5,
				self.initData.dy*0.5, -10,10)
		glMatrixMode(GL_MODELVIEW)

		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		glPushMatrix()

		base()
		self.rover()
		for o in self.tele.objects:
			if isinstance(o,StaticObject):
				staticObject(o,highlight=True)
				pass
			else:
				martian(o)

		# previously remembered objects
		drawNode(self.staticMap.tree)
		for o in self.staticMap.staticObjects:
			staticObject(o)
			
		#self.testIntersection()

		glPopMatrix()
		glutSwapBuffers()

