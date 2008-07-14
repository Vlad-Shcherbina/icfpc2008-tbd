from predictor import *
from controller import *

class Insurance(object):
    """
    This message handler have to be registered in cerebellum AFTER
    high-level logic
    """
    def __init__(self):
        pass
    def runStart(self,currentRun):
        """message handler"""
        self.rover = None

    def processTelemetry(self,tele):
        """message handler"""
        
        self.lookAhead = 1.0
        
        smp = serverMovementPredictor
        
        actualRover = smp.predict(smp.latency)[-1]
        if smp.rover is None:
            self.predictedTrace = []
            return
        self.predictedTrace = predict(actualRover,[],self.lookAhead,dt=0.05)

        return
        
        badness = self.traceBadness(self.predictedTrace)
        
        if badness>0:
            print "ATTENTION! DANGER",badness
            #print 50*"="
            self.avoid(actualRover)
        
    def traceBadness(self,trace):
        for p in trace:
            obj = staticMap.intersect(p.x, p.y)
            if obj is not None:
                if obj.kind == "c":
                    return 10
                elif obj.kind == "b":
                    return 1
        return 0
    
    def avoid(self,actualRover):
        smp = serverMovementPredictor
        
        candidates = [(-1,1),(-1,-1),(-1,0)]
        #candidates = [(-1,0)]
        
        curTime = time.clock()
        
        minimum = 1e10
        for control in candidates:
            cmds = [ControlRecord(control,curTime+smp.latency)]
            trace = predict(actualRover,cmds,self.lookAhead,dt=0.05)
            badness = self.traceBadness(trace)
            if badness<minimum:
                minimum = badness
                bestControl = control
        if minimum == 0:
            print "avoided!,",bestControl
        cerebellum.setControl(bestControl)

    def draw(self):
        from visualizer import *    
        glBegin(GL_LINE_STRIP)
        glColor3f(1,1,0)
        for p in self.predictedTrace:
            glVertex2f(p.x,p.y)
        glEnd()