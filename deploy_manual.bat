@echo off
echo 🚀 Deploy Manual do Sistema Estelar na Locaweb
echo =============================================

echo.
echo 1️⃣ Fazendo commit das mudanças...
git add .
git commit -m "Deploy: Correções do menu e configurações de produção"

echo.
echo 2️⃣ Enviando para o repositório...
git push origin main

echo.
echo 3️⃣ Criando script de deploy para o servidor...
echo.
echo ✅ Deploy local concluído!
echo.
echo 📋 Próximos passos no servidor Locaweb:
echo ======================================
echo 1. Conecte no servidor via SSH
echo 2. Execute: cd /var/www/sistema-estelar
echo 3. Execute: git pull origin main
echo 4. Execute: chmod +x deploy_servidor.sh
echo 5. Execute: ./deploy_servidor.sh
echo.
echo OU execute os comandos individuais:
echo wget https://raw.githubusercontent.com/seu-usuario/sistema-estelar/main/deploy_servidor.sh
echo chmod +x deploy_servidor.sh
echo ./deploy_servidor.sh
echo.
pause