import sys, os, threading
import signal, time

from Menu import showMenu, handleMenu
from SocketManager import SocketManager, recive_from, send_to
from AuxFunctions import *

PORT = 5000
IP = '127.0.0.1'

class Node:
    def __init__(self, ip, port):
        self.id = getHash(f'{ip}:{port}')
        self.ip = ip
        self.port = port
        self.pred = None
        self.succ = as_json(self)
        self.fingerTable = {}
        self.is_debbuging = True
        try:
            self.update_all_fingers_table()
            self.server_socket = SocketManager(ip, port, is_server = True)
            print(f"[LISTENING] Node (ID: {self.id}) is listening on {IP}:{PORT}")
        except:
            print("Socket not opened. The port is being used\nClosing program...")
            os._exit(1)

    def start(self):
        threading.Thread(target=self.menu).start()
        threading.Thread(target=self.time_loop, args=()).start()
        while True:
            conn, addr = self.server_socket.socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def menu(self):
        while True:
            showMenu()
            handleMenu(self)

    def time_loop(self):
        while True:
            # Ping every 3 seconds
            time.sleep(3)
            # If only one node, no need to ping
            if as_json(self) == self.succ:
                continue
            self.check_predecessor()
            try:
                self.stablize()
                self.update_all_fingers_table()
            except:
                log('WARNING', 'A node disconected abruptly, stabilizing the network', True)
                self.find_new_successor()

    def getFromNode(self, node, key, value = 1):
        if node['id'] == self.id:
            return self.get_local(key, value)
        return self.get_remote(node, key, value)

    def get_local(self, key, value):
        actionList = {
            'PRED': lambda: self.pred,
            'SUCC': lambda: self.succ,
            'CPF': lambda: self.closest_preceding_finger(value['id']),
        }
        action = actionList.get(key, lambda: print(f'[WARNING] Error geting node information'))
        log('LOG', f'get {key} returns {action()}', False)
        return action()

    def get_remote(self, node, key, value):
        socket = SocketManager(node['ip'], node['port'])
        socket.send({key: value})
        data = socket.recive()
        socket.close()
        return list(data.values())[0]

    def handle_client(self, conn, addr):
        data = recive_from(conn)
        actionList = {
            'JOIN': lambda: self.handle_incoming_join(conn, addr, data['JOIN']),
            'PRED': lambda: send_to(conn, {'predecessor': self.pred}),
            'SUCC': lambda: send_to(conn, {'successor': self.succ}),
            'NOTIFY': lambda: self.notify(data['NOTIFY']),
            'CPF': lambda: send_to(conn, {'finger': self.closest_preceding_finger(data['CPF']['id'])}),
            'PING': lambda: None,
            'SUCC_LEAVE': lambda: self.handle_successor_leave(data['SUCC_LEAVE']),
            'PRED_LEAVE': lambda: self.handle_predecessor_leave(data['PRED_LEAVE']),
        }
        action = list(data.keys())[0]
        actionList.get(action, lambda: warning_from_address(addr))()

    def handle_incoming_join(self, conn, addr, newNode):
        log('NEW CONNECTION', f'{addr} trying to connect.', self.is_debbuging)
        successor = self.find_successor(newNode['id'])
        send_to(conn, {'successor': successor})
        if self.succ['id'] == self.id: # Only node in network
            self.succ = newNode
            self.pred = newNode
        log('NEW CONNECTION', 'Node entered the network', self.is_debbuging)

    def handle_successor_leave(self, node):
        log('INFO', f'Successor {self.succ} left, new successor is {node}', True)
        self.succ = node

    def handle_predecessor_leave(self, node):
        log('INFO', f'Predecessor {self.succ} left, new predecessor is {node}', True)
        self.pred = node

    def join(self, ip, port):  # sourcery skip: extract-method
        log('JOIN', f'Trying to connect with node in {ip}:{port}', True)
        try:
            socket = SocketManager(ip, port)
            socket.send({'JOIN': as_json(self)})
            data = socket.recive()
            self.pred = None
            self.succ = data['successor']
            log('LOG', f'Successor is: {self.succ}')
            log('JOIN', 'Node connected, Wait a few seconds until network stabilizes', self.is_debbuging)
            socket.close()
        except:
            log('JOIN',f'Connection failed, is there a node running in {ip}:{port}?', True)

    def find_successor(self, id):
        node = self.find_predecessor(id)
        return self.getFromNode(node, 'SUCC')

    def find_predecessor(self, id):
        node = as_json(self)
        succ = self.getFromNode(node, 'SUCC')
        while not is_between(id, node['id'], succ['id']):
            node = self.getFromNode(node, 'CPF', {'id': id})
            succ = self.getFromNode(node, 'SUCC')
        return node

    def closest_preceding_finger(self, id):
        for _, value in sorted(self.fingerTable.items(), reverse=True):
            if is_between(value['id'], self.id, id):
                return value
        return as_json(self)


    def stablize(self):
        log('LOG', 'Stabilizing')
        node = self.getFromNode(self.succ,'PRED')
        if node is not None and is_between(node['id'], self.id, self.succ['id']):
            log('LOG', f'Change successor from {self.succ} to {node}', self.is_debbuging)
            self.succ = node
        self.send_notify(self.succ)

    def notify(self, node):
        log('LOG', f'notified by {node}')
        if self.pred is None or is_between(node['id'], self.pred['id'], self.id):
            log('LOG', f'Change pred from {self.pred} to {node}', self.is_debbuging)
            self.pred = node

    def send_notify(self, node):
        socket = SocketManager(node['ip'], node['port'])
        socket.send({'NOTIFY': as_json(self)})
        socket.close()

    def check_predecessor(self):
        if self.pred is not None and failed(self.pred):
            log('WARNING',f'Predecessor node {self.pred} disconeccted abruptly', True)
            self.pred = None

    def find_new_successor(self):
        if (not failed(self.succ)):
            return
        log('INFO', f'Successor node {self.succ} is not in the network anymore', True)
        new_successor = as_json(self)
        for _, value in sorted(self.fingerTable.items()):
            if not failed(value):
                new_successor = value
                break
        self.succ = new_successor
        log('INFO', f'New successor founded: {self.succ}', True)

    def update_all_fingers_table(self):
        for i in range(MAX_BITS):
            entryId = calc_entryId(self.id, i)
            # If only one node in network
            if self.succ == as_json(self):
                self.fingerTable[entryId] = as_json(self)
                continue
            # If multiple nodes in network, we find succ for each entryID
            log('LOG', f'Updating finger table entry {entryId}', False)
            self.fingerTable[entryId] = self.find_successor(entryId)

    # Add replica de datos mas tarde
    def leave(self):
        if as_json(self) != self.succ:
            self.announce_leave()
        self.pred = None
        self.succ = as_json(self)
        log('LEAVE', 'Node network left', self.is_debbuging)

    def announce_leave(self):
        succ_socket = SocketManager(self.succ['ip'], self.succ['port'])
        succ_socket.send({'PRED_LEAVE': as_json(self.pred)})
        succ_socket.close()
        pred_socket = SocketManager(self.pred['ip'], self.pred['port'])
        pred_socket.send({'SUCC_LEAVE': as_json(self.succ)})
        pred_socket.close()

    def exit(self):
        self.leave()
        print("[LEAVE] Good bye")
        os._exit(1)


def main():
    print(f"[STARTING] starting Node")
    node = Node(IP, PORT)
    node.start()
    node.server_socket.close()

if __name__ == "__main__":
    # Get params from console
    if len(sys.argv) < 2:
        print("Arguments not supplied (Defaults used)")
    else:
        PORT = int(sys.argv[1])
    # Handle Ctrl+C exit
    def handler(signum, frame):
        os.system("clear")
        os._exit(1)

    signal.signal(signal.SIGINT, handler)

    main()



