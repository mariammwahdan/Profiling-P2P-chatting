from socket import *
import threading
import logging

from oauthlib.uri_validate import port

import db
class ClientThread(threading.Thread):
    # initializations for client thread
    def __init__(self, ip, port, tcpClientSocket):
        threading.Thread.__init__(self)
        # ip of the connected peer
        self.ip = ip
        # port number of the connected peer
        self.port = port
        # socket of the peer
        self.tcpClientSocket = tcpClientSocket
        hostname = gethostname()
        IPAddr = gethostbyname(hostname)
        self.udpSocket = socket(AF_INET,SOCK_DGRAM) #udp socket for chat room broadcasting
        self.udpSocket.bind((IPAddr,0))
        # username, online status and udp server initializations
        self.username = None
        self.isOnline = True
        self.udpServer = None
        print("\033[35m")
        print("New thread started for " + ip + ":" + str(port))

    def run(self):
        # locks for thread which will be used for thread synchronization
        self.lock = threading.Lock()
        print("\033[35m")
        print("Connection from: " + self.ip + ":" + str(port))
        print("\033[35m")
        print("IP Connected: " + self.ip)

        while True:
            try:
                # waits for incoming messages from peers
                message = self.tcpClientSocket.recv(1024).decode().split(":")
                logging.info("Received from " + self.ip + ":" + str(self.port) + " -> " + " ".join(message))
                #   Create Account   #
                if message[0] == "CRT":
                    # Create Account is sent to peer,
                    # if an account with this username already exists
                    if db.is_account_exist(message[1]):
                        response = "EXST"
                        print("\033[35m")
                        print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # join-success is sent to peer,
                    # if an account with this username is not exist, and the account is created
                    else:
                        db.register(message[1], message[2])
                        response = "OK"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "LOG":
                    # WCRE is sent to peer,
                    # if an account with the username does not exist
                    if not db.is_account_exist(message[1]):
                        response = "WCRE"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # AON is sent to peer,
                    # if an account with the username already online
                    elif db.is_account_online(message[1]):
                        response = "AON"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # OK is sent to peer,
                    # if an account with the username exists and not online
                    else:
                        # retrieves the account's password, and checks if the one entered by the user is correct
                        retrievedPass = db.get_password(message[1])
                        # if password is correct, then peer's thread is added to threads list
                        # peer is added to db with its username, port number, and ip address
                        if retrievedPass == message[2]:
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username] = self
                            finally:
                                self.lock.release()


                            db.user_login(message[1], self.ip, message[3])
                            # OK is sent to peer,
                            # and a udp server thread is created for this peer, and thread is started
                            # timer thread of the udp server is started
                            response = "OK"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)

                #   LOGOUT  #
                elif message[0] == "LGO":
                    # if user is online,
                    # removes the user from onlinePeers list
                    # and removes the thread for this user from tcpThreads
                    # socket is closed and timer thread of the udp for this
                    # user is cancelled
                    if len(message) > 1 and message[1] is not None and db.is_account_online(message[1]):
                        db.user_logout(message[1])
                        self.lock.acquire()
                        try:
                            if message[1] in tcpThreads:
                                del tcpThreads[message[1]]
                        finally:
                            self.lock.release()
                        print("\033[35m")
                        print(self.ip + ":" + str(self.port) + " is logged out")
                        self.tcpClientSocket.close()
                        self.udpServer.timer.cancel()
                        break

                    else:
                        self.tcpClientSocket.close()
                        break
                #   SEARCH  #
                elif message[0] == "SRCH":
                    # checks if an account with the username exists
                    if db.is_account_exist(message[1]):
                        # checks if the account is online
                        # and sends the related response to peer
                        if db.is_account_online(message[1]):
                            peer_info = db.get_peer_ip_port(message[1])
                            response = "IP: " + peer_info[0] + ":" + peer_info[1]
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                        else:
                            response = "NON"
                            logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                            self.tcpClientSocket.send(response.encode())
                    # enters if username does not exist
                    else:
                        response = "NOTEXST"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "GOP":
                    online_peers = db.get_online_peers()
                    response = "NOP:" + str(len(online_peers)) + "\nPeers:"
                    for peer in online_peers:
                        response += peer
                        response += "\n"

                    self.tcpClientSocket.send(response.encode())

                elif message[0] == "CCR":
                    if db.is_roomName_exist(message[1]):
                        response = "EXST"
                        print("\033[35m")
                        print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    # join-success is sent to peer,
                    # if an account with this username is not exist, and the account is created
                    else:
                        db.createChatRoom(message[1], message[2], self.ip, message[3])
                        response = "OK"
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())

                elif message[0] == "JCR":
                    if not db.is_roomName_exist(message[1]):
                        response = "NOTEXST"
                        print("\033[35m")
                        print("From-> " + self.ip + ":" + str(self.port) + " " + response)
                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + response)
                        self.tcpClientSocket.send(response.encode())
                    else:
                        print('ana da5lt')
                        db.addChatRoomMember(message[1], message[2], self.ip, message[3])
                        members = db.getRoomMembers(message[1])
                        IPs = members["userIPs"]
                        names = members["userNames"]
                        ports = members["userPorts"]
                        # logging.info(members)
                        # logging.info(str(IPs))
                        # logging.info(names)
                        # logging.info(ports)
                        # logging.info("Length of IPs: " + str(len(IPs)))
                        # logging.info("Length of names: " + str(len(names)))
                        # logging.info("Length of ports: " + str(len(ports)))

                        for i in range(len(IPs)):
                            if names[i] == message[2]:
                                continue
                            update = "JUPDT:" + message[2] + ":" + self.ip + ":" + str(message[3])
                            print("message is ", update)
                            print("IP is ", IPs[i], "port is ", ports[i])
                            self.udpSocket.sendto(update.encode(), (IPs[i], int(ports[i])))
                        response = "OK\n"
                        for i in range(len(IPs)):
                            response += (names[i] + ":" + str(IPs[i]) + ":" + str(ports[i]))
                            if i < len(IPs) - 1:  # If it's not the last iteration
                                response += "\n"

                        logging.info("Send to " + self.ip + ":" + str(self.port) + " -> " + str(response))
                        try:
                            self.tcpClientSocket.send(response.encode())
                        except Exception as e:
                            logging.error("Error sending message: " + str(e))

                elif message[0] == "XUPDT":
                    members = db.getRoomMembers(message[1])
                    IPs = members["userIPs"]
                    names = members["userNames"]
                    ports = members["userPorts"]
                    remove = "XUPDT:" + message[2] + ":" + self.ip + ":" + str(message[3])
                    db.removeRoomMember(message[1], message[2], self.ip, message[3])
                    for i in range(len(IPs)):
                        if names[i] == message[2]:
                            continue
                        self.udpSocket.sendto(remove.encode(), (IPs[i], int(ports[i])))
                    if len(IPs) == 1:
                        db.removeRoom(message[1])

                elif message[0] == "GCR":
                    chatrooms = db.getRooms()
                    response = "NOCR:" + str(len(chatrooms)) + "\nRooms:"
                    for room in chatrooms:
                        response += room
                        response += "\n"
                    self.tcpClientSocket.send(response.encode())
            except OSError as oErr:
                pass
                # logging.error("OSError: {0}".format(oErr))

                # function for resettin the timeout for the udp timer thread

        def resetTimeout(self):
            self.udpServer.resetTimer()



tcpThreads = {}

