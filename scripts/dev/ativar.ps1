# Script de ativacao do ambiente virtual e servidor Django
# Uso: .\scripts\dev\ativar.ps1 ou usar o wrapper na raiz: .\ativar.ps1

# Mudar para o diretorio raiz do projeto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "..\.."
Set-Location $projectRoot

Write-Host "=== Sistema Estelar - Ativacao ===" -ForegroundColor Cyan

# Verificar se o ambiente virtual existe
if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Write-Host "ERRO: Ambiente virtual nao encontrado!" -ForegroundColor Red
    Write-Host "Execute: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Ativar ambiente virtual
Write-Host "`n[1/3] Ativando ambiente virtual..." -ForegroundColor Yellow
& "venv\Scripts\activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao ativar ambiente virtual!" -ForegroundColor Red
    Write-Host "Tente executar: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Ambiente virtual ativado" -ForegroundColor Green

# Verificar se Django esta instalado
Write-Host "`n[2/3] Verificando dependencias..." -ForegroundColor Yellow
python -c "import django; print('Django encontrado')" 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: Django nao encontrado. Instalando dependencias..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao instalar dependencias!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] Dependencias verificadas" -ForegroundColor Green

# Verificar migracoes
Write-Host "`n[3/3] Verificando banco de dados..." -ForegroundColor Yellow
python manage.py check 2>&1 | Out-Null

Write-Host "[OK] Sistema pronto!" -ForegroundColor Green

Write-Host "`n=== Comandos disponiveis ===" -ForegroundColor Cyan
Write-Host "  python manage.py runserver          - Iniciar servidor de desenvolvimento"
Write-Host "  python manage.py migrate            - Aplicar migracoes"
Write-Host "  python manage.py createsuperuser    - Criar usuario admin"
Write-Host "  python manage.py collectstatic      - Coletar arquivos estaticos"
Write-Host "`nPara iniciar o servidor, execute:" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Cyan
