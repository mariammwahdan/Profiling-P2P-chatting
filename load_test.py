import threading
import time
from socket import socket, AF_INET, SOCK_STREAM
import random
import string

# Configuration
REGISTRY_HOST = '192.168.1.11'  
REGISTRY_PORT = 15600           
NUM_USERS = 46                  # Number of concurrent users
MESSAGE_INTERVAL = 1            

# Function to simulate a user
def simulate_user(username, password):
    try:
        # Connect to registry
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((REGISTRY_HOST, REGISTRY_PORT))

        # Create account
        create_account_msg = f"CRT:{username}:{password}"
        client_socket.send(create_account_msg.encode())
        response = client_socket.recv(1024).decode()
        print(f"[{username}] Account Creation Response: {response}")

        # Login
        peer_port = random.randint(50000, 60000)
        login_msg = f"LOG:{username}:{password}:{peer_port}"
        client_socket.send(login_msg.encode())
        response = client_socket.recv(1024).decode()
        print(f"[{username}] Login Response: {response}")

        if response == "OK":
            
            actions = ['search', 'create_room', 'join_room', 'send_hello']
            action = random.choice(actions)

            if action == 'search':
                # Search for a random peer
                search_user = f"user{random.randint(1, NUM_USERS)}"
                search_msg = f"SRCH:{search_user}"
                client_socket.send(search_msg.encode())
                response = client_socket.recv(1024).decode()
                print(f"[{username}] Search Response: {response}")

            elif action == 'create_room':
                # Create a chat room
                room_name = f"room{random.randint(1, 100)}"
                create_room_msg = f"CCR:{room_name}:{username}:{peer_port}"
                client_socket.send(create_room_msg.encode())
                response = client_socket.recv(1024).decode()
                print(f"[{username}] Create Room Response: {response}")

            elif action == 'join_room':
                # Join a chat room
                room_name = f"room{random.randint(1, 100)}"
                join_room_msg = f"JCR:{room_name}:{username}:{peer_port}"
                client_socket.send(join_room_msg.encode())
                response = client_socket.recv(1024).decode()
                print(f"[{username}] Join Room Response: {response}")

            elif action == 'send_hello':
                # Send HELLO messages to keep session alive
                hello_msg = f"HELLO {username}"
                client_socket.send(hello_msg.encode())
                print(f"[{username}] Sent HELLO")

        # Logout
        logout_msg = f"LGO:{username}"
        client_socket.send(logout_msg.encode())
        print(f"[{username}] Logged out")

        client_socket.close()

    except Exception as e:
        print(f"[{username}] Error: {e}")


# Function to start multiple user threads
def start_load_test():
    threads = []

    for i in range(NUM_USERS):
        username = f"user{i+1}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        thread = threading.Thread(target=simulate_user, args=(username, password))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print("Load testing completed.")


if __name__ == "__main__":
    start_load_test()
