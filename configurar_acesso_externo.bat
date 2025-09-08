@echo off
echo ========================================
echo  Configuracao de Acesso Externo
echo  Sistema Estelar - Locaweb
echo ========================================
echo.

echo [1/5] Verificando arquivos de configuracao...
if not exist "nginx.conf" (
    echo ERRO: Arquivo nginx.conf nao encontrado!
    pause
    exit /b 1
)

if not exist "gunicorn.conf.py" (
    echo ERRO: Arquivo gunicorn.conf.py nao encontrado!
    pause
    exit /b 1
)

echo [2/5] Configurando nginx...
echo Criando arquivo de configuracao do nginx...

(
echo server {
echo     listen 80;
echo     server_name _;
echo.    
echo     # Configuracoes de arquivos estaticos
echo     location /static/ {
echo         alias /var/www/sistema-estelar/staticfiles/;
echo         expires 1y;
echo         add_header Cache-Control "public, immutable";
echo     }
echo.    
echo     # Configuracoes de arquivos de midia
echo     location /media/ {
echo         alias /var/www/sistema-estelar/media/;
echo         expires 1y;
echo         add_header Cache-Control "public";
echo     }
echo.    
echo     # Configuracoes da aplicacao Django
echo     location / {
echo         proxy_pass http://127.0.0.1:8000;
echo         proxy_set_header Host $host;
echo         proxy_set_header X-Real-IP $remote_addr;
echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo         proxy_set_header X-Forwarded-Proto $scheme;
echo         proxy_redirect off;
echo     }
echo.    
echo     # Configuracoes de seguranca
echo     add_header X-Frame-Options "SAMEORIGIN" always;
echo     add_header X-Content-Type-Options "nosniff" always;
echo     add_header X-XSS-Protection "1; mode=block" always;
echo     add_header Referrer-Policy "no-referrer-when-downgrade" always;
echo }
) > nginx_sistema_estelar.conf

echo [3/5] Configurando supervisor...
echo Criando arquivo de configuracao do supervisor...

(
echo [program:sistema-estelar]
echo command=/var/www/sistema-estelar/venv/bin/gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
echo directory=/var/www/sistema-estelar
echo user=www-data
echo autostart=true
echo autorestart=true
echo redirect_stderr=true
echo stdout_logfile=/var/log/supervisor/sistema-estelar.log
echo stderr_logfile=/var/log/supervisor/sistema-estelar_error.log
) > supervisor_sistema_estelar.conf

echo [4/5] Criando script de instalacao...
echo Criando script de instalacao automatica...

(
echo #!/bin/bash
echo echo "Instalando Sistema Estelar na Locaweb..."
echo.
echo # Copiar configuracao do nginx
echo sudo cp nginx_sistema_estelar.conf /etc/nginx/sites-available/sistema-estelar
echo sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
echo sudo rm -f /etc/nginx/sites-enabled/default
echo.
echo # Testar e reiniciar nginx
echo sudo nginx -t
echo sudo systemctl restart nginx
echo.
echo # Copiar configuracao do supervisor
echo sudo cp supervisor_sistema_estelar.conf /etc/supervisor/conf.d/sistema-estelar.conf
echo sudo supervisorctl reread
echo sudo supervisorctl update
echo sudo supervisorctl start sistema-estelar
echo.
echo # Configurar permissoes
echo sudo chown -R www-data:www-data /var/www/sistema-estelar
echo sudo chmod -R 755 /var/www/sistema-estelar
echo.
echo # Coletar arquivos estaticos
echo python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production
echo.
echo # Executar migracoes
echo python manage.py migrate --settings=sistema_estelar.settings_production
echo.
echo echo "Instalacao concluida!"
echo echo "Teste acessando: http://seu-dominio.com.br"
) > instalar_locaweb.sh

echo [5/5] Criando arquivo de comandos manuais...
echo Criando arquivo com comandos para execucao manual...

(
echo # Comandos para executar no servidor Locaweb
echo.
echo # 1. Copiar arquivos de configuracao
echo sudo cp nginx_sistema_estelar.conf /etc/nginx/sites-available/sistema-estelar
echo sudo cp supervisor_sistema_estelar.conf /etc/supervisor/conf.d/sistema-estelar.conf
echo.
echo # 2. Ativar site no nginx
echo sudo ln -sf /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/
echo sudo rm -f /etc/nginx/sites-enabled/default
echo.
echo # 3. Testar e reiniciar nginx
echo sudo nginx -t
echo sudo systemctl restart nginx
echo.
echo # 4. Configurar supervisor
echo sudo supervisorctl reread
echo sudo supervisorctl update
echo sudo supervisorctl start sistema-estelar
echo.
echo # 5. Configurar permissoes
echo sudo chown -R www-data:www-data /var/www/sistema-estelar
echo sudo chmod -R 755 /var/www/sistema-estelar
echo.
echo # 6. Coletar arquivos estaticos
echo python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production
echo.
echo # 7. Executar migracoes
echo python manage.py migrate --settings=sistema_estelar.settings_production
echo.
echo # 8. Testar a aplicacao
echo curl http://localhost:8000
echo curl http://seu-dominio.com.br
) > comandos_locaweb.txt

echo.
echo ========================================
echo  CONFIGURACAO CONCLUIDA!
echo ========================================
echo.
echo Arquivos criados:
echo - nginx_sistema_estelar.conf
echo - supervisor_sistema_estelar.conf
echo - instalar_locaweb.sh
echo - comandos_locaweb.txt
echo.
echo PROXIMOS PASSOS:
echo 1. Copie estes arquivos para o servidor Locaweb
echo 2. Execute: chmod +x instalar_locaweb.sh
echo 3. Execute: ./instalar_locaweb.sh
echo.
echo OU execute os comandos manualmente conforme o arquivo comandos_locaweb.txt
echo.
pause