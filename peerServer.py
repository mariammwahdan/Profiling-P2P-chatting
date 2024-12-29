from socket import *
import threading
import time
import select
import logging
from hashlib import sha256


# Server side of peer
class PeerServer(threading.Thread):

    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        # keeps the username of the peer
        self.username = username
        # tcp socket for peer server
        self.tcpServerSocket = socket(AF_INET, SOCK_STREAM)
        # port number of the peer server
        self.peerServerPort = peerServerPort

        self.isInChatRoom = 0
        # if 1, then user is already chatting with someone
        # if 0, then user is not chatting with anyone
        self.isChatRequested = 0
        # keeps the socket for the peer that is connected to this peer
        self.connectedPeerSocket = None
        # keeps the ip of the peer that is connected to this peer's server
        self.connectedPeerIP = None
        # keeps the port number of the peer that is connected to this peer's server
        self.connectedPeerPort = None
        # online status of the peer
        self.isOnline = True
        # keeps the username of the peer that this peer is chatting with
        self.chattingClientName = None

    # main method of the peer server thread
    def run(self):

        print("\033[91m")
        print("Peer server started...")
        print("\033[0m")

        # gets the ip address of this peer
        # first checks to get it for Windows devices
        # if the device that runs this application is not windows
        # it checks to get it for macOS devices
        hostname = gethostname()
        try:
            self.peerServerHostname = gethostbyname(hostname)
        except gaierror:
            import netifaces as ni
            self.peerServerHostname = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']

        # ip address of this peer
        # self.peerServerHostname = 'localhost'
        # socket initializations for the server of the peer
        self.tcpServerSocket.bind((self.peerServerHostname, self.peerServerPort))
        self.tcpServerSocket.listen(4)
        # inputs sockets that should be listened
        inputs = [self.tcpServerSocket]
        # server listens as long as there is a socket to listen in the inputs list and the user is online
        while inputs and self.isOnline:
            # monitors for the incoming connections
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                # If a server waits to be connected enters here
                for s in readable:
                    # if the socket that is receiving the connection is
                    # the tcp socket of the peer's server, enters here
                    if s is self.tcpServerSocket:
                        # accepts the connection, and adds its connection socket to the inputs list
                        # so that we can monitor that socket as well
                        connected, addr = s.accept()
                        connected.setblocking(0)
                        inputs.append(connected)
                        # if the user is not chatting, then the ip and the socket of
                        # this peer is assigned to server variables
                        if self.isChatRequested == 0:
                            # print("\033[34m")
                            # print(self.username + " is connected from " + str(addr))
                            # print("\033[0m")
                            self.connectedPeerSocket = connected
                            self.connectedPeerIP = addr[0]
                    # if the socket that receives the data is the one that
                    # is used to communicate with a connected peer, then enters here
                    else:
                        # message is received from connected peer
                        messageReceived = s.recv(1024).decode()
                        # logs the received message
                        logging.info("Received from " + str(self.connectedPeerIP) + " -> " + str(messageReceived))
                        # if message is a request message it means that this is the receiver side peer server
                        # so evaluate the chat request
                        if len(messageReceived) > 11 and messageReceived[:12] == "CHAT-REQUEST":
                            # text for proper input choices is printed however OK or REJECT is taken as input in main process of the peer
                            # if the socket that we received the data belongs to the peer that we are chatting with,
                            # enters here
                            if not self.isInChatRoom and s is self.connectedPeerSocket:
                                # parses the message
                                messageReceived = messageReceived.split()
                                # gets the port of the peer that sends the chat request message
                                self.connectedPeerPort = int(messageReceived[1])
                                # gets the username of the peer sends the chat request message
                                self.chattingClientName = messageReceived[2]
                                # prints prompt for the incoming chat request
                                print("\033[34m")
                                print("Incoming chat request from " + self.chattingClientName + " >> ")
                                print("\033[0m")
                                print("\033[34m")
                                print("Enter OK to accept or REJECT to reject:  ")
                                print("\033[0m")
                                # makes isChatRequested = 1 which means that peer is chatting with someone
                                self.isChatRequested = 1
                            # if the socket that we received the data does not belong to the peer that we are chatting with
                            # and if the user is already chatting with someone else(isChatRequested = 1), then enters here
                            elif self.isInChatRoom or (s is not self.connectedPeerSocket and self.isChatRequested == 1):
                                # sends a busy message to the peer that sends a chat request when this peer is
                                # already chatting with someone else
                                message = "BUSY"
                                s.send(message.encode())
                                # remove the peer from the inputs list so that it will not monitor this socket
                                inputs.remove(s)
                        # if an OK message is received then ischatrequested is made 1 and then next messages will be shown to the peer of this server
                        elif messageReceived == "OK":
                            self.isChatRequested = 1
                        # if an REJECT message is received then ischatrequested is made 0 so that it can receive any other chat requests
                        elif messageReceived == "REJECT":
                            self.isChatRequested = 0
                            inputs.remove(s)
                        # if a message is received, and if this is not a quit message ':q' and
                        # if it is not an empty message, show this message to the user
                        elif messageReceived[:2] != ":q" and len(messageReceived) != 0:
                            print("\033[94m")
                            print(self.chattingClientName + ": " + messageReceived)
                            print("\033[0m")
                        # if the message received is a quit message ':q',
                        # makes ischatrequested 1 to receive new incoming request messages
                        # removes the socket of the connected peer from the inputs list
                        elif messageReceived[:2] == ":q":
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            # connected peer ended the chat
                            if len(messageReceived) == 2:
                                print("\033[34m")
                                print("User you're chatting with ended the chat")
                                print("\033[0m")
                                print("\033[34m")
                                print("Press enter to quit the chat: ")
                                print("\033[0m")
                        # if the message is an empty one, then it means that the
                        # connected user suddenly ended the chat(an error occurred)
                        elif len(messageReceived) == 0:
                            self.isChatRequested = 0
                            inputs.clear()
                            inputs.append(self.tcpServerSocket)
                            print("\033[31m")
                            print("User you're chatting with suddenly ended the chat")
                            print("\033[0m")
                            print("\033[34m")
                            print("Press enter to quit the chat: ")
                            print("\033[0m")
            # handles the exceptions, and logs them
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except ValueError as vErr:
                logging.error("ValueError: {0}".format(vErr))

class PeerClient(threading.Thread):
    # variable initializations for the client side of the peer
    def __init__(self, ipToConnect, portToConnect, username, peerServer, responseReceived):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipToConnect = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portToConnect = portToConnect
        # client side tcp socket initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        # keeps the server of this client
        self.peerServer = peerServer
        # keeps the phrase that is used when creating the client
        # if the client is created with a phrase, it means this one received the request
        # this phrase should be none if this is the client of the requester peer
        self.responseReceived = responseReceived
        # keeps if this client is ending the chat or not
        self.isEndingChat = False


    # main method of the peer client thread
    def run(self):
        print("\033[34m")
        print("Peer client started...")
        print("\033[0m")
        # connects to the server of other peer
        self.tcpClientSocket.connect((self.ipToConnect, self.portToConnect))
        # if the server of this peer is not connected by someone else and if this is the requester side peer client then enters here
        if self.peerServer.isChatRequested == 0 and self.responseReceived is None:
            # composes a request message and this is sent to server and then this waits a response message from the server this client connects
            requestMessage = "CHAT-REQUEST " + str(self.peerServer.peerServerPort)+ " " + self.username
            # logs the chat request sent to other peer
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + requestMessage)
            # sends the chat request
            self.tcpClientSocket.send(requestMessage.encode())
            print("\033[34m")
            print("Request message " + requestMessage + " is sent...")
            print("\033[0m")
            # received a response from the peer which the request message is sent to
            self.responseReceived = self.tcpClientSocket.recv(1024).decode()
            # logs the received message
            print("\033[34m")
            logging.info("Received from " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + self.responseReceived)
            print("\033[0m")
            print("\033[34m")
            print("Response is " + self.responseReceived)
            print("\033[0m")
            # parses the response for the chat request
            self.responseReceived = self.responseReceived.split()
            # if response is ok then incoming messages will be evaluated as client messages and will be sent to the connected server
            if self.responseReceived[0] == "OK":
                # changes the status of this client's server to chatting
                self.peerServer.isChatRequested = 1
                # sets the server variable with the username of the peer that this one is chatting
                self.peerServer.chattingClientName = self.responseReceived[1]
                # as long as the server status is chatting, this client can send messages
                while self.peerServer.isChatRequested == 1:
                    # message input prompt
                    messageSent = input(self.username + ": ")
                    # sends the message to the connected peer, and logs it
                    self.tcpClientSocket.send(messageSent.encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                    # if the quit message is sent, then the server status is changed to not chatting
                    # and this is the side that is ending the chat
                    if messageSent == ":q":
                        self.peerServer.isChatRequested = 0
                        self.isEndingChat = True
                        break
                # if peer is not chatting, checks if this is not the ending side
                if self.peerServer.isChatRequested == 0:
                    if not self.isEndingChat:
                        # tries to send a quit message to the connected peer
                        # logs the message and handles the exception
                        try:
                            self.tcpClientSocket.send(":q ending-side".encode())
                            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                        except BrokenPipeError as bpErr:
                            logging.error("BrokenPipeError: {0}".format(bpErr))
                    # closes the socket
                    self.responseReceived = None
                    self.tcpClientSocket.close()
            # if the request is rejected, then changes the server status, sends a reject message to the connected peer's server
            # logs the message and then the socket is closed
            elif self.responseReceived[0] == "REJECT":
                self.peerServer.isChatRequested = 0
                print("\033[34m")
                print("client of requester is closing...")
                print("\033[0m")
                self.tcpClientSocket.send("REJECT".encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> REJECT")
                self.tcpClientSocket.close()
            # if a busy response is received, closes the socket
            elif self.responseReceived[0] == "BUSY":
                print("\033[31m")
                print("Receiver peer is busy")
                print("\033[0m")
                self.tcpClientSocket.close()
        # if the client is created with OK message it means that this is the client of receiver side peer
        # so it sends an OK message to the requesting side peer server that it connects and then waits for the user inputs.
        elif self.responseReceived == "OK":
            # server status is changed
            self.peerServer.isChatRequested = 1
            # ok response is sent to the requester side
            okMessage = "OK"
            self.tcpClientSocket.send(okMessage.encode())
            logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + okMessage)
            print("\033[34m")
            print("Client with OK message is created... and sending messages")
            print("\033[0m")
            # client can send messsages as long as the server status is chatting
            while self.peerServer.isChatRequested == 1:
                # input prompt for user to enter message
                messageSent = input(self.username + ": ")
                self.tcpClientSocket.send(messageSent.encode())
                logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> " + messageSent)
                # if a quit message is sent, server status is changed
                if messageSent == ":q":
                    self.peerServer.isChatRequested = 0
                    self.isEndingChat = True
                    break
            # if server is not chatting, and if this is not the ending side
            # sends a quitting message to the server of the other peer
            # then closes the socket
            if self.peerServer.isChatRequested == 0:
                if not self.isEndingChat:
                    self.tcpClientSocket.send(":q ending-side".encode())
                    logging.info("Send to " + self.ipToConnect + ":" + str(self.portToConnect) + " -> :q")
                self.responseReceived = None
                self.tcpClientSocket.close()



class peerRoom:
    def __init__(self, ipToConnect, portToConnect, username,peerUdpSocket,peerTCPsocket,roomName):
        threading.Thread.__init__(self)
        # keeps the ip address of the peer that this will connect
        self.ipList = ipToConnect
        # keeps the username of the peer
        self.username = username
        # keeps the port number that this client should connect
        self.portList = portToConnect
        # udp port of the peer
        self.peerTCPsocket = peerTCPsocket
        # keeps the server of this client
        # keeps if this client is ending the chat or not
        self.isInChatRoom = True
        self.udpClientSocket = peerUdpSocket
        self.roomName = roomName

    def receive_message(self):
            inputs = [self.udpClientSocket]
            while inputs and self.isInChatRoom:
                readable, writable, exceptional = select.select(inputs, [], [],0.1)
                for s in readable:
                    if s is self.udpClientSocket:
                        try:
                            data, address = self.udpClientSocket.recvfrom(1024)
                            decoded = data.decode()
                            splitted = decoded.split(":")

                            if splitted[0] == "JUPDT":
                                self.ipList.append(splitted[2])
                                self.portList.append(splitted[3])
                                print("\033[92m")
                                print(splitted[1],":Joined The Room!!!!!")
                                print("\033[0m")
                            elif splitted[0] == "XUPDT":
                                index = -1
                                for i in range(len(self.ipList)):
                                    if self.ipList[i] == splitted[2] and int(self.portList[i]) == int(splitted[3]):
                                        index = i
                                        break
                                if index != -1:
                                    self.ipList.pop(index)
                                    self.portList.pop(index)
                                print("\033[31m")
                                print(splitted[1], "has left the room :(")
                                print("\033[0m")
                            else:
                                print(f"{decoded}")
                        except:
                            pass

    def send_message(self):
            while self.isInChatRoom:
                messageSent = input()
                if messageSent == ":q":
                    self.isInChatRoom = False
                    remove = "XUPDT:" + self.roomName + ":" + self.username + ":" + str(self.udpClientSocket.getsockname()[1])
                    self.peerTCPsocket.send(remove.encode())
                    logging.info("Exit is sent")
                else:
                    for ip, port in zip(self.ipList, self.portList):
                        self.udpClientSocket.sendto((self.username + ":" + messageSent).encode(), (ip, int(port)))


    # main method of the peer room thread
    def run(self):
        send_thread = threading.Thread(target=self.send_message)
        receive_thread = threading.Thread(target=self.receive_message)
        send_thread.start()
        receive_thread.start()

        send_thread.join()
        logging.info("Send Thread STopped")
        receive_thread.join(0.1)
        logging.info("Recieve thred stoppped")

# main process of the peer
class peerMain:

    # peer initializations
    def __init__(self):
        # ip address of the registry
        self.registryName = input("\033[34mEnter IP address of registry: \033[0m")
        #self.registryName = 'localhost'
        # port number of the registry
        self.registryPort = 15600
        # tcp socket connection to registry
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        # initializes udp socket which is used to send hello messages
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        # udp port of the registry
        self.registryUDPPort = 15500
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # peer is in chat room
        self.isInChatRoom = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None
        
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            # menu selection prompt
            if not self.isOnline:
                choice = input('''\033[34mChoose: \n
Create account: 1\n
Login: 2\n
Logout: 3\n
\033[0m''')
            else:
                choice = input('''\033[34mChoose: \n
Logout: 3\n
Search: 4\n
Start a chat: 5\n
Get Online Peers: 6\n
Create a Chat Room: 7\n
Join a chat Room: 8\n
View Chat Rooms: 9\n\033[0m''')                

            # if choice is 1, creates an account with the username
            # and password entered by the user
            if choice == "1":
                username = input("\033[34musername: \033[0m")
                password = input("\033[34mpassword: \033[0m")
                
                self.createAccount(username, password)
            # if choice is 2 and user is not logged in, asks for the username
            # and the password to login
            elif choice == "2" and not self.isOnline:
                username = input("\033[34musername: \033[0m")
                password = input("\033[34mpassword: \033[0m")
                # asks for the port number for server's tcp socket
                peerServerPort = int(input("\033[34m Enter a port number for peer server: \033[0m"))
                
                status = self.login(username, password, peerServerPort)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage()
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print("\033[92m")
                print("Logged out successfully")
                print("\033[0m")
            # is peer is not logged in and exits the program
            elif choice == "3":
                self.logout(2)
            # if choice is 4 and user is online, then user is asked
            # for a username that is wanted to be searched
            elif choice == "4" and self.isOnline:
                username = input("\033[34mUsername to be searched: ")
                searchStatus = self.searchUser(username)
                # if user is found its ip address is shown to user
                if searchStatus is not None and searchStatus != 0:
                    print("\033[92m")
                    print("IP address of " + username + " is " + searchStatus)
                    print("\033[0m")
            # if choice is 5 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice == "5" and self.isOnline:
                username = input("\033[34mEnter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus != None and searchStatus != 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()
            elif choice is "6" and self.isOnline:
                self.getOnlineUsers()

            elif choice is "7" and self.isOnline:
                roomName = input("\033[34mEnter the name of the chat room: ")
                self.createChatRoom(roomName,self.loginCredentials[0])


            elif choice is "8" and self.isOnline:
                roomName = input("\033[34mEnter the name of the chat room: ")
                self.joinChatRoom(roomName,self.loginCredentials[0])  

            elif choice is "9" and self.isOnline:
                self.getAvailableChatRoom()               
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice.upper() == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()

            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break

            elif self.isOnline:
                if self.peerServer.connectedPeerSocket != None:
                    self.peerServer.connectedPeerSocket.send("REJECT".encode())
                    self.peerServer.isChatRequested = 0
                    logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
                else:
                    print("Invalid Choice, Try Again\n")
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # account creation function
    def createAccount(self, username, password):
        # join message to create an account is composed and sent to registry
        # if response is success then informs the user for account creation
        # if response is exist then informs the user for account existence
        message = "CRT:" + username + ":" + sha256(password.encode('utf-8')).hexdigest()
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "OK":
            print("\033[92m")
            print("Account created...")
            print("\033[0m")
        elif response == "EXST":
            print("\033[31m")
            print("choose another username or login...")
            print("\033[0m")

    # login function
    def login(self, username, password, peerServerPort):
        # a login message is composed and sent to registry
        # an integer is returned according to each response
        message = "LOG:" + username + ":" + sha256(password.encode('utf-8')).hexdigest() + ":" + str(peerServerPort)
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "OK":
            print("\033[92m")
            print("Logged in successfully...")
            print("\033[0m")
            return 1
        #elif response == "login-account-not-exist":
            #print("Account does not exist...")
            #return 0
        elif response == "AON":
            print("\033[31m")
            print("Account is already online...")
            print("\033[0m")
            return 2
        elif response == "WCRE":
            print("\033[31m")
            print("Wrong password...")
            print("\033[0m")
            return 3
    
    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        if option == 1:
            message = "LGO:" + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SRCH:" + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))

        #ip?
        if response[0] == "IP:":
            print("\033[92m")
            print(username + " is found successfully...")
            print("\033[0m")
            return response[1]
        elif response[0] == "NON":
            print("\033[34m")
            print(username + " is not online...")
            print("\033[0m")
            return 0
        elif response[0] == "NOTEXST":
            print("\033[31m")
            print(username + " is not found")
            print("\033[0m")
            return None
        
    #function to get a list of online users
    def getOnlineUsers(self):
        #Ask Registry to return usernames of online peers
        message = "GOP"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        print(response)

    
    def createChatRoom(self,roomName,userName):
        hostname = gethostname()
        IPAddr = gethostbyname(hostname)
        udpSocket = socket(AF_INET,SOCK_DGRAM)
        udpSocket.bind((IPAddr,0))
        message = "CCR:" + roomName + ":" + userName + ":" + str(udpSocket.getsockname()[1])
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + response)
        if response == "OK":
            self.isInChatRoom = True
            print("\033[92m")
            print(roomName," created...")
            self.peerServer.isInChatRoom = True
            roomObj = peerRoom([],[],self.loginCredentials[0],udpSocket,self.tcpClientSocket,roomName)
            roomObj.run()
            self.peerServer.isInChatRoom = False
            print("\033[0m")
        elif response == "EXST":
            print("\033[31m")
            print("Chat Room Name Already Exists")
            print("\033[0m")

    def joinChatRoom(self,roomName,userName):
        hostname = gethostname()
        IPAddr = gethostbyname(hostname)
        udpSocket = socket(AF_INET,SOCK_DGRAM)
        udpSocket.bind((IPAddr,0))
        message = "JCR:" + roomName + ":" + userName + ":" + str(udpSocket.getsockname()[1])
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split('\n')
    
        logging.info("Received from " + self.registryName + " -> " + str(response))
      
        if response[0] == "OK":
            self.isInChatRoom = True
            print("\033[92m")
            print("Welcome to ",roomName," Chat Room, Say Hi")
            print("\033[0m")
            IPs = list()
            names = list()
            myname = self.loginCredentials[0]
            ports = list()
            myport = None
            for line in response[1:]:
                line = line.split(":")
                if line[0] == self.loginCredentials[0]: #Don't let user create a socket with himself
                    myport = line[2]
                    continue
                names.append(line[0])
                IPs.append(line[1])
                ports.append(line[2])
            self.peerServer.isInChatRoom = True
            roomObj = peerRoom(IPs,ports,myname,udpSocket,self.tcpClientSocket,roomName)
            roomObj.run()
            self.peerServer.isInChatRoom = False

        elif response[0] == "NOTEXST":
            print("\033[31m")
            print("Chat Room Doesn't Exist")
            print("\033[0m")
    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
            
    def exitChatRoom(self,userName):
        message = "XUPDT:" + userName
        self.tcpClientSocket.send(message.encode())

    def sendHelloMessage(self):
        message = "HELLO " + self.loginCredentials[0]
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()

    def getAvailableChatRoom(self):
        # Ask Registry to return list of available rooms
        message = "GCR"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode()
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        print(response)              


# peer is started
main = peerMain()
