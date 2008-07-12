#!/usr/bin/python

import time

from protocol import *
from cerebellum import Cerebellum


##################
# main

if len(sys.argv) != 3:
	print "specify ip and port"
	exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])

conn = Connection(ip,port)
cereb = Cerebellum(conn)
conn.start()

t = time.clock()
while conn.isRunning():
	if time.clock() > t+0.5:
		t = time.clock()
		cereb.printInfo()
	cereb.update()
	
