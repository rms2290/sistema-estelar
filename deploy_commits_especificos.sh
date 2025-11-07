#!/bin/bash
# Script de Deploy para Commits Específicos - Sistema Estelar
# Execute este script NO SERVIDOR Locaweb após conectar via SSH
# Uso: ./deploy_commits_especificos.sh [numero_de_commits]
# Exemplo: ./deploy_commits_especificos.sh 2 (para os 2 últimos commits)

echo "========================================================="
echo "  DEPLOY SISTEMA ESTELAR - COMMITS ESPECÍFICOS"
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

# Número de commits a fazer deploy (padrão: 2)
NUM_COMMITS=${1:-2}

log_info "Diretorio correto verificado!"
log_info "Fazendo deploy dos ultimos $NUM_COMMITS commits..."

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

# 2. Verificar status do git
log_info "Verificando status do repositorio Git..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main 2>/dev/null || echo "")

if [ -z "$REMOTE_COMMIT" ]; then
    log_warning "Nao foi possivel obter commit remoto. Continuando com commits locais..."
fi

# 3. Obter os commits a serem aplicados
log_info "Identificando commits a serem aplicados..."
COMMITS_TO_DEPLOY=$(git log --oneline -$NUM_COMMITS --format="%h %s")
log_info "Commits que serao aplicados:"
echo "$COMMITS_TO_DEPLOY" | while read line; do
    echo "   - $line"
done

# 4. Salvar estado atual
log_info "Salvando estado atual do repositorio..."
git stash push -m "Estado antes do deploy de commits especificos - $(date +%Y%m%d_%H%M%S)"

# 5. Atualizar código do repositório remoto
log_info "Atualizando codigo do repositorio remoto..."
if git fetch origin main; then
    log_info "Codigo atualizado do remoto!"
else
    log_warning "Nao foi possivel atualizar do remoto. Continuando com commits locais..."
fi

# 6. Obter o commit base (antes dos commits que queremos)
BASE_COMMIT=$(git rev-parse HEAD~$NUM_COMMITS 2>/dev/null)
if [ -z "$BASE_COMMIT" ]; then
    log_warning "Nao foi possivel determinar commit base. Usando HEAD~$NUM_COMMITS..."
    BASE_COMMIT="HEAD~$NUM_COMMITS"
fi

# 7. Criar uma branch temporária para os commits específicos
TEMP_BRANCH="deploy-temp-$(date +%s)"
log_info "Criando branch temporaria: $TEMP_BRANCH"
git checkout -b "$TEMP_BRANCH" "$BASE_COMMIT" 2>/dev/null || {
    log_warning "Nao foi possivel criar branch temporaria. Tentando outra abordagem..."
    git checkout "$CURRENT_BRANCH"
}

# 8. Aplicar apenas os commits específicos usando cherry-pick
log_info "Aplicando commits especificos..."
COMMIT_HASHES=$(git log --reverse --oneline -$NUM_COMMITS --format="%h")

for commit_hash in $COMMIT_HASHES; do
    log_info "Aplicando commit: $commit_hash"
    if git cherry-pick "$commit_hash" 2>/dev/null; then
        log_info "Commit $commit_hash aplicado com sucesso!"
    else
        log_error "Falha ao aplicar commit $commit_hash!"
        log_warning "Tentando continuar com os outros commits..."
        git cherry-pick --abort 2>/dev/null
    fi
done

# 9. Voltar para a branch principal e fazer merge
log_info "Voltando para branch principal: $CURRENT_BRANCH"
git checkout "$CURRENT_BRANCH" 2>/dev/null || git checkout main

# Se a branch temporária foi criada, fazer merge
if git show-ref --verify --quiet refs/heads/"$TEMP_BRANCH"; then
    log_info "Fazendo merge dos commits..."
    if git merge "$TEMP_BRANCH" --no-edit; then
        log_info "Merge concluido com sucesso!"
        git branch -d "$TEMP_BRANCH" 2>/dev/null
    else
        log_error "Falha no merge!"
        git merge --abort 2>/dev/null
        exit 1
    fi
fi

# 10. Ativar ambiente virtual
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

# 11. Atualizar pip
log_info "Atualizando pip..."
pip install --upgrade pip --quiet

# 12. Instalar dependências
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

# 13. Executar migrações
log_info "Executando migracoes do banco de dados..."
if python manage.py migrate; then
    log_info "Migracoes aplicadas com sucesso!"
else
    log_error "Falha ao aplicar migracoes!"
    exit 1
fi

# 14. Coletar arquivos estáticos
log_info "Coletando arquivos estaticos..."
if python manage.py collectstatic --noinput; then
    log_info "Arquivos estaticos coletados!"
else
    log_warning "Erro ao coletar arquivos estaticos (continuando...)"
fi

# 15. Verificar configuração
log_info "Verificando configuracao do Django..."
python manage.py check

# 16. Criar diretórios necessários
log_info "Criando diretorios necessarios..."
mkdir -p logs
mkdir -p media
mkdir -p cache
mkdir -p staticfiles

# 17. Ajustar permissões
log_info "Ajustando permissoes..."
chmod -R 755 staticfiles/ 2>/dev/null || log_warning "Nao foi possivel ajustar permissoes de staticfiles"
chmod 664 db.sqlite3 2>/dev/null || log_warning "Nao foi possivel ajustar permissoes de db.sqlite3"

# 18. Reiniciar serviços
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

# 19. Reiniciar Nginx
if command -v nginx &> /dev/null; then
    log_info "Testando configuracao do Nginx..."
    if sudo nginx -t 2>/dev/null; then
        log_info "Recarregando Nginx..."
        sudo systemctl reload nginx 2>/dev/null && log_info "Nginx recarregado!" || log_warning "Erro ao recarregar Nginx"
    else
        log_warning "Configuracao do Nginx com erro. Pulando reload..."
    fi
fi

# 20. Verificar status
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

# 21. Exibir logs recentes
echo ""
echo "========================================================="
echo "  ULTIMAS LINHAS DO LOG"
echo "========================================================="
if [ -f "logs/gunicorn.log" ]; then
    tail -10 logs/gunicorn.log
else
    log_warning "Log do Gunicorn nao encontrado"
fi

# 22. Exibir resumo dos commits aplicados
echo ""
echo "========================================================="
echo "  RESUMO DOS COMMITS APLICADOS"
echo "========================================================="
git log --oneline -$NUM_COMMITS

# Finalizar
echo ""
echo "========================================================="
echo "  DEPLOY CONCLUIDO!"
echo "========================================================="
echo ""
log_info "Commits aplicados: $NUM_COMMITS"
log_info "Proximos passos:"
echo "   1. Acesse o sistema no navegador"
echo "   2. Teste as funcionalidades principais"
echo "   3. Monitore os logs: tail -f logs/gunicorn.log"
echo ""
echo "========================================================="

