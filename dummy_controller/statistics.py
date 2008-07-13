import os

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
                