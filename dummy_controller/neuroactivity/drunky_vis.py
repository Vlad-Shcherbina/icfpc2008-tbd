from visualizer import *


def line(x1, y1, x2, y2):
    glBegin(GL_LINE_LOOP)
    glVertex2f(x1,y1)
    glVertex2f(x2,y2)
    glEnd()
        
def target(x, y):
    glColor3f(0,1,1)
    circle(x,y, 0.5)
    line(x-2,y-2,x+2,y+2)
    line(x-2,y+2,x+2,y-2)



class DrunkyVisualizer():
    def __init__(self, drunky):
		self.drunky = drunky

    def display(self):
		for o in self.drunky.objectcloud:
			glColor3f(1,0,0)
			sector(self.drunky.tele.x, self.drunky.tele.y, 40, o[1]-o[2], o[1]+o[2])
			sector(self.drunky.tele.x, self.drunky.tele.y, 39, o[1]-o[2], o[1]+o[2])

def createDrawer(drunky):
    return DrunkyVisualizer(drunky).display
