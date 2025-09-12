#!/usr/bin/env python3
"""
Script para configurar o servidor Locaweb
Execute este script no servidor Linux
"""

import os
import subprocess
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
    print("🚀 Configurando Sistema Estelar na Locaweb")
    print("=" * 50)
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # 1. Parar processos existentes
    print("\n1️⃣ Parando processos existentes...")
    run_command("pkill -f 'python manage.py runserver'", "Parando servidor de desenvolvimento")
    run_command("pkill -f 'gunicorn'", "Parando gunicorn")
    
    # 2. Instalar dependências
    print("\n2️⃣ Instalando dependências...")
    run_command("pip install gunicorn", "Instalando gunicorn")
    run_command("pip install -r requirements_production.txt", "Instalando dependências de produção")
    
    # 3. Configurar nginx
    print("\n3️⃣ Configurando nginx...")
    
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
    
    # Salvar configuração do nginx
    with open("/tmp/sistema-estelar-nginx.conf", "w") as f:
        f.write(nginx_config)
    
    run_command("sudo cp /tmp/sistema-estelar-nginx.conf /etc/nginx/sites-available/sistema-estelar", 
                "Copiando configuração do nginx")
    
    # Ativar site
    run_command("sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/", 
                "Ativando site no nginx")
    run_command("sudo rm -f /etc/nginx/sites-enabled/default", "Removendo site padrão")
    
    # Testar e reiniciar nginx
    if run_command("sudo nginx -t", "Testando configuração do nginx"):
        run_command("sudo systemctl restart nginx", "Reiniciando nginx")
    else:
        print("❌ Erro na configuração do nginx")
        return False
    
    # 4. Configurar supervisor
    print("\n4️⃣ Configurando supervisor...")
    
    # Instalar supervisor se necessário
    run_command("sudo apt update", "Atualizando pacotes")
    run_command("sudo apt install -y supervisor", "Instalando supervisor")
    
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
    
    # Salvar configuração do supervisor
    with open("/tmp/sistema-estelar-supervisor.conf", "w") as f:
        f.write(supervisor_config)
    
    run_command("sudo cp /tmp/sistema-estelar-supervisor.conf /etc/supervisor/conf.d/sistema-estelar.conf", 
                "Copiando configuração do supervisor")
    
    # Configurar supervisor
    run_command("sudo supervisorctl reread", "Recarregando configuração do supervisor")
    run_command("sudo supervisorctl update", "Atualizando supervisor")
    
    # 5. Configurar permissões
    print("\n5️⃣ Configurando permissões...")
    run_command("sudo chown -R www-data:www-data /var/www/sistema-estelar", "Configurando permissões")
    run_command("sudo chmod -R 755 /var/www/sistema-estelar", "Configurando permissões de execução")
    
    # 6. Coletar arquivos estáticos
    print("\n6️⃣ Coletando arquivos estáticos...")
    run_command("python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production", 
                "Coletando arquivos estáticos")
    
    # 7. Executar migrações
    print("\n7️⃣ Executando migrações...")
    run_command("python manage.py migrate --settings=sistema_estelar.settings_production", 
                "Executando migrações")
    
    # 8. Iniciar aplicação
    print("\n8️⃣ Iniciando aplicação...")
    run_command("sudo supervisorctl start sistema-estelar", "Iniciando aplicação")
    
    # 9. Verificar status
    print("\n9️⃣ Verificando status...")
    
    # Verificar nginx
    if run_command("sudo systemctl is-active nginx", "Verificando status do nginx"):
        print("✅ Nginx está ativo")
    else:
        print("❌ Nginx não está ativo")
    
    # Verificar supervisor
    if run_command("sudo supervisorctl status sistema-estelar", "Verificando status da aplicação"):
        print("✅ Aplicação está rodando")
    else:
        print("❌ Aplicação não está rodando")
    
    # Testar conectividade
    print("\n🔟 Testando conectividade...")
    run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000", "Testando porta 8000")
    run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost", "Testando nginx")
    
    print("\n🎉 Configuração concluída!")
    print("=" * 50)
    print("📋 Próximos passos:")
    print("1. Configure seu domínio no arquivo /etc/nginx/sites-available/sistema-estelar")
    print("2. Acesse: http://seu-dominio.com.br")
    print("3. Monitore os logs: sudo tail -f /var/log/supervisor/sistema-estelar.log")
    print("\n🔧 Comandos úteis:")
    print("- Ver status: sudo supervisorctl status sistema-estelar")
    print("- Reiniciar app: sudo supervisorctl restart sistema-estelar")
    print("- Ver logs: sudo tail -f /var/log/supervisor/sistema-estelar.log")
    print("- Ver logs nginx: sudo tail -f /var/log/nginx/error.log")

if __name__ == "__main__":
    main()





