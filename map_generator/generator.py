#!/usr/bin/python
import psyco
psyco.full()

import os
import sys
from random import *

print "use: generator.py <mapsize> <craters> <boulders> <runs> <enemies>"
size = int(sys.argv[1])
n_craters = int(sys.argv[2])
n_boulders = int(sys.argv[3])
n_runs = int(sys.argv[4])
n_enemies = int(sys.argv[5])

maxradius = 30

fname = "map_%s_c%s_b%s_r%s_e%s.wrld" % (size, n_craters, n_boulders, n_runs, n_enemies)

f = open(fname, 'w' )

craters = ""
for _ in xrange(0, n_craters):
    if _ > 0: craters += ","
    craters += """
            {
                "x" : %f,
                "y" : %f,
                "r" : %f
              }
    """ % (randrange(-size/2, size/2), randrange(-size/2, size/2), random()*maxradius)

boulders = ""
for _ in xrange(0, n_boulders):
    if _ > 0: boulders += ","
    boulders += """
        {
                "x" : %f,
                "y" : %f,
                "r" : %f
          }
    """ % (randrange(-size/2, size/2), randrange(-size/2, size/2), random()*maxradius)


enemies = ""
for _ in xrange(0, n_enemies):
    if _ > 0: enemies += ","
    enemies += """
                  {
                    "x" : %f,
                    "y" : %f,
                    "dir" : %f,
                    "speed" : %f,
                    "view" : %f
                  }
    """ % (randrange(-size/2, size/2), randrange(-size/2, size/2), random()*360, randrange(0, 30), randrange(30, 100))

runs = ""
for _ in xrange(0, n_runs):
    if _ > 0: runs += ","
    runs += """
        {
            "vehicle" : {
                "x" : %f,
                "y" : %f,
                "dir" : %f
              },
            "enemies" : [
    %s
              ]
          }
    """ % (randrange(-size/2, size/2), randrange(-size/2, size/2), random()*360, enemies)

maps = """
{
    "size" : %d,
    "timeLimit" : 30000,
    "vehicleParams" : {
        "maxSpeed" : 20,
        "accel" : 2,
        "brake" : 3,
        "turn" : 20,
        "hardTurn" : 60,
        "frontView" : 60,
	    "rotAccel" : 120,
        "rearView" : 30
      },
    "martianParams" : {
        "maxSpeed" : 20,
        "accel" : 2,
        "brake" : 3,
        "turn" : 20,
        "hardTurn" : 60,
        "rotAccel" : 120,
        "frontView" : 60,
        "rearView" : 30
      },
    "craters" : [
%s
      ],
    "boulders" : [
%s
      ],
    "runs" : [
%s
      ]
}

""" % (size, craters, boulders, runs)

f.write(maps)
