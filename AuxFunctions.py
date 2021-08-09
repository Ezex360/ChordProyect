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

def as_json(node):
    return node if (type(node) is dict) else {'id': node.id, 'ip': node.ip, 'port': node.port}

def getFromNode(instance, node, key, value = 1):
    if node['id'] == instance.id:
        return get(instance, key, value)
    socket = SocketManager(node['ip'], node['port'])
    socket.send({key: value})
    data = socket.recive()
    socket.close()
    return list(data.values())[0]

def get(instance, key, value):
    actionList = {
        'PRED': lambda: instance.pred,
        'SUCC': lambda: instance.succ,
        'CPF': lambda: instance.closest_preceding_finger(value)
    }
    action = actionList.get(key, lambda: print(f'[WARNING] Error geting node information'))
    log('LOG', f'get {key} returns {action()}', not instance.is_debbuging)
    return action()

def log(type, text, is_debbuging = False):
    if is_debbuging:
        print(f'[{type}] {text}')

def warning_from_address(addr):
    log('WARNING', f'Message from {addr} does not match with server API', True)
