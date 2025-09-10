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

# Ativar ambiente virtual (se existir)
if [ -d "venv" ]; then
    echo "🐍 Ativando ambiente virtual..."
    source venv/bin/activate
fi

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
python manage.py collectstatic --noinput

# Aplicar migrações
echo "🗄️ Aplicando migrações..."
python manage.py migrate

# Verificar configuração
echo "🔍 Verificando configuração..."
python manage.py check

# Reiniciar serviços
echo "🔄 Reiniciando serviços..."

# Reiniciar gunicorn (se estiver rodando)
if pgrep -f "gunicorn" > /dev/null; then
    echo "🔄 Reiniciando Gunicorn..."
    pkill -f "gunicorn"
    sleep 2
    # Iniciar gunicorn em background
    nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &
fi

# Reiniciar nginx
echo "🔄 Reiniciando Nginx..."
sudo systemctl reload nginx

# Verificar status dos serviços
echo "📊 Verificando status dos serviços..."
echo "Gunicorn:"
pgrep -f "gunicorn" && echo "✅ Gunicorn rodando" || echo "❌ Gunicorn não está rodando"

echo "Nginx:"
sudo systemctl status nginx --no-pager -l

echo ""
echo "🎉 Deploy concluído com sucesso!"
echo "========================================================="
echo "📋 Próximos passos:"
echo "1. Verifique os logs em logs/gunicorn.log"
echo "2. Teste o acesso ao site"
echo "3. Monitore o desempenho"
echo "4. Configure backup automático se necessário"

