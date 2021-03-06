import sys
import time

from protocol import *
from cerebellum import Cerebellum
from misc import *
from static_map import StaticMap
from predictor import physicalValues,serverMovementPredictor

visualize = eval(open("visualize.config").readline())

if len(sys.argv) != 3:
    print "specify ip and port"
    exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])

connection = Connection(ip,port)
cerebellum = Cerebellum(connection)

staticMap = StaticMap()
cerebellum.registerMessageHandler(staticMap)

cerebellum.registerMessageHandler(physicalValues)
cerebellum.registerMessageHandler(serverMovementPredictor)



def mainLoop():
    cerebellum.mainLoop()
