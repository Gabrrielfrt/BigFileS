import socket
import os
import json
import time
import shutil
from threading import Thread
from utils import (
    send_json, receive_json, 
    send_file, receive_file,
    list_files, create_file_or_dir,
    remove_file_or_dir, validate_path
)
from config import SERVER_HOST, SERVER_PORT, ERROR_MESSAGES

class BigFileSNode:
    def __init__(self, storage_dir='node_storage'):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Cria o diretório root automaticamente
        self.root_dir = os.path.join(self.storage_dir, 'root')
        os.makedirs(self.root_dir, exist_ok=True)
        print(f"Diretório root criado em: {self.root_dir}")
        
        self.node_id = None
        self.node_port = None
        self.node_socket = None
        self.register_with_server()
        self.keep_alive_thread = Thread(target=self.send_keep_alive, daemon=True)
        self.keep_alive_thread.start()


class BigFileSNode:
    def __init__(self, storage_dir='node_storage'):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)
        self.node_id = None
        self.node_port = None
        self.node_socket = None
        self.register_with_server()
        self.keep_alive_thread = Thread(target=self.send_keep_alive, daemon=True)
        self.keep_alive_thread.start()

    def register_with_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((SERVER_HOST, SERVER_PORT))
                send_json(s, {
                    'operation': 'register_node',
                    'host': 'localhost'
                })
                response = receive_json(s)
                
                if response and response.get('status') == 'success':
                    self.node_id = str(response['node_id'])
                    self.node_port = response['node_port']
                    print(f"Nó {self.node_id} registrado com sucesso na porta {self.node_port}")
                else:
                    raise Exception("Falha no registro: " + str(response))
                
            self.node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.node_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.node_socket.bind(('localhost', self.node_port))
            self.node_socket.listen(5)
        except Exception as e:
            print(f"Erro ao registrar nó: {e}")
            raise

    def send_keep_alive(self):
        while True:
            time.sleep(30)  # Envia a cada 30 segundos
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((SERVER_HOST, SERVER_PORT))
                    send_json(s, {
                        'operation': 'keep_alive',
                        'node_id': self.node_id
                    })
            except Exception as e:
                print(f"Erro ao enviar keep-alive: {e}")

    def handle_client(self, client_socket):
        try:
            data = receive_json(client_socket)
            if not data:
                return

            operation = data.get('operation')
            path = data.get('path', '')
            
            try:
                full_path = validate_path(self.storage_dir, path)
            except ValueError as e:
                send_json(client_socket, {'status': 'error', 'message': str(e)})
                return

            response = {}

            if operation == 'ls':
                response = list_files(full_path)
            elif operation == 'mk':
                is_dir = data.get('is_dir', False)
                content = data.get('content')
                response = create_file_or_dir(full_path, is_dir, content)
            elif operation == 'rm':
                response = remove_file_or_dir(full_path)
            elif operation == 'read':
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    response = {'status': 'success', 'content': content}
                except Exception as e:
                    response = {'status': 'error', 'message': str(e)}
            elif operation == 'cp':
                new_path = validate_path(self.storage_dir, data.get('new_path'))
                try:
                    shutil.copy2(full_path, new_path)
                    response = {'status': 'success'}
                except Exception as e:
                    response = {'status': 'error', 'message': str(e)}
            elif operation == 'get':
                try:
                    if send_file(client_socket, full_path):
                        return  # Arquivo enviado com sucesso
                    else:
                        response = {'status': 'error', 'message': 'Falha ao enviar arquivo'}
                except Exception as e:
                    response = {'status': 'error', 'message': str(e)}
            elif operation == 'send':
                file_name = data.get('file_name')
                dest_path = validate_path(self.storage_dir, file_name)
                if receive_file(client_socket, dest_path):
                    response = {'status': 'success'}
                else:
                    response = {'status': 'error', 'message': 'Falha ao receber arquivo'}
            else:
                response = {'status': 'error', 'message': ERROR_MESSAGES['invalid_command']}

            send_json(client_socket, response)

        except Exception as e:
            print(f"Erro ao processar requisição: {e}")
            send_json(client_socket, {'status': 'error', 'message': str(e)})
        finally:
            client_socket.close()

    def start(self):
        try:
            print(f"Nó {self.node_id} pronto para receber conexões...")
            while True:
                client_socket, addr = self.node_socket.accept()
                print(f"Conexão aceita de {addr[0]}:{addr[1]}")
                client_thread = Thread(
                    target=self.handle_client, 
                    args=(client_socket,),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print(f"\nDesligando nó {self.node_id}...")
        except Exception as e:
            print(f"Erro no nó {self.node_id}: {e}")
        finally:
            self.node_socket.close()

if __name__ == "__main__":
    node = BigFileSNode()
    node.start()