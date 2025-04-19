# Configurações compartilhadas
import socket

# Configurações de rede
SERVER_HOST = 'localhost'
SERVER_PORT = 5000
NODE_PORT_START = 5001

# Protocolo
BUFFER_SIZE = 4096
ENCODING = 'utf-8'
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Operações suportadas
OPERATIONS = {
    'mk': 'Criar arquivo/diretório',
    'ls': 'Listar arquivos',
    'read': 'Ler arquivo',
    'cp': 'Copiar arquivo',
    'get': 'Baixar arquivo',
    'rm': 'Remover arquivo/diretório',
    'send': 'Enviar arquivo para nó',
    'nodes': 'Listar nós disponíveis'
}

# Mensagens de erro
ERROR_MESSAGES = {
    'node_not_found': 'Nó não encontrado. Use o comando "nodes" para listar nós disponíveis.',
    'invalid_command': 'Comando inválido. Digite "help" para ver as operações disponíveis.',
    'missing_args': 'Argumentos insuficientes para o comando.'
}