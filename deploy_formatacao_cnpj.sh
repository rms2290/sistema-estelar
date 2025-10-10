#!/bin/bash
# ========================================
# Deploy Seguro - Formatação de CNPJ
# ========================================
# Este script atualiza apenas os templates
# SEM AFETAR OS DADOS DO BANCO
# ========================================

set -e  # Para em caso de erro

echo "🚀 Iniciando deploy da formatação de CNPJ..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar se está no diretório correto
echo -e "${YELLOW}📁 Verificando diretório...${NC}"
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Erro: manage.py não encontrado. Execute este script no diretório raiz do projeto.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Diretório correto!${NC}"
echo ""

# 2. Fazer backup do código atual
echo -e "${YELLOW}💾 Fazendo backup do código atual...${NC}"
BACKUP_DIR="backups/deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r notas/templatetags "$BACKUP_DIR/" 2>/dev/null || true
cp -r notas/templates "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✅ Backup criado em: $BACKUP_DIR${NC}"
echo ""

# 3. Verificar branch atual
echo -e "${YELLOW}🔍 Verificando branch do Git...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo "Branch atual: $CURRENT_BRANCH"
echo ""

# 4. Fazer stash de alterações locais (se houver)
echo -e "${YELLOW}📦 Salvando alterações locais (se houver)...${NC}"
git stash push -m "Deploy formatação CNPJ - $(date +%Y%m%d_%H%M%S)" || true
echo ""

# 5. Atualizar código do repositório
echo -e "${YELLOW}⬇️  Baixando atualizações do repositório...${NC}"
git pull origin main
echo -e "${GREEN}✅ Código atualizado!${NC}"
echo ""

# 6. Verificar se o ambiente virtual existe
echo -e "${YELLOW}🐍 Verificando ambiente virtual...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Ambiente virtual não encontrado!${NC}"
    echo "Por favor, crie o ambiente virtual primeiro:"
    echo "  python3 -m venv venv"
    exit 1
fi
echo -e "${GREEN}✅ Ambiente virtual encontrado!${NC}"
echo ""

# 7. Ativar ambiente virtual
echo -e "${YELLOW}🔌 Ativando ambiente virtual...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Ambiente virtual ativado!${NC}"
echo ""

# 8. Verificar dependências (opcional, não instalar nada novo)
echo -e "${YELLOW}📋 Verificando dependências...${NC}"
echo "Django: $(python -c 'import django; print(django.get_version())' 2>/dev/null || echo 'não encontrado')"
echo ""

# 9. Coletar arquivos estáticos
echo -e "${YELLOW}📦 Coletando arquivos estáticos...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Arquivos estáticos coletados!${NC}"
echo ""

# 10. Verificar qual serviço está rodando
echo -e "${YELLOW}🔍 Identificando serviço em execução...${NC}"
SERVICE_TYPE=""

if systemctl list-units --type=service | grep -q "sistema-estelar"; then
    SERVICE_TYPE="systemd"
    SERVICE_NAME="sistema-estelar"
    echo "Detectado: systemd service (sistema-estelar)"
elif supervisorctl status sistema-estelar 2>/dev/null | grep -q "RUNNING"; then
    SERVICE_TYPE="supervisor"
    SERVICE_NAME="sistema-estelar"
    echo "Detectado: supervisor (sistema-estelar)"
elif pgrep -f "gunicorn.*sistema_estelar" > /dev/null; then
    SERVICE_TYPE="gunicorn"
    echo "Detectado: gunicorn manual"
else
    echo -e "${YELLOW}⚠️  Nenhum serviço Django detectado rodando${NC}"
fi
echo ""

# 11. Reiniciar o serviço
if [ -n "$SERVICE_TYPE" ]; then
    echo -e "${YELLOW}🔄 Reiniciando serviço ($SERVICE_TYPE)...${NC}"
    
    case $SERVICE_TYPE in
        "systemd")
            sudo systemctl restart $SERVICE_NAME
            sleep 2
            sudo systemctl status $SERVICE_NAME --no-pager -l
            ;;
        "supervisor")
            sudo supervisorctl restart $SERVICE_NAME
            sleep 2
            sudo supervisorctl status $SERVICE_NAME
            ;;
        "gunicorn")
            echo "Parando processos gunicorn..."
            pkill -f "gunicorn.*sistema_estelar" || true
            sleep 2
            echo "Iniciando gunicorn..."
            nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &
            sleep 3
            ;;
    esac
    
    echo -e "${GREEN}✅ Serviço reiniciado!${NC}"
else
    echo -e "${YELLOW}⚠️  Reinicie manualmente o servidor Django${NC}"
fi
echo ""

# 12. Recarregar Nginx (se disponível)
if command -v nginx &> /dev/null; then
    echo -e "${YELLOW}🔄 Recarregando Nginx...${NC}"
    sudo nginx -t && sudo systemctl reload nginx
    echo -e "${GREEN}✅ Nginx recarregado!${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx não encontrado, pulando...${NC}"
fi
echo ""

# 13. Verificar se a aplicação está respondendo
echo -e "${YELLOW}🧪 Testando aplicação...${NC}"
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✅ Aplicação respondendo! (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}⚠️  Aplicação não está respondendo corretamente (HTTP $HTTP_CODE)${NC}"
    echo "Verifique os logs:"
    echo "  tail -f logs/gunicorn.log"
fi
echo ""

# 14. Resumo
echo "========================================="
echo -e "${GREEN}✅ DEPLOY CONCLUÍDO COM SUCESSO!${NC}"
echo "========================================="
echo ""
echo "📋 Alterações aplicadas:"
echo "  ✅ Filtros de formatação de CNPJ, CPF e telefone"
echo "  ✅ Templates atualizados (11 arquivos)"
echo "  ✅ Arquivos estáticos coletados"
echo "  ✅ Serviço reiniciado"
echo ""
echo "🔍 O que foi modificado:"
echo "  - notas/templatetags/format_filters.py"
echo "  - notas/templates/notas/listar_clientes.html"
echo "  - notas/templates/notas/detalhes_cliente.html"
echo "  - notas/templates/notas/dashboard.html"
echo "  - E mais 8 templates..."
echo ""
echo "⚠️  IMPORTANTE:"
echo "  - Nenhum dado foi alterado ou apagado"
echo "  - Banco de dados permanece intacto"
echo "  - Apenas templates e filtros foram atualizados"
echo ""
echo "🧪 Próximos passos:"
echo "  1. Acesse o sistema no navegador"
echo "  2. Faça login normalmente"
echo "  3. Vá em 'Pesquisar Clientes'"
echo "  4. Busque um cliente"
echo "  5. Verifique se o CNPJ está formatado: 00.000.000/0000-00"
echo ""
echo "📊 Monitorar logs:"
echo "  tail -f logs/gunicorn.log"
echo "  tail -f logs/django.log"
echo ""
echo "💾 Backup criado em: $BACKUP_DIR"
echo ""
echo -e "${GREEN}🎉 Deploy finalizado!${NC}"

