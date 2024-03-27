import socket
import os
import sys
import time
import random
import string


def generate_random_socket_name():
    """Generate a random name for the client socket."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main(server_socket_path):
    # Generate a random name for the client socket
    client_socket_path = generate_random_socket_name() + ".sock"

    # Create a client socket
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Connect to the server
        server_socket.connect(server_socket_path)
    except ConnectionRefusedError:
        print("Connection to the server failed. Server may have terminated.")
        sys.exit(1)

    # Bind the client socket
    client_socket.bind(client_socket_path)
    client_socket.listen(5)

    # Send the client socket path to the server
    server_socket.send(client_socket_path.encode())

    # Accept connections from the server
    connection, _ = client_socket.accept()

    # Pass the file descriptors to the server
    server_socket.send(str(os.dup(0)).encode())  # Send stdin file descriptor
    server_socket.send(str(os.dup(1)).encode())  # Send stdout file descriptor
    server_socket.send(str(os.dup(2)).encode())  # Send stderr file descriptor

    # Close the unused ends of the sockets
    server_socket.close()

    # Wait for the exit code from the server
    exit_code = int(client_socket.recv(1024).decode())

    # Close the client socket
    client_socket.close()

    # Exit with the received exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python client.py <server_socket_path>")
        sys.exit(1)

    server_socket_path = sys.argv[1]
    main(server_socket_path)
