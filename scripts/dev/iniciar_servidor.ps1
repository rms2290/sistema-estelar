# Script para iniciar o servidor Django diretamente
# Uso: .\scripts\dev\iniciar_servidor.ps1 ou usar o wrapper na raiz: .\iniciar_servidor.ps1

# Mudar para o diretório raiz do projeto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "..\.."
Set-Location $projectRoot

Write-Host "=== Iniciando Servidor Django ===" -ForegroundColor Cyan

# Verificar se o ambiente virtual está ativo
if (-not $env:VIRTUAL_ENV) {
    Write-Host "AVISO: Ambiente virtual não está ativo. Ativando..." -ForegroundColor Yellow
    if (Test-Path "venv\Scripts\activate.ps1") {
        & "venv\Scripts\activate.ps1"
    } else {
        Write-Host "ERRO: Ambiente virtual não encontrado!" -ForegroundColor Red
        Write-Host "Execute primeiro: .\ativar.ps1" -ForegroundColor Yellow
        exit 1
    }
}

# Verificar se Django está disponível
python -c "import django" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Django não encontrado!" -ForegroundColor Red
    Write-Host "Execute: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Verificar se django-ratelimit está instalado
python -c "import django_ratelimit" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: django-ratelimit não encontrado. Instalando..." -ForegroundColor Yellow
    pip install django-ratelimit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao instalar django-ratelimit!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ django-ratelimit instalado" -ForegroundColor Green
}

Write-Host "✓ Ambiente verificado" -ForegroundColor Green
Write-Host "`nIniciando servidor em http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Pressione Ctrl+C para parar o servidor`n" -ForegroundColor Gray

# Iniciar servidor
python manage.py runserver


