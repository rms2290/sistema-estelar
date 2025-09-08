#!/bin/bash
# Script para reiniciar o Sistema Estelar de forma segura

echo "🔄 Reiniciando Sistema Estelar..."

# Parar supervisor
if command -v supervisorctl &> /dev/null; then
    echo "⏹️  Parando aplicação..."
    supervisorctl stop sistema-estelar
    sleep 5
fi

# Limpar cache
echo "🧹 Limpando cache..."
rm -rf cache/*
rm -rf /tmp/gunicorn*

# Reiniciar supervisor
if command -v supervisorctl &> /dev/null; then
    echo "▶️  Iniciando aplicação..."
    supervisorctl start sistema-estelar
    sleep 10
    
    # Verificar status
    echo "✅ Status da aplicação:"
    supervisorctl status sistema-estelar
else
    echo "❌ Supervisor não encontrado. Reinicie manualmente."
fi

echo "🎉 Reinicialização concluída!"
