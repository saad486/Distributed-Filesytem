import os
import config
import threading
import sys
import time
import socket
import queue as Queue
#####Locks##########################
import struct


activeConnectionList = []
connectionList = [config.SERVER_CONFIG[1],config.SERVER_CONFIG[2]]

HOST = config.SERVER_CONFIG[0]
PORT = 9999
directory = config.SERVER_CONFIG[3]

listList = []
replicatedFileList = []

activeConnectionListLock = threading.Lock()
listListLock = threading.Lock()
threadLock = threading.Lock()
replicatedFileListLock = threading.Lock()
#######threading locks#########
#--------------------------------------------------------------------------------
class connectionReciever(threading.Thread):
	def __init__(self, sock):
		threading.Thread.__init__(self)
		self.sock = sock


	def run(self):
		global connectionList
		self.sock.bind((HOST, PORT))
		self.sock.listen(5)
		while True:
			conn, addr = self.sock.accept()
			print("Connection established")
			###add to connetion list####
			activeConnectionListLock.acquire(True)
			activeConnectionList.append([addr[0],addr[1],conn])
			print('socket recv append  ', conn, addr[1])
			activeConnectionListLock.release()
			###new communication thread intiated

			###list exhange
			msg = conn.recv(1024)
			print(msg.decode()+'Early')

			fileToBeUpdatedList  = []
			tempList = []
			fileTobeDeletedList = ''
			list = msg.decode().split('\n')
			for l in list:
				localFileName = l.split('#')
				if len(localFileName) > 1:
					for x in replicatedFileList:
						replicatedFileName = x.split('#')
						if replicatedFileName[1] != '*':
							if localFileName[0] == replicatedFileName[0] and int(localFileName[1]) != int(replicatedFileName[1]):
								print(localFileName[0],localFileName[1], 'replication update needed')
								fileToBeUpdatedList.append([localFileName[0],localFileName[1],replicatedFileName[1]])
						elif localFileName[0] == replicatedFileName[0]:
							fileTobeDeletedList = fileTobeDeletedList + replicatedFileName[0] + '\n'

			fileTobeDeletedList = fileTobeDeletedList.rstrip('\n')
			print(fileTobeDeletedList+'fileTodelete')
			print(fileToBeUpdatedList)
			print('A##############################')

			if len(fileToBeUpdatedList) == 0 and fileTobeDeletedList == '':
				conn.sendall('ok'.encode())
				ret = conn.recv(1024)
				if ret.decode() == 'send':
					conn.sendall(localList.encode())

			if len(fileToBeUpdatedList) > 0 or fileTobeDeletedList != '':

				if len(fileToBeUpdatedList) > 0 and fileTobeDeletedList != '':
					conn.sendall('update and delete'.encode())
					ret = recv_one_message(conn)
					if ret == 'send'.encode():
						send_one_message(conn,str(len(fileToBeUpdatedList)).encode())
						ret= recv_one_message(conn)
						if ret == 'ok'.encode():
							for x in fileToBeUpdatedList:
								nameToSend = x[0]+'#'+x[1]+'\n'+x[0]+'#'+x[2]
								send_one_message(conn,nameToSend.encode())
								ret = recv_one_message(conn)
								if ret == 'send'.encode():
									f = open(directory+'/'+x[0]+'#'+x[2])
									l = f.read(1024)
									while (l):
										send_one_message(conn,l.encode())
										l = f.read(1024)
									send_one_message(conn,'EOF'.encode())
									f.close()
							ret = conn.recv(1024)
							print('ret ok',ret )
							if ret.decode() == 'ok':
								conn.sendall('delete'.encode())
								ret = conn.recv(1024)
								if ret.decode() == 'ok':
									send_one_message(conn,fileTobeDeletedList.encode())
							msg = recv_one_message(conn)

				elif len(fileToBeUpdatedList) > 0:
					print('update m ho')
					conn.sendall('update'.encode())
					ret = recv_one_message(conn)
					if ret == 'send'.encode():
						send_one_message(conn,str(len(fileToBeUpdatedList)).encode())
						ret= recv_one_message(conn)
						if ret == 'ok'.encode():
							for x in fileToBeUpdatedList:
								nameToSend = x[0]+'#'+x[1]+'\n'+x[0]+'#'+x[2]
								send_one_message(conn,nameToSend.encode())
								ret = recv_one_message(conn)
								if ret == 'send'.encode():
									f = open(directory+'/'+x[0]+'#'+x[2])
									l = f.read(1024)
									while (l):
										send_one_message(conn,l.encode())
										l = f.read(1024)
										send_one_message(conn,'EOF'.encode())
									f.close()
						msg = recv_one_message(conn)

				elif fileTobeDeletedList != '':
					print('Delete')
					conn.sendall('delete'.encode())
					ret = recv_one_message(conn)
					if ret == 'send'.encode():
						send_one_message(conn,fileTobeDeletedList.encode())
					msg = recv_one_message(conn)


			listListLock.acquire()
			listList.append([conn,msg.decode(),addr[0]])
			listListLock.release()


			thread = communtionRecieverThread(conn)
			thread.start()

#------------------------------------------------------------------------------
class communtionRecieverThread(threading.Thread):
	def __init__(self, conn):
		threading.Thread.__init__(self)
		self.conn = conn

	def run(self):
		while True:
			data = self.conn.recv(1024)
			if not data:
				removeConnections(self.conn)
				break
			print(data,'ss')
			command = data.decode()
			list = command.split(' ')

			if list[0] == 'ls':
				appendList = ''
				recieveList = self.conn.recv(1024)
				print('got the file',recieveList.decode())
				###send List##############################
				removeList = []
				ipAddr = ''
				for y in listList:
					if y[0] == self.conn:
						removeList = y
						ipAddr = y[2]
						break

				listListLock.acquire(True)
				listList.remove(removeList)
				listList.append([self.conn,recieveList.decode(),ipAddr])
				listListLock.release()

			if list[0] == 'create':
				f = open(directory+'/'+list[1] +'#'+str(0),'wb')
				while True:
					data = recv_one_message(self.conn)
					print(data)
					if data.endswith('EOF'.encode()):
						data = data[:-3]
						f.write(data)
						break
					f.write(data)
				f.close()
				listRecieve = recv_one_message(self.conn)
				updateIntoList(self.conn, listRecieve.decode())
				localListUpdate()
				self.conn.sendall('ls'.encode())
				time.sleep(3)
				self.conn.sendall(localList.encode())
				print('done done')

				removeList = []
				check = False
				for x in replicatedFileList:
					listx = x.split('#')
					if listx[0] == list[1] and listx[1] == '*':
						removeList = x
						check = True
						break
				if check == True:
					replicatedFileListLock.acquire(True)
					replicatedFileList.remove(removeList)	###removing * files
					replicatedFileListLock.release()

				replicatedFileListLock.acquire(True)
				replicatedFileList.append(list[1] +'#'+str(0))	###Keeping track of replicated files
				replicatedFileListLock.release()

				sendReplicatedListOther(self.conn)

			if list[0] == 'upload':
				######################33
				removeList = []
				check = False
				for x in replicatedFileList:
					listx = x.split('#')
					if listx[0] == list[1] and listx[1] == '*':
						removeList = x
						check = True
						break
				if check == True:
					replicatedFileListLock.acquire(True)
					replicatedFileList.remove(removeList)	###removing * files
					replicatedFileListLock.release()
				##########################################################3
				os.remove(directory+'/'+list[1])
				fileStip = list[1].split('#')
				version = int(fileStip[1]) + 1
				removeFromReplicatedList(list[1],fileStip[0]+'#'+str(version))
				f = open(directory+'/'+fileStip[0]+'#'+str(version),'wb')
				while True:
					data = recv_one_message(self.conn)
					print(data)
					if data.endswith('EOF'.encode()):
						data = data[:-3]
						f.write(data)
						break
					f.write(data)
				f.close()
				listRecieve = recv_one_message(self.conn)
				updateIntoList(self.conn, listRecieve.decode())

				localListUpdate()
				self.conn.sendall('ls'.encode())
				time.sleep(3)
				self.conn.sendall(localList.encode())
				print('done done')
				sendReplicatedListOther(self.conn)


			if list[0] == 'sendOther':
				listRecieve = recv_one_message(self.conn)
				updateIntoList(self.conn, listRecieve.decode())
				localListUpdate()
				self.conn.sendall('ls'.encode())
				time.sleep(3)
				self.conn.sendall(localList.encode())
				print('done')

			if list[0] == 'delete':
				isReplicated = False
				fileName = ''
				for x in replicatedFileList:
					if list[1] == x:
						isReplicated = True
						fileName = x
						break

				if isReplicated == True:
					os.remove(directory+'/'+fileName)
					deleteStrip = fileName.split('#')
					replicatedFileListLock.acquire(True)
					replicatedFileList.remove(fileName)
					replicatedFileList.append(deleteStrip[0]+'#'+'*')
					replicatedFileListLock.release()

				localListUpdate()
				listRecieve = recv_one_message(self.conn)
				updateIntoList(self.conn, listRecieve.decode())
				self.conn.sendall('ls'.encode())
				time.sleep(3)
				self.conn.sendall(localList.encode())
				sendReplicatedListOther(self.conn)
#---------------------------------------------------------------------
def updateIntoList(conn, recieveList):
	removeL = []
	for y in listList:
		if y[0] == conn:
			removeL = y
			ipAddr = y[2]
			break

	listListLock.acquire(True)
	listList.remove(removeL)
	listList.append([conn,recieveList,ipAddr])
	listListLock.release()

#-----------------------------------------------------------------------
class createReplicationThread(threading.Thread):
	def __init__(self, command):
		threading.Thread.__init__(self)
		self.command = command

	def run(self):
		print('Here in replication thread')

		replicatedFileListLock.acquire(True)
		replicatedFileList.append(commandList[1] +'#'+str(0))	###Keeping track of replicated files
		replicatedFileListLock.release()

		for x in activeConnectionList:
			x[2].sendall(self.command.encode())
			sendFile(commandList[1] +'#'+str(0),x[2])
			send_one_message(x[2],localList.encode())
			#recieveList = recv_one_message(x[2])
			#print(recieveList)
			#ret = recv_one_message(x[2])
			#print(ret)
			#ret = x[2].recv(1024)
			#print(ret,' done')
			"""if ret == 'EOF'.encode():
				print('replication done')"""
		###Recieving List listing####################
		#time.sleep(10)

		"""for x in activeConnectionList:
			x[2].sendall('ls'.encode())
			print('sent ls')
			recieveList = recv_one_message(x[2])
			print(recieveList)

			removeList = []
			for y in listList:
				if y[0] == x[2]:
					removeList = y
					break

			listListLock.acquire(True)
			listList.remove(removeList)
			listList.append([x[2],recieveList.decode()])
			listListLock.release()
		"""
#------------------------------------------------------------------------
class updateReplicatedFiles(threading.Thread):
		def __init__(self, command ,fileName, version):
			threading.Thread.__init__(self)
			self.command = command
			self.fileName = fileName
			self.version = version

		def run(self):
			versionUpdate = self.version + 1
			removeFromReplicatedList(self.fileName+'#'+str(self.version),self.fileName+'#'+str(versionUpdate))
			for x in activeConnectionList:
				x[2].sendall(self.command.encode())
				sendFile(self.fileName+'#'+str(versionUpdate),x[2])
				send_one_message(x[2],localList.encode())

#--------------------------------------------------------------------------------
class deleteReplicatedFiles(threading.Thread):
		def __init__(self, command):
			threading.Thread.__init__(self)
			self.command = command

		def run(self):
			for x in activeConnectionList:
				x[2].sendall(self.command.encode())
				send_one_message(x[2],localList.encode())

#------------------------------------------------------------------------
def sendReplicatedListOther(conn):
	for x in activeConnectionList:
		if x[2] != conn:
			x[2].sendall('sendOther'.encode())
			time.sleep(2)
			send_one_message(x[2],localList.encode())
			print('done done sending sendOther')


#-----------------------------------------------------------------------
def isInList(soc):

	check = False
	for x in activeConnectionList:
		if soc == x[1]:
			check = True
			break
	return check
#---------------------------------------------------------------------
def localListUpdate():
	global localList

	localList = ''
	oslist = os.listdir(directory)
	for l in oslist:
		localList = localList + str(l) + '\n'

#-------------------------------------------------------------------
def removeConnections(conn):
	removeConn = []
	for x in activeConnectionList:
		if x[2] == conn:
			removeConn = x
			break
	activeConnectionListLock.acquire(True)
	activeConnectionList.remove(removeConn)
	activeConnectionListLock.release()

	removeList = []
	print('conn == ', conn)

	for x in listList:
		print(x)
		if x[0] == conn:
			removeList = x
			break

	listListLock.acquire(True)
	listList.remove(removeList)
	listListLock.release()


#------------------------------------------------------------------
def fileFinding(fileName, systemList):
	##boolean
	checkLocal = 0
	thisList = []
	print(thisList)

	list  = systemList.split('\n')
	print('fileName : ', fileName)
	for l in list:
		#print(l, 'list')
		if l == fileName:
			print("Found Locally")
			thisList.append(fileName)
			checkLocal = 1
			break
	foundFile = 0
	if checkLocal == 0:
		for x in listList:
			print(x)
			list = x[1].split('\n')
			for l in list:
				print(l,' :remote')
				if l == fileName:
					foundFile = 1
					thisList.append(l)
					break
			print(thisList)
			if foundFile == 1 and len(thisList)==1:
				thisList.append(x[2])
				break

	return thisList
#--------------------------------------------------------
def download(fileName, conn, systemList):
	print(systemList, 'listing')
	list = fileFinding(fileName, systemList)
	print(list,'download')
	if len(list)==0:
		conn.sendall('No such file exists'.encode())

	elif len(list) > 1:
		print('Sending request',list[1])
		conn.send('Not local'.encode())
		ret = conn.recv(1024)
		if ret.decode() == 'ok':
			conn.send(list[1].encode())
		#conn.recv(1024)


	elif len(list) == 1:
		print('local')
		conn.send('local'.encode())
		ret = conn.recv(1024)
		print('local ',ret)
		if ret.decode() == 'ok':
			f = open(directory+'/'+fileName,'rb')
			l = f.read(1024)
			while (l):
				conn.send(l)
				l = f.read(1024)
			f.close()
			conn.send('EOF'.encode())
#--------------------------------------------------------
def upload(fileName, conn):
	f = open(directory+'/'+fileName,'wb')
	conn.send('send'.encode())
	while True:
		data = conn.recv(1024)
		print(data)
		if data.endswith('EOF'.encode()):
			data = data[:-3]
			f.write(data)
			break
		f.write(data)
	f.close()


#--------------------------------------------------------
def createFile(fileName, conn):
	print('sending')
	conn.send('send'.encode())
	f = open(directory+'/'+fileName,'wb')
	while True:
		data = conn.recv(1024)
		if data.endswith('EOF'.encode()):
			data = data[:-3]
			f.write(data)
			break
		f.write(data)
	f.close()
#--------------------------------------------------------
def sendFile(fileName, conn):
	time.sleep(2)
	f = open(directory+'/'+fileName,'rb')
	l = f.read(1024)
	while(l):
		send_one_message(conn,l)
		l = f.read(1024)
	send_one_message(conn,'EOF'.encode())
	f.close()

#-----------------------------------------------------
def send_one_message(sock, data):
    length = len(data)
    sock.sendall(struct.pack('!I', length))
    sock.sendall(data)

def recv_one_message(sock):
    lengthbuf = recvall(sock, 4)
    length, = struct.unpack('!I', lengthbuf)
    return recvall(sock, length)

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf
#------------------------------------------------
def removeFromReplicatedList(removeFile, addFile):

	removeIndex = ''
	for x in replicatedFileList:
		if x == removeFile:
			removeIndex = x
			break
	replicatedFileListLock.acquire(True)
	replicatedFileList.remove(removeIndex)
	replicatedFileList.append(addFile)
	replicatedFileListLock.release()


#-----------------------------------------------
def replicationListUpdate():
	oslist = os.listdir(directory)
	for l in oslist:
		list = l.split('#')
		if len(list)>1:
			replicatedFileListLock.acquire(True)
			replicatedFileList.append(l)
			replicatedFileListLock.release()

#------------------------------------------------
####Lists variable##############################
localList = ''
#############################


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
localListUpdate()

replicationListUpdate()

print(replicatedFileList)

try:
	thread1 = connectionReciever(sock)
	thread1.start()
except:
	print('Unable to try the listening thread')

###update locallist############################3


for soc in connectionList:
	activeConnectionListLock.acquire(True)
	check = isInList(soc)
	activeConnectionListLock.release()

	if check == True:
		pass
	else:
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		#server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.settimeout(3)
		try:
			ret = server.connect_ex((soc,PORT))
			print('ret ', ret)
			server.settimeout(None)
		except:
			print('Unable to connect')

		if ret == 0:
			activeConnectionListLock.acquire(True)
			activeConnectionList.append([soc,PORT,server])
			activeConnectionListLock.release()
			server.sendall(localList.encode())
			msg = server.recv(1024)
			print(msg)

			if msg.decode() == 'update and delete':
				send_one_message(server,'send'.encode())
				le = recv_one_message(server)
				send_one_message(server,'ok'.encode())
				for x in range(0,int(le.decode())):
					listOfName = recv_one_message(server)
					listOfFiles = listOfName.decode().split('\n')
					os.remove(directory+'/'+listOfFiles[0])
					f = open(directory+'/'+listOfFiles[1],'wb')
					send_one_message(server,'send'.encode())
					while True:
						data = recv_one_message(server)
						print('repl',data)
						if data.endswith('EOF'.encode()):
							data = data[:-3]
							f.write(data)
							break
						f.write(data)
					f.close()
					replicatedFileListLock.acquire(True)
					replicatedFileList.append(listOfFiles[1])
					replicatedFileListLock.release()

				server.sendall('ok'.encode())

				ret = server.recv(1024)

				if ret.decode() == 'delete':
					server.sendall('ok'.encode())
					listOfDeleted = recv_one_message(server)
					list = listOfDeleted.decode().split('\n')
					for x in list:
						removeList = []
						for y in replicatedFileList:
							listx = y.split('#')
							if listx[0] == x:
								os.remove(directory+'/'+y)
								removeList = y
								break

						replicatedFileListLock.acquire(True)
						replicatedFileList.remove(removeList)
						replicatedFileListLock.release()
				localListUpdate()
				listListLock.acquire()
				listList.append([server,msg.decode(),soc])
				listListLock.release()
				#
				#

				# 	server.sendall('ok'.encode())
				# 	listOfDeleted = recv_one_message(server)
				# 	list = listOfDeleted.decode.split('\n')
				# 	for x in list:
				# 		removeList = []
				# 		for y in replicatedFileList:
				# 			listx = y.split('#')
				# 			if listx[0] == x:
				# 				os.remove(directory+'/'+y)
				# 				removeList = y
				# 				break
				 		# replicatedFileListLock.acquire(True)
						# replicatedFileList.remove(removeList)
						# replicatedFileListLock.release()

				#localListUpdate()

				send_one_message(server,localList.encode())

			elif msg.decode() == 'update':
				send_one_message(server,'send'.encode())
				le = recv_one_message(server)
				send_one_message(server,'ok'.encode())
				for x in range(0,int(le.decode())):
					listOfName = recv_one_message(server)
					listOfFiles = listOfName.decode().split('\n')
					os.remove(directory+'/'+listOfFiles[0])
					f = open(directory+'/'+listOfFiles[1],'wb')
					send_one_message(server,'send'.encode())
					while True:
						data = recv_one_message(server)
						print('repl',data)
						if data.endswith('EOF'.encode()):
							data = data[:-3]
							f.write(data)
							break
						f.write(data)
					f.close()
					localListUpdate()
					replicatedFileListLock.acquire(True)
					replicatedFileList.append(listOfFiles[1])
					replicatedFileListLock.release()
					localListUpdate()
					listListLock.acquire()
					listList.append([server,msg.decode(),soc])
					listListLock.release()
					send_one_message(server,localList.encode())

			elif msg.decode() == 'delete':
				send_one_message(server,'send'.encode())
				listOfDeleted = recv_one_message(server)
				list = listOfDeleted.decode().split('\n')
				for x in list:
					removeList = []
					for y in replicatedFileList:
						listx = y.split('#')
						if listx[0] == x:
							os.remove(directory+'/'+y)
							removeList = y
							break

					replicatedFileListLock.acquire(True)
					replicatedFileList.remove(removeList)
					replicatedFileListLock.release()
				localListUpdate()
				listListLock.acquire()
				listList.append([server,msg.decode(),soc])
				listListLock.release()
				send_one_message(server,localList.encode())

			elif msg.decode() == 'ok':
				server.sendall('send'.encode())
				msg = server.recv(1024)
				listListLock.acquire()
				listList.append([server,msg.decode(),soc])
				listListLock.release()

			thread = communtionRecieverThread(server)
			thread.start()

####Client##################################
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind((HOST,6666))

print('Connect to Address ',str(client.getsockname()[0])+ ' : ' +str(client.getsockname()[1]))
client.listen(5)
while True:
	conn, addr = client.accept()
	while True:
		data = conn.recv(1024)
		print(data)
		if not data:
			print('Client disconnected')
			conn.close()
			break

		command = data.decode()

		commandList = command.split(' ')
		if commandList[0] == 'ls':

			append = ''

			for x in listList:
				list = x[1].split('\n')
				for y in list:
					listsplity = y.split('#')
					if len(listsplity) > 1:
						pass
					else: append = append + listsplity[0] + '\n'
				append = append.rstrip('\n')
				append = append + '\n'
			#append = append + '\n'

			listSplit = localList.split('\n')
			for x in listSplit:
				sendList = x.split('#')
				append = append + sendList[0] + '\n'

			append = append.rstrip('\n')

			conn.send(append.encode())

		elif commandList[0] == 'download':
			isReplicated = False
			for x in replicatedFileList:
				list = x.split('#')
				if list[0] == commandList[1]:
					fileName = x
					isReplicated = True
					break
			if isReplicated == True:
				download(fileName,conn, localList)
			else:
				download(commandList[1],conn, localList)

			print('File sent')

		elif commandList[0] == 'create':
			createFile(commandList[1]+'#'+str(0),conn)
			####################################
			removeList = []
			check = False
			for x in replicatedFileList:
				listx = x.split('#')
				if listx[0] == commandList[1] and listx[1] == '*':
					removeList = x
					check = True
					break
			if check == True:
				replicatedFileListLock.acquire(True)
				replicatedFileList.remove(removeList)	###removing * files
				replicatedFileListLock.release()

			###################################################33

			localListUpdate()
			###Thread here####################
			threadReplication = createReplicationThread(data.decode())
			threadReplication.start()

		elif commandList[0] == 'delete':
			print('delete command')
			isReplicated = False
			fileName = ''

			for x in replicatedFileList:
				splitName = x.split('#')
				if splitName[0] == commandList[1]:
					isReplicated = True
					fileName = x
					break

			if isReplicated == True:
				conn.sendall('Local'.encode())
				ret = conn.recv(1024)
				if ret == 'ok'.encode():
					deleteStrip = fileName.split('#')
					os.remove(directory+'/'+fileName)
					localListUpdate()
					replicatedFileListLock.acquire(True)
					replicatedFileList.remove(fileName)
					replicatedFileList.append(deleteStrip[0]+'#'+'*')
					replicatedFileListLock.release()
					thread = deleteReplicatedFiles('delete '+fileName)
					thread.start()
					print('file uploaded')

			else:
				list = fileFinding(commandList[1],localList)

				if len(list)==0:
					conn.sendall('No such file exists'.encode())

				elif len(list) > 1:
					conn.sendall('Not local'.encode())
					ret = conn.recv(1024)
					if ret == 'ok'.encode():
						conn.sendall(list[1].encode())
				else:
					conn.sendall('Local'.encode())
					ret = conn.recv(1024)
					if ret.decode() == 'ok':
						os.remove(directory+"/"+commandList[1])
						localListUpdate()
						for x in  activeConnectionList:
							x[2].sendall(data)
							ret = x[2].recv(1024)
							if ret.decode() == 'ok':
								send_one_message(x[2],localList.encode())



		elif commandList[0] == 'upload':
			######################33
			removeList = []
			check = False
			for x in replicatedFileList:
				listx = x.split('#')
				if listx[0] == commandList[1] and listx[1] == '*':
					removeList = x
					check = True
					break
			if check == True:
				replicatedFileListLock.acquire(True)
				replicatedFileList.remove(removeList)	###removing * files
				replicatedFileListLock.release()
			##########################################################3
			print('Upload command')
			isReplicated = False
			fileName = ''

			for x in replicatedFileList:
				splitName = x.split('#')
				if splitName[0] == commandList[1]:
					isReplicated = True
					fileName = x
					break


			if isReplicated == True:
				conn.sendall('Local'.encode())
				ret = conn.recv(1024)
				if ret == 'ok'.encode():
					uploadStrip = fileName.split('#')
					version = -1
					print('here')
					os.remove(directory+'/'+fileName)
					version = int(uploadStrip[1])
					createFile(uploadStrip[0]+'#'+str(version + 1),conn)
					localListUpdate()
					threadReplicationUpdation = updateReplicatedFiles('upload '+fileName,uploadStrip[0],version)
					threadReplicationUpdation.start()
					print('file uploaded')

			else:
				list = fileFinding(commandList[1],localList)

				if len(list)==0:
					conn.sendall('No such file exists'.encode())

				elif len(list) > 1:
					conn.sendall('Not local'.encode())
					ret = conn.recv(1024)
					if ret == 'ok'.encode():
						conn.sendall(list[1].encode())

				else:
					conn.sendall('Local'.encode())
					ret = conn.recv(1024)
					if ret.decode() == 'ok':
						upload(commandList[1], conn)

		else:
			conn.sendall('Wrong Command! Please try again :)'.encode())
