import socket
import threading
from config import SERVER_HOST, SERVER_PORT, NODE_PORT_START

class BigFileSServer:
    def __init__(self):
        self.nodes = {}
        self.next_port = NODE_PORT_START
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Servidor rodando em {SERVER_HOST}:{SERVER_PORT}")

    def handle_client(self, client_socket):
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            parts = data.split('|')
            if parts[0] == 'REGISTER':
                node_id = len(self.nodes) + 1
                node_port = self.next_port
                self.next_port += 1
                self.nodes[node_id] = {'host': parts[1], 'port': node_port}
                client_socket.send(f"OK|{node_id}|{node_port}".encode())
            elif parts[0] == 'GET_NODES':
                nodes_str = str(self.nodes)
                client_socket.send(nodes_str.encode())

        client_socket.close()

    def start(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    server = BigFileSServer()
    server.start()