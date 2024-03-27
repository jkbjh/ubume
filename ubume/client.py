import argparse
import socket
import os
import sys
import time
import random
import string
from util import send_msg, recv_msg, install_signal_forwarder


def generate_random_socket_name():
    """Generate a random name for the client socket."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main(server_socket_path, main_module, args):
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
    send_msg(server_socket, os.getpid())
    print("file descriptors sent!")

    worker_pid = recv_msg(server_socket)
    install_signal_forwarder(worker_pid)

    print("sending args")
    send_msg(server_socket, (main_module, args))
    #--- waiting for the server
    exit_code = recv_msg(server_socket)
    server_socket.close()
    # Exit with the received exit code
    sys.exit(exit_code)


if __name__ == "__main__":
    print(repr(sys.argv))
    if "--" in sys.argv:
        sep_index = sys.argv.index("--")
        client_args = sys.argv[sep_index+1:]
        sys.argv = sys.argv[:sep_index]
    else:
        client_args = []
    print("client_args:", repr(client_args))
    print("sys.argv:", repr(sys.argv))

    parser = argparse.ArgumentParser(description="Client script for connecting to a server")
    parser.add_argument("server_socket_path", type=str, help="Path to the server socket")
    parser.add_argument("module", type=str, help="python main module to load")
    args = parser.parse_args()
    main(args.server_socket_path, args.module, client_args)
