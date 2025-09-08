#!/usr/bin/env python3
"""
Script de Deploy Automatizado para Locaweb
Sistema Estelar
"""

import os
import subprocess
import sys
from pathlib import Path

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

def check_requirements():
    """Verifica se os requisitos estão instalados"""
    print("🔍 Verificando requisitos...")
    
    requirements = [
        ("nginx", "nginx -v"),
        ("python3", "python3 --version"),
        ("pip", "pip --version"),
    ]
    
    for name, command in requirements:
        if not run_command(command, f"Verificando {name}"):
            print(f"❌ {name} não está instalado ou não está no PATH")
            return False
    
    return True

def setup_nginx():
    """Configura o nginx"""
    print("\n🔧 Configurando nginx...")
    
    # Criar diretório se não existir
    run_command("sudo mkdir -p /etc/nginx/sites-available", "Criando diretório sites-available")
    run_command("sudo mkdir -p /etc/nginx/sites-enabled", "Criando diretório sites-enabled")
    
    # Configuração do nginx
    nginx_config = """server {
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
}"""
    
    # Salvar configuração
    with open("/tmp/sistema-estelar-nginx.conf", "w") as f:
        f.write(nginx_config)
    
    # Copiar para o nginx
    run_command("sudo cp /tmp/sistema-estelar-nginx.conf /etc/nginx/sites-available/sistema-estelar", 
                "Copiando configuração do nginx")
    
    # Ativar site
    run_command("sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/", 
                "Ativando site no nginx")
    
    # Remover site padrão
    run_command("sudo rm -f /etc/nginx/sites-enabled/default", "Removendo site padrão")
    
    # Testar configuração
    if run_command("sudo nginx -t", "Testando configuração do nginx"):
        run_command("sudo systemctl restart nginx", "Reiniciando nginx")
        return True
    
    return False

def setup_django():
    """Configura o Django para produção"""
    print("\n🔧 Configurando Django...")
    
    # Criar diretórios necessários
    run_command("mkdir -p logs", "Criando diretório de logs")
    run_command("mkdir -p media", "Criando diretório de mídia")
    
    # Instalar dependências
    run_command("pip install -r requirements_production.txt", "Instalando dependências de produção")
    
    # Coletar arquivos estáticos
    run_command("python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production", 
                "Coletando arquivos estáticos")
    
    # Executar migrações
    run_command("python manage.py migrate --settings=sistema_estelar.settings_production", 
                "Executando migrações")
    
    # Configurar permissões
    run_command("sudo chown -R www-data:www-data /var/www/sistema-estelar", "Configurando permissões")
    run_command("sudo chmod -R 755 /var/www/sistema-estelar", "Configurando permissões de execução")
    
    return True

def setup_supervisor():
    """Configura o supervisor para manter o gunicorn rodando"""
    print("\n🔧 Configurando supervisor...")
    
    # Instalar supervisor
    run_command("sudo apt update", "Atualizando pacotes")
    run_command("sudo apt install -y supervisor", "Instalando supervisor")
    
    # Configuração do supervisor
    supervisor_config = """[program:sistema-estelar]
command=/var/www/sistema-estelar/venv/bin/gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
directory=/var/www/sistema-estelar
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sistema-estelar.log
stderr_logfile=/var/log/supervisor/sistema-estelar_error.log
"""
    
    # Salvar configuração
    with open("/tmp/sistema-estelar-supervisor.conf", "w") as f:
        f.write(supervisor_config)
    
    # Copiar para o supervisor
    run_command("sudo cp /tmp/sistema-estelar-supervisor.conf /etc/supervisor/conf.d/sistema-estelar.conf", 
                "Copiando configuração do supervisor")
    
    # Recarregar supervisor
    run_command("sudo supervisorctl reread", "Recarregando configuração do supervisor")
    run_command("sudo supervisorctl update", "Atualizando supervisor")
    run_command("sudo supervisorctl start sistema-estelar", "Iniciando aplicação")
    
    return True

def test_deployment():
    """Testa o deployment"""
    print("\n🧪 Testando deployment...")
    
    # Testar nginx
    if run_command("sudo systemctl is-active nginx", "Verificando status do nginx"):
        print("✅ Nginx está ativo")
    else:
        print("❌ Nginx não está ativo")
        return False
    
    # Testar supervisor
    if run_command("sudo supervisorctl status sistema-estelar", "Verificando status da aplicação"):
        print("✅ Aplicação está rodando")
    else:
        print("❌ Aplicação não está rodando")
        return False
    
    # Testar conectividade
    if run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000", "Testando conectividade"):
        print("✅ Aplicação está respondendo")
    else:
        print("❌ Aplicação não está respondendo")
        return False
    
    return True

def main():
    """Função principal"""
    print("🚀 Iniciando deploy do Sistema Estelar na Locaweb")
    print("=" * 50)
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # Verificar requisitos
    if not check_requirements():
        print("❌ Requisitos não atendidos")
        sys.exit(1)
    
    # Configurar nginx
    if not setup_nginx():
        print("❌ Falha na configuração do nginx")
        sys.exit(1)
    
    # Configurar Django
    if not setup_django():
        print("❌ Falha na configuração do Django")
        sys.exit(1)
    
    # Configurar supervisor
    if not setup_supervisor():
        print("❌ Falha na configuração do supervisor")
        sys.exit(1)
    
    # Testar deployment
    if not test_deployment():
        print("❌ Falha no teste do deployment")
        sys.exit(1)
    
    print("\n🎉 Deploy concluído com sucesso!")
    print("=" * 50)
    print("📋 Próximos passos:")
    print("1. Configure seu domínio no arquivo /etc/nginx/sites-available/sistema-estelar")
    print("2. Configure SSL/HTTPS se necessário")
    print("3. Configure backup automático do banco de dados")
    print("4. Monitore os logs em /var/log/supervisor/sistema-estelar.log")

if __name__ == "__main__":
    main()