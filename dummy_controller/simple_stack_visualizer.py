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

class StackVisualizer(Visualizer):
    def __init__(self, logic, cerebellum, staticMap, keyHandler = None):
        Visualizer.__init__(self, cerebellum, staticMap, keyHandler)
        self.logic = logic
        
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
            
        for t in self.logic.targets:
            tx, ty = t
            target(tx, ty)
            
        #self.testIntersection()

        glPopMatrix()
        glutSwapBuffers()
