@echo off
REM Script de ativação do ambiente virtual e servidor Django (CMD)
REM Uso: scripts\dev\ativar.bat ou usar o wrapper na raiz: ativar.bat

REM Mudar para o diretório raiz do projeto
cd /d "%~dp0\..\.."

echo === Sistema Estelar - Ativacao ===

REM Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute: python -m venv venv
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo.
echo [1/3] Ativando ambiente virtual...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERRO: Falha ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo Ambiente virtual ativado

REM Verificar se Django está instalado
echo.
echo [2/3] Verificando dependencias...
python -c "import django" 2>nul

if errorlevel 1 (
    echo AVISO: Django nao encontrado. Instalando dependencias...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERRO: Falha ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo Dependencias verificadas

REM Verificar sistema
echo.
echo [3/3] Verificando banco de dados...
python manage.py check >nul 2>&1

echo Sistema pronto!
echo.
echo === Comandos disponiveis ===
echo   python manage.py runserver          - Iniciar servidor de desenvolvimento
echo   python manage.py migrate            - Aplicar migracoes
echo   python manage.py createsuperuser    - Criar usuario admin
echo.
echo Para iniciar o servidor, execute:
echo   python manage.py runserver
echo.



