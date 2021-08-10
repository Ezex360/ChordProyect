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

def as_json(node):
    return node if (type(node) is dict) else {'id': node.id, 'ip': node.ip, 'port': node.port}

def failed(node):
    try:
        socket = SocketManager(node['ip'], node['port'])
        socket.send({'PING': 1})
        socket.close()
        return False
    except:
        return True

def log(type, text, is_debbuging = False):
    if is_debbuging:
        print(f'[{type}] {text}')

def warning_from_address(addr):
    log('WARNING', f'Message from {addr} does not match with server API', True)
