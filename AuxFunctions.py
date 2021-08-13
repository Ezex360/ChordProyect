from SocketManager import *
import hashlib

MAX_BITS = 8    # 8-bit
MAX_NODES = 2 ** MAX_BITS

def getHash(key):
    result = hashlib.sha1(key.encode())
    return int(result.hexdigest(), 16) % MAX_NODES

def is_between(key, ID1, ID2):
    #ID1 is smaller value, #ID2 is larger value
    if ID1 == ID2:
        return True
    wrap = ID1 > ID2 #Boolean to see if wrapping occured.
    if not wrap:
        return key > ID1 and key <=ID2
    else:
        return key > ID1 or key <= ID2

def calc_entryId(id, index):
    return (id + (2 ** index)) % MAX_NODES

# Dictionary helper functions
def as_json(node):
    return node if (type(node) is dict) else {'id': node.id, 'ip': node.ip, 'port': node.port}

def dict_first_key(dict):
    return list(dict.keys())[0]

def dict_value(dict):
    return list(dict.values())[0]

def dict_item(dict):
    return list(dict.items())[0]

def failed(node):
    try:
        socket = SocketManager(node['ip'], node['port'])
        socket.send({'PING': 1})
        socket.close()
        return False
    except:
        return True

def node_address(node):
    return (node['ip'], node['port'])

def warning_from_address(addr):
    print(f'[WARNING] Message from {addr} does not match with server API')
