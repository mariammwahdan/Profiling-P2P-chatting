import threading
import socket
import time
from hashlib import sha256
import logging

# Registry server configuration
REGISTRY_IP = '192.168.1.6'
REGISTRY_PORT = 15600
REGISTRY_UDP_PORT = 15500
# Spike test configuration
NUM_PEERS = 100
BATCH_SIZE = 20

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_free_port():
    # Get a free port dynamically
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    _, port = s.getsockname()
    s.close()
    return port

def register_user(username, password):
    # Register a user
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((REGISTRY_IP, REGISTRY_PORT))
        hashed_password = sha256(password.encode('utf-8')).hexdigest()
        register_message = f"CRT:{username}:{hashed_password}"
        client_socket.sendall(register_message.encode())
        response = client_socket.recv(1024).decode()
        logging.info(f"Register response for {username}: {response}")
        client_socket.close()
        return response
    except Exception as e:
        logging.error(f"Error during registration for {username} : {e}")
        time.sleep(1)

def send_hello_message(username):
    # Send periodic hello messages to the registry
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = f"HELLO {username}"
    while True:
        udp_socket.sendto(message.encode(), (REGISTRY_IP, REGISTRY_UDP_PORT))
        time.sleep(1)

def simulate_login(username, password, peer_server_port):
    # Simulate a login attempt and start sending hello messages
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((REGISTRY_IP, REGISTRY_PORT))
        hashed_password = sha256(password.encode('utf-8')).hexdigest()
        login_message = f"LOG:{username}:{hashed_password}:{peer_server_port}"
        client_socket.sendall(login_message.encode())
        response = client_socket.recv(1024).decode()
        logging.info(f"Login response for {username}: {response}")
        if response == "OK":
            # Start hello messages in a separate thread
            hello_thread = threading.Thread(target=send_hello_message, args=(username,), daemon=True)
            hello_thread.start()
        client_socket.close()
    except Exception as e:
        logging.error(f"Error during login for {username}: {e}")

def batch_test(threads, batch_size):
    # Run threads in batches
    for i in range(0, len(threads), batch_size):
        batch_threads = threads[i:i + batch_size]
        for thread in batch_threads:
            thread.start()
        for thread in batch_threads:
            thread.join()

# Main Spike Test
if __name__ == "__main__":
    print("Registering users...")
    for i in range(NUM_PEERS):
        username = f"user{i}"
        password = f"pass{i}"
        register_user(username, password)
    time.sleep(5)

    print("Starting spike test for user logins...")
    threads = []
    for i in range(NUM_PEERS):
        username = f"user{i}"
        password = f"pass{i}"
        peer_server_port = get_free_port()
        thread = threading.Thread(target=simulate_login, args=(username, password, peer_server_port))
        threads.append(thread)

    batch_test(threads, BATCH_SIZE)
    print("Spike test completed.")