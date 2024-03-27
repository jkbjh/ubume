import socket
import os
import sys
import signal


def handle_client(client_socket, client_address):
    # Receive the file descriptors from the client
    stdin_fd = int(client_socket.recv(1024).decode())
    stdout_fd = int(client_socket.recv(1024).decode())
    stderr_fd = int(client_socket.recv(1024).decode())

    # Duplicate the file descriptors to stdin, stdout, and stderr
    os.dup2(stdin_fd, 0)
    os.dup2(stdout_fd, 1)
    os.dup2(stderr_fd, 2)

    # Create a new socket for communicating with the client
    server_to_client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_to_client_socket.connect(client_address)

    # Perform a simple task (in this case, "Hello, World!")
    print("Hello, World!")

    # Pass the exit code to the client
    exit_code = 0  # You can set any exit code here
    server_to_client_socket.send(str(exit_code).encode())

    # Close the sockets
    client_socket.close()
    server_to_client_socket.close()


def main(socket_path, timeout):
    # Set up the server socket
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(socket_path)
    server_socket.listen(5)

    print("Server is listening...")

    # Set timeout for accepting connections
    signal.signal(signal.SIGALRM, lambda signum, frame: sys.exit(0))

    while True:
        try:
            # Reset the timeout for each iteration
            signal.alarm(timeout)

            client_socket, client_address = server_socket.accept()
            print(f"Connection from {client_address}")

            # Fork a child process
            pid = os.fork()
            if pid == 0:  # Child process
                server_socket.close()  # Close the server socket in the child process
                handle_client(client_socket, client_address)
                sys.exit(0)
            else:  # Parent process
                client_socket.close()  # Close the client socket in the parent process
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python server.py <socket_path> <timeout>")
        sys.exit(1)

    socket_path = sys.argv[1]
    timeout = int(sys.argv[2])

    main(socket_path, timeout)
