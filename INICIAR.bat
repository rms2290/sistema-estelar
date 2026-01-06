@echo off
REM Script para iniciar o servidor a partir de qualquer diretório
REM Uso: Execute este arquivo de qualquer lugar

cd /d "%~dp0"
python manage.py runserver


