import socket

host = ""
port = 12345

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))

s.listen(1)

conn, addr = s.accept()
print 'Connected by', addr

for i in range(5):
	conn.send("I 10 10 999.9 1 2 1 2 3.3 ;")
	conn.send("T 3450 aL -234.040 811.100 47.5 8.450 b -220.000 750.000 12.000 m -240.000 812.000 90.0 9.100 ;")
	conn.send("S 0 ;")
	conn.send("E 0 999.9 ;")
#while 1:
#    data = conn.recv(1024)
#    if not data: break
#    conn.send(data)


conn.close()

