import psyco
psyco.full()

from threading import Thread	
import sys
from math import *
from random import random
import time

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from protocol import *


name = 'suka glut'

def circle(x,y,r,segments=50):
	glBegin(GL_LINE_LOOP)
	for i in range(segments):
		a = 2*3.1415/segments*i
		glVertex2f(x+r*cos(a),y+r*sin(a))
	glEnd()



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
	print node
	print node.childs
	print node.objects
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
		#self.setDaemon(True)
		self.terminate = False
		
		self.cerebellum = cerebellum
		self.staticMap = staticMap
		self.keyHandler = keyHandler
		
		cerebellum.registerMessageHandler(self)
		

	def run(self):
		glutInit([])
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		glutInitWindowSize(800,800)
		glutCreateWindow(name)
		glEnable(GL_DEPTH_TEST)

		glClearColor(0.,0.,0.,1.)
		glutDisplayFunc(self.display)
		glutIdleFunc(self.idle)
		if (self.keyHandler):
			glutKeyboardFunc(self.keyhandler)

		glutMainLoop()
		
	def idle(self):
		if self.terminate:
			print "terminate"
			#exit()
		time.sleep(0.01)
		glutPostRedisplay()

	def processInitData(self,initData):
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
				
	def base(self):
		glColor3f(0,1,0)
		circle(0,0,5)
		for i in range(1,5):
			circle(0,0,i)
			
	def martian(self,martian):
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
	
	def display(self):
		if not hasattr(self,"initData"): return
		if self.terminate:
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

		if self.cerebellum.runInProgress and hasattr(self,"tele"):
			self.base()
			self.rover()
			for o in self.tele.objects:
				if isinstance(o,StaticObject):
					staticObject(o,highlight=True)
					pass
				else:
					self.martian(o)

			# previously remembered objects
			drawNode(self.staticMap.tree)
			for o in self.staticMap.staticObjects:
				staticObject(o)

		glPopMatrix()
		glutSwapBuffers()

