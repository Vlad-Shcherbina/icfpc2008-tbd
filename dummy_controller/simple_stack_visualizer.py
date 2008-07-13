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

class StackVisualizer():
    def __init__(self, logic):
        self.logic = logic
        
    def display(self):
        for t in self.logic.targets:
            o , tx, ty = t
            target(tx, ty)

def createDrawer(logic):
    rt = StackVisualizer(logic)
    return rt.display