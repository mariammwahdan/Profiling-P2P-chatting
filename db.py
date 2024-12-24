import pymongo
from pymongo import MongoClient

#Includes database operations
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
