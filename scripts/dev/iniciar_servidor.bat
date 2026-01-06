@echo off
REM Script para iniciar o servidor Django diretamente (CMD)
REM Uso: scripts\dev\iniciar_servidor.bat ou usar o wrapper na raiz: iniciar_servidor.bat

REM Mudar para o diretório raiz do projeto
cd /d "%~dp0\..\.."

echo === Iniciando Servidor Django ===

REM Verificar se o ambiente virtual está ativo
if "%VIRTUAL_ENV%"=="" (
    echo AVISO: Ambiente virtual nao esta ativo. Ativando...
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    ) else (
        echo ERRO: Ambiente virtual nao encontrado!
        echo Execute primeiro: ativar.bat
        pause
        exit /b 1
    )
)

REM Verificar se Django está disponível
python -c "import django" 2>nul
if errorlevel 1 (
    echo ERRO: Django nao encontrado!
    echo Execute: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Verificar se django-ratelimit está instalado
python -c "import django_ratelimit" 2>nul
if errorlevel 1 (
    echo AVISO: django-ratelimit nao encontrado. Instalando...
    pip install django-ratelimit
    if errorlevel 1 (
        echo ERRO: Falha ao instalar django-ratelimit!
        pause
        exit /b 1
    )
    echo django-ratelimit instalado
)

echo Ambiente verificado
echo.
echo Iniciando servidor em http://127.0.0.1:8000
echo Pressione Ctrl+C para parar o servidor
echo.

REM Iniciar servidor
python manage.py runserver


