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
	for i in range(1,6):
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

class Visualizer(Thread):
	def __init__(self, cerebellum, staticMap, keyHandler = None):
		Thread.__init__(self)
		self.terminate = False
		self.drawers = []
		
		self.cerebellum = cerebellum
		cerebellum.registerMessageHandler(self)
		
		self.staticMap = staticMap
		self.registerDrawer(staticMap.drawer)
		
		self.keyHandler = keyHandler
		
		
	def registerDrawer(self,drawer):
		self.drawers.append(drawer)

	def run(self):
		glutInit([])
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		glutInitWindowSize(800,800)
		self.window = glutCreateWindow(name)
#		glEnable(GL_DEPTH_TEST)

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
		circle(0,0,0.5)

		glRotatef(t.dir,0,0,1)
		longAxis = (d.maxSensor+d.minSensor)*0.5
		shortAxis = sqrt(d.maxSensor*d.minSensor)
		glTranslatef((d.maxSensor-d.minSensor)*0.5,0,0)
		glScalef(longAxis,shortAxis,0.001)
		glColor3f(0.5,0.5,0.5)
		glScalef(1,1,0.001)
		circle(0,0,1)

		glPopMatrix()
		
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

		base()
		self.rover()
		for o in self.tele.objects:
			if isinstance(o,StaticObject):
				pass
			else:
				martian(o)

		for drawer in self.drawers:
			drawer()

		glutSwapBuffers()

