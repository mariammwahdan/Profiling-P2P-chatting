from socket import *
import threading
import select
import logging
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