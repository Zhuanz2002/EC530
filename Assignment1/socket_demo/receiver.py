# socket_demo/receiver.py
import socket

HOST = "127.0.0.1"
PORT = 50007

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"Receiver listening on {HOST}:{PORT} ...")
        conn, addr = s.accept()
        with conn:
            print("Connected by", addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print("Received:", data.decode("utf-8", errors="replace"))

if __name__ == "__main__":
    main()
