import socket
import json

BUFFER = 4096
FORMAT='utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
PORT = 5052
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)
SERVER_ADDR = ('127.0.0.1', 5050)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind(ADDR)
print(f'trying to connect at {SERVER_ADDR}')
client.connect(SERVER_ADDR)

def send(msg):
    data = {"message": msg}
    message = json.dumps(data)
    client.send(message.encode(FORMAT))

def disconnect():
    client.send(json.dumps({"disconnect": 1}).encode(FORMAT))

loop = 1
while loop:
    message = input("Mensaje a enviar: ")
    if message!="chau":
        send(message)
    else:
        loop = 0
        disconnect()