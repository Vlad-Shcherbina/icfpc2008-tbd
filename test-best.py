vals = [2, 3, -5, 0]

result = [el * el for el in vals if el > 0]

result = map(lambda x : x*x, vals)

print result



m = [[3] * 4 for _ in xrange(4)]
m[1][1] = 5
print m