import threading
import random
import logging
from peer import peerMain

# Configure logging
logging.basicConfig(
    filename="soak_test_results.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def simulate_user_operations(user_id):
    username = f"user{user_id}"
    password = f"pass{user_id}"
    peer_port = 15000 + user_id

    try:
        # Create account
        peer_instance = peerMain()
        peer_instance.createAccount(username, password)
        logging.info(f"User {user_id}: Account created successfully.")

        # Log in
        peer_instance.login(username, password, peer_port)
        logging.info(f"User {user_id}: Logged in successfully.")

        # Perform random operations
        operations = [
            lambda: peer_instance.searchUser(f"user{random.randint(1, 48)}"),
            lambda: peer_instance.getOnlineUsers(),
            lambda: peer_instance.createChatRoom(f"room{user_id}", username),
            lambda: peer_instance.getAvailableChatRoom()
        ]

        for _ in range(5):  # Each user performs 5 random operations
            operation = random.choice(operations)
            try:
                operation()
                logging.info(f"User {user_id}: Operation {operation.__name__} completed successfully.")
            except Exception as e:
                logging.error(f"User {user_id}: Error during operation {operation.__name__} - {e}")

        # Log out
        peer_instance.logout(1)
        logging.info(f"User {user_id}: Logged out successfully.")

    except Exception as e:
        logging.error(f"User {user_id}: Fatal error - {e}")

if __name__ == "__main__":
    # Create and start threads for 48 users
    threads = []
    for user_id in range(1, 49):
        thread = threading.Thread(target=simulate_user_operations, args=(user_id,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    logging.info("Soak testing completed.")
