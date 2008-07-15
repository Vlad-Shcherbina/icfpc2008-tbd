"""
Renders maps in icfpc2008 .wrld format.

Usage:
    showmap.py <map.wrld>
"""

import sys
import time
import math

from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *

import demjson

name = 'pyglut template'

winW = 400
winH = 400

# view parameters
x = 0
y = 0
size = 1

def drawEllipse(x,y,max,min,dir):
    glPushMatrix()
    glTranslatef(x,y,0)
    glRotatef(dir,0,0,1)
    longAxis = (max+min)*0.5
    shortAxis = math.sqrt(max*min)
    glTranslatef((max-min)*0.5,0,0)
    glScalef(longAxis,shortAxis,0.001)
    glBegin(GL_QUADS)
    drawTexRect(-1,-1,1,1)
    glEnd()
    glPopMatrix()

class Map(object):
    def __init__(self,fileName):
        data = demjson.decode(open(sys.argv[1]).read())
        self.size = data["size"]
        self.boulders = [(b["x"],b["y"],b["r"]) for b in data["boulders"]]
        self.craters = [(b["x"],b["y"],b["r"]) for b in data["craters"]]
        
        vp = data["vehicleParams"]
        self.frontView = vp ["frontView"]  
        self.rearView = vp ["rearView"]
        
        self.runs = data["runs"]  
        
    def __str__(self):
        return "map size %s"%self.size
        
    def draw(self):
        glDisable(djpmGL_TEXTURE_2D)
        glColor3f(0.6,0.2,0)
        glBegin(GL_QUADS)
        drawTexRect(-0.5*self.size,-0.5*self.size,0.5*self.size,0.5*self.size)
        glEnd()
        
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        glColor3f(1,0.3,0)
        for x,y,r in self.boulders:
            drawTexRect(x-r,y-r,x+r,y+r)
            
        glColor3f(0.3,0.1,0)
        for x,y,r in self.craters:
            drawTexRect(x-r,y-r,x+r,y+r)
            
        glColor3f(0,1,0)
        drawTexRect(-5,-5,5,5) # base
        glEnd()
        
        for run in self.runs:
            glColor4f(0,0,1,0.4)
            x = run["vehicle"]["x"]
            y = run["vehicle"]["y"]
            dir = run["vehicle"]["dir"]
            drawEllipse(x,y, self.frontView,self.rearView, dir)
            
            glBegin(GL_QUADS)
            glColor3f(1,1,1)
            drawTexRect(x-0.5,y-0.5,x+0.5,y+0.5)

            for e in run["enemies"]:
                x = e["x"]
                y = e["y"]
                dir = e["dir"]
                view = e["view"]
                glColor4f(1,0,0.5,0.2)
                drawTexRect(x-view,y-view,x+view,y+view)
                glColor3f(0,0,0)
                drawTexRect(x-0.4,y-0.4,x+0.4,y+0.4)
                glColor3f(1,0,0)
                drawTexRect(x-0.3,y-0.3,x+0.3,y+0.3)
            glEnd()
            
        

def drawTexRect(x1, y1, x2, y2):
    glTexCoord2f(0,0)
    glVertex2f(x1,y1)
    glTexCoord2f(1,0)
    glVertex2f(x2,y1)
    glTexCoord2f(1,1)
    glVertex2f(x2,y2)
    glTexCoord2f(0,1)
    glVertex2f(x1,y2)

def display():
    global winW,winH
    glViewport(0,0,winW,winH)

    glClearColor(00,0.0,0.0,1.0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    if winW!=0:
        glOrtho(x-0.5*size,x+0.5*size,y-0.5*size,y+0.5*size,-1,1)
        glScalef(float(winH)/winW,1,1)
        
    glMatrixMode(GL_MODELVIEW)
    
    global map


    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glPushMatrix()
    map.draw()
    glPopMatrix()
    
    glutSwapBuffers()
    glutPostRedisplay()

mx = 0
my = 0
zoomIn = False
zoomOut = False

t = 0
 
def idle():
    global t
    global x,y,size
    
    dt = time.clock()-t
    t += dt
    
    zoomSpeed = 2
    zoom = math.exp(-dt*zoomSpeed)
    if zoomIn:
        size *= zoom
        x = mx+zoom*(x-mx)
        y = my+zoom*(y-my)
        
    if zoomOut:
        size /= zoom
        #x = mx+zoom*(x-mx)
        #y = my+zoom*(y-my)
        
    if size < 10:
        size = 10
    global map
    if size > map.size:
        size = map.size
    
    if x-0.5*size<-0.5*map.size:
        x = -0.5*map.size + 0.5*size
    if y-0.5*size<-0.5*map.size:
        y = -0.5*map.size + 0.5*size
    if x+0.5*size> 0.5*map.size:
        x =  0.5*map.size - 0.5*size
    if y+0.5*size> 0.5*map.size:
        y =  0.5*map.size - 0.5*size
    
    
    glutPostRedisplay()

def mouseMove(xx,yy):
    global mx,my
    mx = (float(xx)/winW-0.5)*size+x
    my = (float(winH-yy)/winH-0.5)*size+y
    print mx,my

def mouse(button,state,x,y):
    global zoomIn,zoomOut
    if button == GLUT_LEFT_BUTTON:
        zoomIn = state==GLUT_DOWN
    if button == GLUT_RIGHT_BUTTON:
        zoomOut = state==GLUT_DOWN
    print zoomIn,zoomOut

def keyboard(key,x,y):
    if key == chr(27):
        sys.exit()

def resize(w,h):
    global winW,winH
    winW,winH = w,h
    
def initTexture():
    size = 256
    data = ""
    for i in range(size):
        for j in range(size):
            r2 = (i-size/2)**2+(j-size/2)**2
            data += chr(255)*3
            if r2 < (0.75*size/2)**2:
                data += chr(255)
            else:
                data += chr(0)
    gluBuild2DMipmaps(
        GL_TEXTURE_2D, 4, 
        size, size,
        GL_RGBA, GL_UNSIGNED_BYTE, 
        data);
        
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,
                    GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,
                    GL_LINEAR_MIPMAP_LINEAR)

def initGlut():
    global winW,winH
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(winW,winH)
    glutCreateWindow(name)
    
    glutDisplayFunc(display)
    glutReshapeFunc(resize)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(mouseMove)
    glutPassiveMotionFunc(mouseMove)
    glutIdleFunc(idle)

#############################3
def main():
    global map

    if len(sys.argv)!=2:
        print __doc__
        return
    
    map = Map(sys.argv[1])
    
    global size
    size = map.size
    print map
    
    initGlut()
    
    initTexture()
    
    glutMainLoop()
    

if __name__ == '__main__': 
    main()