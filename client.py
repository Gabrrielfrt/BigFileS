import socket
import os
import sys
from utils import send_json, receive_json, send_file, receive_file
from config import (
    SERVER_HOST, 
    SERVER_PORT, 
    OPERATIONS, 
    ERROR_MESSAGES,
    MAX_FILE_SIZE
)

class BigFileSClient:
    def __init__(self):
        self.server_socket = None
        self.nodes = {}
        self.connect_to_server()
        self.update_nodes()

    def connect_to_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"Conectado ao servidor em {SERVER_HOST}:{SERVER_PORT}")
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            sys.exit(1)

    def update_nodes(self):
        """Atualiza a lista de nós disponíveis"""
        try:
            send_json(self.server_socket, {'operation': 'get_nodes'})
            response = receive_json(self.server_socket)
            if response and response['status'] == 'success':
                self.nodes = response['nodes']
                print(f"Lista de nós atualizada. Total: {len(self.nodes)}")
            else:
                print("Erro ao obter nós:", response.get('message', 'Desconhecido'))
        except Exception as e:
            print(f"Erro ao atualizar nós: {e}")

    def show_available_nodes(self):
        """Mostra os nós disponíveis"""
        if not self.nodes:
            print("Nenhum nó disponível.")
            return
        
        print("\nNós disponíveis:")
        for node_id, info in self.nodes.items():
            print(f"  Nó {node_id}: {info['host']}:{info['port']} - {info['status']}")

    def execute_operation(self, node_id, operation, **kwargs):
        node_id = str(node_id)  # Garante que o ID seja string
        
        if node_id not in self.nodes:
            print(ERROR_MESSAGES['node_not_found'])
            self.show_available_nodes()
            return None

        node = self.nodes[node_id]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # Timeout de 10 segundos
                s.connect((node['host'], node['port']))
                data = {'operation': operation, **kwargs}
                
                if operation == 'send':
                    file_path = kwargs.get('file_path')
                    if not os.path.exists(file_path):
                        print(f"Arquivo não encontrado: {file_path}")
                        return {'status': 'error', 'message': 'Arquivo não encontrado'}
                    
                    if os.path.getsize(file_path) > MAX_FILE_SIZE:
                        print(f"Arquivo muito grande (limite: {MAX_FILE_SIZE/1024/1024}MB)")
                        return {'status': 'error', 'message': 'Arquivo muito grande'}
                    
                    send_json(s, data)
                    if send_file(s, file_path):
                        return receive_json(s)
                    else:
                        return {'status': 'error', 'message': 'Falha ao enviar arquivo'}
                
                elif operation == 'get':
                    send_json(s, data)
                    file_name = os.path.basename(kwargs.get('path', 'file'))
                    if receive_file(s, file_name):
                        print(f"Arquivo recebido: {file_name}")
                        return {'status': 'success'}
                    else:
                        return {'status': 'error', 'message': 'Falha ao receber arquivo'}
                
                else:
                    send_json(s, data)
                    return receive_json(s)
        except socket.timeout:
            print("Tempo limite excedido ao tentar conectar com o nó.")
            return {'status': 'error', 'message': 'Timeout'}
        except Exception as e:
            print(f"Erro durante a operação: {e}")
            return {'status': 'error', 'message': str(e)}

    def interactive_mode(self):
        print("\nBem-vindo ao BigFileS Client")
        print("Operações disponíveis:")
        for cmd, desc in OPERATIONS.items():
            print(f"  {cmd}: {desc}")
        print("  help: Mostrar esta ajuda")
        print("  exit: Sair")

        while True:
            try:
                command = input("\n> ").strip().split()
                if not command:
                    continue

                cmd = command[0].lower()
                if cmd == 'exit':
                    break
                elif cmd == 'help':
                    print("\nAjuda:")
                    for cmd, desc in OPERATIONS.items():
                        print(f"  {cmd}: {desc}")
                    print("  exit: Sair")
                elif cmd == 'nodes':
                    self.update_nodes()
                    self.show_available_nodes()
                elif cmd in OPERATIONS:
                    try:
                        node_id = command[1]
                        if cmd == 'mk':
                            path = command[2]
                            is_dir = len(command) > 3 and command[3] == 'dir'
                            result = self.execute_operation(node_id, cmd, path=path, is_dir=is_dir)
                        elif cmd == 'ls':
                            path = command[2] if len(command) > 2 else ''
                            result = self.execute_operation(node_id, cmd, path=path)
                        elif cmd == 'read':
                            path = command[2]
                            result = self.execute_operation(node_id, cmd, path=path)
                        elif cmd == 'cp':
                            src_path = command[2]
                            dest_path = command[3]
                            result = self.execute_operation(node_id, cmd, path=src_path, new_path=dest_path)
                        elif cmd == 'rm':
                            path = command[2]
                            result = self.execute_operation(node_id, cmd, path=path)
                        elif cmd == 'get':
                            node_path = command[2]
                            local_name = command[3] if len(command) > 3 else os.path.basename(node_path)
                            result = self.execute_operation(node_id, cmd, path=node_path, file_name=local_name)
                        elif cmd == 'send':
                            local_path = command[2]
                            node_path = command[3] if len(command) > 3 else os.path.basename(local_path)
                            result = self.execute_operation(
                                node_id, cmd, 
                                file_name=node_path,
                                file_path=local_path
                            )

                        if result:
                            if result['status'] == 'success':
                                if cmd == 'ls' and 'files' in result:
                                    print("\nArquivos:")
                                    for f in result['files']:
                                        print(f"  {f['name']} {'(dir)' if f['is_dir'] else ''} ({f['size']} bytes)")
                                elif cmd == 'read' and 'content' in result:
                                    print("\nConteúdo:")
                                    print(result['content'])
                                else:
                                    print("\nOperação realizada com sucesso")
                            else:
                                print(f"\nErro: {result.get('message', 'Desconhecido')}")
                    except IndexError:
                        print(f"\nUso incorreto. Formato: {cmd} <node_id> <path> [args...]")
                        print(f"Exemplo: {cmd} 1 /path/to/file")
                        if cmd == 'send':
                            print(f"Para enviar arquivo: send <node_id> <local_path> [remote_path]")
                        elif cmd == 'get':
                            print(f"Para baixar arquivo: get <node_id> <remote_path> [local_name]")
                else:
                    print(ERROR_MESSAGES['invalid_command'])
            except KeyboardInterrupt:
                print("\nUse 'exit' para sair")
            except Exception as e:
                print(f"\nErro: {e}")

if __name__ == "__main__":
    try:
        client = BigFileSClient()
        client.interactive_mode()
    except KeyboardInterrupt:
        print("\nCliente encerrado.")
    finally:
        print("Conexões encerradas.")