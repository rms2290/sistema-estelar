# Script para iniciar o servidor a partir de qualquer diretório
# Uso: Execute este arquivo de qualquer lugar

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
python manage.py runserver


