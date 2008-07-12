from threading import Thread	
import sys
import math

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

from protocol import *


name = 'suka glut'

def circle(x,y,r):
	glBegin(GL_LINE_LOOP)
	for i in range(100):
		a = 2*3.1415/100*i
		glVertex2f(x+r*math.cos(a),y+r*math.sin(a))
	glEnd()
		

class Visualizer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.displayCommands = []
		self.initData = None
		self.telemetry = None
		self.terminate = False

	def run(self):
		print "hello"
		glutInit(sys.argv)
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		glutInitWindowSize(400,400)
		glutCreateWindow(name)
#		glEnable(GL_DEPTH_TEST)

		glClearColor(0.,0.,0.,1.)
		glutDisplayFunc(self.display)
		glutIdleFunc(self.idle)

		glutMainLoop()

	def idle(self):
		if self.terminate:
			exit()
		glutPostRedisplay()


	def rover(self):
		t = self.telemetry
		d = self.initData
		glPushMatrix()
		glTranslatef(t.vehicleX,t.vehicleY,0)
		glColor3f(1,1,1)
		glutSolidSphere(0.5,20,10)

		glRotatef(t.vehicleDir,0,0,1)
		smallAxis = math.sqrt(d.maxSensor*d.minSensor)
		glScalef(d.maxSensor+d.minSensor,smallAxis,0.001)
		glTranslatef((d.maxSensor-d.minSensor)*0.5,0,0)
		glColor3f(0.5,0.5,0.5)
		circle(0,0,1)
		glPopMatrix()

	def staticObject(self,obj,highlight=False):
		if obj.kind=="h":
			glColor3f(0,1,0)
		elif obj.kind=="c":
			glColor3f(0,1,0)
		elif obj.kind=="b":
			glColor3f(1,1,1)
		circle(obj.x,obj.y,obj.radius)
		if highlight:
			for i in range(10):
				circle(obj.x,obj.y,obj.radius*i/10)
			
	def martian(self,martian):
		glPushMatrix()
		glTranslatef(martian.x,martian.y,0)
		glColor3f(1,0,0)
		glutSolidSphere(0.4,20,10)
		glTranslatef(
			0.4*math.cos(math.radians(martian.dir)),
			0.4*math.sin(math.radians(martian.dir)),
			0)
		glutSolidSphere(0.2,20,10)
		glPopMatrix()
	
	def display(self):
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glOrtho(-self.initData.dx*0.5,
				self.initData.dx*0.5,
				-self.initData.dy*0.5,
				self.initData.dy*0.5, -10,10)
		glMatrixMode(GL_MODELVIEW)

		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
		glPushMatrix()

		for c in self.displayCommands:
			eval(c)

		for o in self.cerebellum.staticObjects:
			self.staticObject(o)

		if self.telemetry:
			self.rover()
			for o in self.telemetry.objects:
				if isinstance(o,StaticObject):
					self.staticObject(o,highlight=True)
				else:
					self.martian(o)

		glPopMatrix()
		glutSwapBuffers()

