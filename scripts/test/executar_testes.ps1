# Script para executar todos os testes do projeto
# Uso: .\scripts\test\executar_testes.ps1 [opcoes]

param(
    [string]$Tipo = "todos",  # todos, modelos, forms, views, services, integracao
    [switch]$Cobertura = $false,
    [switch]$Verbose = $false,
    [string]$Arquivo = ""
)

# Ativar ambiente virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "[ERRO] Ambiente virtual nao encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== EXECUTANDO TESTES ===" -ForegroundColor Cyan
Write-Host "Tipo: $Tipo" -ForegroundColor Yellow

# Construir comando pytest
$pytestArgs = @()

if ($Verbose) {
    $pytestArgs += "-vv"
} else {
    $pytestArgs += "-v"
}

if ($Cobertura) {
    $pytestArgs += "--cov=notas"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=html"
}

# Selecionar arquivos de teste baseado no tipo
switch ($Tipo) {
    "modelos" {
        $pytestArgs += "notas/tests/test_models.py"
    }
    "forms" {
        $pytestArgs += "notas/tests/test_forms.py"
    }
    "views" {
        $pytestArgs += "notas/tests/test_views.py"
    }
    "services" {
        $pytestArgs += "notas/tests/test_services.py"
    }
    "integracao" {
        $pytestArgs += "notas/tests/test_integration.py"
    }
    "imports" {
        $pytestArgs += "notas/tests/test_imports.py"
    }
    default {
        if ($Arquivo) {
            $pytestArgs += $Arquivo
        } else {
            $pytestArgs += "notas/tests/"
        }
    }
}

# Executar testes
Write-Host "`nExecutando: pytest $($pytestArgs -join ' ')" -ForegroundColor Yellow
pytest $pytestArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Todos os testes passaram!" -ForegroundColor Green
    if ($Cobertura) {
        Write-Host "`nRelatorio de cobertura gerado em: htmlcov/index.html" -ForegroundColor Cyan
    }
} else {
    Write-Host "`n[ERRO] Alguns testes falharam!" -ForegroundColor Red
    exit 1
}


