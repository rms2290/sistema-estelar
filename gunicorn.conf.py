"""
Configuração OTIMIZADA do Gunicorn para produção com baixo consumo de memória
"""
import multiprocessing
import os

# Configurações básicas
bind = "0.0.0.0:8000"

# OTIMIZAÇÃO: Reduzir número de workers para economizar memória
# Para servidores com pouca RAM (1-2GB): usar 1 worker
# Para servidores com mais RAM (2-4GB): usar 2 workers
workers = 1  # Reduzido para 1 worker para economizar memória

worker_class = "sync"
worker_connections = 1000

# OTIMIZAÇÃO: Reduzir max_requests para liberar memória mais frequentemente
max_requests = 300  # Reduzido para reiniciar workers mais frequentemente e liberar memória
max_requests_jitter = 30  # Reduzido para variação menor

timeout = 30
keepalive = 2

# Configurações de logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# OTIMIZAÇÃO: Desabilitar preload_app para economizar memória
preload_app = False  # Mudado de True para False

daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# OTIMIZAÇÃO: Usar /tmp em vez de /dev/shm para economizar memória
worker_tmp_dir = "/tmp"

# OTIMIZAÇÃO: Configurações de memória
worker_memory_limit = 200 * 1024 * 1024  # 200MB por worker
