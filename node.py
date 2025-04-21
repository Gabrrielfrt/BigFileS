import socket
import os
import shutil
import threading
from config import SERVER_HOST, SERVER_PORT

class BigFileSNode:
    def __init__(self):
        self.storage = 'node_storage'
        self.root_dir = os.path.join(self.storage, 'root')  # Caminho para o diretório root
        
        # Cria a estrutura de diretórios
        os.makedirs(self.root_dir, exist_ok=True)  # Cria node_storage/root
        print(f"Diretório root criado em: {os.path.abspath(self.root_dir)}")
        
        self.register_node()

    def register_node(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((SERVER_HOST, SERVER_PORT))
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            s.send(f"REGISTER|{local_ip}".encode())
            
            response = s.recv(1024).decode().split('|')
            if response[0] == 'OK':
                self.node_id = response[1]
                self.port = int(response[2])
                print(f"Nó {self.node_id} registrado na porta {self.port}")
                self.start_server()
        finally:
            s.close()

    def handle_operation(self, conn):
        try:
            data = conn.recv(1024).decode().split('|')
            operation = data[0]
            relative_path = data[1].lstrip('/')
            full_path = os.path.join(self.root_dir, relative_path)
            
            # Todas as operações usam caminhos relativos ao root_dir
            relative_path = data[1].lstrip('/')  # Remove barras iniciais
            full_path = os.path.join(self.root_dir, relative_path)
            
            # Verifica se o caminho está dentro do diretório root
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.root_dir)):
                conn.send("ERRO|Acesso fora do diretório root".encode())
                return

            if operation == 'MK':
                #formato: MK|path|TYPE|content
                obj_type = data[2]  # DIR ou FILE
                content = data[3] if len(data) > 3 else ''

                if obj_type == 'DIR':
                    os.makedirs(full_path, exist_ok=True)
                    conn.send("OK|Diretório criado".encode())
                else:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, 'w') as f:
                        f.write(content)
                    conn.send(f"OK|Arquivo criado com {len(content)} bytes".encode())

            elif operation == 'LS':
                files = os.listdir(full_path)
                conn.send(str(files).encode())

            elif operation == 'READ':
                with open(full_path, 'r') as f:
                    conn.send(f.read().encode())

            elif operation == 'CP':
                new_relative_path = data[2].lstrip('/')
                new_full_path = os.path.join(self.root_dir, new_relative_path)
                shutil.copy2(full_path, new_full_path)
                conn.send("OK".encode())

            elif operation == 'RM':
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
                conn.send("OK".encode())

            elif operation == 'GET':
                with open(full_path, 'rb') as f:
                    conn.send(f.read())

            elif operation == 'SEND':
                with open(full_path, 'wb') as f:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        f.write(data)
                conn.send("OK".encode())

        except Exception as e:
            conn.send(f"ERRO|{str(e)}".encode())
        finally:
            conn.close()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', self.port))
                s.listen(5)
                print(f"Nó {self.node_id} respondendo em {socket.gethostbyname(socket.gethostname())}:{self.port}")
                print(f"Armazenamento root em: {os.path.abspath(self.root_dir)}")
                
                while True:
                    conn, addr = s.accept()
                    print(f"Conexão recebida de {addr}")
                    threading.Thread(target=self.handle_operation, args=(conn,)).start()
            except Exception as e:
                print(f"Falha no servidor do nó: {str(e)}")
                exit(1)

if __name__ == "__main__":
    print("Iniciando nó...")
    node = BigFileSNode()