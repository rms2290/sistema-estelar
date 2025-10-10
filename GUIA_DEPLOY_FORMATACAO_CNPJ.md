# 🚀 Deploy - Formatação de CNPJ (Sem Perda de Dados)

## 📋 O que será atualizado

✅ **Será modificado:**
- Filtros de template para formatação de CNPJ, CPF e telefone
- 11 templates HTML (telas de cliente)
- Arquivos estáticos

❌ **NÃO será modificado:**
- Banco de dados (db.sqlite3)
- Models (estrutura de dados)
- Dados existentes
- Configurações do servidor

---

## 🔐 Credenciais SSH

Antes de começar, tenha em mãos:
- **Host:** seu_servidor.locaweb.com.br
- **Usuário:** seu_usuario
- **Senha:** sua_senha
- **Caminho do projeto:** /home/seu_usuario/sistema-estelar (ajuste conforme necessário)

---

## 📝 Passo a Passo

### **1️⃣ Conectar ao Servidor via SSH**

No seu computador, abra o terminal e execute:

```bash
ssh seu_usuario@seu_servidor.locaweb.com.br
```

Digite a senha quando solicitado.

---

### **2️⃣ Navegar até o Diretório do Projeto**

```bash
cd /caminho/para/sistema-estelar
# ou
cd ~/sistema-estelar
# ou
cd /home/seu_usuario/sistema-estelar
```

Verifique se está no lugar certo:

```bash
ls -la
# Deve mostrar: manage.py, notas/, venv/, etc.
```

---

### **3️⃣ Fazer Upload do Script de Deploy**

**Opção A: Usar o script automático**

No servidor, faça o download do script:

```bash
# Baixar o script do repositório
curl -o deploy_formatacao_cnpj.sh https://raw.githubusercontent.com/rms2290/sistema-estelar/main/deploy_formatacao_cnpj.sh

# Dar permissão de execução
chmod +x deploy_formatacao_cnpj.sh
```

**Opção B: Copiar o script manualmente (se a Opção A não funcionar)**

No seu computador local, envie o arquivo via SCP:

```bash
scp deploy_formatacao_cnpj.sh seu_usuario@seu_servidor:/caminho/para/sistema-estelar/
```

Depois, no servidor:

```bash
chmod +x deploy_formatacao_cnpj.sh
```

---

### **4️⃣ Executar o Script de Deploy**

```bash
./deploy_formatacao_cnpj.sh
```

O script irá:
1. ✅ Fazer backup do código atual
2. ✅ Baixar as alterações do GitHub
3. ✅ Coletar arquivos estáticos
4. ✅ Reiniciar o serviço automaticamente
5. ✅ Testar se a aplicação está respondendo

**Observação:** Se o script solicitar senha sudo, digite a senha do usuário.

---

### **5️⃣ Deploy Manual (Alternativa ao Script)**

Se preferir fazer manualmente, siga estes passos:

#### **5.1. Fazer Backup**

```bash
# Criar diretório de backup
mkdir -p backups/deploy_$(date +%Y%m%d_%H%M%S)

# Copiar templates atuais
cp -r notas/templatetags backups/deploy_$(date +%Y%m%d_%H%M%S)/
cp -r notas/templates backups/deploy_$(date +%Y%m%d_%H%M%S)/

echo "✅ Backup criado!"
```

#### **5.2. Atualizar o Código**

```bash
# Salvar alterações locais (se houver)
git stash

# Atualizar do repositório
git pull origin main

# Ver o que foi atualizado
git log -1 --stat

echo "✅ Código atualizado!"
```

#### **5.3. Ativar Ambiente Virtual**

```bash
source venv/bin/activate
# Deve aparecer (venv) no prompt
```

#### **5.4. Coletar Arquivos Estáticos**

```bash
python manage.py collectstatic --noinput
echo "✅ Arquivos estáticos coletados!"
```

#### **5.5. Reiniciar o Serviço**

**Opção A: Com systemd**
```bash
sudo systemctl restart sistema-estelar
sudo systemctl status sistema-estelar
```

**Opção B: Com supervisor**
```bash
sudo supervisorctl restart sistema-estelar
sudo supervisorctl status sistema-estelar
```

**Opção C: Com gunicorn manual**
```bash
# Parar
pkill -f gunicorn

# Aguardar
sleep 2

# Iniciar
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &

# Verificar
ps aux | grep gunicorn
```

#### **5.6. Recarregar Nginx**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🧪 Testar o Deploy

### **1. Testar Conectividade**

```bash
curl -I http://localhost:8000
# Deve retornar: HTTP/1.1 200 OK ou HTTP/1.1 302 Found
```

### **2. Verificar Logs**

```bash
# Ver últimas 20 linhas do log
tail -20 logs/gunicorn.log

# Monitorar em tempo real
tail -f logs/gunicorn.log
```

### **3. Testar no Navegador**

1. Acesse: `http://seu-dominio.com.br`
2. Faça login normalmente
3. Vá em **"Pesquisar Clientes"**
4. Faça uma busca
5. **Verifique:** O CNPJ deve aparecer formatado: **00.000.000/0000-00**
6. Clique em **"Ver Detalhes"** de um cliente
7. **Verifique:** O CNPJ também deve estar formatado

### **4. Telas que Foram Atualizadas**

✅ Verifique a formatação nestas telas:

- [ ] Listagem de clientes (`/notas/clientes/`)
- [ ] Detalhes do cliente
- [ ] Dashboard (`/notas/`)
- [ ] Totalizador por cliente
- [ ] Impressão de romaneio
- [ ] Impressão de nota fiscal
- [ ] Relatório de depósito
- [ ] Relatório de mercadorias
- [ ] Detalhes de agenda de entrega

---

## ⚠️ Solução de Problemas

### **Problema: Erro "Permission denied" ao executar script**

```bash
chmod +x deploy_formatacao_cnpj.sh
./deploy_formatacao_cnpj.sh
```

### **Problema: Erro "git pull failed"**

```bash
# Ver status
git status

# Se houver conflitos, salve alterações
git stash

# Tente novamente
git pull origin main
```

### **Problema: Serviço não reinicia**

```bash
# Ver logs de erro
journalctl -u sistema-estelar -n 50

# ou
sudo supervisorctl tail sistema-estelar stderr

# Reiniciar manualmente
sudo systemctl restart sistema-estelar
```

### **Problema: CNPJ não está formatado**

1. Verificar se os templates foram atualizados:
```bash
grep "format_cnpj" notas/templates/notas/listar_clientes.html
# Deve retornar: {{ cliente.cnpj|format_cnpj }}
```

2. Verificar se o filtro existe:
```bash
grep "def format_cnpj" notas/templatetags/format_filters.py
# Deve retornar a função
```

3. Limpar cache do navegador (Ctrl+Shift+Del)

4. Recarregar arquivos estáticos:
```bash
python manage.py collectstatic --clear --noinput
```

5. Reiniciar o serviço novamente

### **Problema: Erro 502 Bad Gateway**

```bash
# Verificar se gunicorn está rodando
ps aux | grep gunicorn

# Se não estiver, iniciar
cd /caminho/para/sistema-estelar
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 sistema_estelar.wsgi:application
```

---

## 📊 Verificações Finais

### **Checklist Pós-Deploy**

- [ ] Código atualizado do GitHub
- [ ] Backup criado
- [ ] Arquivos estáticos coletados
- [ ] Serviço reiniciado com sucesso
- [ ] Nginx recarregado
- [ ] Aplicação responde no navegador
- [ ] Login funciona normalmente
- [ ] CNPJ aparece formatado na listagem
- [ ] CNPJ aparece formatado nos detalhes
- [ ] Telefone também está formatado
- [ ] Todos os dados anteriores estão intactos

---

## 📞 Comandos Úteis

### **Ver logs em tempo real**

```bash
# Gunicorn
tail -f logs/gunicorn.log

# Django
tail -f logs/django.log

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### **Status dos serviços**

```bash
# Systemd
sudo systemctl status sistema-estelar

# Supervisor
sudo supervisorctl status sistema-estelar

# Nginx
sudo systemctl status nginx
```

### **Reverter alterações (se necessário)**

```bash
# Reverter último commit
git reset --hard HEAD~1

# Restaurar do backup
ULTIMO_BACKUP=$(ls -t backups/ | head -1)
cp -r backups/$ULTIMO_BACKUP/templatetags notas/
cp -r backups/$ULTIMO_BACKUP/templates notas/

# Reiniciar serviço
sudo systemctl restart sistema-estelar
```

---

## ✅ Resumo das Alterações

**Arquivos Modificados:**
1. `notas/templatetags/format_filters.py` - Adicionados filtros de formatação
2. `notas/templates/notas/listar_clientes.html` - Aplicado filtro format_cnpj
3. `notas/templates/notas/detalhes_cliente.html` - Aplicado filtro format_cnpj
4. `notas/templates/notas/dashboard.html` - Aplicado filtro format_cnpj
5. Mais 8 templates atualizados

**Tipo de Alteração:**
- ✅ Apenas templates (apresentação)
- ✅ Apenas filtros (formatação visual)
- ❌ Nenhuma migração de banco
- ❌ Nenhuma alteração em models
- ❌ Nenhum dado será perdido

---

## 🎉 Deploy Concluído!

Após seguir todos os passos, a formatação de CNPJ estará ativa em todas as telas!

**Formato aplicado:**
- **CNPJ:** 00.000.000/0000-00
- **Telefone:** (00) 00000-0000

**Data do Deploy:** _____________
**Responsável:** _____________
**Commit:** 6796c92

