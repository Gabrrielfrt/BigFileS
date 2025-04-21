import socket
import os
from config import SERVER_HOST, SERVER_PORT

class BigFileSClient:
    def __init__(self):
        self.nodes = {}
        try:
            self.connect_to_server()
            self.update_nodes()
        except Exception as e:
            print(f"Erro ao iniciar cliente: {e}")
            exit(1)

    def connect_to_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((SERVER_HOST, SERVER_PORT))
            print(f"Conectado ao servidor em {SERVER_HOST}:{SERVER_PORT}")
        except socket.error as e:
            print(f"Erro de conexão: Verifique se o servidor está rodando e o IP está correto")
            raise

    def update_nodes(self):
        try:
            self.server_socket.send("GET_NODES".encode())
            response = self.server_socket.recv(1024).decode()
            self.nodes = eval(response)
            print("Nós disponíveis:", self.nodes)
        except Exception as e:
            print(f"Erro ao obter nós: {e}")
            self.nodes = {}

    def send_command(self, node_id, command):
        try:
            if node_id not in self.nodes:
                print(f"Erro: Nó {node_id} não encontrado")
                return None

            node = self.nodes[node_id]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # Timeout de 5 segundos
            s.connect((node['host'], node['port']))
            s.send(command.encode())
            response = s.recv(1024)
            s.close()
            return response
        except socket.timeout:
            print(f"Timeout: Nó {node_id} não respondeu")
            return None
        except Exception as e:
            print(f"Erro ao enviar comando: {e}")
            return None

    def interactive_mode(self):
        print("\n=== BigFileS Client (Digite 'help' para ajuda) ===")
        
        while True:
            try:
                cmd_input = input("> ").strip()
                if not cmd_input:
                    continue
                    
                cmd = cmd_input.split()
                cmd_name = cmd[0].lower()

                if cmd_name == 'exit':
                    break
                    
                elif cmd_name == 'help':
                    self.show_help()
                    
                elif cmd_name == 'nodes':
                    try:
                        self.update_nodes()
                    except Exception as e:
                        print(f"Erro ao atualizar nós: {e}")
                        
                elif cmd_name in ['mk', 'ls', 'read', 'rm', 'cp', 'get', 'send']:
                    self.handle_operation(cmd_name, cmd)
                    
                else:
                    print(f"Comando desconhecido: {cmd_name}")

            except KeyboardInterrupt:
                print("\nUse 'exit' para sair")
            except Exception as e:
                print(f"Erro: {e}")


    def show_help(self):
        print("\nComandos disponíveis:")
        print("  mk <nó> <path> [conteúdo|DIR] - Criar arquivo (com conteúdo) ou diretório")
        print("  ls <nó> <path> - Listar arquivos")
        print("  read <nó> <path> - Ler arquivo")
        print("  cp <nó> <origem> <destino> - Copiar arquivo")
        print("  rm <nó> <path> - Remover arquivo/diretório")
        print("  get <nó> <remoto> [local] - Baixar arquivo")
        print("  nodes - Listar nós disponíveis")
        print("  exit - Sair")

    def handle_operation(self, operation, cmd_parts):
        try:
            if len(cmd_parts) < 3:
                raise ValueError(f"Faltam argumentos para '{operation}'")

            node_id = int(cmd_parts[1])
            path = cmd_parts[2]

            if operation == 'mk':
                #formato: mk <nó> <path> [conteúdo|DIR]
                is_dir = len(cmd_parts) > 3 and cmd_parts[3].upper() == 'DIR'
                content = ' '.join(cmd_parts[3:]) if not is_dir and len(cmd_parts) > 3 else ''

                command = f"MK|{path}|{'DIR' if is_dir else 'FILE'}|{content}"
                response = self.send_command(node_id, command)
                print(response.decode() if response else "Sem resposta")

            elif operation == 'ls':
                command = f"LS|{path}"
                response = self.send_command(node_id, command)
                if response:
                    print(eval(response.decode()))
                else:
                    print("Falha ao listar arquivos")

            elif operation == 'read':
                command = f"READ|{path}"
                response = self.send_command(node_id, command)
                print(response.decode() if response else "Falha ao ler arquivo ou o arquivo está vazio")

            elif operation == 'cp':
                if len(cmd_parts) < 4:
                    raise ValueError("Falta caminho de destino")
                dest = cmd_parts[3]
                command = f"CP|{path}|{dest}"
                response = self.send_command(node_id, command)
                print(response.decode() if response else "Falha ao copiar")

            elif operation == 'rm':
                command = f"RM|{path}"
                response = self.send_command(node_id, command)
                print(response.decode() if response else "Falha ao remover")

            elif operation == 'get':
                local_path = cmd_parts[3] if len(cmd_parts) > 3 else os.path.basename(path)
                command = f"GET|{path}"
                response = self.send_command(node_id, command)
                if response:
                    with open(local_path, 'wb') as f:
                        f.write(response)
                    print(f"Arquivo salvo como {local_path}")
                else:
                    print("Falha ao baixar arquivo ou o arquivo está vazio")

        except ValueError as e:
            print(f"Erro de sintaxe: {e}")
        except FileNotFoundError as e:
            print(f"Erro: {e}")
        except Exception as e:
            print(f"Erro ao executar operação: {e}")

if __name__ == "__main__":
    try:
        client = BigFileSClient()
        client.interactive_mode()
    except Exception as e:
        print(f"Erro fatal: {e}")
    finally:
        print("Cliente encerrado")