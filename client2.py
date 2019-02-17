import clientConfig

import socket
HOST = clientConfig.CLIENT_CONFIG[0]
import subprocess

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
	if msg.decode() == 'Local':
		sock.sendall('ok'.encode())
		msg = sock.recv(1024)
		if msg == 'send'.encode():
			f = open(fileName,'rb')
			l = f.read(1024)
			while (l):
				sock.sendall(l)
				l = f.read(1024)
			f.close()
			sock.send('EOF'.encode())
			return None
	else:
		sock.sendall('ok'.encode())
		msg = sock.recv(1024)
		addr = msg.decode()
		b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		b.connect((addr,6666))
		b.sendall(sendVariable.encode())
		msgFromAnotherServer = b.recv(1024)
		if msgFromAnotherServer.decode() == 'Local':
			b.sendall('ok'.encode())
			msgFromAnotherServer = b.recv(1024)
			if msgFromAnotherServer.decode() == 'send':
				f = open(fileName,'rb')
				l = f.read(1024)
				while (l):
					b.sendall(l)
					l = f.read(1024)
				f.close()
				b.send('EOF'.encode())
				return b
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
s.connect((HOST,clientConfig.CLIENT_CONFIG[1] ))

while True:
	data = input("prompt:")
	if data == '':
		print('Type Error! Empty data string')

	else:
		s.sendall(data.encode())
		msg = s.recv(1024)
		if not msg:
			s.close()
			break

		listOfData = data.split(' ')

		if listOfData[0] == 'ls':
			print(msg.decode()+'\n')

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
					saveFile(b, listOfData[1])
					proc = subprocess.Popen(['leafpad', listOfData[1]])
					proc.wait()
						##save in the list
					serverFileList.append([addr,listOfData[1]])
					s.close()
					s = b

			elif msg.decode() == 'local':
				saveFile(s,listOfData[1])
				proc = subprocess.Popen(['leafpad', listOfData[1]])
				proc.wait()
				serverFileList.append([HOST,listOfData[1]])

			else:
				print(msg.decode()+'\n')

		elif listOfData[0] == 'create':
			proc = subprocess.Popen(['leafpad', listOfData[1]])
			proc.wait()
			createFiles(s,listOfData[1],msg)

		elif listOfData[0] == 'upload':
			proc = subprocess.Popen(['leafpad', listOfData[1]])
			proc.wait()
			tempSock = uploadFile(s,listOfData[1],msg)
			if tempSock != None:
				s = tempSock

		elif listOfData[0] == 'delete':
			if msg.decode() == 'Local':
				s.sendall('ok'.encode())

			elif msg.decode() == 'Not local':
				s.sendall('ok'.encode())
				ret = s.recv(1024)
				addr = ret.decode()
				b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				b.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				b.connect((addr,6666))
				b.sendall(data.encode())

				ret = b.recv(1024)
				if ret.decode() == 'Local':
					b.sendall('ok'.encode())
					s = b
			else:
				print(msg.decode()+'\n')

		else:
			print(msg.decode()+'\n')
