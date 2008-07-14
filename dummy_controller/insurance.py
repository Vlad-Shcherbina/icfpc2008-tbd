from predictor import *
import controller

class Insurance(object):
    """
    This message handler have to be registered in cerebellum AFTER
    high-level logic
    """
    def __init__(self):
        self.predictedTrace = []
        pass
    def runStart(self,currentRun):
        """message handler"""
        self.rover = None

    def fixControl(self,control):
        smp = serverMovementPredictor

        #print "brake: ",physicalValues.brake
        if abs(physicalValues.brake)>1e-2:
            self.lookAhead = min(smp.rover.speed/abs(physicalValues.brake),3)
        else:
            self.lookAhead = 0.567
        print "look ahead ",self.lookAhead
        
        actualRover = smp.predict(smp.latency)[-1]
        cmd = ControlRecord(control)
        self.predictedTrace = predict(actualRover,[cmd],self.lookAhead,dt=0.05)
        
        badness = self.traceBadness(self.predictedTrace)
        if badness>0:
            print "danger",badness
            control = (-1,-control[1])
        
        return control

    def processTelemetry(self,tele):
        """message handler"""
        return
        
    def traceBadness(self,trace):
        for p in trace:
            obj = controller.staticMap.intersect(p.x, p.y)
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