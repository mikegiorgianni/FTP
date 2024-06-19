import socket
from datetime import datetime
import os
import sys
from subprocess import call
import threading

# opening the log file to write to later
f = open("FTPlogs.txt", "a")
f.write("This is the Log for the FTP client/server communication\n")

# preparing datetimeobj to be used in the logs
dto = datetime.now()

# converting dto to string
timeStamp = str(dto.hour + dto.minute + dto.second + dto.microsecond)

#creating socket connection to FTP server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '10.246.251.93'
buffer = 2048
username = "cs472"
password = "hw2ftp"

def main():
	# username and pass for test server
	# default test ip is 10.246.251.93
	port = 0
	while port == 0:
		try:
			port = int(input('What is the port that you want to connect over : '))
		except:
			port = 21
	sock.connect((host, port))
	data = sock.recv(buffer)
	myPrint(timeStamp + "	Connecting to file server! \n")
	myPrint(data)
	'''
	data = sock.recv(buffer)
	myPrint(data)
	strData = str(data)
	if (strData.startswith('Port=')):
		list = strData.split('=')
		userport = list[1].strip()
		portnum = int(userport)
		myPrint(portnum)
		th = listeningThread(portnum)
		th.start()
'''
	auth()
	commandLine()

#the login authentication to an FTP server
def auth():
	myPrint(timeStamp + "	beginning the logon procedure \n" )
	try:
		#send data
		#user = input('What is the user name : ')
		sock.sendall(bytes("USER " + username + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		myPrint(data)
		#password = input()
		sock.sendall(bytes("PASS " + password + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		myPrint(data)
		myPrint(timeStamp + "	Username and Password accepted! \n" )
	except KeyboardInterrupt:
		disconnect()
	except:
		myPrint("The username or password is incorrect! ")
		raise

#The basic CLI I created
def commandLine():
	myPrint("What would you like to do : \n")
	command = input("FTP -> " )

	if command.lower()  == "cwd":
		cwd()
		commandLine()
	elif command.lower() == "exit":
		disconnect()
	elif command.lower() == "help":
		myPrint("The available commands are : cwd, pwd, user, port, pasv, ,put, exit \n")
		commandLine()
	elif command.lower() == "pwd":
		pwd()
		commandLine()
	elif command.lower() == "user":
		usr()
		commandLine()
	elif command.lower() == "put":
		put_file()
		commandLine()
	elif command.lower() == "port":
		port_mode()
		commandLine()
	elif command.lower() == "pasv":
		pasv_mode()
		commandLine()
	elif command.lower() == "eprt":
		eprt()
		commandLine()
	elif command.lower() == "test":
		test()
		commandLine()
	else:
		myPrint("You can type help for available commands!\n")
		commandLine()

#Change current directory
def cwd():
	path = input("Please enter the path to the new directory : " )
	sock.sendall(bytes("CWD " + path + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

#basically ls call
def pwd():
	sock.sendall(b'PWD\r\n')
	data = sock.recv(buffer)
	myPrint(data)

def syst():
	sock.sendall(b'SYST\r\n')
	data = sock.recv(buffer)
	myPrint(data)

def usr():
	sock.sendall(b'USER\r\n')
	data = sock.recv(buffer)
	myPrint(data)
	user = input("Username : ")
	sock.sendall(bytes(user + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)
	pas = input("Password : ")
	sock.sendall(bytes(pas + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

def port_mode():
	ipAddr = get_ip()
	print(ipAddr)
	addrList = ipAddr.split('.')

	remPort = 9000 % 256
	if (remPort > 0):
		p1 = int((9000 - remPort)/256)
		p2 = int(remPort)

	tosend = "PORT " + addrList[0] + "," + addrList[1] + "," + addrList[2] + "," + addrList[3] + "," + str(p1) + "," + str(p2)
	print(tosend)
	sock.sendall(bytes(tosend + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

def put_file():
	filename = input("What is the name of the file : ")
	
	modeSelector = input("1 for PORT \n" + "2 for PASV \n" + "3 for EPRT \n" + "4 for EPSV \n" + "Enter your selection here : ")
	
	if (modeSelector == "1"):
		port_mode()
		remPort = 9000 % 256
		if (remPort > 0):
			p1 = int((9000 - remPort)/256)
			p2 = int(remPort)

		data_port = int((p1 * 256) + p2)

		ipAddr = get_ip()
		sock.sendall(bytes("STOR " + filename + "\r\n", 'utf-8'))
		dataSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		dataSock.bind((ipAddr, data_port))
		dataSock.listen()

		myPrint(str("STOR " + filename))
		data = sock.recv(buffer)
		myPrint(data)
		(conn, addr) = dataSock.accept()
		file = open(filename, 'r+')
		line = file.read(buffer)
		while(line):
			myPrint("Sending file...")
			conn.send(bytes(line, 'utf-8'))
			line = file.read(buffer)
		file.close()
		myPrint("Data has been sent successfully!")
		conn.close()
		data = sock.recv(buffer)
		myPrint(data)
	elif (modeSelector == "2"):
		psock = pasv_mode()
		file = open(filename, 'r+')
		line = file.read(buffer)
		while(line):
			myPrint("Sending file...")
			psock.send(bytes(line, 'utf-8'))
			line = file.read(buffer)
		file.close()
		myPrint("Data has been sent successfully!")
		psock.close()


def pasv_mode():
	sock.sendall(b'PASV\r\n')
	data = sock.recv(buffer)
	myPrint(data)
	strData = str(data)
	list = strData.split(' ')
	list2 = list[4].split(',')
	myPrint(list2)
	list3 = list2[0].split("(")
	ipAddr = list3[1] + "." + list2[1] + "." + list2[2] + "." + list2[3]
	myPrint("Ip for the socket is : " + ipAddr)
	list4 = list2[5].split(")")
	myPrint(list2[4])
	myPrint(list4[0])
	data_port = (int(list2[4]) * 256) + int(list4[0])
	myPrint("The data port for the socket is : " + str(data_port))
	psock = socket.socket()
	psock.connect((ipAddr, data_port))
	myPrint("we are connected")
	return psock



def eprt():
	netprt = input("Please enter 1 for ipv4 or 2 for ipv6 : ")
	netaddr = input("Please enter the address to connect : ")
	tcpport = input("Please enter the port to transfer over : ")
	tosend = "EPRT |" + netprt + "|" + netaddr + "|" + tcpport + "|" + "\r\n"
	print(tosend)
	sock.sendall(bytes(tosend, 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)
	strData = str(data)
	list = strData.split(' ')
	if (list[0] == "200"):
		myPrint("Connection success!")
	elif (list[0] == "522"):
		myPrint("Connection Unsuccessful see error above")
	else:
		myPrint("Connection Unsuccessful see error above")

def test():
	command = input("What is it you would like to test : ")
	sock.sendall(bytes(command + "\r\n", 'utf-8'))
	try:
		data = sock.recv(buffer)
		myPrint(data)
		data = sock.recv(buffer)
		myPrint(data)
	except KeyboardInterrupt:
		commandLine()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#for a way to exit the program
def disconnect():
	sock.sendall(b'quit\r\n')
	data = sock.recv(buffer)
	myPrint(data)

def myPrint(data):
	f.write(str(data))
	print(str(data))

class listeningThread(threading.Thread):
	def __init__(self, port):
		self.port = port
	def run(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.bind('127.0.0.1', port)
		(clientsock, address) = serversock.accept()
		while True:
			data = clientsock.recv(buffer)
			myPrint(data)
			# if statement regarding data, for now it just prints info from the server

if __name__ == '__main__':
	main()
	f.close()
	print("Its working")