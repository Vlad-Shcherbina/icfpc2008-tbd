from threading import Thread	
import sys
import math

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

name = 'suka glut'

class Visualizer(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.displayCommands = []
		self.initData = None
		self.telemetry = None

	def run(self):
		print "hello"
		glutInit(sys.argv)
		glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
		glutInitWindowSize(400,400)
		glutCreateWindow(name)
		glEnable(GL_DEPTH_TEST)

		glClearColor(0.,0.,0.,1.)
		glutDisplayFunc(self.display)
		glutIdleFunc(self.idle)

		glutMainLoop()

	def idle(self):
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
		glutSolidSphere(1,20,10)
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
	
		if self.telemetry:
			self.rover()	
#		glColor3f(1,1,0)
#		glutSolidSphere(1,10,10)
		glPopMatrix()
		glutSwapBuffers()


if __name__ == '__main__': 
	v = Visualizer(10,10)
	print "x"
	v.start()