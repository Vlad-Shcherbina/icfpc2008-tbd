from compiler.ast import Pass
import os
from misc import * 

class Stats(object):
	def __init__(self):
		#################
		# private variables
		self.timeOffsetFilter = None
		self.currentControl = (0, 0)
		self.commandsInPrevFrame
		
		##################
		# publicly available accumulated statistics
		
		self.x = 0.0
		self.y = 0.0
		self.dir = 0.0
		self.speed = 0.0
		
		self.maxSpeed = 0.0
		self.maxTurn = 0.0
		self.maxHardTurn = 0.0
		
		self.lastTelemetry = None 

	def getTimeOffset(self):
		return self.timeOffsetFilter.value
	timeOffset = property(getTimeOffset)
	
	def getFrameRelativeTime(self):
		return time.clock() - self.timeOffset - self.lastTelemetry.timeStamp
	frameRelativeTime = property(getFrameRelativeTime)
		
	
	
	# public interface invoked by cerebellum
	def processInitData(self, message):
		self.maxSpeed = message.maxSpeed
		self.maxTurn = message.maxTurn
		self.maxHardTurn = message.maxHardTurn
	
	def runStart(self, runNumber):
		self.timeOffsetFilter = None
		self.lastTelemetry = None
		pass
	
	def processTelemetry(self, message):
		# time offset
		newOffset = message.localTimeStamp - message.timeStamp
		if self.timeOffsetFilter is None:
			self.timeOffsetFilter = FOFilter(0.5, newOffset)
		else: 
			diff = self.timeOffsetFilter.value - newOffset 
			self.timeOffsetFilter.next(newOffset)
#			print "%6.3f %6.3f %6.3f" % (message.localTimeStamp, self.timeOffsetFilter.value, diff)
			
		self.lastTelemetry = message
	
	def processEvent(self, message):
		pass
	
	def commandSent(self, control):
		pass 

class FakeStats(object):
	def processInitData(self, message):
		pass
	
	def runStart(self, runNumber):
		pass
	
	def processTelemetry(self, message):
		pass
	
	def processEvent(self, message):
		pass
	
	def commandSent(self, control):
		pass
	
# returns singlton stats object
_stats = None
def getStats():
	global _stats
	if (_stats is None):
		_stats = FakeStats() #it isn't used anyway
	return _stats



#		#update reception latency
#		if self.clockOffset == None:
#			self.clockOffset = FOFilter(0.0, time.clock() - tele.timeStamp);
#			self.avgReceptionLatency = FOFilter(0.1, 0.0)
#		else:
#			clock = time.clock()
#			newOffset =  clock - tele.timeStamp
#			diff = self.clockOffset.value - newOffset 
##			print "%6.3f %6.3f %6.3f" % (clock, self.clockOffset.value, diff)
#			self.avgReceptionLatency.next(abs(diff))
#			self.clockOffset.next(newOffset)
			

class CommandHistory(object):
	def __init__(self):
		self.commands = []
		self.prev = None
		self.semaphore = Semaphore()
		
	def cmd(self,command):
		self.semaphore.acquire()
		for c in command:
			if c in "ablr":
				self.commands.append([time.clock(),c,"current"])
		print self.commands
		self.semaphore.release()
		
	def processTelemetry(self,tele):
		cur = RoverState(tele)
		if self.prev is not None:
			t=time.clock()
			#self.semaphore.acquire()
			def popCommand(command):
				for i in range(len(self.commands)):
					if self.commands[i][1] == command and \
						self.commands[i][2] != "annihilated":
						cmd = self.commands.pop(i)
#						print cmd
						if cmd[2] == "current":
							# command was processed in closed tele
							statistics.goodLatency(t-cmd[0])
						elif cmd[2] == "outdated":
							# was not
							statistics.badLatency(t-cmd[0])
						else:
							assert False
						return
				for i in range(len(self.commands)):
					if self.commands[i][1] == command and \
						self.commands[i][2] == "annihilated":
						cmd = self.commands.pop(i)
						return
				assert False
				
			for i in range(cur.forwardControl-self.prev.forwardControl):
				popCommand("a")
			for i in range(self.prev.forwardControl-cur.forwardControl):
				popCommand("b")
			for i in range(cur.turnControl-self.prev.turnControl):
				popCommand("l")
			for i in range(self.prev.turnControl-cur.turnControl):
				popCommand("r")
				
			statusChange = {
				"current":"outdated",
				"outdated":"outdated",
				"annihilated":"annihilated"}
			for c in self.commands:
				if c[2]=="current":
					c[2]="outdated" 

			# annihilate outdated pairs
			def findPair(pos,neg,annihilated):
				posIndex = None
				negIndex = None
				for i in range(len(self.commands)):
					if posIndex is None and \
						self.commands[i][1]==pos and \
						(self.commands[i][2]=="annihilated")==annihilated:
						posIndex = i
					if negIndex is None and \
						self.commands[i][1]==neg and \
						(self.commands[i][2]=="annihilated")==annihilated:
						negIndex = i
				if posIndex is not None and negIndex is not None:
					return (posIndex,negIndex)
				else:
					return None
			for pos,neg in [("a","b"),("l","r")]:
				pair = findPair(pos,neg,annihilated=False)
				if pair is not None:
					self.commands[pair[0]][2]="annihilated"
					self.commands[pair[1]][2]="annihilated"
				pair = findPair(pos,neg,annihilated=True)
				if pair is not None:
					if self.commands[pair[0]][0]<t-1 and\
						self.commands[pair[1]][0]<t-1:
						self.commands.pop(max(pair))
						self.commands.pop(min(pair))
			#self.semaphore.release()
		self.prev = cur













# internal stuff

goodLatencies = []

def goodLatency(lat):
#    print "good",lat
    goodLatencies.append(lat)
    pass


badLatencies = []

def badLatency(lat):
#    print "baad",lat
    badLatencies.append(lat)
    pass

def delaysToGraph(delays,height=100,seconds=1):
    steps = 100
    freqs = [0 for i in range(steps)]
    for d in delays:
        f = int(d*steps/seconds)
        if f<steps:
            freqs[f] += 1
    
    freqs = ",".join([str(int(100*f/(1e-2+max(freqs)))) for f in freqs])
    marks = "|".join([str(0.1*i) for i in range(seconds*10+1)])
    
    res = "http://chart.apis.google.com/chart?" +\
        "cht=lc&chd=t:%s&chs=400x%s&chl=%s"%(freqs,height,marks)
    return res

def showFinalStats():
    fout = open("log/stats.html","wt")
    fout.write("<html><body></body></html>")
    fout.write("good latencies: <br/> <img src='%s'/> <hr/>"%
                delaysToGraph(goodLatencies))
    fout.write("bad latencies: <br/> <img src='%s'/> <hr/>"%
                delaysToGraph(badLatencies))
    fout.close()
    os.system("start log\\stats.html")
                