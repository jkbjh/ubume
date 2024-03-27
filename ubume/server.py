import importlib
import socket
import os
import sys
import signal
from .util import send_msg, recv_msg, start_selfkill_watchdog_daemon, unlink_disconnected_socket, ConnectionTest
import runpy


def handle_client(client_socket, client_address):
    # --- Send PIDs and Socket IDs.
    stdin = recv_msg(client_socket)
    if stdin is ConnectionTest:
        return

    stdout = recv_msg(client_socket)
    stderr = recv_msg(client_socket)
    client_pid = recv_msg(client_socket)
    start_selfkill_watchdog_daemon(client_pid)
    send_msg(client_socket, os.getpid())
    # --- setup file descriptors to replace stdin,stdout, stderr
    fobj_stdin = open(stdin, "r")
    fobj_stdout = open(stdout, "w")
    fobj_stderr = open(stderr, "w")
    stdin_fd = fobj_stdin.fileno()
    stdout_fd = fobj_stdout.fileno()
    stderr_fd = fobj_stderr.fileno()

    # Duplicate the file descriptors to stdin, stdout, and stderr
    os.dup2(stdin_fd, 0)
    os.dup2(stdout_fd, 1)
    os.dup2(stderr_fd, 2)

    main_module, args = recv_msg(client_socket)

    module = importlib.import_module(main_module)
    sys.argv = [main_module] + args
    try:
        runpy.run_module(main_module, run_name="__main__")
        exit_code = 0
    except SystemExit as se:
        exit_code = se.code
    send_msg(client_socket, exit_code)
    # Close the sockets
    client_socket.close()


def main(socket_path, timeout):
    # Set up the server socket
    unlink_disconnected_socket(socket_path)
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    #server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(socket_path)
    server_socket.listen(5)

    # Set timeout for accepting connections
    def exit_and_cleanup(signum, frame):
        os.unlink(socket_path)
        sys.exit(0)
    signal.signal(signal.SIGALRM, exit_and_cleanup)

    while True:
        try:
            # Reset the timeout for each iteration
            signal.alarm(timeout)
            client_socket, client_address = server_socket.accept()

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
    if len(sys.argv) != 4:
        print("Usage: python server.py <socket_path> <timeout> <module>")
        sys.exit(1)

    socket_path = sys.argv[1]
    timeout = int(sys.argv[2])
    module = sys.argv[3]
    importlib.import_module(module)

    main(socket_path, timeout)
