import socket
import os
import sys
import time
import random
import string
from util import send_msg, recv_msg

def generate_random_socket_name():
    """Generate a random name for the client socket."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main(server_socket_path):
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Connect to the server
        print(f"connecting to server {server_socket_path}")
        server_socket.connect(server_socket_path)
        print("connected")
    except ConnectionRefusedError:
        print("Connection to the server failed. Server may have terminated.")
        sys.exit(1)

    # Pass the file descriptors to the server
    print("sending file descriptors")
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/0")
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/1")
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/2")
    print("file descriptors sent!")

    exit_code = recv_msg(server_socket)
    server_socket.close()
    # Exit with the received exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python client.py <server_socket_path>")
        sys.exit(1)

    server_socket_path = sys.argv[1]
    main(server_socket_path)
