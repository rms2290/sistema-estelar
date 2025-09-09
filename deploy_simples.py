#!/usr/bin/env python3
"""
Script de Deploy Simples para Locaweb
Sistema Estelar - Deploy Automatizado
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
    print("🚀 Deploy Simples do Sistema Estelar na Locaweb")
    print("=" * 60)
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # 1. Fazer commit das mudanças
    print("\n1️⃣ Fazendo commit das mudanças...")
    run_command("git add .", "Adicionando arquivos ao git")
    run_command("git commit -m 'Deploy: Correções do menu e configurações de produção'", "Fazendo commit")
    
    # 2. Fazer push para o repositório
    print("\n2️⃣ Enviando para o repositório...")
    run_command("git push origin main", "Enviando para o GitHub")
    
    # 3. Criar script de deploy para o servidor
    print("\n3️⃣ Criando script de deploy para o servidor...")
    
    deploy_script = """#!/bin/bash

echo "🚀 Deploy do Sistema Estelar na Locaweb"
echo "======================================"

# Atualizar código
echo "1. Atualizando código..."
cd /var/www/sistema-estelar
git pull origin main

# Parar processos existentes
echo "2. Parando processos existentes..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# Instalar dependências
echo "3. Instalando dependências..."
pip install gunicorn
pip install -r requirements.txt

# Coletar arquivos estáticos
echo "4. Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# Executar migrações
echo "5. Executando migrações..."
python manage.py migrate --settings=sistema_estelar.settings_production

# Configurar nginx
echo "6. Configurando nginx..."
sudo tee /etc/nginx/sites-available/sistema-estelar > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Configurações de arquivos estáticos
    location /static/ {
        alias /var/www/sistema-estelar/staticfiles/;
        expires 1h;
        add_header Cache-Control "public, no-cache";
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
echo "7. Ativando site no nginx..."
sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar e reiniciar nginx
echo "8. Testando e reiniciando nginx..."
sudo nginx -t && sudo systemctl restart nginx

# Configurar permissões
echo "9. Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# Iniciar gunicorn
echo "10. Iniciando gunicorn..."
nohup gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 sistema_estelar.wsgi_production:application > gunicorn.log 2>&1 &

# Aguardar e verificar
sleep 5

echo "11. Verificando status..."
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn está rodando"
else
    echo "❌ Gunicorn não está rodando, tentando iniciar manualmente..."
    gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 sistema_estelar.wsgi_production:application &
fi

# Testar aplicação
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
echo "🎉 Deploy concluído!"
echo "Acesse: http://seu-dominio.com.br"
echo "Logs: tail -f gunicorn.log"
echo "Status: ps aux | grep gunicorn"
"""
    
    # Salvar script
    with open("deploy_servidor.sh", "w") as f:
        f.write(deploy_script)
    
    print("✅ Script de deploy criado: deploy_servidor.sh")
    
    # 4. Instruções para o usuário
    print("\n4️⃣ Instruções para executar no servidor Locaweb:")
    print("=" * 60)
    print("1. Conecte no servidor Locaweb via SSH")
    print("2. Execute: cd /var/www/sistema-estelar")
    print("3. Execute: git pull origin main")
    print("4. Execute: chmod +x deploy_servidor.sh")
    print("5. Execute: ./deploy_servidor.sh")
    print("")
    print("OU execute os comandos individuais:")
    print("wget https://raw.githubusercontent.com/seu-usuario/sistema-estelar/main/deploy_servidor.sh")
    print("chmod +x deploy_servidor.sh")
    print("./deploy_servidor.sh")
    
    print("\n🎉 Preparação do deploy concluída!")
    print("Agora execute o script no servidor Locaweb.")

if __name__ == "__main__":
    main()
