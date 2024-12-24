from pymongo import MongoClient


# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client.get_database('p2p-chat')

    # checks if an account with the username exists
    def is_account_exist(self, username):
        if self.db.accounts.count_documents({'username': username}) > 0:
            return True
        else:
            return False

    # registers a user
    def register(self, username, password):
        account = {
            "username": username,
            "password": password
        }
        self.db.accounts.insert_one(account)

    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]

    # checks if an account with the username online
    def is_account_online(self, username):
        if self.db.online_peers.count_documents({"username": username}) > 0:
            return True
        else:
            return False

    # logs in the user
    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)

    # logs out the user
    def user_logout(self, username):
        self.db.online_peers.delete_one({"username": username})

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return res["ip"], res["port"]

    # returns a list of online users
    def get_online_peers(self):
        online_peers_list = list()
        for online_peer in self.db.online_peers.find():
            online_peers_list.append(online_peer['username'])
        return online_peers_list


def is_roomName_exist(self, roomName):
    if self.db.rooms.count_documents({'roomName': roomName}) > 0:
        return True
    else:
        return False

        # Create Chat Room


def createChatRoom(self, roomName, userName, userIP, userPort):
    room = {
        "roomName": roomName,
        "userNames": [userName],
        "userIPs": [userIP],
        "userPorts": [userPort]
    }
    self.db.rooms.insert_one(room)


def addChatRoomMember(self, roomName, userName, userIP, userPort):
    query = {'roomName': roomName}
    newPeer = {"$push": {"userNames": userName,
                         "userIPs": userIP,
                         "userPorts": userPort}}
    self.db.rooms.update_one(query, newPeer)


def getRoomMembers(self, roomName):
    return self.db.rooms.find_one({"roomName": roomName})


def removeRoomMember(self, roomName, userName, IP, port):
    # Get the room document
    room = self.db.rooms.find_one({'roomName': roomName})
    print(f"Before update: {room}\n")
    if userName in room['userNames']:
        index = room['userNames'].index(userName)
        room['userNames'].pop(index)
        room['userIPs'].pop(index)
        room['userPorts'].pop(index)
        self.db.rooms.update_one({'roomName': roomName}, {'$set': room})
        room = self.db.rooms.find_one({'roomName': roomName})
        print(f"After update: {room}")


def removeRoom(self, roomName):
    self.db.rooms.delete_one({'roomName': roomName})


def getRooms(self):
    chatroom = list()
    for chat in self.db.rooms.find():
        chatroom.append(chat['roomName'])
    # print(chatroom)
    return chatroom
# db = DB()
# db.getRooms()
# db.removeRoomMember("room","rafik2","192.168.1.106","49733")
