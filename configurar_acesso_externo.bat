@echo off
echo ========================================
echo Configurando Acesso Externo ao Sistema
echo ========================================
echo.

echo 1. Verificando IP do servidor...
ipconfig | findstr "IPv4"
echo.

echo 2. Verificando se o servidor está rodando...
netstat -an | findstr :8000
echo.

echo 3. Para permitir conexões no firewall, execute como administrador:
echo netsh advfirewall firewall add rule name="Django Sistema Estelar" dir=in action=allow protocol=TCP localport=8000
echo.

echo 4. URL de acesso:
echo http://192.168.15.22:8000
echo.

echo 5. Credenciais de teste:
echo Admin: admin / 123456
echo Funcionario: Celso / 123456
echo Cliente: cliente / 123456
echo.

echo 6. Para iniciar o servidor:
echo python manage.py runserver 0.0.0.0:8000
echo.

pause 