@echo off
title Servidor Estelar
cd /d "%~dp0"
echo Iniciando servidor em http://127.0.0.1:8000/
echo.
python manage.py runserver
pause
