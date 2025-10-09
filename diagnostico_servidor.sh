#!/bin/bash
# Script de Diagnóstico do Servidor - Sistema Estelar
# Execute este script no servidor para verificar a configuração

echo "========================================================="
echo "  DIAGNOSTICO DO SERVIDOR - SISTEMA ESTELAR"
echo "========================================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para check
check_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

check_erro() {
    echo -e "${RED}[ERRO]${NC} $1"
}

check_aviso() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

# 1. Verificar diretório
echo "1. VERIFICANDO DIRETORIO..."
if [ -f "manage.py" ]; then
    check_ok "Diretorio correto (manage.py encontrado)"
    echo "   Caminho: $(pwd)"
else
    check_erro "Arquivo manage.py nao encontrado!"
    echo "   Voce esta em: $(pwd)"
    echo "   Execute este script no diretorio raiz do projeto Django"
    exit 1
fi
echo ""

# 2. Verificar Python
echo "2. VERIFICANDO PYTHON..."
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    check_ok "Python instalado: $PYTHON_VERSION"
else
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        check_ok "Python3 instalado: $PYTHON_VERSION"
    else
        check_erro "Python nao encontrado!"
    fi
fi
echo ""

# 3. Verificar ambiente virtual
echo "3. VERIFICANDO AMBIENTE VIRTUAL..."
if [ -d "venv" ]; then
    check_ok "Ambiente virtual encontrado em: venv/"
    if [ -f "venv/bin/activate" ]; then
        check_ok "Script de ativacao existe"
    else
        check_erro "Script de ativacao nao encontrado!"
    fi
elif [ -d "../venv" ]; then
    check_ok "Ambiente virtual encontrado em: ../venv/"
else
    check_aviso "Ambiente virtual nao encontrado em venv/ ou ../venv/"
fi

# Verificar se está ativo
if [[ "$VIRTUAL_ENV" != "" ]]; then
    check_ok "Ambiente virtual ATIVO"
    echo "   Caminho: $VIRTUAL_ENV"
else
    check_aviso "Ambiente virtual NAO esta ativo"
    echo "   Execute: source venv/bin/activate"
fi
echo ""

# 4. Verificar Git
echo "4. VERIFICANDO GIT..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    check_ok "Git instalado: $GIT_VERSION"
    
    if [ -d ".git" ]; then
        check_ok "Repositorio Git inicializado"
        GIT_BRANCH=$(git branch --show-current 2>/dev/null)
        echo "   Branch atual: $GIT_BRANCH"
        
        GIT_REMOTE=$(git remote get-url origin 2>/dev/null)
        if [ ! -z "$GIT_REMOTE" ]; then
            echo "   Remote: $GIT_REMOTE"
        fi
    else
        check_aviso "Nao e um repositorio Git"
    fi
else
    check_erro "Git nao esta instalado!"
fi
echo ""

# 5. Verificar arquivos importantes
echo "5. VERIFICANDO ARQUIVOS IMPORTANTES..."
ARQUIVOS=("manage.py" "requirements.txt" "db.sqlite3" "sistema_estelar/settings.py")
for arquivo in "${ARQUIVOS[@]}"; do
    if [ -f "$arquivo" ]; then
        TAMANHO=$(ls -lh "$arquivo" | awk '{print $5}')
        check_ok "$arquivo ($TAMANHO)"
    else
        check_aviso "$arquivo nao encontrado"
    fi
done
echo ""

# 6. Verificar diretórios
echo "6. VERIFICANDO DIRETORIOS..."
DIRETORIOS=("notas" "sistema_estelar" "static" "staticfiles" "logs" "media")
for dir in "${DIRETORIOS[@]}"; do
    if [ -d "$dir" ]; then
        ITENS=$(ls -1 "$dir" 2>/dev/null | wc -l)
        check_ok "$dir/ ($ITENS itens)"
    else
        check_aviso "$dir/ nao encontrado"
    fi
done
echo ""

# 7. Verificar banco de dados
echo "7. VERIFICANDO BANCO DE DADOS..."
if [ -f "db.sqlite3" ]; then
    DB_SIZE=$(ls -lh db.sqlite3 | awk '{print $5}')
    check_ok "Banco de dados: db.sqlite3 ($DB_SIZE)"
    
    DB_PERM=$(ls -l db.sqlite3 | awk '{print $1}')
    echo "   Permissoes: $DB_PERM"
    
    if [ -r "db.sqlite3" ] && [ -w "db.sqlite3" ]; then
        check_ok "Permissoes de leitura e escrita OK"
    else
        check_erro "Problemas de permissao no banco de dados!"
    fi
else
    check_aviso "Banco de dados nao encontrado (sera criado nas migracoes)"
fi
echo ""

# 8. Verificar Gunicorn
echo "8. VERIFICANDO GUNICORN..."
if pgrep -f "gunicorn" > /dev/null; then
    NUM_PROCESSOS=$(pgrep -f "gunicorn" | wc -l)
    check_ok "Gunicorn esta RODANDO ($NUM_PROCESSOS processos)"
    echo "   PIDs: $(pgrep -f gunicorn | tr '\n' ' ')"
else
    check_aviso "Gunicorn NAO esta rodando"
fi
echo ""

# 9. Verificar Nginx
echo "9. VERIFICANDO NGINX..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1)
    check_ok "Nginx instalado: $NGINX_VERSION"
    
    if systemctl is-active --quiet nginx 2>/dev/null; then
        check_ok "Nginx esta ATIVO"
    else
        check_aviso "Status do Nginx desconhecido"
    fi
else
    check_erro "Nginx nao esta instalado!"
fi
echo ""

# 10. Verificar Supervisor
echo "10. VERIFICANDO SUPERVISOR..."
if command -v supervisorctl &> /dev/null; then
    check_ok "Supervisor instalado"
    
    SUPERVISOR_STATUS=$(sudo supervisorctl status 2>/dev/null | grep sistema)
    if [ ! -z "$SUPERVISOR_STATUS" ]; then
        echo "   $SUPERVISOR_STATUS"
    else
        check_aviso "Sistema Estelar nao encontrado no Supervisor"
    fi
else
    check_aviso "Supervisor nao esta instalado"
fi
echo ""

# 11. Testar conectividade
echo "11. TESTANDO CONECTIVIDADE..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 2>/dev/null)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        check_ok "Aplicacao respondendo (HTTP $HTTP_CODE)"
    else
        check_aviso "Aplicacao pode nao estar respondendo (HTTP $HTTP_CODE)"
    fi
else
    check_aviso "curl nao instalado, nao foi possivel testar"
fi
echo ""

# 12. Verificar logs
echo "12. VERIFICANDO LOGS..."
if [ -d "logs" ]; then
    check_ok "Diretorio de logs existe"
    
    if [ -f "logs/gunicorn.log" ]; then
        LOG_SIZE=$(ls -lh logs/gunicorn.log | awk '{print $5}')
        check_ok "gunicorn.log ($LOG_SIZE)"
        echo "   Ultimas 5 linhas:"
        tail -5 logs/gunicorn.log | sed 's/^/   | /'
    else
        check_aviso "gunicorn.log nao encontrado"
    fi
    
    if [ -f "logs/django.log" ]; then
        LOG_SIZE=$(ls -lh logs/django.log | awk '{print $5}')
        check_ok "django.log ($LOG_SIZE)"
    fi
else
    check_aviso "Diretorio logs/ nao existe"
fi
echo ""

# 13. Verificar permissões
echo "13. VERIFICANDO PERMISSOES..."
OWNER=$(ls -ld . | awk '{print $3":"$4}')
echo "   Proprietario do diretorio: $OWNER"

if [ -w "." ]; then
    check_ok "Permissao de escrita no diretorio"
else
    check_erro "Sem permissao de escrita no diretorio!"
fi
echo ""

# 14. Informações do sistema
echo "14. INFORMACOES DO SISTEMA..."
echo "   Hostname: $(hostname)"
echo "   Sistema: $(uname -s)"
echo "   Arquitetura: $(uname -m)"

if command -v free &> /dev/null; then
    MEMORIA=$(free -h | grep Mem | awk '{print $2}')
    echo "   Memoria Total: $MEMORIA"
fi

if command -v df &> /dev/null; then
    DISCO=$(df -h . | tail -1 | awk '{print $4}')
    echo "   Espaco Disponivel: $DISCO"
fi
echo ""

# Resumo final
echo "========================================================="
echo "  RESUMO DO DIAGNOSTICO"
echo "========================================================="
echo ""

# Contar checks
CHECKS_OK=0
CHECKS_ERRO=0
CHECKS_AVISO=0

# Verificações críticas
if [ -f "manage.py" ]; then ((CHECKS_OK++)); else ((CHECKS_ERRO++)); fi
if [ -d "venv" ] || [ -d "../venv" ]; then ((CHECKS_OK++)); else ((CHECKS_AVISO++)); fi
if command -v git &> /dev/null; then ((CHECKS_OK++)); else ((CHECKS_ERRO++)); fi
if [ -f "db.sqlite3" ]; then ((CHECKS_OK++)); else ((CHECKS_AVISO++)); fi

echo "Status Geral:"
echo "  ✓ OK: $CHECKS_OK"
echo "  ⚠ Avisos: $CHECKS_AVISO"
echo "  ✗ Erros: $CHECKS_ERRO"
echo ""

if [ $CHECKS_ERRO -eq 0 ]; then
    check_ok "Sistema parece estar configurado corretamente!"
    echo ""
    echo "Proximos passos:"
    echo "  1. Ative o ambiente virtual: source venv/bin/activate"
    echo "  2. Execute o deploy: bash deploy_atualizacao.sh"
    echo "  3. Ou siga o PASSO_A_PASSO_LOCAWEB.md"
else
    check_aviso "Alguns problemas foram encontrados."
    echo "  Consulte o PASSO_A_PASSO_LOCAWEB.md para resolver."
fi

echo ""
echo "========================================================="

