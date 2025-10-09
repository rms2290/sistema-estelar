# 🚀 Guia de Deploy - Atualização Sistema Estelar na Locaweb

## 📋 Pré-requisitos
- Acesso SSH ao servidor Locaweb
- Git instalado no servidor
- Python 3.8+ instalado
- Permissões de administrador (sudo)

---

## 🔐 Credenciais do Sistema

**Usuário Master Admin:**
- **Username:** `admin`
- **Password:** `123456`
- **Email:** admin@estelar.com

**⚠️ IMPORTANTE:** Altere esta senha após o primeiro login!

---

## 📦 Atualizações Incluídas

### ✅ Melhorias no Layout de Impressão
- Layout do romaneio completamente redesenhado
- Informações da empresa no cabeçalho
- Campos organizados: Romaneio, Motorista e Cliente
- Número do romaneio no canto superior direito
- Todos os textos em maiúsculo e negrito

### ✅ Relatórios de Mercadorias
- Novo relatório de mercadorias no depósito
- Botão de impressão com visualização prévia
- Dados do cliente no relatório
- Layout otimizado para impressão

### ✅ Melhorias de Interface
- Menu lateral simplificado para clientes
- Ícones corrigidos (Font Awesome atualizado)
- Botões de impressão padronizados

### ✅ Sistema Limpo
- Banco de dados zerado
- Pronto para início de operação
- Apenas usuário admin criado

---

## 🛠️ Passo a Passo do Deploy

### **1️⃣ Conectar ao Servidor**

```bash
# Conectar via SSH
ssh seu_usuario@seu_servidor_locaweb.com.br

# Navegar até o diretório do projeto
cd /caminho/para/sistema-estelar
```

### **2️⃣ Fazer Backup do Banco de Dados Atual**

```bash
# Criar diretório de backup se não existir
mkdir -p backups

# Backup do banco de dados
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# Verificar backup
ls -lh backups/
```

### **3️⃣ Atualizar o Código do Repositório**

```bash
# Verificar branch atual
git branch

# Fazer stash de alterações locais (se houver)
git stash

# Atualizar código
git pull origin main

# Verificar se atualizou
git log -1
```

### **4️⃣ Ativar Ambiente Virtual**

```bash
# Ativar o ambiente virtual
source venv/bin/activate

# Verificar se está ativo (deve mostrar (venv) no prompt)
```

### **5️⃣ Instalar/Atualizar Dependências**

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências de produção
pip install -r requirements_production.txt

# Verificar instalação
pip list | grep Django
```

### **6️⃣ Executar Migrações do Banco de Dados**

```bash
# Verificar migrações pendentes
python manage.py showmigrations

# Executar migrações
python manage.py migrate

# Verificar se aplicou corretamente
python manage.py migrate --plan
```

### **7️⃣ Coletar Arquivos Estáticos**

```bash
# Coletar arquivos estáticos (CSS, JS, imagens)
python manage.py collectstatic --noinput

# Verificar se coletou
ls -lh staticfiles/css/
```

### **8️⃣ Criar Usuário Admin (se necessário)**

```bash
# Se precisar criar o usuário admin manualmente
python manage.py shell

# No shell Python, execute:
from notas.models import Usuario
user = Usuario.objects.create_superuser(
    username='admin',
    email='admin@estelar.com',
    password='123456',
    first_name='Administrador',
    last_name='Master',
    tipo_usuario='admin'
)
print("Usuario criado!")
exit()
```

### **9️⃣ Reiniciar o Serviço**

**Opção A: Com Gunicorn + Supervisor**
```bash
# Reiniciar via supervisor
sudo supervisorctl restart sistema-estelar

# Verificar status
sudo supervisorctl status sistema-estelar
```

**Opção B: Com Gunicorn Manualmente**
```bash
# Parar processo atual
pkill -f gunicorn

# Aguardar 2 segundos
sleep 2

# Iniciar novamente
nohup gunicorn --bind 127.0.0.1:8000 --workers 3 --timeout 120 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &

# Verificar se está rodando
ps aux | grep gunicorn
```

**Opção C: Com systemd**
```bash
# Reiniciar serviço
sudo systemctl restart sistema-estelar

# Verificar status
sudo systemctl status sistema-estelar
```

### **🔟 Reiniciar Nginx**

```bash
# Testar configuração do nginx
sudo nginx -t

# Se ok, reiniciar nginx
sudo systemctl reload nginx

# Verificar status
sudo systemctl status nginx
```

---

## 🧪 Testes Pós-Deploy

### **1. Testar Conectividade Local**
```bash
# Testar se a aplicação está respondendo
curl -I http://localhost:8000

# Deve retornar HTTP 200 ou 302
```

### **2. Verificar Logs**
```bash
# Ver últimas linhas do log do gunicorn
tail -f logs/gunicorn.log

# Ver log do Django
tail -f logs/django.log

# Ver log do nginx
sudo tail -f /var/log/nginx/error.log
```

### **3. Testar no Navegador**
1. Acesse: `http://seu-dominio.com.br`
2. Faça login com: `admin` / `123456`
3. Teste as funcionalidades:
   - ✅ Cadastro de clientes
   - ✅ Cadastro de motoristas
   - ✅ Cadastro de veículos
   - ✅ Lançamento de notas fiscais
   - ✅ Criação de romaneios
   - ✅ Impressão de romaneios
   - ✅ Relatório de mercadorias

---

## 🐛 Solução de Problemas

### **Problema: Aplicação não inicia**
```bash
# Verificar logs de erro
tail -100 logs/gunicorn.log

# Verificar se há processo travado
ps aux | grep gunicorn | grep -v grep

# Matar processos travados
pkill -9 -f gunicorn

# Iniciar novamente
gunicorn --bind 127.0.0.1:8000 sistema_estelar.wsgi:application
```

### **Problema: Erro 502 Bad Gateway**
```bash
# Verificar se gunicorn está rodando
ps aux | grep gunicorn

# Se não estiver, iniciar
cd /caminho/para/sistema-estelar
source venv/bin/activate
gunicorn --bind 127.0.0.1:8000 sistema_estelar.wsgi:application
```

### **Problema: Arquivos estáticos não carregam**
```bash
# Recoletar arquivos estáticos
python manage.py collectstatic --clear --noinput

# Verificar permissões
ls -la staticfiles/

# Ajustar permissões se necessário
sudo chown -R www-data:www-data staticfiles/
sudo chmod -R 755 staticfiles/
```

### **Problema: Erro de permissão no banco de dados**
```bash
# Verificar permissões do db.sqlite3
ls -la db.sqlite3

# Ajustar permissões
sudo chown www-data:www-data db.sqlite3
sudo chmod 664 db.sqlite3
```

### **Problema: Migrações não aplicam**
```bash
# Verificar estado das migrações
python manage.py showmigrations

# Fazer fake migrate se necessário (cuidado!)
python manage.py migrate --fake-initial

# Ou aplicar migração específica
python manage.py migrate notas 0036
```

---

## 📊 Monitoramento Pós-Deploy

### **Verificar Uso de Recursos**
```bash
# Uso de CPU e memória
top -b -n 1 | grep gunicorn

# Espaço em disco
df -h

# Processos Python
ps aux | grep python
```

### **Monitorar Logs em Tempo Real**
```bash
# Abrir múltiplas abas do terminal e executar:

# Aba 1: Log do Gunicorn
tail -f logs/gunicorn.log

# Aba 2: Log do Django
tail -f logs/django.log

# Aba 3: Log do Nginx
sudo tail -f /var/log/nginx/access.log
```

---

## 🔒 Configurações de Segurança

### **Após Deploy, Configure:**

1. **Alterar senha do admin**
   - Faça login no sistema
   - Acesse configurações de usuário
   - Altere para uma senha forte

2. **Configurar SECRET_KEY**
   - Gere uma nova SECRET_KEY
   - Atualize no arquivo de configuração
   - Reinicie a aplicação

3. **Configurar ALLOWED_HOSTS**
   - Adicione seu domínio em `settings.py`
   - Exemplo: `ALLOWED_HOSTS = ['seu-dominio.com.br', 'www.seu-dominio.com.br']`

4. **Habilitar HTTPS**
   - Configure certificado SSL
   - Atualize nginx para redirecionar HTTP → HTTPS
   - Configure `SECURE_SSL_REDIRECT = True`

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs primeiro
2. Consulte a documentação do Django
3. Verifique as issues do GitHub
4. Entre em contato com o suporte técnico

---

## ✅ Checklist de Deploy

- [ ] Backup do banco de dados realizado
- [ ] Código atualizado do GitHub
- [ ] Dependências instaladas/atualizadas
- [ ] Migrações aplicadas
- [ ] Arquivos estáticos coletados
- [ ] Usuário admin criado/verificado
- [ ] Gunicorn reiniciado
- [ ] Nginx reiniciado
- [ ] Teste de conectividade OK
- [ ] Login no sistema OK
- [ ] Funcionalidades principais testadas
- [ ] Senha do admin alterada
- [ ] Logs sendo monitorados

---

## 🎉 Deploy Concluído!

Após completar todos os passos, seu sistema estará atualizado e funcionando com todas as novas funcionalidades!

**Data do Deploy:** _____________
**Responsável:** _____________
**Versão:** 1.0.0 (Sistema Zerado - Produção Inicial)

