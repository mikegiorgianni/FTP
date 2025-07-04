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
host = '127.0.0.1'
buffer = 2048
#username = "mike"
#password = "pass"
is_logged_in = False
curr_dir = ""

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
	#auth()
	commandLine()

#the login authentication to an FTP server NOTE: was moved to the user command
def auth():
	myPrint(timeStamp + "	beginning the logon procedure \n" )
	try:
		#send data
		username = input('What is the user name : ')
		sock.sendall(bytes("user " + username + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		myPrint(data)
		password = input('What is the password : ')
		sock.sendall(bytes("pass " + password + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		myPrint(data)
		myPrint(timeStamp + "	Username and Password accepted! \n" )
	except KeyboardInterrupt:
		disconnect()
	except:
		myPrint("The username or password is incorrect! ")
		raise

#basic CLI
def commandLine():
	myPrint("What would you like to do : \n")
	command = input("FTP -> " )

	if command.lower()  == "cwd":
		cwd()
		commandLine()
	elif command.lower() == "quit":
		disconnect()
	elif command.lower() == "help":
		myPrint("The available commands are : cwd, pwd, user, port, pasv, syst, put, exit \n")
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
	elif command.lower() == "syst":
		syst()
		commandLine()
	elif command.lower() == "echo":
		echo()
		commandLine()

	else:
		myPrint("You can type help for available commands!\n")
		commandLine()

#Change current directory
def cwd():
	path = input("Please enter the path to the new directory : " )
	sock.sendall(bytes("cwd " + path + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)
	#add a check to see if the directory exists if not ask user if they want to create it
	if data.startswith(b'250'):
		myPrint("Directory changed successfully!")
	else:
		myPrint("Directory does not exist!")
		create = input("Would you like to create it? (y/n) ")
		if create.lower() == "y":
			sock.sendall(bytes("mkd " + path + "\r\n", 'utf-8'))
			data = sock.recv(buffer)
			myPrint(data)
			if data.startswith(b'257'):
				myPrint("Directory '%s' created successfully!" %path + "\n" + "Would you like to change to it? (y/n) ")
				change = input()
				if change.lower() == "y":
					cwd()
		else:
			myPrint("Directory not changed!")


#basically ls call
def pwd():
	sock.sendall(bytes("pwd\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

def syst():
	sock.sendall(bytes("syst\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

def usr():
	#sock.sendall(b'USER\r\n')
	#data = sock.recv(buffer)
	#myPrint(data)
	global is_logged_in
	if not is_logged_in:

		user = input("Username : ")
		sock.sendall(bytes("user " + user + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		myPrint(data)
		pas = input("Password : ")
		sock.sendall(bytes(pas + "\r\n", 'utf-8'))
		data = sock.recv(buffer)
		if data.startswith(b'230'):
			myPrint("Login successful!")
			is_logged_in = True
		else:
			myPrint("Login failed! Please try again.")
			return
	else:
		myPrint("You are already logged in!")

def echo():
	msg = input("What would you like to echo : ")
	sock.sendall(bytes(msg + "\r\n", 'utf-8'))
	data = sock.recv(buffer)
	myPrint(data)

def port_mode():
	ipAddr = get_ip()
	myPrint(ipAddr)
	addrList = ipAddr.split('.')

	remPort = 9000 % 256
	if (remPort > 0):
		p1 = int((9000 - remPort)/256)
		p2 = int(remPort)

	tosend = "PORT " + addrList[0] + "," + addrList[1] + "," + addrList[2] + "," + addrList[3] + "," + str(p1) + "," + str(p2)
	myPrint(tosend)
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
	print("Disconnected from server")

def myPrint(data):
	f.write(str(data))
	print(str(data))

class listeningThread(threading.Thread):
	def __init__(self, port):
		self.port = port
	def run(self):
		serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serversock.bind('127.0.0.1', self.port)
		(clientsock, address) = serversock.accept()
		while True:
			data = clientsock.recv(buffer)
			myPrint(data)
			# if statement regarding data, for now it just prints info from the server

if __name__ == '__main__':
	main()
	f.close()