# 🚀 PASSO A PASSO - Deploy na Locaweb (SIMPLIFICADO)

## 📋 Informações Importantes

**Credenciais do Sistema:**
- Username: `admin`
- Password: `123456`

---

## 🔐 PASSO 1: Conectar ao Servidor via SSH

### **Windows (PowerShell ou CMD):**
```powershell
ssh seu_usuario@seu_dominio.com.br
# OU
ssh seu_usuario@IP_DO_SERVIDOR
```

### **Exemplo:**
```powershell
ssh estelar@sistema.com.br
```

**Digite a senha do SSH quando solicitado.**

---

## 📂 PASSO 2: Localizar o Diretório do Projeto

### **2.1 - Ver onde você está:**
```bash
pwd
```

### **2.2 - Listar diretórios:**
```bash
ls -la
```

### **2.3 - Localizar o projeto (possíveis localizações):**

**Opção A - Diretório público:**
```bash
cd public_html
ls -la
```

**Opção B - Diretório home:**
```bash
cd ~
ls -la
```

**Opção C - Diretório www:**
```bash
cd /var/www
ls -la
```

**Opção D - Buscar o projeto:**
```bash
find ~ -name "manage.py" -type f 2>/dev/null
```

### **2.4 - Entrar no diretório do projeto:**
```bash
cd /caminho/encontrado/sistema-estelar
# Substitua pelo caminho correto que você encontrou
```

### **2.5 - Verificar se está no lugar certo:**
```bash
ls -la
# Você deve ver: manage.py, notas/, sistema_estelar/, etc.
```

---

## 📥 PASSO 3: Atualizar o Código do GitHub

### **3.1 - Verificar status atual:**
```bash
git status
```

### **3.2 - Fazer backup de alterações locais (se houver):**
```bash
git stash
```

### **3.3 - Atualizar código:**
```bash
git pull origin main
```

**Você deve ver mensagens indicando arquivos atualizados.**

---

## 🐍 PASSO 4: Ativar o Ambiente Virtual Python

### **4.1 - Verificar se o ambiente virtual existe:**
```bash
ls -la | grep venv
```

### **4.2 - Ativar o ambiente virtual:**

**Se o venv está no diretório atual:**
```bash
source venv/bin/activate
```

**Se o venv está um nível acima:**
```bash
source ../venv/bin/activate
```

**Você saberá que funcionou quando aparecer `(venv)` no início da linha do terminal.**

### **4.3 - Verificar se está ativo:**
```bash
which python
# Deve mostrar: /caminho/para/venv/bin/python
```

---

## 📦 PASSO 5: Instalar/Atualizar Dependências

### **5.1 - Atualizar o pip:**
```bash
pip install --upgrade pip
```

### **5.2 - Instalar dependências de produção:**
```bash
pip install -r requirements_production.txt
```

**OU, se não tiver requirements_production.txt:**
```bash
pip install -r requirements.txt
```

**Aguarde a instalação (pode levar alguns minutos).**

---

## 🗄️ PASSO 6: Fazer Backup do Banco de Dados

### **6.1 - Criar diretório de backup:**
```bash
mkdir -p backups
```

### **6.2 - Copiar banco de dados:**
```bash
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

### **6.3 - Verificar backup:**
```bash
ls -lh backups/
```

---

## 🔄 PASSO 7: Executar Migrações

### **7.1 - Ver migrações pendentes:**
```bash
python manage.py showmigrations
```

### **7.2 - Executar migrações:**
```bash
python manage.py migrate
```

**Você deve ver mensagens como "Applying notas.0036... OK"**

---

## 📄 PASSO 8: Coletar Arquivos Estáticos

### **8.1 - Coletar CSS, JS e imagens:**
```bash
python manage.py collectstatic --noinput
```

**Aguarde a coleta dos arquivos.**

---

## ✅ PASSO 9: Verificar Configuração

### **9.1 - Verificar se está tudo OK:**
```bash
python manage.py check
```

**Deve mostrar "System check identified no issues"**

---

## 🔄 PASSO 10: Reiniciar os Serviços

### **10.1 - Descobrir como o Gunicorn está rodando:**

**Verificar processos:**
```bash
ps aux | grep gunicorn
```

**Verificar supervisor:**
```bash
sudo supervisorctl status
```

**Verificar systemd:**
```bash
sudo systemctl list-units | grep sistema
```

### **10.2 - OPÇÃO A: Reiniciar via Supervisor (Recomendado)**

```bash
# Ver status
sudo supervisorctl status

# Reiniciar
sudo supervisorctl restart sistema-estelar

# Verificar se reiniciou
sudo supervisorctl status sistema-estelar
```

### **10.3 - OPÇÃO B: Reiniciar via systemd**

```bash
# Reiniciar
sudo systemctl restart sistema-estelar

# Verificar status
sudo systemctl status sistema-estelar
```

### **10.4 - OPÇÃO C: Reiniciar Gunicorn Manualmente**

```bash
# Parar processos atuais
pkill -f gunicorn

# Aguardar 2 segundos
sleep 2

# Iniciar novamente
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &

# Verificar se está rodando
ps aux | grep gunicorn
```

---

## 🌐 PASSO 11: Reiniciar o Nginx

### **11.1 - Testar configuração:**
```bash
sudo nginx -t
```

### **11.2 - Recarregar Nginx:**
```bash
sudo systemctl reload nginx
```

### **11.3 - Verificar status:**
```bash
sudo systemctl status nginx
```

---

## 🧪 PASSO 12: Testar se Funcionou

### **12.1 - Testar localmente no servidor:**
```bash
curl -I http://localhost:8000
```

**Deve retornar: HTTP/1.1 200 OK ou HTTP/1.1 302 Found**

### **12.2 - Ver logs em tempo real:**
```bash
tail -f logs/gunicorn.log
```

**Pressione Ctrl+C para sair.**

### **12.3 - Ver últimas 50 linhas do log:**
```bash
tail -50 logs/gunicorn.log
```

---

## 🌍 PASSO 13: Testar no Navegador

### **13.1 - Acessar o site:**
Abra o navegador e acesse:
```
http://seu-dominio.com.br
```

### **13.2 - Fazer login:**
- **Username:** `admin`
- **Password:** `123456`

### **13.3 - Alterar senha:**
1. Após fazer login, vá em configurações
2. Altere a senha para uma senha segura
3. Anote a nova senha em local seguro

---

## ✅ PASSO 14: Testar Funcionalidades

Teste as seguintes funcionalidades para garantir que está tudo OK:

- [ ] Login funciona
- [ ] Cadastrar um cliente de teste
- [ ] Cadastrar um motorista de teste
- [ ] Cadastrar um veículo de teste
- [ ] Lançar uma nota fiscal
- [ ] Criar um romaneio
- [ ] Imprimir o romaneio (verificar layout)
- [ ] Acessar relatório de mercadorias
- [ ] Verificar se os ícones aparecem corretamente
- [ ] Verificar se o CSS está carregando

---

## 🐛 TROUBLESHOOTING - Problemas Comuns

### **Problema 1: "Permission denied" ao executar comandos**

**Solução:**
```bash
# Ajustar permissões do banco de dados
chmod 664 db.sqlite3

# Ajustar permissões dos diretórios
chmod 755 logs/ media/ staticfiles/
```

### **Problema 2: Gunicorn não inicia**

**Verificar log de erros:**
```bash
tail -100 logs/gunicorn.log
```

**Tentar iniciar manualmente para ver erros:**
```bash
gunicorn --bind 127.0.0.1:8000 sistema_estelar.wsgi:application
```

### **Problema 3: Erro 502 Bad Gateway**

**Significa que o Nginx não consegue se conectar ao Gunicorn.**

**Verificar se Gunicorn está rodando:**
```bash
ps aux | grep gunicorn
```

**Se não estiver, iniciar:**
```bash
gunicorn --bind 127.0.0.1:8000 --workers 3 sistema_estelar.wsgi:application
```

### **Problema 4: CSS e imagens não carregam (Erro 404)**

**Coletar arquivos estáticos novamente:**
```bash
python manage.py collectstatic --clear --noinput
```

**Ajustar permissões:**
```bash
chmod -R 755 staticfiles/
```

### **Problema 5: Erro "No module named..."**

**Reinstalar dependências:**
```bash
pip install -r requirements_production.txt --force-reinstall
```

### **Problema 6: "Not a git repository"**

**Você não está no diretório correto. Volte ao PASSO 2.**

### **Problema 7: Ambiente virtual não ativa**

**Verificar se existe:**
```bash
ls -la venv/bin/activate
```

**Se não existir, criar novo:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_production.txt
```

---

## 📊 COMANDOS ÚTEIS DE MONITORAMENTO

### **Ver processos Python rodando:**
```bash
ps aux | grep python
```

### **Ver processos Gunicorn:**
```bash
ps aux | grep gunicorn
```

### **Ver uso de memória:**
```bash
free -h
```

### **Ver uso de disco:**
```bash
df -h
```

### **Ver logs do Nginx:**
```bash
sudo tail -f /var/log/nginx/error.log
```

### **Ver logs do sistema:**
```bash
sudo journalctl -u sistema-estelar -f
```

---

## 🎯 RESUMO DOS COMANDOS PRINCIPAIS

Se tudo estiver configurado corretamente, você pode usar este resumo:

```bash
# 1. Conectar
ssh seu_usuario@seu_servidor.com.br

# 2. Ir para o diretório
cd /caminho/para/sistema-estelar

# 3. Atualizar código
git pull origin main

# 4. Ativar ambiente
source venv/bin/activate

# 5. Instalar dependências
pip install -r requirements_production.txt

# 6. Migrar banco
python manage.py migrate

# 7. Coletar estáticos
python manage.py collectstatic --noinput

# 8. Reiniciar serviço
sudo supervisorctl restart sistema-estelar
sudo systemctl reload nginx

# 9. Verificar
curl -I http://localhost:8000
tail -50 logs/gunicorn.log
```

---

## 📞 PRECISA DE AJUDA?

Se encontrar algum erro:

1. **Copie a mensagem de erro completa**
2. **Verifique os logs:**
   ```bash
   tail -100 logs/gunicorn.log
   tail -100 logs/django.log
   sudo tail -100 /var/log/nginx/error.log
   ```
3. **Anote o que estava fazendo quando o erro ocorreu**
4. **Tire um print da tela se necessário**

---

## ✅ CHECKLIST FINAL

Após completar o deploy, verifique:

- [ ] Servidor SSH acessível
- [ ] Código atualizado do GitHub
- [ ] Ambiente virtual ativado
- [ ] Dependências instaladas
- [ ] Migrações aplicadas
- [ ] Arquivos estáticos coletados
- [ ] Gunicorn rodando
- [ ] Nginx rodando
- [ ] Site acessível no navegador
- [ ] Login funcionando
- [ ] Senha do admin alterada
- [ ] Funcionalidades principais testadas
- [ ] Logs sem erros críticos

---

## 🎉 DEPLOY CONCLUÍDO!

Parabéns! Se você chegou até aqui e tudo está funcionando, o deploy foi um sucesso!

**Lembre-se:**
- Monitore os logs regularmente
- Faça backup do banco de dados periodicamente
- Mantenha o sistema atualizado
- Documente qualquer configuração adicional que fizer

**BOA SORTE! 🚀**

