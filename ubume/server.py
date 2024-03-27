import socket
import os
import sys
import signal
from util import send_msg, recv_msg


def handle_client(client_socket, client_address):
    print("waiting for file descriptors")
    # Receive the file descriptors from the client
    stdin = recv_msg(client_socket)
    stdout = recv_msg(client_socket)
    stderr = recv_msg(client_socket)
    print(stdin, stdout, stderr)
    fobj_stdin = open(stdin, "r")
    fobj_stdout = open(stdout, "w")
    fobj_stderr = open(stderr, "w")
    stdin_fd = fobj_stdin.fileno()
    stdout_fd = fobj_stdout.fileno()
    stderr_fd = fobj_stderr.fileno()
    print(stdin_fd, stdout_fd, stderr_fd)

    print("hello world on server")
    # Duplicate the file descriptors to stdin, stdout, and stderr
    os.dup2(stdin_fd, 0)
    os.dup2(stdout_fd, 1)
    os.dup2(stderr_fd, 2)


    # Perform a simple task (in this case, "Hello, World!")
    print("Hello, World! (from server)")

    # Pass the exit code to the client
    exit_code = 0  # You can set any exit code here
    send_msg(client_socket, exit_code)

    # Close the sockets
    client_socket.close()
    #server_to_client_socket.close()


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
