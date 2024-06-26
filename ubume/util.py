import struct
import pickle
import os
import errno
import time
import sys
import threading
import signal
import stat
import socket

class ConnectionTest:
    pass


def unlink_disconnected_socket(filename):
    if not os.path.exists(filename):
        return
    if not is_socket(filename):
        return
    if is_disconnected_socket(filename):
        print(f"unlinking socket {filename}")
        os.unlink(filename)


def is_socket(filename):
    return stat.S_ISSOCK(os.stat(filename).st_mode)


def is_disconnected_socket(filename):
    try:
        # Try to connect to the socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(filename)
        s.close()
        return False  # Socket is still connected
    except (ConnectionRefusedError, FileNotFoundError):
        return True  # Socket is disconnected or file does not exist


def install_signal_forwarder(target_pid):
    signal_handler = make_signal_forwarder(target_pid)
    for sig in range(1, signal.NSIG):
        try:
            signal.signal(sig, signal_handler)
        except (OSError, RuntimeError):
            pass  # Skip signals that cannot be caught


def make_signal_forwarder(target_pid):
    def signal_handler(signum, frame):
        # Send the received signal to a different PID
        os.kill(target_pid, signum)
        print(f"Caught signal {signum} and sent it to PID {target_pid}")

    return signal_handler


def send_msg(socket, data):
    databuf = pickle.dumps(data)
    length = len(databuf)
    socket.send(struct.pack("L", length))
    socket.send(databuf)


def recv_msg(socket):
    (length,) = struct.unpack("L", socket.recv(8))
    databuf = socket.recv(length)
    return pickle.loads(databuf)


def is_running(pid):
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            return False
    return True


def watchdog_selfkill(pid, sleep=5, killsignal=9):
    while True:
        time.sleep(sleep)
        if is_running(pid):
            continue
        sys.stderr.write(f"ubume: requester died unexpectedly, self kill signal {killsignal}\n")
        os.kill(os.getpid(), killsignal)


def start_selfkill_watchdog_daemon(pid):
    thread = threading.Thread(target=lambda: watchdog_selfkill(pid), daemon=True)
    thread.start()
