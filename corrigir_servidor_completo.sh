#!/bin/bash

echo "🔧 Script Completo para Corrigir o Servidor Locaweb"
echo "=================================================="

# 1. Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Execute este script no diretório raiz do projeto Django"
    exit 1
fi

# 2. Parar processos existentes
echo "🔄 1. Parando processos existentes..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# 3. Instalar dependências
echo "🔄 2. Instalando dependências..."
pip install gunicorn
pip install -r requirements.txt

# 4. Criar arquivo de configuração de produção se não existir
echo "🔄 3. Criando configuração de produção..."
if [ ! -f "sistema_estelar/settings_production.py" ]; then
    echo "Criando settings_production.py..."
    cat > sistema_estelar/settings_production.py << 'EOF'
"""
Configurações para produção na Locaweb
"""
import os
from .settings import *

# Configurações de segurança para produção
DEBUG = False
ALLOWED_HOSTS = ['*']

# Configurações de banco de dados para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Configurações de arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações de sessão
SESSION_COOKIE_SECURE = False  # HTTP para desenvolvimento
CSRF_COOKIE_SECURE = False     # HTTP para desenvolvimento

# Configurações de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configurações de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# Configurações de timezone
TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True

# Configurações de idioma
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True
EOF
    echo "✅ Arquivo settings_production.py criado"
else
    echo "✅ Arquivo settings_production.py já existe"
fi

# 5. Criar arquivo WSGI de produção se não existir
echo "🔄 4. Criando WSGI de produção..."
if [ ! -f "sistema_estelar/wsgi_production.py" ]; then
    echo "Criando wsgi_production.py..."
    cat > sistema_estelar/wsgi_production.py << 'EOF'
"""
WSGI config for sistema_estelar project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings_production')

application = get_wsgi_application()
EOF
    echo "✅ Arquivo wsgi_production.py criado"
else
    echo "✅ Arquivo wsgi_production.py já existe"
fi

# 6. Criar diretórios necessários
echo "🔄 5. Criando diretórios necessários..."
mkdir -p logs
mkdir -p media
mkdir -p staticfiles

# 7. Configurar nginx
echo "🔄 6. Configurando nginx..."
sudo tee /etc/nginx/sites-available/sistema-estelar > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Configurações de arquivos estáticos
    location /static/ {
        alias /var/www/sistema-estelar/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Configurações de arquivos de mídia
    location /media/ {
        alias /var/www/sistema-estelar/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Configurações da aplicação Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Configurações de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
EOF

# Ativar site
sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar e reiniciar nginx
if sudo nginx -t; then
    sudo systemctl restart nginx
    echo "✅ Nginx configurado e reiniciado"
else
    echo "❌ Erro na configuração do nginx"
    exit 1
fi

# 8. Configurar permissões
echo "🔄 7. Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# 9. Coletar arquivos estáticos
echo "🔄 8. Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# 10. Executar migrações
echo "🔄 9. Executando migrações..."
python manage.py migrate --settings=sistema_estelar.settings_production

# 11. Iniciar gunicorn
echo "🔄 10. Iniciando gunicorn..."
# Parar qualquer gunicorn existente
pkill -f gunicorn 2>/dev/null || true

# Iniciar gunicorn em background
nohup gunicorn --bind 0.0.0.0:8000 sistema_estelar.wsgi_production:application > gunicorn.log 2>&1 &

# Aguardar um pouco
sleep 3

# 12. Verificar status
echo "🔄 11. Verificando status..."

# Verificar nginx
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx está ativo"
else
    echo "❌ Nginx não está ativo"
fi

# Verificar gunicorn
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn está rodando"
else
    echo "❌ Gunicorn não está rodando"
    echo "Logs do gunicorn:"
    tail -20 gunicorn.log
fi

# Testar conectividade
echo "🔄 12. Testando conectividade..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    echo "✅ Aplicação respondendo na porta 8000"
else
    echo "❌ Aplicação não está respondendo na porta 8000"
    echo "Tentando iniciar gunicorn manualmente..."
    gunicorn --bind 0.0.0.0:8000 sistema_estelar.wsgi_production:application &
    sleep 2
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    echo "✅ Nginx funcionando"
else
    echo "❌ Nginx não está funcionando"
fi

echo ""
echo "🎉 Configuração concluída!"
echo "========================="
echo "📋 Informações importantes:"
echo "- Aplicação: http://localhost:8000"
echo "- Nginx: http://localhost"
echo "- Logs do gunicorn: tail -f gunicorn.log"
echo "- Logs do nginx: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "🔧 Comandos úteis:"
echo "- Ver processos: ps aux | grep gunicorn"
echo "- Parar gunicorn: pkill -f gunicorn"
echo "- Iniciar gunicorn: gunicorn --bind 0.0.0.0:8000 sistema_estelar.wsgi_production:application"
echo "- Reiniciar nginx: sudo systemctl restart nginx"
echo ""
echo "🌐 Acesse: http://seu-dominio.com.br"



