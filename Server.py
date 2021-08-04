import socket 
import threading
import json

BUFFER = 4096
FORMAT='utf-8'
PORT = 5050
IP = "127.0.0.1"
ADDR = (IP, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        message = conn.recv(BUFFER).decode(FORMAT)
        if message:
            data = json.loads(message)
            if 'message' in data.keys():
                print(f'[{addr}] {data["message"]}')
            if 'disconnect' in data.keys():
                connected = False
                print(f"[DISCONNECTION] {addr} disconnected.")

    conn.close()
        

def start():
    server.listen()
    print(f"[LISTENING] Node is listening on {ADDR}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[STARTING] starting Node")
start()