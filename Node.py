import socket 
import threading
import json
import sys

BUFFER = 4096
FORMAT='utf-8'
PORT = 5001
IP = '127.0.0.1'
ADDR = (IP, PORT)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
    threading.Thread(target=message_promt).start()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

def send(msg):
    data = {"message": msg}
    message = json.dumps(data)
    client.send(message.encode(FORMAT))

def disconnect():
    client.send(json.dumps({"disconnect": 1}).encode(FORMAT))

def message_promt():
    port = int(input("Ingrese el puerto a conectarse\n"))
    client.connect((IP, port))
    loop = 1
    while loop:
        message = input("Mensaje a enviar: ")
        if message!="chau":
            send(message)
        else:
            loop = 0
            disconnect()

if len(sys.argv) < 2:
    print("Arguments not supplied (Defaults used)")
else:
    PORT = int(sys.argv[1])

print("[STARTING] starting Node")
start()