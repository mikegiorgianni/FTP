#!/usr/bin/python3

from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
import multiprocessing
import socket, os
import argparse
import traceback
import time
import datetime
import sys




class State():

    def __init__(self):
        #get state of user logon
        self.logged_in = False

        #get state of data connection
        self.passive_mode = False
        #clients passive data connection
        self.passive_conn = None

        #username and password
        self.username = None
        self.password = None

        #clients connection
        self.conn = None

        #get current working directory
        self.pwd = os.getcwd()

        #ip address for client
        self.addr = None

    def validate_login(self):
        #checks userfile for valid credentials
        with open('userfile.txt', 'r') as file:
            for line in file.readlines():
                if line.strip() == self.username + ":" + self.password:
                    self.logged_in = True
                    return True
            return False

class FTPServer():
    #for log file and PORT calls
    def __init__(self, log_file, port):

        self.log_file = log_file

        #host is set to localhost to ensure proper binding
        self.host = '127.0.0.1'

        self.explicit_TLS = True

        self.pasv_mode = False

        self.port_mode = False

        self.port = int(port)

        self.user_file = 'userfile.txt'

    def config_check(self):
        with open('serverconfig.txt', 'r') as file:
            for line in file.readlines():
                #check for active tranfer
                if line.strip() == "port_mode = True":
                    self.port_mode = True
                    self.log("active transfer (port) is enabled VIA configuration file")
                else:
                    self.log("active tranfer is disable VIA configuration file")
                #check for passive transfer
                if line.strip() == "pasv_mode = True":
                    self.pasv_mode = True
                    self.log("passive transfer enabled VIA configuration file")
                else:
                    self.log("passive tranfer is disable VIA configuration file")
                
                if self.pasv_mode and self.port_mode == False:
                    self.log("FATAL: No data transfer mode in configuration file!")

    #helper for printing to the log file
    def log(self, msg):
        currTime = str(datetime.datetime.now())
        with open(self.log_file, 'a+') as fi:
            fi.write(currTime + " : " + str(msg) + "\n")
            print(msg)

    #For processing incoming data and returning the args to be passed to data_handler()
    def data_proc(self, data):
        data = data.decode().strip().lower()
        self.log("Recieved data: " + data)
        args = data.split(' ')
        return args


    #helper to format the message
    def format_msg(self, code, msg):
        if msg:
            c_msg = str(code) + ": " + str(msg) + "\n"
        else:
            c_msg = str(code) + "\n"

        return c_msg.encode()

    #helper to send the formatted message
    def send_msg(self, state, c_msg):
        self.log(c_msg)
        state.conn.send(c_msg)
        #self.conn.send(c_msg)

    def data_handler(self, command, state, args = " "):
        
        self.log("Attempting " + command + " with arguments " + args[0])

        if not state.logged_in and command not in ["user", "pass", "syst", "quit", "auth"]:
            self.send_msg(state, self.format_msg(530, "Access denied, not logged in"))
            return
        
        if command == "user":
            #if user is not logged in, log their username and ask for password
            if not state.logged_in:
                state.username = args[0]
                self.send_msg(state, self.format_msg(331, "What is the password?"))
                data = state.conn.recv(1024)
                temp = FTPServer.data_proc(self, data)
                state.password = temp[0]
                #validate the user after recv both username and password -- basic oracle attack protection
                if state.validate_login():
                    self.send_msg(state, self.format_msg(230, "Password accepted: User logged in"))
                    self.log("Password accepted User: " + state.username + " is logged in")
                else:
                    self.send_msg(state, self.format_msg(530, "Incorrect password"))
                    self.log("Access denied to User: " + str(state.username) + " IP: " + str(state.addr))

                    state.username = None
                    state.password = None

                ### Maybe just merge pass command code here to make the login verfication work
                ### idk why you would want to call pass seperately anyways/ dont think you normally would
            #if they are accessing server without logging in so we dont save the password or username
            else:
                self.send_msg(state, self.format_msg(230, "Already logged in"))

        

        elif command == "quit":
            self.send_msg(state, self.format_msg(221, "Goodbye"))
            self.log("User: " + self.username + " has disconnected")
            return True

        elif command == "syst":
            self.send_msg(state, self.format_msg(215, "Win10 Mike's Server"))
            self.log("Win10 Mike's Server")

        elif command == "pwd":
            self.send_msg(state, self.format_msg(257, "The current directory is: " + state.pwd))
            self.log("Current directory is: " + state.pwd)

        elif command == "cwd":
            #create way for users to easily naviagate the server without typing the whole path everytime
            #idea: when user logs in automatically set cwd to the user dir
            ### SUDO CODE ###
            #if args[1] == "..":
                #curpath = state.pwd.split("\")
                #parentpath = "/".join(curpath[:-1])
                #os.chdir(parentpath)
                #log change to users state.pwd
                #send confirmation to client
            ##################
            if os.path.isdir(args[0]):
                state.cwd = os.chdir(args[0])
                self.send_msg(state, self.format_msg(250, "Directory successfully changed"))
            else:
                self.send_msg(state, self.format_msg(550, "Directory was not changed"))
            
        elif command == "cdup":
            state.cwd = os.path.dirname(state.cwd)

        elif command == "pasv":
            if self.pasv_mode == False:
                self.send_msg(state, self.format_msg(425, "Passive mode disabled VIA config file"))
                self.log("Config file says no to passive data connections")
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #bind to any available port
                sock.bind((self.host, 0))
                #get the IP of the socket connection, should be local host
                ip = sock.getsockname()[0].replace(".", ",")
                #get the port num to find p1 and p2
                port = sock.getsockname()[1]
                p1 = port // 256
                p2 = port % 256
            
                self.send_msg(state, self.format_msg(227, "Entering passive mode" + "(" + ip + ", " + p1 + ", " + p2 + ")"))
                self.log("Entering passive mode " + ip + ", " + p1 + ", " + p2)

                sock.listen(1)
                conn, addr = sock.accept()


                #verify that the connection is from the same person
                if state.addr[0] != addr[0] and not ip.startswith("192.168.1"):
                    self.send_msg(state, self.format_msg(425, "Could not open the data connection for PASV"))
                    self.log("Could not open data connection addresses don't match")
                else:
                    self.log("PASV data connection opened")

                    state.passive_mode = True
                    state.passive_conn = conn

        elif command == "epsv":
            if self.pasv_mode == False:
                self.send_msg(state, self.format_msg(425, "Passive mode disabled VIA config file"))
                self.log("Passive mode disabled VIA config file")
            else:
                #same as pasv but listens for IPv4, IPv6 is unavaiable on my system
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind((self.host, 0))
                port = sock.getsockname()[1]

                self.send_msg(state, self.format_msg(229, "Entering Extended Passive Mode" + "(|||" + port + "|)"))

                sock.listen(1)
                conn, addr = sock.accept()

                
                if addr[0] != state.addr[0]:
                    self.send_msg(state, self.format_msg(425, "Could not open the data connection for EPSV"))
                    self.log("Could not open the data connection for EPSV")
                else:
                    self.log("EPSV data connection opened")

                    state.passive_mode = True
                    state.passive_conn = conn

        elif command == "port":
            if self.port_mode == False:
                self.send_msg(state, self.format_msg(425, "Active mode disabled VIA config file"))
                self.log("Active mode disabled VIA config file")
            else:
                data = args[0].split(",")
                ip, p1, p2 = ".".join(data[0:-2]), data[-2], data[-1]
                port = int(p1) * 256 + int(p2)

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                orig_ip = state.addr[0].split(":")[-1]

                if ip != orig_ip:
                    self.send_msg(state, self.format_msg(425, "Could not open the data connection for PORT"))
                    self.log("Could not open the data connection for PORT")
                    return
                
                sock.connect((ip, port))

                state.passive_mode = True
                state.passive_conn = sock

                self.send_msg(state, self.format_msg(200, "PORT command successful"))

        elif command == "eprt":
            if self.port_mode == False:
                self.send_msg(state, self.format_msg(425, "Active mode disabled VIA config file"))
                self.log("Active mode disabled VIA config file")
            else:
                #similar to PORT
                data = args[0].split("|")
                protocol = data[1]
                ip, port = data[2], int(data[3])

                if ip != state.addr[0]:
                    self.send_msg(state, self.format_msg(425, "Could not open the data connection for EPRT"))
                    self.log("Could not open the data connection for EPRT")
                    return

                if protocol == "1":
                    sock = socket.socket()
                    sock.connect((ip, port))
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((ip, port))
                
                state.passive_mode = True
                state.passive_conn = sock

                self.send_msg(state, self.format_msg(200, "EPRT Command successful"))

        elif command == "retr":

            #check for data connection
            if not state.passive_mode:
                self.send_msg(state, self.format_msg(425, "Please enter passive mode to transfer data"))
                return

            file = args[0]

            #if only file use cwd + file if not use the full path
            if not file.startswith("/"):
                path = os.path.join(state.cwd, file)
            else:
                path = file

            if os.path.isfile(path):
                self.send_msg(state, self.format_msg(150, "Opening BINARY mode data connection for " + file))

                perm_denied = False

                try:
                    with open(path, 'rb') as fi:
                        for line in fi.readlines():
                            state.passive_conn.send(line)
                except PermissionError:
                    self.send_msg(state, self.format_msg(500, "Permission denied."))
                    perm_denied = True
                
                state.passive_conn.close()
                state.passive_mode = False

                if not perm_denied:
                    self.send_msg(state, self.format_msg(226, "Transfer complete"))
            else:
                self.send_msg(state, self.format_msg(550, "Failed to open file"))

        elif command == "stor":
            
            if not state.passive_mode:
                self.send_msg(state, self.format_msg(425, "Enter passive mode first to transfer data"))
                return
            
            file = args[0]

            if not file.startswith("/"):
                path = os.path.join(state.cwd, file)
            else:
                path = file
            
            self.send_msg(state, self.format_msg(150, "Ok to send file"))

            perm_denied = False

            try:
                #try to open file, if permission errors let user know
                with open(path, 'w+') as fi:

                    data = state.passive_conn.recv(1024).decode()

                    while True:

                        data_ = state.passive_conn.recv(1024).decode()

                        if not data_:
                            break

                        data += data_

                    fi.write(data)
            except PermissionError:
                self.send_msg(state, self.format_msg(500, "Permission denied"))
                perm_denied = True

                #Close connection and set passive_mode to False
                state.passive_conn.close()
                state.passive_mode = False

            if not perm_denied:
                self.send_msg(state, self.format_msg(226, "Transfer complete"))

        #Add AUTH TLS handling here
        #should be able to catch AUTH TLS by keyword AUTH
        
        #EXTRA CREDIT FOR 10 points 
        #SSL for python example
        #https://stackoverflow.com/questions/26851034/opening-a-ssl-socket-connection-in-python
        
        #elif command == "auth":

            #Check if Explicit or Implicit TLS, only explicit due to preference
            #if self.explicit_TLS:
                #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                #sock.connect((self.host, 990))
            #else:
                #self.send_msg(state, self.format_msg(200, "Explicity TLS enabled, secure connection over port 990"))
                #self.log("Explicit TLS disabled cannot auth")

        elif command.lower() == "list":

            #check for data connection
            if state.passive_mode:
                files = os.popen('ls -la {cwd}'.format(cwd = state.cwd)).read().strip()
                self.send_msg(state, self.format_msg(150, "Directory listing is: "))

                for line in files.split("\n"):
                    state.passive_conn.send((line + "\r\n").encode())

                #close data connection and set passive_mode to False
                state.passive_conn.close()
                state.passive_mode = False

                self.send_msg(state, self.format_msg(226, "Directory sent"))
            else:
                self.send_msg(state, self.format_msg(425, "Please enter passive mode to transfer data"))
        
        else:
            self.send_msg(state, self.format_msg(500, "Command unknown"))

    #THE PROBLEM LIES HERE 07/08/24
    def connection_handler(self, connection, address):

        try:
            connection.send(self.format_msg(220, "Connected to Mikes FTP Server"))
            #intialize a state for the client
            state = State()
            state.conn = connection
            state.addr = address

            while True:
                #data = connection.recv(1024)
                #This way seems to show the client input more reliably 
                data = state.conn.recv(1024)
                if not data:
                    self.log("No data recieved connection closed")
                    break

                args = FTPServer.data_proc(self, data)
                if args[0] == "quit":
                    self.log("User wants to terminate connection")
                    break
                elif len(args) == 1:
                    FTPServer.data_handler(self, args[0], state)
                else:
                    FTPServer.data_handler(self, args[0], state, args[1:])
                #### OLD CODE BLOCK ####
                #decode data of command
                #data = data.decode().strip()
                #get arguments from command recieved
                #args = data.split(' ')

                #self.log("Recieved data: " + data)

                #send data to data_handler and returns true if quit was called
                #This check must be getting called and severing the connection
                #quit = self.data_handler(args[0].lower(), args[1:], state)

                #GOT TO MOVE THIS - need to make a loop in the main maybe; something like while state.conn == true --> recv data send to data_handler
                #cannot be above the function declaration
                #self.data_handler(args[0].lower(), args[1:], state)
                #if args[0] == "quit":
                    #self.log("User wants to terminate connection")
                    #break
                #### OLD CODE BLOCK ####
            #state.conn.close()
            self.log("Connection has been closed")
            connection.close()
        
        except Exception as ex:
            print(ex)
            if state.passive_mode:
                if state.passive_conn:
                    try:
                        state.passive_conn.close()
                    except Exception:
                        pass
            try:
                connection.close()
            except Exception:
                pass


    def listen_for_new(self):
        with ThreadPoolExecutor(max_workers = multiprocessing.cpu_count()) as pool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:

                try:
                    server.bind((self.host, self.port))
                except Exception as e:
                    traceback.print_exc()

                #accepts new connection
                server.listen()

                self.log("Listening on Port: " + str(server.getsockname()[1]))

                while True:
                    connection, address = server.accept()
                    pool.submit(self.connection_handler, connection, address)
                
                self.log("Server Shutdown")

if __name__ == "__main__":

    #CLI argument parser
    #check for log file since its madatory
    #alternative port is optional default is 21 was having issues with default port 21 
    # #so I just had it choose any open port

    parser = argparse.ArgumentParser(description='FTPServer help')
    parser.add_argument('log_file', metavar='log_file', type=str, help='log file to store session logs')
    parser.add_argument('port', default=21, nargs='?', help='Optional: Default is 21')

    args = parser.parse_args()

    try:
        port = int(args.port)
        if port < 0:
            raise ValueError("Port number is invalid. Less than 0")
    except ValueError:
        print("Port " + args.port + " given is not a valid port number")
        sys.exit(1)

    server = FTPServer(**vars(args))
    server.listen_for_new()

    print("Server shut down")