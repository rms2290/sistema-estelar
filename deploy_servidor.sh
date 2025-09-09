#!/bin/bash
# Script de Deploy para Servidor Locaweb - Sistema Estelar
# Execute este script no servidor após fazer git pull

echo "🚀 Iniciando deploy do Sistema Estelar no servidor Locaweb"
echo "========================================================="

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo "❌ Execute este script no diretório raiz do projeto Django"
    exit 1
fi

# Atualizar código do repositório
echo "📥 Atualizando código do repositório..."
git pull origin main

# Ativar ambiente virtual
echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar/atualizar dependências
echo "📦 Instalando dependências de produção..."
pip install -r requirements_production.txt

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p logs
mkdir -p media
mkdir -p cache
mkdir -p staticfiles

# Coletar arquivos estáticos
echo "📄 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# Executar migrações
echo "🗄️ Executando migrações do banco de dados..."
python manage.py migrate --settings=sistema_estelar.settings_production

# Configurar permissões
echo "🔐 Configurando permissões..."
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# Parar serviços existentes
echo "⏹️ Parando serviços existentes..."
sudo supervisorctl stop sistema-estelar 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Configurar nginx
echo "🌐 Configurando nginx..."
sudo cp nginx_sistema_estelar.conf /etc/nginx/sites-available/sistema-estelar
sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar configuração do nginx
echo "🧪 Testando configuração do nginx..."
if sudo nginx -t; then
    echo "✅ Configuração do nginx válida"
else
    echo "❌ Erro na configuração do nginx"
    exit 1
fi

# Configurar supervisor
echo "👨‍💼 Configurando supervisor..."
sudo cp /dev/null /etc/supervisor/conf.d/sistema-estelar.conf
sudo tee /etc/supervisor/conf.d/sistema-estelar.conf > /dev/null <<EOF
[program:sistema-estelar]
command=/var/www/sistema-estelar/venv/bin/gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
directory=/var/www/sistema-estelar
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sistema-estelar.log
stderr_logfile=/var/log/supervisor/sistema-estelar_error.log
environment=PATH="/var/www/sistema-estelar/venv/bin"
EOF

# Recarregar supervisor
echo "🔄 Recarregando supervisor..."
sudo supervisorctl reread
sudo supervisorctl update

# Iniciar serviços
echo "▶️ Iniciando serviços..."
sudo systemctl start nginx
sudo supervisorctl start sistema-estelar

# Aguardar um momento para os serviços iniciarem
echo "⏳ Aguardando serviços iniciarem..."
sleep 5

# Verificar status dos serviços
echo "🔍 Verificando status dos serviços..."
echo "Nginx status:"
sudo systemctl is-active nginx

echo "Aplicação status:"
sudo supervisorctl status sistema-estelar

# Testar conectividade
echo "🌐 Testando conectividade..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    echo "✅ Aplicação está respondendo corretamente"
else
    echo "❌ Aplicação não está respondendo"
    echo "Verifique os logs: sudo supervisorctl tail -f sistema-estelar"
fi

echo ""
echo "🎉 Deploy concluído!"
echo "==================="
echo "📋 Informações importantes:"
echo "- Logs da aplicação: /var/log/supervisor/sistema-estelar.log"
echo "- Logs de erro: /var/log/supervisor/sistema-estelar_error.log"
echo "- Logs do nginx: /var/log/nginx/error.log"
echo "- Status dos serviços: sudo supervisorctl status"
echo ""
echo "🔧 Comandos úteis:"
echo "- Reiniciar aplicação: sudo supervisorctl restart sistema-estelar"
echo "- Ver logs em tempo real: sudo supervisorctl tail -f sistema-estelar"
echo "- Verificar status: sudo supervisorctl status sistema-estelar"
echo "- Reiniciar nginx: sudo systemctl restart nginx"
