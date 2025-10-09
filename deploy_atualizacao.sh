#!/bin/bash
# Script de Deploy Automatizado - Sistema Estelar
# Execute este script NO SERVIDOR Locaweb após conectar via SSH

echo "========================================================="
echo "  DEPLOY SISTEMA ESTELAR - ATUALIZACAO"
echo "========================================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para exibir mensagens
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    log_error "Execute este script no diretorio raiz do projeto Django!"
    exit 1
fi

log_info "Diretorio correto verificado!"

# 1. Backup do banco de dados
log_info "Fazendo backup do banco de dados..."
mkdir -p backups
if [ -f "db.sqlite3" ]; then
    BACKUP_FILE="backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    cp db.sqlite3 "$BACKUP_FILE"
    log_info "Backup criado: $BACKUP_FILE"
else
    log_warning "Arquivo db.sqlite3 nao encontrado. Pulando backup..."
fi

# 2. Fazer stash de alterações locais
log_info "Salvando alteracoes locais..."
git stash

# 3. Atualizar código
log_info "Atualizando codigo do repositorio..."
if git pull origin main; then
    log_info "Codigo atualizado com sucesso!"
else
    log_error "Falha ao atualizar codigo!"
    exit 1
fi

# 4. Ativar ambiente virtual
log_info "Ativando ambiente virtual..."
if [ -d "venv" ]; then
    source venv/bin/activate
    log_info "Ambiente virtual ativado!"
else
    log_warning "Ambiente virtual nao encontrado em venv/"
    if [ -d "../venv" ]; then
        source ../venv/bin/activate
        log_info "Ambiente virtual ativado de ../venv!"
    else
        log_error "Ambiente virtual nao encontrado!"
        exit 1
    fi
fi

# 5. Atualizar pip
log_info "Atualizando pip..."
pip install --upgrade pip --quiet

# 6. Instalar dependências
log_info "Instalando/atualizando dependencias..."
if [ -f "requirements_production.txt" ]; then
    pip install -r requirements_production.txt --quiet
    log_info "Dependencias de producao instaladas!"
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    log_info "Dependencias instaladas!"
else
    log_error "Arquivo requirements.txt nao encontrado!"
    exit 1
fi

# 7. Executar migrações
log_info "Executando migracoes do banco de dados..."
if python manage.py migrate; then
    log_info "Migracoes aplicadas com sucesso!"
else
    log_error "Falha ao aplicar migracoes!"
    exit 1
fi

# 8. Coletar arquivos estáticos
log_info "Coletando arquivos estaticos..."
if python manage.py collectstatic --noinput; then
    log_info "Arquivos estaticos coletados!"
else
    log_warning "Erro ao coletar arquivos estaticos (continuando...)"
fi

# 9. Verificar configuração
log_info "Verificando configuracao do Django..."
python manage.py check

# 10. Criar diretórios necessários
log_info "Criando diretorios necessarios..."
mkdir -p logs
mkdir -p media
mkdir -p cache
mkdir -p staticfiles

# 11. Ajustar permissões
log_info "Ajustando permissoes..."
chmod -R 755 staticfiles/ 2>/dev/null || log_warning "Nao foi possivel ajustar permissoes de staticfiles"
chmod 664 db.sqlite3 2>/dev/null || log_warning "Nao foi possivel ajustar permissoes de db.sqlite3"

# 12. Reiniciar serviços
log_info "Reiniciando servicos..."

# Tentar reiniciar via supervisor
if command -v supervisorctl &> /dev/null; then
    log_info "Reiniciando via Supervisor..."
    sudo supervisorctl restart sistema-estelar 2>/dev/null && log_info "Supervisor: OK" || log_warning "Supervisor nao configurado"
fi

# Tentar reiniciar via systemd
if command -v systemctl &> /dev/null; then
    log_info "Reiniciando via systemd..."
    sudo systemctl restart sistema-estelar 2>/dev/null && log_info "systemd: OK" || log_warning "systemd nao configurado"
fi

# Reiniciar gunicorn manualmente se necessário
if pgrep -f "gunicorn" > /dev/null; then
    log_info "Reiniciando Gunicorn manualmente..."
    pkill -f "gunicorn"
    sleep 2
    nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &
    log_info "Gunicorn reiniciado!"
else
    log_warning "Gunicorn nao estava rodando. Iniciando..."
    nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &
    log_info "Gunicorn iniciado!"
fi

# 13. Reiniciar Nginx
if command -v nginx &> /dev/null; then
    log_info "Testando configuracao do Nginx..."
    if sudo nginx -t 2>/dev/null; then
        log_info "Recarregando Nginx..."
        sudo systemctl reload nginx 2>/dev/null && log_info "Nginx recarregado!" || log_warning "Erro ao recarregar Nginx"
    else
        log_warning "Configuracao do Nginx com erro. Pulando reload..."
    fi
fi

# 14. Verificar status
echo ""
echo "========================================================="
echo "  VERIFICACAO DE STATUS"
echo "========================================================="

# Verificar Gunicorn
if pgrep -f "gunicorn" > /dev/null; then
    log_info "Gunicorn: RODANDO"
    echo "   Processos: $(pgrep -f gunicorn | wc -l)"
else
    log_error "Gunicorn: NAO ESTA RODANDO!"
fi

# Verificar Nginx
if systemctl is-active --quiet nginx 2>/dev/null; then
    log_info "Nginx: ATIVO"
else
    log_warning "Nginx: Status desconhecido"
fi

# Testar conectividade
log_info "Testando conectividade..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    log_info "Aplicacao respondendo! (HTTP $HTTP_CODE)"
else
    log_warning "Aplicacao pode nao estar respondendo (HTTP $HTTP_CODE)"
fi

# 15. Exibir logs recentes
echo ""
echo "========================================================="
echo "  ULTIMAS LINHAS DO LOG"
echo "========================================================="
if [ -f "logs/gunicorn.log" ]; then
    tail -10 logs/gunicorn.log
else
    log_warning "Log do Gunicorn nao encontrado"
fi

# Finalizar
echo ""
echo "========================================================="
echo "  DEPLOY CONCLUIDO!"
echo "========================================================="
echo ""
log_info "Credenciais de acesso:"
echo "   Username: admin"
echo "   Password: 123456"
echo ""
log_warning "IMPORTANTE: Altere a senha apos o primeiro login!"
echo ""
log_info "Proximos passos:"
echo "   1. Acesse o sistema no navegador"
echo "   2. Faca login e altere a senha"
echo "   3. Teste as funcionalidades principais"
echo "   4. Monitore os logs: tail -f logs/gunicorn.log"
echo ""
echo "========================================================="

