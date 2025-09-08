#!/bin/bash

# Script para resolver o problema de HTTPS no servidor Locaweb
# Execute: chmod +x resolver_problema.sh && ./resolver_problema.sh

echo "🔧 Resolvendo problema de HTTPS no Sistema Estelar"
echo "================================================="

# 1. Parar servidor atual
echo "1. Parando servidor atual..."
pkill -f "python manage.py runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true

# 2. Instalar gunicorn
echo "2. Instalando gunicorn..."
pip install gunicorn

# 3. Criar configuração nginx
echo "3. Criando configuração do nginx..."
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

# 4. Ativar site
echo "4. Ativando site no nginx..."
sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Testar e reiniciar nginx
echo "5. Testando e reiniciando nginx..."
sudo nginx -t && sudo systemctl restart nginx

# 6. Configurar permissões
echo "6. Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# 7. Coletar arquivos estáticos
echo "7. Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# 8. Executar migrações
echo "8. Executando migrações..."
python manage.py migrate --settings=sistema_estelar.settings_production

# 9. Iniciar gunicorn
echo "9. Iniciando gunicorn..."
nohup gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application > /dev/null 2>&1 &

# 10. Verificar status
echo "10. Verificando status..."
sleep 3
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Aplicação rodando na porta 8000"
else
    echo "❌ Problema na aplicação"
fi

if curl -s http://localhost > /dev/null; then
    echo "✅ Nginx funcionando"
else
    echo "❌ Problema no nginx"
fi

echo ""
echo "🎉 Configuração concluída!"
echo "Acesse: http://seu-dominio.com.br"
echo "Para ver logs: tail -f nohup.out"

