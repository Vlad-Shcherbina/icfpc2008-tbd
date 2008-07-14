"""
Pathfinder is a callable that 
accepts current rover state and target coordinates 
and returns trace.

Empty list means that no path was found
"""

from predictor import *

def moveTo(rover,targetX,targetY,targetRadius=2,dt=None):
    if dt is None:
        dt = DEFAULT_DT
    rover = copy(rover)
    commands = []
    curCommand = 0
    trace = []
    n = 0
    
    rover = serverMovementPredictor.predict(serverMovementPredictor.latency,
                                            rover)[-1]
    
    while (rover.x-targetX)**2+(rover.y-targetY)**2>targetRadius**2 and n<200:
        command = ControlRecord((0,0),
                                rover.localT)

        desiredDir=degrees(atan2(targetY-rover.y,
                                 targetX-rover.x))
        dDir = subtractAngles(desiredDir, rover.dir)

        if dDir>10:
            command.turnControl = 2
        elif dDir>3:
            command.turnControl = 1
        elif dDir>-3:
            command.turnControl = 0
        elif dDir>-10:
            command.turnControl = -1
        else:
            command.turnControl = -2        

        dirX = cos(radians(rover.dir))
        dirY = sin(radians(rover.dir))
        dot = dirX*(targetX-rover.x)+dirY*(targetY-rover.y)
        if dot>0:
            command.forwardControl = 1
        else:
            command.forwardControl = 0

            
        commands.append(command)
        curCommand = roverSimulationStep(rover, dt, commands, curCommand)
        trace.append(copy(rover))
        n += 1

    return trace
