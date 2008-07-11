import sys

print reduce(lambda a, y: "TBD-"+y+"-"+a+y, sys.argv[1:], "TBD")
