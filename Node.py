import socket 
import threading
import json
import sys
import os
import signal

from collections import OrderedDict

BUFFER = 4096
FORMAT='utf-8'
PORT = 5000
IP = '127.0.0.1'

class Node:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.address = (ip, port)
        self.pred = self.address  
        self.succ = self.address
        self.fingerTable = OrderedDict()
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listenThread = None
        self.promptThread = None
        try:
            self.serverSocket.bind((IP, PORT))
            self.serverSocket.listen()
            print(f"[LISTENING] Node is listening on {IP}:{PORT}")
        except socket.error:
            print("Socket not opened")

    def start(self):
        promptThread = threading.Thread(target=self.message_promt)
        promptThread.start()
        while True:
            conn, addr = self.serverSocket.accept()
            self.listenThread = threading.Thread(target=self.handle_client, args=(conn, addr))
            self.listenThread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

    def handle_client(self, conn, addr):
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

    def send(self, msg):
        data = {"message": msg}
        message = json.dumps(data)
        self.clientSocket.send(message.encode(FORMAT))

    def disconnect(self):
        self.clientSocket.send(json.dumps({"disconnect": 1}).encode(FORMAT))
        self.clientSocket.close()
        os._exit(1)

    def message_promt(self):
        try:
            port = int(input("Ingrese el puerto a conectarse\n"))
            self.clientSocket.connect((IP, port))
            loop = 1
            while loop:
                message = input("Mensaje a enviar: ")
                if message!="chau":
                    self.send(message)
                else:
                    loop = 0
                    self.disconnect()
        except:
            print("Error while connecting to a client")

if len(sys.argv) < 2:
    print("Arguments not supplied (Defaults used)")
else:
    PORT = int(sys.argv[1])

# Handle Ctrl+C exit
def handler(signum, frame):
    os._exit(1)

signal.signal(signal.SIGINT, handler)

print(f"[STARTING] starting Node")
node = Node(IP, PORT)
node.start()
node.ServerSocket.close()