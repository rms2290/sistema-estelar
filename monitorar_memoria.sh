#!/bin/bash
# Script para monitorar uso de memória do sistema
# Execute: bash monitorar_memoria.sh

echo "========================================================="
echo "  MONITORAMENTO DE MEMÓRIA - SISTEMA ESTELAR"
echo "========================================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Uso geral de memória
echo "📊 USO GERAL DE MEMÓRIA:"
echo "----------------------------------------"
free -h
echo ""

# 2. Processos Python/Gunicorn
echo "🐍 PROCESSOS PYTHON/GUNICORN:"
echo "----------------------------------------"
ps aux | grep -E "gunicorn|python.*manage" | grep -v grep | awk '{printf "%-8s %6s%% %s\n", $2, $4, $11}' | sort -k2 -rn
echo ""

# 3. Top 10 processos usando mais memória
echo "🔝 TOP 10 PROCESSOS USANDO MAIS MEMÓRIA:"
echo "----------------------------------------"
ps aux --sort=-%mem | head -11 | awk 'NR==1 {printf "%-8s %6s %10s %s\n", $1, $2, $4, $11} NR>1 {printf "%-8s %6s%% %10s %s\n", $1, $2, $4, $11}'
echo ""

# 4. Uso de memória do Gunicorn
echo "⚙️  USO DE MEMÓRIA DO GUNICORN:"
echo "----------------------------------------"
GUNICORN_PIDS=$(pgrep -f gunicorn)
if [ -z "$GUNICORN_PIDS" ]; then
    echo "❌ Gunicorn não está rodando"
else
    TOTAL_MEM=0
    for pid in $GUNICORN_PIDS; do
        MEM=$(ps -p $pid -o %mem --no-headers | tr -d ' ')
        RSS=$(ps -p $pid -o rss --no-headers)
        RSS_MB=$((RSS / 1024))
        TOTAL_MEM=$((TOTAL_MEM + RSS_MB))
        echo "  PID $pid: ${MEM}% (${RSS_MB}MB)"
    done
    echo "  Total Gunicorn: ${TOTAL_MEM}MB"
fi
echo ""

# 5. Recomendações
echo "💡 RECOMENDAÇÕES:"
echo "----------------------------------------"
TOTAL_MEM_GB=$(free -g | awk '/^Mem:/ {print $2}')
USED_MEM_PERCENT=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')

if [ "$USED_MEM_PERCENT" -gt 90 ]; then
    echo -e "${RED}⚠️  ALERTA: Uso de memória acima de 90%!${NC}"
    echo "   - Considere reduzir workers do Gunicorn para 1"
    echo "   - Verifique processos não relacionados"
    echo "   - Considere upgrade de plano"
elif [ "$USED_MEM_PERCENT" -gt 80 ]; then
    echo -e "${YELLOW}⚠️  ATENÇÃO: Uso de memória acima de 80%${NC}"
    echo "   - Monitore o uso regularmente"
    echo "   - Considere otimizações adicionais"
else
    echo -e "${GREEN}✓ Uso de memória dentro do normal${NC}"
fi

echo ""
echo "========================================================="

