#!/usr/bin/python

from protocol import *



##################3
# main

if len(sys.argv) != 3:
	print "specify ip and port"
	exit(1)
ip = sys.argv[1]
port = int(sys.argv[2])


conn = Connection(ip,port)

currentRun = 0
runInProgress = False

while True:
	while conn.messages != []:
		message = conn.messages.pop(0)

		# message handling routine is here
#		print message.__dict__
		if isinstance(message,InitData):
			print "Init message"
		elif isinstance(message,Telemetry):
			runInProgress = True
			print message.__dict__
			conn.sendCommand("a;")
		elif isinstance(message,EndOfRun):
			print "Run ended with score",message.score
			runInProgress = False
			currentRun += 1
			if currentRun == maxRuns:
				print "the end"
				conn.close()
				exit(0)
	conn.update()
	
