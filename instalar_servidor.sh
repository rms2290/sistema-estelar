#!/bin/bash

echo "🚀 Instalando Sistema Estelar na Locaweb"
echo "========================================"

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Execute este script no diretório raiz do projeto Django"
    exit 1
fi

# 1. Parar processos existentes
echo "🔄 Parando processos existentes..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# 2. Instalar dependências
echo "🔄 Instalando dependências..."
pip install gunicorn
pip install -r requirements_production.txt

# 3. Configurar nginx
echo "🔄 Configurando nginx..."

# Criar arquivo de configuração do nginx
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

# Ativar site no nginx
sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar e reiniciar nginx
echo "🔄 Testando configuração do nginx..."
if sudo nginx -t; then
    echo "✅ Configuração do nginx OK"
    sudo systemctl restart nginx
    echo "✅ Nginx reiniciado"
else
    echo "❌ Erro na configuração do nginx"
    exit 1
fi

# 4. Configurar supervisor
echo "🔄 Configurando supervisor..."

# Instalar supervisor se não estiver instalado
if ! command -v supervisorctl &> /dev/null; then
    sudo apt update
    sudo apt install -y supervisor
fi

# Criar arquivo de configuração do supervisor
sudo tee /etc/supervisor/conf.d/sistema-estelar.conf > /dev/null << 'EOF'
[program:sistema-estelar]
command=/var/www/sistema-estelar/venv/bin/gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
directory=/var/www/sistema-estelar
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sistema-estelar.log
stderr_logfile=/var/log/supervisor/sistema-estelar_error.log
EOF

# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update

# 5. Configurar permissões
echo "🔄 Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# 6. Coletar arquivos estáticos
echo "🔄 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# 7. Executar migrações
echo "🔄 Executando migrações..."
python manage.py migrate --settings=sistema_estelar.settings_production

# 8. Iniciar aplicação
echo "🔄 Iniciando aplicação..."
sudo supervisorctl start sistema-estelar

# 9. Verificar status
echo "🔄 Verificando status..."

# Verificar nginx
if sudo systemctl is-active --quiet nginx; then
    echo "✅ Nginx está ativo"
else
    echo "❌ Nginx não está ativo"
fi

# Verificar supervisor
if sudo supervisorctl status sistema-estelar | grep -q "RUNNING"; then
    echo "✅ Aplicação está rodando"
else
    echo "❌ Aplicação não está rodando"
    echo "Logs do supervisor:"
    sudo supervisorctl status sistema-estelar
fi

# Testar conectividade
echo "🔄 Testando conectividade..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    echo "✅ Aplicação está respondendo na porta 8000"
else
    echo "❌ Aplicação não está respondendo na porta 8000"
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    echo "✅ Nginx está respondendo"
else
    echo "❌ Nginx não está respondendo"
fi

echo ""
echo "🎉 Instalação concluída!"
echo "========================="
echo "📋 Próximos passos:"
echo "1. Configure seu domínio no arquivo /etc/nginx/sites-available/sistema-estelar"
echo "2. Acesse: http://seu-dominio.com.br"
echo "3. Monitore os logs: sudo tail -f /var/log/supervisor/sistema-estelar.log"
echo ""
echo "🔧 Comandos úteis:"
echo "- Ver status: sudo supervisorctl status sistema-estelar"
echo "- Reiniciar app: sudo supervisorctl restart sistema-estelar"
echo "- Ver logs: sudo tail -f /var/log/supervisor/sistema-estelar.log"
echo "- Ver logs nginx: sudo tail -f /var/log/nginx/error.log"

