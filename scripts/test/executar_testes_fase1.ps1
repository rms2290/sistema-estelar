# Script para executar testes da Fase 1
# Uso: .\scripts\test\executar_testes_fase1.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "..\.."
Set-Location $projectRoot

Write-Host "`n=== TESTES DA FASE 1: SEGURANÇA CRÍTICA ===" -ForegroundColor Cyan
Write-Host "`n"

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

$erros = 0
$sucessos = 0

# Teste 1: Verificar configuração do Django
Write-Host "1. Verificando configuração do Django..." -ForegroundColor Yellow
$result = python manage.py check 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Sistema sem erros" -ForegroundColor Green
    $sucessos++
} else {
    Write-Host "   [ERRO] Erros encontrados!" -ForegroundColor Red
    Write-Host $result
    $erros++
}

# Teste 2: Verificar se .env existe
Write-Host "`n2. Verificando arquivo .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   [OK] Arquivo .env existe" -ForegroundColor Green
    $sucessos++
    
    # Verificar se SECRET_KEY está no .env
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "SECRET_KEY=") {
        Write-Host "   [OK] SECRET_KEY configurada" -ForegroundColor Green
        $sucessos++
    } else {
        Write-Host "   [ERRO] SECRET_KEY nao encontrada no .env!" -ForegroundColor Red
        $erros++
    }
} else {
    Write-Host "   [ERRO] Arquivo .env nao encontrado!" -ForegroundColor Red
    Write-Host "   Execute: python scripts/config/criar_env.py" -ForegroundColor Yellow
    $erros++
}

# Teste 3: Verificar se django-ratelimit está instalado
Write-Host "`n3. Verificando django-ratelimit..." -ForegroundColor Yellow
$result = python -c "import django_ratelimit; print('OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] django-ratelimit instalado" -ForegroundColor Green
    $sucessos++
} else {
    Write-Host "   [ERRO] django-ratelimit nao encontrado!" -ForegroundColor Red
    Write-Host "   Execute: pip install django-ratelimit" -ForegroundColor Yellow
    $erros++
}

# Teste 4: Verificar se decorators existem
Write-Host "`n4. Verificando decorators..." -ForegroundColor Yellow
if (Test-Path "notas\decorators.py") {
    Write-Host "   [OK] Arquivo decorators.py existe" -ForegroundColor Green
    $sucessos++
} else {
    Write-Host "   [ERRO] Arquivo decorators.py nao encontrado!" -ForegroundColor Red
    $erros++
}

# Teste 5: Verificar se .env está no .gitignore
Write-Host "`n5. Verificando .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    $gitignore = Get-Content ".gitignore" -Raw
    if ($gitignore -match "\.env") {
        Write-Host "   [OK] .env esta no .gitignore" -ForegroundColor Green
        $sucessos++
    } else {
        Write-Host "   [AVISO] .env nao esta no .gitignore (recomendado adicionar)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   [AVISO] Arquivo .gitignore nao encontrado" -ForegroundColor Yellow
}

# Teste 6: Teste de rate limiting (se script existir)
Write-Host "`n6. Testando rate limiting..." -ForegroundColor Yellow
if (Test-Path "scripts\test\test_rate_limiting.py") {
    $result = python scripts\test\test_rate_limiting.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Rate limiting funcionando" -ForegroundColor Green
        $sucessos++
    } else {
        Write-Host "   [ERRO] Teste de rate limiting falhou" -ForegroundColor Red
        Write-Host $result
        $erros++
    }
} else {
    Write-Host "   [AVISO] Script de teste nao encontrado" -ForegroundColor Yellow
}

# Resumo
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Sucessos: $sucessos" -ForegroundColor Green
Write-Host "Erros: $erros" -ForegroundColor $(if ($erros -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($erros -eq 0) {
    Write-Host "[OK] Todos os testes automatizados passaram!" -ForegroundColor Green
    Write-Host "`nProximos passos:" -ForegroundColor Yellow
    Write-Host "  1. Execute testes manuais conforme docs/TESTES_FASE1.md" -ForegroundColor White
    Write-Host "  2. Teste rate limiting no navegador (5 tentativas erradas)" -ForegroundColor White
    Write-Host "  3. Teste controle de acesso (admin vs funcionario vs cliente)" -ForegroundColor White
} else {
    Write-Host "[ERRO] Alguns testes falharam. Corrija os erros antes de continuar." -ForegroundColor Red
}

Write-Host ""

