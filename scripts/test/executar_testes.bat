@echo off
REM Script para executar todos os testes do projeto
REM Uso: scripts\test\executar_testes.bat [tipo] [opcoes]

setlocal

set TIPO=%1
if "%TIPO%"=="" set TIPO=todos

echo.
echo === EXECUTANDO TESTES ===
echo Tipo: %TIPO%

REM Ativar ambiente virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERRO] Ambiente virtual nao encontrado!
    exit /b 1
)

REM Executar testes
if "%TIPO%"=="modelos" (
    pytest notas/tests/test_models.py -v
) else if "%TIPO%"=="forms" (
    pytest notas/tests/test_forms.py -v
) else if "%TIPO%"=="views" (
    pytest notas/tests/test_views.py -v
) else if "%TIPO%"=="services" (
    pytest notas/tests/test_services.py -v
) else if "%TIPO%"=="integracao" (
    pytest notas/tests/test_integration.py -v
) else if "%TIPO%"=="cobertura" (
    pytest notas/tests/ --cov=notas --cov-report=term-missing --cov-report=html
    echo.
    echo Relatorio de cobertura gerado em: htmlcov/index.html
) else (
    pytest notas/tests/ -v
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [OK] Todos os testes passaram!
) else (
    echo.
    echo [ERRO] Alguns testes falharam!
    exit /b 1
)

endlocal


