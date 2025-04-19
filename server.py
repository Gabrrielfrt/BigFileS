import socket
import json
from threading import Thread, Lock
from config import SERVER_HOST, SERVER_PORT, NODE_PORT_START, OPERATIONS, ERROR_MESSAGES
from utils import send_json, receive_json, send_file, receive_file

class BigFileSServer:
    def __init__(self):
        self.nodes = {}
        self.next_node_port = NODE_PORT_START
        self.lock = Lock()
        self.setup_server()

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_HOST, SERVER_PORT))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {SERVER_HOST}:{SERVER_PORT}")

    def handle_client(self, client_socket):
        try:
            while True:
                data = receive_json(client_socket)
                if not data:
                    break

                operation = data.get('operation')
                if operation == 'register_node':
                    self.register_node(client_socket, data)
                elif operation == 'get_nodes':
                    self.send_nodes(client_socket)
                elif operation == 'get_operations':
                    send_json(client_socket, {'operations': OPERATIONS})
                else:
                    send_json(client_socket, {
                        'status': 'error', 
                        'message': ERROR_MESSAGES['invalid_command']
                    })

        except Exception as e:
            print(f"Erro no cliente: {e}")
        finally:
            client_socket.close()

    def register_node(self, client_socket, data):
        with self.lock:
            node_id = str(len(self.nodes) + 1)
            node_port = self.next_node_port
            self.next_node_port += 1
            
            self.nodes[node_id] = {
                'host': data.get('host', 'localhost'),
                'port': node_port,
                'status': 'active',
                'last_seen': time.time()
            }
            
            send_json(client_socket, {
                'status': 'success',
                'node_id': node_id,
                'node_port': node_port
            })
            print(f"Nó {node_id} registrado na porta {node_port}")

    def send_nodes(self, client_socket):
        # Remove nós inativos
        current_time = time.time()
        inactive_nodes = [
            node_id for node_id, node in self.nodes.items()
            if current_time - node.get('last_seen', 0) > 60  # 60 segundos de timeout
        ]
        
        for node_id in inactive_nodes:
            del self.nodes[node_id]
            print(f"Nó {node_id} removido por inatividade")
        
        send_json(client_socket, {
            'status': 'success',
            'nodes': self.nodes
        })

    def start(self):
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Conexão aceita de {addr[0]}:{addr[1]}")
                client_thread = Thread(
                    target=self.handle_client, 
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\nDesligando servidor...")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    import time
    server = BigFileSServer()
    server.start()