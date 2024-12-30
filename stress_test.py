

import socket
import threading
import random
import time

HOST = "192.168.1.8"
PORT = 15600
NUM_CLIENTS = 500
OPERATIONS = ["CRT", "LOG", "SRCH", "CCR", "JCR", "GCR"]


def client_simulation(client_id):
    try:

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        username = f"user{client_id}"
        password = "pass123"
        create_account_msg = f"CRT:{username}:{password}"
        print('trying to signup')
        client_socket.sendall(create_account_msg.encode())
        response = client_socket.recv(1024).decode()
        print(f"Client {client_id} (Create Account) received: {response}")

        port = PORT + client_id  # Simulated client port
        login_msg = f"LOG:{username}:{password}:{port}"
        print('trying to login')
        client_socket.sendall(login_msg.encode())
        response = client_socket.recv(1024).decode()

        print(f"Client {client_id} (Login) received: {response}")


        if "OK" in response:
            for _ in range(20):

                search_user = f"user{random.randint(0, NUM_CLIENTS)}"
                message = f"SRCH:{search_user}"
                client_socket.sendall(message.encode())
                response = client_socket.recv(1024).decode()


                print(f"Client {client_id} performed search: {response}")

                room_name = f"room{client_id}"
                room_port = random.randint(5000, 6000)
                message = f"CCR:{room_name}:{client_id}:{room_port}"
                client_socket.sendall(message.encode())
                response = client_socket.recv(1024).decode()


                print(f"Client {client_id} performed Create Chat room: {response}")

                room_name = f"room{random.randint(0, NUM_CLIENTS)}"
                room_port = random.randint(5000, 6000)
                message = f"JCR:{room_name}:{client_id}:{room_port}"
                client_socket.sendall(message.encode())
                response = client_socket.recv(1024).decode()

                print(f"Client {client_id} performed join Group Chat: {response}")

                message = "GCR"


                client_socket.sendall(message.encode())
                response = client_socket.recv(1024).decode()


                print(f"Client {client_id} performed Get Group Chats: {response}")




        client_socket.close()
    except Exception as e:
        print(f"Client {client_id} encountered an error: {e}")


def main():
    threads = []


    for i in range(NUM_CLIENTS):
        thread = threading.Thread(target=client_simulation, args=(i,))
        threads.append(thread)
        thread.start()


    for thread in threads:
        thread.join()

    print("Stress test completed.")


if __name__ == "__main__":
    main()
