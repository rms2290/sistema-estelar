#!/bin/bash
# Script para monitorar uso de memória do Sistema Estelar

echo "=== MONITORAMENTO DE MEMÓRIA ==="
echo "Data: $(date)"
echo

# Memória total do sistema
echo "📊 Memória do Sistema:"
free -h
echo

# Processos do Gunicorn
echo "🔍 Processos Gunicorn:"
ps aux | grep gunicorn | grep -v grep
echo

# Uso de memória por processo
echo "💾 Uso de Memória por Processo:"
ps aux --sort=-%mem | head -10
echo

# Verificar se há vazamentos de memória
echo "🔍 Verificando vazamentos de memória:"
ps aux | grep python | awk '{sum+=$6} END {print "Total Python processes memory: " sum/1024 " MB"}'
echo

# Status dos workers
echo "⚙️  Status dos Workers:"
if command -v supervisorctl &> /dev/null; then
    supervisorctl status sistema-estelar
else
    echo "Supervisor não encontrado"
fi
echo

echo "=== FIM DO MONITORAMENTO ==="
