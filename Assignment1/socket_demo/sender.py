# socket_demo/sender.py
import socket
import time

HOST = "127.0.0.1"
PORT = 50007

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        for i in range(5):
            msg = f"hello {i}"
            s.sendall(msg.encode("utf-8"))
            time.sleep(0.5)

if __name__ == "__main__":
    main()
