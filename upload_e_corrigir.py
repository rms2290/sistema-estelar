#!/usr/bin/env python3
"""
Script para fazer upload e corrigir o servidor Locaweb
Execute este script no Windows
"""

import subprocess
import os
import sys

def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"\n🔄 {description}")
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Sucesso: {description}")
        if result.stdout:
            print(f"Saída: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {description}")
        print(f"Código de erro: {e.returncode}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False

def main():
    print("🚀 Upload e Correção Automática do Servidor Locaweb")
    print("=" * 60)
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # 1. Fazer commit das mudanças
    print("\n1️⃣ Fazendo commit das mudanças...")
    run_command("git add .", "Adicionando arquivos ao git")
    run_command("git commit -m 'Corrigir configuração do servidor - adicionar arquivos de produção'", "Fazendo commit")
    
    # 2. Fazer push para o repositório
    print("\n2️⃣ Enviando para o repositório...")
    run_command("git push", "Enviando para o GitHub")
    
    # 3. Criar script de correção
    print("\n3️⃣ Criando script de correção...")
    
    script_correcao = """#!/bin/bash

echo "🔧 Corrigindo servidor Locaweb automaticamente"
echo "=============================================="

# Atualizar código
echo "1. Atualizando código..."
cd /var/www/sistema-estelar
git pull

# Parar processos
echo "2. Parando processos existentes..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# Instalar dependências
echo "3. Instalando dependências..."
pip install gunicorn
pip install -r requirements.txt

# Criar settings_production.py se não existir
echo "4. Criando configuração de produção..."
if [ ! -f "sistema_estelar/settings_production.py" ]; then
    cat > sistema_estelar/settings_production.py << 'EOF'
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True
EOF
fi

# Criar wsgi_production.py se não existir
echo "5. Criando WSGI de produção..."
if [ ! -f "sistema_estelar/wsgi_production.py" ]; then
    cat > sistema_estelar/wsgi_production.py << 'EOF'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings_production')
application = get_wsgi_application()
EOF
fi

# Configurar nginx
echo "6. Configurando nginx..."
sudo tee /etc/nginx/sites-available/sistema-estelar > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    location /static/ {
        alias /var/www/sistema-estelar/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/sistema-estelar/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
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
sudo nginx -t && sudo systemctl restart nginx

# Configurar permissões
echo "7. Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# Coletar arquivos estáticos
echo "8. Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# Executar migrações
echo "9. Executando migrações..."
python manage.py migrate --settings=sistema_estelar.settings_production

# Iniciar gunicorn
echo "10. Iniciando gunicorn..."
pkill -f gunicorn 2>/dev/null || true
nohup gunicorn --bind 0.0.0.0:8000 sistema_estelar.wsgi_production:application > gunicorn.log 2>&1 &

# Aguardar e verificar
sleep 3

echo "11. Verificando status..."
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn está rodando"
else
    echo "❌ Gunicorn não está rodando, tentando iniciar manualmente..."
    gunicorn --bind 0.0.0.0:8000 sistema_estelar.wsgi_production:application &
fi

if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Aplicação funcionando"
else
    echo "❌ Aplicação com problemas"
fi

if curl -s http://localhost > /dev/null; then
    echo "✅ Nginx funcionando"
else
    echo "❌ Nginx com problemas"
fi

echo ""
echo "🎉 Correção concluída!"
echo "Acesse: http://seu-dominio.com.br"
echo "Logs: tail -f gunicorn.log"
"""
    
    # Salvar script
    with open("corrigir_servidor.sh", "w") as f:
        f.write(script_correcao)
    
    print("✅ Script de correção criado: corrigir_servidor.sh")
    
    # 4. Instruções para o usuário
    print("\n4️⃣ Instruções para executar no servidor:")
    print("=" * 50)
    print("1. Conecte no servidor Locaweb")
    print("2. Execute: cd /var/www/sistema-estelar")
    print("3. Execute: git pull")
    print("4. Execute: chmod +x corrigir_servidor.sh")
    print("5. Execute: ./corrigir_servidor.sh")
    print("")
    print("OU execute os comandos individuais:")
    print("wget https://raw.githubusercontent.com/rms2290/sistema-estelar/main/corrigir_servidor_completo.sh")
    print("chmod +x corrigir_servidor_completo.sh")
    print("./corrigir_servidor_completo.sh")
    
    print("\n🎉 Upload concluído! Agora execute no servidor.")

if __name__ == "__main__":
    main()




