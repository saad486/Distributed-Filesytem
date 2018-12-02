import socket
HOST = '192.168.1.103'
import subprocess
import config

serverFileList = []

#------------------------------------------------
def saveFile(sock, file):
	sock.send('ok'.encode())
	f = open(file,'wb')
	while True:
		data = sock.recv(1024)
		if data.endswith('EOF'.encode()):
			data = data[:-3]
			f.write(data)
			break
		f.write(data)
	f.close()
#--------------------------------------------

def uploadFile(sock, fileName, msg=''):
	sendVariable ='upload '+fileName
	if msg.decode() == 'send':
		f = open(fileName,'rb')
		l = f.read(1024)
		while (l):
			sock.sendall(l)
			l = f.read(1024)
		f.close()
		sock.send('EOF'.encode())
#-------------------------------------------

#---------------------------------------
def createFiles(sock,fileName, msg=''):
	if msg == '':
		sendVariable ='create '+fileName
		sock.send(sendVariable.encode())
		ret = sock.recv(1024)
	else:
		ret = msg
	print(ret)
	if ret.decode() == 'send':
		f = open(fileName,'rb')
		l = f.read(1024)
		while(l):
			sock.sendall(l)
			l = f.read(1024)
		f.close()
		sock.send('EOF'.encode())

#-------------------------------------------
print("Enter the port no:\n")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
PORT = input("prompt:\n")
s.connect((HOST, int(PORT)))

while True:
	data = input("prompt:")
	s.sendall(data.encode())
	msg = s.recv(1024)
	print(msg,'client')
	print(msg)
	if not msg:
		s.close()
		break

	listOfData = data.split(' ')

	if listOfData[0] == 'ls':
		print(msg.decode())

	elif listOfData[0] == 'download':
		if msg.decode() == 'Not local':
			s.send('ok'.encode())
			addr = s.recv(1024)

			b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			b.connect((addr,6666))
			b.sendall(data.encode())
			msgFromAnotherServer = b.recv(1024)

			if msgFromAnotherServer.decode() == 'local':
				print('Got the file remotely')
				saveFile(b, listOfData[1])
				proc = subprocess.Popen(['leafpad', listOfData[1]])
				proc.wait()
					##save in the list
				serverFileList.append([addr,listOfData[1]])
				s.close()
				s = b

		elif msg.decode() == 'local':
			print('Got the file locally')
			saveFile(s,listOfData[1])
			proc = subprocess.Popen(['leafpad', listOfData[1]])
			proc.wait()
			serverFileList.append([HOST,listOfData[1]])

	elif listOfData[0] == 'create':
		proc = subprocess.Popen(['leafpad', listOfData[1]])
		proc.wait()
		createFiles(s,listOfData[1],msg)

	elif listOfData[0] == 'upload':
		print('here upload')
		proc = subprocess.Popen(['leafpad', listOfData[1]])
		proc.wait()
		uploadFile(s,listOfData[1],msg)
