import socket, json

BUFFER = 4096
FORMAT='utf-8'

def send_to(connection, jsonData):
    connection.send(json.dumps(jsonData).encode(FORMAT))

def recive_from(connection):
    try:
        message = connection.recv(BUFFER).decode(FORMAT)
        return json.loads(message)
    except:
        raise Exception(f'[ERROR] Failed to recive data')

class SocketManager:
    def __init__(self, ip, port, is_server = False):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if is_server:
            self.socket.bind(self.address())
            self.socket.listen()
        else:
            self.socket.connect(self.address())

    def address(self):
        return (self.ip, self.port)

    def close(self):
        self.socket.close()

    def send(self, jsonData):
        send_to(self.socket, jsonData)

    def recive(self):
        return recive_from(self.socket)

