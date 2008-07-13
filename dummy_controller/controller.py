import sys
import time

from protocol import *
from cerebellum import Cerebellum
from misc import *

visualize = eval(open("visualize.config").readline())

if len(sys.argv) != 3:
    print "specify ip and port"
    exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])

connection = Connection(ip,port)
cerebellum = Cerebellum(connection)

def mainLoop():
    cerebellum.mainLoop()
