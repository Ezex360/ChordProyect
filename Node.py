import sys, os, threading
import signal, time

from Menu import show_menu, handle_menu
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
        self.finger_table = {}
        self.hash_table = {}
        self.cache = {}
        self.is_replicating = True
        try:
            self.restart_cache_counter()
            self.update_all_fingers_table()
            self.server_socket = SocketManager(ip, port, is_server = True)
            print(f"[LISTENING] Node (ID: {self.id}) is listening on {IP}:{PORT}")
        except:
            print("Socket not opened. The port is being used\nClosing program...")
            os._exit(1)

    # Initialize threads of menu and time_loop, and listen for other nodes connections
    def start(self):
        threading.Thread(target=self.menu).start()
        threading.Thread(target=self.time_loop, args=()).start()
        while True:
            conn, addr = self.server_socket.socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    # Menu Thread function
    def menu(self):
        while True:
            show_menu()
            handle_menu(self)

    def exit(self):
        self.leave()
        print("[LEAVE] Good bye")
        os._exit(1)

    # Periodically called function
    def time_loop(self):
        self.restart_cache_counter()
        while True:
            # Ping every 3 seconds
            time.sleep(3)
            self.clean_cache()
            # If only one node, no need to ping
            if as_json(self) == self.succ and self.pred is None:
                continue
            self.check_predecessor()
            try:
                self.stablize()
                self.update_all_fingers_table()
            except:
                print(f'[WARNING] A node disconected abruptly, stabilizing the network')
                self.find_new_successor()
                self.finger_table_temporary_fix()

    # Intercept node messages and respond accordingly
    def handle_client(self, conn, addr):
        data = recive_from(conn)
        action = dict_first_key(data)
        actionList = {
            'JOIN'      : lambda: self.handle_incoming_join(conn, addr, data[action]),
            'PRED'      : lambda: self.send_predecessor(conn),
            'SUCC'      : lambda: self.send_successor(conn),
            'NOTIFY'    : lambda: self.notify(data[action]),
            'CPF'       : lambda: self.handle_send_closest_preceding_finger(conn, data[action]),
            'PING'      : lambda: None,
            'SUCC_LEAVE': lambda: self.handle_successor_leave(data[action]),
            'PRED_LEAVE': lambda: self.handle_predecessor_leave(data[action]),
            'SET'       : lambda: self.handle_set(data[action]),
            'GET'       : lambda: self.handle_get(conn, data[action]),
            'REPLICATE' : lambda: self.handle_replicate(data[action]),
            'RM_REPLICA_KEY': lambda: self.handle_remove_replicated_key(data[action]),
        }
        # Ejecute action recived from the connected node
        actionList.get(action, lambda: warning_from_address(addr))()

    def handle_incoming_join(self, conn, addr, newNode):
        print(f'[NEW CONNECTION] {addr} trying to connect.')
        successor = self.find_successor(newNode['id'])
        send_to(conn, {'successor': successor})
        if self.succ['id'] == self.id: # Only node in network
            self.succ = newNode
            self.pred = newNode
            self.send_hash_table_to_predecessor()
        print(f'[NEW CONNECTION] Node entered the network')

    def send_predecessor(self, conn):
        send_to(conn, {'predecessor': self.pred})

    def send_successor(self, conn):
        send_to(conn, {'successor': self.succ})

    def handle_send_closest_preceding_finger(self, conn, node):
        send_to(conn, {'finger': self.closest_preceding_finger(node['id'])})

    def handle_successor_leave(self, node):
        print(f'[INFO] Successor {self.succ} left, new successor is {node}')
        self.succ = node

    def handle_predecessor_leave(self, node):
        print(f'[INFO] Predecessor {self.pred} left, new predecessor is {node}')
        self.pred = node

    def handle_set(self, data):
        self.add_to_hashtable(data)
        if self.is_replicating and self.id != self.succ['id']:
            self.get_from_node(self.succ, 'REPLICATE', data)

    def add_to_hashtable(self, data):
        key, value = dict_item(data)
        print(f'[INFO] Saving pair ({key},{value}) in local hashtable')
        self.hash_table[key] = value

    def handle_get(self, conn, key):
        send_to(conn, {'value': self.hash_table.get(key)})

    def handle_replicate(self, data):
        print(f'[INFO] Reciving data to replicate')
        self.add_to_hashtable(data)

    def handle_remove_replicated_key(self, key):
        if self.is_replica_key(key) and key in self.hash_table.keys():
            print(f'[INFO] Removing replicated key {key}!')
            self.hash_table.pop(key)

    # Send join request to another node
    def join(self, ip, port):
        print(f'[JOIN] Trying to connect with node in {ip}:{port}')
        try:
            socket = SocketManager(ip, port)
            socket.send({'JOIN': as_json(self)})
            data = socket.recive()
            self.pred = None
            self.succ = data['successor']
            socket.close()
            print(f'[JOIN] Node connected, Wait a few seconds until network stabilizes')
        except:
            print(f'[JOIN] Connection failed, is there a node running in {ip}:{port}?')

    # Node and key finding functions
    def find_successor(self, id):
        node = self.find_predecessor(id)
        return self.get_from_node(node, 'SUCC')

    def find_predecessor(self, id):
        node = as_json(self)
        succ = self.get_from_node(node, 'SUCC')
        while not is_between(id, node['id'], succ['id']):
            node = self.get_from_node(node, 'CPF', {'id': id})
            succ = self.get_from_node(node, 'SUCC')
        return node

    def closest_preceding_finger(self, id):
        for _, value in sorted(self.finger_table.items(), reverse=True):
            if is_between(value['id'], self.id, id):
                return value
        return as_json(self)

    def get_from_node(self, node, key, value = 1):
        if node['id'] == self.id:
            return self.get_local(key, value)
        return self.get_remote(node, key, value)

    def get_local(self, key, value):
        actionList = {
            'PRED': lambda: self.pred,
            'SUCC': lambda: self.succ,
            'CPF' : lambda: self.closest_preceding_finger(value['id']),
            'SET' : lambda: self.handle_set(value),
            'GET' : lambda: self.hash_table.get(value),
        }
        action = actionList.get(key, lambda: print(f'[WARNING] Error geting node information'))
        return action()

    def get_remote(self, node, key, value):
        non_reciving_keys = ['SET', 'REPLICATE', 'RM_REPLICA_KEY']
        socket = SocketManager(node['ip'], node['port'])
        socket.send({key: value})
        if key in non_reciving_keys:
            socket.close()
            return
        data = socket.recive()
        socket.close()
        return dict_value(data)

    # Finger table specific functions
    def update_all_fingers_table(self):
        for i in range(MAX_BITS):
            entryId = calc_entryId(self.id, i)
            # If only one node in network
            if self.succ == as_json(self):
                self.finger_table[entryId] = as_json(self)
                continue
            #print(f'[LOG] Updating finger table entry {entryId}')
            # If multiple nodes in network, we find succ for each entryID
            self.finger_table[entryId] = self.find_successor(entryId)

    def finger_table_temporary_fix(self):
        # If there was a sudden disconnect, initialize the finger table with the new succesor
        for key in self.finger_table.keys():
            self.finger_table[key] = self.succ

    # Stabilizing related functions
    def stablize(self):
        node = self.get_from_node(self.succ,'PRED')
        if node is not None and is_between(node['id'], self.id, self.succ['id']):
            print(f'[LOG] Change successor from {self.succ} to {node}')
            self.succ = node
        self.send_notify(self.succ)

    def notify(self, node):
        if self.pred is None or is_between(node['id'], self.pred['id'], self.id):
            print(f'[LOG] Change predecessor from {self.pred} to {node}')
            self.pred = node
            self.send_hash_table_to_predecessor()

    def send_notify(self, node):
        socket = SocketManager(node['ip'], node['port'])
        socket.send({'NOTIFY': as_json(self)})
        socket.close()

    def check_predecessor(self):
        if self.pred is not None and failed(self.pred):
            print(f'[WARNING] Predecessor node {self.pred} disconeccted abruptly')
            self.pred = None

    def find_new_successor(self):
        if (not failed(self.succ)):
            return
        print(f'[INFO] Successor node {self.succ} is not in the network anymore')
        new_successor = as_json(self)
        for _, value in sorted(self.finger_table.items()):
            # Search in finger table for the first node that is still conected
            if not failed(value):
                new_successor = value
                break
        self.succ = new_successor
        print(f'[INFO] New successor founded: {self.succ}')

    def send_hash_table_to_predecessor(self):
        print(f'[INFO] Sending hash table contents to predecessor {self.pred}')
        data = self.hash_table.copy()
        for key, value in data.items():
            if is_between(getHash(key), self.id, self.pred['id']):
                self.get_from_node(self.pred, 'SET', {key: value})
                if self.is_replicating:
                    self.get_from_node(self.succ, 'RM_REPLICA_KEY', key)
                else:
                    self.hash_table.pop(key)

    # Leave functions
    def leave(self):
        if as_json(self) != self.succ:
            self.announce_leave()
            if self.is_replicating:
                self.replicate_data_before_leave()
            else:
                self.send_hash_table_to_successor()
        self.hash_table = {}
        self.pred = None
        self.succ = as_json(self)
        print(f'[LEAVE] Node left the network')

    def announce_leave(self):
        # Create a connection with the succesor and pass its new predecessor
        succ_socket = SocketManager(self.succ['ip'], self.succ['port'])
        succ_socket.send({'PRED_LEAVE': as_json(self.pred)})
        succ_socket.close()
        # Create a connection with the predecessor and pass its new succesor
        pred_socket = SocketManager(self.pred['ip'], self.pred['port'])
        pred_socket.send({'SUCC_LEAVE': as_json(self.succ)})
        pred_socket.close()

    def send_hash_table_to_successor(self):
        print(f'[INFO] Sending hash table contents to successor {self.succ}')
        for key, value in self.hash_table.items():
            self.get_from_node(self.succ, 'SET', {key: value})

    # Hash table related functions
    def set(self, key, value):
        hashedKey = getHash(key)
        node = self.find_successor(hashedKey)
        self.get_from_node(node, 'SET', {key: value})
        self.save_in_cache(key, value)

    def get(self, key):
        self.get_from_cache_if_exists(key)
        hashedKey = getHash(key)
        node = self.find_successor(hashedKey)
        data = self.get_from_node(node, 'GET', key)
        self.save_in_cache(key, data)
        return data

    # Replica specific functions
    def is_replica_key(self, key):
        id_pred, hashed_key  = self.pred['id'], getHash(key)
        return is_between(hashed_key, self.id, id_pred)

    def replicate_data_before_leave(self):
        print(f'[INFO] Replicating data before leaving')
        for key, value in self.hash_table.items():
            self.set(key, value) # Set saves the data in the correct nodes

    # Cache functions
    def save_in_cache(self, key, data):
        self.cache[key] = data

    def get_from_cache_if_exists(self, key):
        if key in self.cache.keys():
            print(f"[GET] Obtained from cache)")
            return self.cache[key]

    def restart_cache_counter(self):
        self.cache_clean_counter = 3

    def clean_cache(self):
        self.cache_clean_counter -= 1
        if self.cache_clean_counter <= 0:
            is_cache_empty = len(self.cache.items()) > 0
            if is_cache_empty:
                self.cache.pop(dict_first_key(self.cache)) # Remove oldest item from cache
            self.restart_cache_counter()

def main():
    print(f"[STARTING] starting Node")
    node = Node(IP, PORT)
    node.start()

if __name__ == "__main__":
    # Get params from console
    if len(sys.argv) < 2:
        print("Port not supplied (Defaults used)")
    else:
        PORT = int(sys.argv[1])
    # Handle Ctrl+C exit
    def handler(signum, frame):
        os._exit(1)

    signal.signal(signal.SIGINT, handler)

    main()



