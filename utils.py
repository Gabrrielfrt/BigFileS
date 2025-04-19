import json
import os
import shutil
from config import BUFFER_SIZE, ENCODING, MAX_FILE_SIZE



def send_json(socket, data):
    """Envia dados JSON através de um socket."""
    try:
        json_data = json.dumps(data)
        socket.send(json_data.encode(ENCODING))
    except Exception as e:
        print(f"Erro ao enviar JSON: {e}")

def receive_json(socket):
    """Recebe dados JSON de um socket."""
    try:
        data = socket.recv(BUFFER_SIZE).decode(ENCODING)
        return json.loads(data)
    except Exception as e:
        print(f"Erro ao receber JSON: {e}")
        return None

def send_file(socket, file_path):
    """Envia um arquivo através de um socket."""
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"Arquivo muito grande (limite: {MAX_FILE_SIZE/1024/1024}MB)")

        # Primeiro envia o tamanho do arquivo
        socket.send(str(file_size).encode(ENCODING))
        socket.recv(BUFFER_SIZE)  # Aguarda confirmação

        # Depois envia o arquivo
        with open(file_path, 'rb') as f:
            while True:
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    break
                socket.send(bytes_read)
        return True
    except Exception as e:
        print(f"Erro ao enviar arquivo: {e}")
        return False

def receive_file(socket, file_path):
    """Recebe um arquivo de um socket e salva no caminho especificado."""
    try:
        # Primeiro recebe o tamanho do arquivo
        file_size = int(socket.recv(BUFFER_SIZE).decode(ENCODING))
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"Arquivo muito grande (limite: {MAX_FILE_SIZE/1024/1024}MB)")
        
        socket.send(b'OK')  # Confirmação
        
        # Depois recebe o arquivo
        received_size = 0
        with open(file_path, 'wb') as f:
            while received_size < file_size:
                bytes_read = socket.recv(min(BUFFER_SIZE, file_size - received_size))
                if not bytes_read:
                    break
                f.write(bytes_read)
                received_size += len(bytes_read)
        return received_size == file_size
    except Exception as e:
        print(f"Erro ao receber arquivo: {e}")
        return False

def list_files(directory):
    """Lista todos os arquivos em um diretório."""
    try:
        files = []
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            files.append({
                'name': item,
                'is_dir': os.path.isdir(full_path),
                'size': os.path.getsize(full_path) if not os.path.isdir(full_path) else 0
            })
        return {'status': 'success', 'files': files}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def create_file_or_dir(path, is_dir=False, content=None):
    """Cria um arquivo ou diretório."""
    try:
        if is_dir:
            os.makedirs(path, exist_ok=True)
        else:
            with open(path, 'w') as f:
                if content:
                    f.write(content)
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def remove_file_or_dir(path):
    """Remove um arquivo ou diretório."""
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def validate_path(base_dir, path):
    """Valida se o caminho está dentro do diretório base."""
    full_path = os.path.abspath(os.path.join(base_dir, path))
    if not full_path.startswith(os.path.abspath(base_dir)):
        raise ValueError("Tentativa de acesso a caminho fora do diretório base")
    return full_path