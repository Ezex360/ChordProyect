import socket, random
import threading
import json
import sys
import os
import signal
import hashlib
import time

from collections import OrderedDict
from Menu import showMenu, handleMenu

BUFFER = 4096
FORMAT='utf-8'
PORT = 5000
IP = '127.0.0.1'

MAX_BITS = 8    # 8-bit
MAX_NODES = 2 ** MAX_BITS

def getHash(key):
    result = hashlib.sha1(key.encode())
    return int(result.hexdigest(), 16) % MAX_NODES

class Node:
    def __init__(self, ip, port):
        self.id = getHash(f'{ip}:{port}')
        self.ip = ip
        self.port = port
        self.address = (ip, port)
        self.pred = {'id': self.id, 'ip': ip, 'port': port }
        self.succ = {'id': self.id, 'ip': ip, 'port': port }
        self.fingerTable = {}
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.updateFingersTable()
            self.serverSocket.bind((IP, PORT))
            self.serverSocket.listen()
            print(f"[LISTENING] Node (ID: {self.id}) is listening on {IP}:{PORT}")
        except socket.error:
            print("Socket not opened. The port is being used\nClosing program...")
            os._exit(1)

    def start(self):
        threading.Thread(target=self.menu).start()
        threading.Thread(target=self.time_loop, args=()).start()
        while True:
            conn, addr = self.serverSocket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()
            #print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")

    def send(self, connection, jsonData):
        connection.send(json.dumps(jsonData).encode(FORMAT))

    def recive(self, connection):
        try:
            message = connection.recv(BUFFER).decode(FORMAT)
            return json.loads(message)
        except:
            raise Exception(f'[ERROR] Failed to recive data from node {connection.host}:{connection.port}')

    def nodeAsJson(self, node):
        return node if (type(node) is dict) else {'id': node.id, 'ip': node.ip, 'port': node.port}

    def getAddressFromJson(self, node):
        return (node['ip'], node['port'])

    def time_loop(self):
        while True:
            # Ping every 5 seconds
            time.sleep(3)
            # If only one node, no need to ping
            if self.nodeAsJson(self) == self.succ:
                continue
            self.stablize()
            self.updateFingersTable()

    def handle_client(self, conn, addr):
        data = self.recive(conn)
        actionList = {
            'JOIN': lambda: self.connect(conn, addr, data['JOIN']),
            'PRED': lambda: self.send(conn, {'predecesor': self.pred}),
            'SUCC': lambda: self.send(conn, {'succesor': self.succ}),
            'NOTIFY': lambda: self.notify(data['NOTIFY']),
            'CPF': lambda: self.handeCPF(conn, data['CPF'])
        }
        action = list(data.keys())[0]
        actionList.get(action, lambda: self.messageError(addr))()

    def handeCPF(self, conn, id):
        print(f'[LOG] Remote CPF {id}')
        self.send(conn, {'finger': self.closest_preceding_finger(id)})

    def messageError(self, addr):
        print(f'[WARNING] Message from {addr} does not match with server API')

    def connect(self, conn, addr, newNode):
        print(f"\n[NEW CONNECTION] {addr} trying to connect.")
        onlyNodeInThNetwork = self.succ['id'] == self.id
        if onlyNodeInThNetwork:
            self.succ = newNode
            self.pred = newNode
            succesor = self.nodeAsJson(self)
        else:
            succesor = self.find_successor(newNode['id'])
        self.send(conn, {'succesor': succesor})
        print(f"\n[NEW CONNECTION] Node entered the network")

    def menu(self):
        while True:
            showMenu()
            handleMenu(self)

    def join(self, address):  # sourcery skip: extract-method
        print(f"[JOIN] Trying to connect with node in {address}")
        #try:
        #    self.handleJoin(address)
        #except:
        #    print(f"[JOIN] Connection failed")
        #    self.clientSocket.close()
        self.handleJoin(address)

    def handleJoin(self, address):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(address)
        self.send(clientSocket, {'JOIN': self.nodeAsJson(self)})
        data = self.recive(clientSocket)
        self.pred = None
        self.succ = data['succesor']
        print(f'[LOG] Succesor is: {self.succ}')
        print(f"[JOIN] Node connected")
        clientSocket.close()

    def find_successor(self, id):
        if id > self.id and id <= self.succ['id']:
            return self.succ
        node = self.getFromNode(self.nodeAsJson(self), 'CPF', id)
        return self.getFromNode(node, 'SUCC')

    def in_between(self, b, a, c):
        if a is None or b is None or c is None:
            return False
        return b in range(a,c) or b in range(c, a)

    def closest_preceding_finger(self, id):
        for _, value in sorted(self.fingerTable.items(), reverse=True):
            if value['id'] > self.id and value['id'] < id:
                return value
        return self.nodeAsJson(self)

    def stablize(self):
        #print('[LOG] Stabilizing')
        node = self.getFromNode(self.succ,'PRED') if self.nodeAsJson(self) != self.succ else self.pred
        if node is not None and node['id'] > self.id and node['id'] < self.succ['id']:
            print(f'[LOG] Change succesor from {self.succ} to {node}')
            self.succ = node
        self.sendNotify(self.succ)

    def notify(self, node):
        #print(f'[LOG] notified by {node}')
        if \
        self.pred is None or \
        (node['id'] > self.pred['id'] and node['id'] < self.id):
            print(f'[LOG] Change pred from {self.pred} to {node}')
            self.pred = node

    def sendNotify(self, node):
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect(self.getAddressFromJson(node))
        self.send(clientSocket, {'NOTIFY': self.nodeAsJson(self)})
        clientSocket.close()

    def getFromNode(self, node, key, value = 1):
        if node['id'] == self.id:
            return self.get(key, value)
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = self.getAddressFromJson(node)
        clientSocket.connect(address)
        self.send(clientSocket, {key: value})
        data = self.recive(clientSocket)
        clientSocket.close()
        return list(data.values())[0]

    def get(self, key, value):
        actionList = {
            'PRED': lambda: self.pred,
            'SUCC': lambda: self.succ,
            'CPF': lambda: self.closest_preceding_finger(value)
        }
        action = actionList.get(key, lambda: print(f'[WARNING] Error geting node information'))
        #print(f'[LOG] get {key} returns {action()}')
        return action()

    def updateFingersTable(self):
        for i in range(MAX_BITS):
            entryId = (self.id + (2 ** i)) % MAX_NODES
            # If only one node in network
            if self.succ == self.nodeAsJson(self):
                self.fingerTable[entryId] = self.nodeAsJson(self)
                continue
            # If multiple nodes in network, we find succ for each entryID
            #print(f'[LOG] Updating finger table entry {entryId}')
            self.fingerTable[entryId] = self.find_successor(entryId)

    def leave(self):
        print("LEAVE")

    def exit(self):
        print("[LEAVE] Good bye")
        os._exit(1)


if len(sys.argv) < 2:
    print("Arguments not supplied (Defaults used)")
else:
    PORT = int(sys.argv[1])

# Handle Ctrl+C exit
def handler(signum, frame):
    os.system("clear")
    os._exit(1)

signal.signal(signal.SIGINT, handler)

print(f"[STARTING] starting Node")
node = Node(IP, PORT)
node.start()
node.ServerSocket.close()