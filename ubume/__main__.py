import runpy
import argparse
import socket
import os
import sys
import time
import random
import string
from .util import send_msg, recv_msg, install_signal_forwarder, ConnectionTest


def wait_for_server(server_socket_path, timeout=30):
    start_time = time.time()
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while (time.time() - start_time) < timeout:
        try:
            # Connect to the server
            # print(f"connecting to server {server_socket_path}")
            server_socket.connect(server_socket_path)
            send_msg(server_socket, ConnectionTest)
            server_socket.close()
            return
        except (ConnectionRefusedError, FileNotFoundError):
            print("*", end="")
            sys.stdout.flush()
            time.sleep(0.5)
            continue
    raise RuntimeError("Server did not start.")


def fork_launch_server(server_socket_path, timeout, main_module):
    # Fork a child process
    pid = os.fork()
    if pid == 0:  # Child process
        os.setsid()
        sys.argv = ["ubume.server", server_socket_path, timeout, main_module]
        runpy.run_module("ubume.server", run_name="__main__")
    else:  # Parent process
        wait_for_server(server_socket_path)


class NoServerError(RuntimeError):
    pass


def generate_random_socket_name():
    """Generate a random name for the client socket."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def main(server_socket_path, main_module, args):
    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        # Connect to the server
        server_socket.connect(server_socket_path)
    except (ConnectionRefusedError, FileNotFoundError) as _:
        raise NoServerError() from None

    # Pass the file descriptors to the server
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/0")
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/1")
    send_msg(server_socket, f"/proc/{os.getpid()}/fd/2")
    send_msg(server_socket, os.getpid())

    worker_pid = recv_msg(server_socket)
    install_signal_forwarder(worker_pid)

    send_msg(server_socket, (main_module, args))
    # --- waiting for the server
    exit_code = recv_msg(server_socket)
    server_socket.close()
    # Exit with the received exit code
    sys.exit(exit_code)


def main_or_launch(server_socket_path, module, client_args):
    for i in range(2):
        try:
            main(args.server_socket_path, args.module, client_args)
            return
        except NoServerError:
            pass
        fork_launch_server(
            args.server_socket_path,
            server_timeout,
            args.module,
        )


if __name__ == "__main__":
    server_timeout = 5
    if "--" in sys.argv:
        sep_index = sys.argv.index("--")
        client_args = sys.argv[sep_index + 1 :]
        sys.argv = sys.argv[:sep_index]
    else:
        client_args = []
    parser = argparse.ArgumentParser(description="Client script for connecting to a server")
    parser.add_argument("server_socket_path", type=str, help="Path to the server socket")
    parser.add_argument("module", type=str, help="python main module to load")
    args = parser.parse_args()
    main_or_launch(args.server_socket_path, args.module, client_args)
