# 🧪 GUIA DE TESTES - FASE 1: SEGURANÇA CRÍTICA

**Data:** 26/11/2025  
**Objetivo:** Validar todas as melhorias de segurança implementadas na Fase 1

---

## 📋 CHECKLIST DE TESTES

### ✅ 1. TESTES DE VALIDAÇÃO DO SISTEMA

#### 1.1 Verificar Configuração do Django
```bash
python manage.py check
```
**Resultado esperado:** `System check identified no issues (0 silenced).`

#### 1.2 Verificar Configuração de Produção
```bash
python manage.py check --deploy
```
**Resultado esperado:** Avisos sobre DEBUG=True são normais em desenvolvimento

#### 1.3 Verificar Migrações
```bash
python manage.py showmigrations
```
**Resultado esperado:** Todas as migrações aplicadas (✓)

---

### ✅ 2. TESTES DE SECRET_KEY

#### 2.1 Verificar se .env existe
```bash
# Windows PowerShell
Test-Path .env

# Deve retornar: True
```

#### 2.2 Verificar se SECRET_KEY está configurada
```bash
python manage.py shell -c "from django.conf import settings; print('SECRET_KEY configurada:', bool(settings.SECRET_KEY))"
```
**Resultado esperado:** `SECRET_KEY configurada: True`

#### 2.3 Testar sem SECRET_KEY (simulação)
```bash
# Fazer backup do .env
Copy-Item .env .env.backup

# Remover SECRET_KEY temporariamente
# (Editar .env e comentar SECRET_KEY)

# Tentar iniciar servidor
python manage.py check

# Resultado esperado: ERRO sobre SECRET_KEY faltando

# Restaurar .env
Copy-Item .env.backup .env
```

---

### ✅ 3. TESTES DE ALLOWED_HOSTS

#### 3.1 Testar acesso local
```bash
# Iniciar servidor
python manage.py runserver

# Acessar no navegador:
# http://localhost:8000/notas/login/
# http://127.0.0.1:8000/notas/login/
```
**Resultado esperado:** Página carrega normalmente

#### 3.2 Testar com Host inválido (simulação)
```bash
# Usar curl ou Postman para testar com Host header inválido
curl -H "Host: evil.com" http://localhost:8000/notas/login/
```
**Resultado esperado:** Django deve rejeitar ou retornar erro 400

---

### ✅ 4. TESTES DE RATE LIMITING (PROTEÇÃO CONTRA BRUTE FORCE)

#### 4.1 Teste Manual - Tentativas de Login

**Passos:**
1. Acesse: `http://localhost:8000/notas/login/`
2. Tente fazer login com senha **ERRADA** 6 vezes seguidas
3. Na 6ª tentativa, você deve ser bloqueado

**Resultado esperado:**
- Primeiras 5 tentativas: Mensagem de erro normal ("Usuário ou senha incorretos")
- 6ª tentativa: Mensagem "Muitas tentativas de login. Aguarde 1 minuto antes de tentar novamente."
- Após 1 minuto: Pode tentar novamente

#### 4.2 Teste Automatizado (Script)
```bash
# Executar script de teste
python scripts/test/test_rate_limiting.py
```

#### 4.3 Verificar que login correto funciona
1. Aguarde 1 minuto após o bloqueio
2. Faça login com credenciais **CORRETAS**
3. Deve funcionar normalmente

---

### ✅ 5. TESTES DE DECORATORS DE CONTROLE DE ACESSO

#### 5.1 Teste de Acesso Admin

**Como Admin:**
1. Faça login como administrador
2. Acesse: `http://localhost:8000/notas/usuarios/`
3. **Resultado esperado:** Página carrega normalmente

**Como Funcionário:**
1. Faça login como funcionário (não admin)
2. Acesse: `http://localhost:8000/notas/usuarios/`
3. **Resultado esperado:** Redirecionado para login ou página de erro de acesso negado

**Sem Login:**
1. Faça logout
2. Acesse: `http://localhost:8000/notas/usuarios/`
3. **Resultado esperado:** Redirecionado para página de login

#### 5.2 Teste de Acesso a Logs de Auditoria

**Como Admin:**
1. Faça login como administrador
2. Acesse: `http://localhost:8000/notas/logs-auditoria/`
3. **Resultado esperado:** Página carrega normalmente

**Como Funcionário:**
1. Faça login como funcionário
2. Acesse: `http://localhost:8000/notas/logs-auditoria/`
3. **Resultado esperado:** Acesso negado ou redirecionado

#### 5.3 Teste de Acesso a Registros Excluídos

**Como Admin:**
1. Faça login como administrador
2. Acesse: `http://localhost:8000/notas/registros-excluidos/`
3. **Resultado esperado:** Página carrega normalmente

**Como Funcionário:**
1. Faça login como funcionário
2. Acesse: `http://localhost:8000/notas/registros-excluidos/`
3. **Resultado esperado:** Acesso negado

---

### ✅ 6. TESTES DE HTTPS E COOKIES SEGUROS

#### 6.1 Verificar Configuração em Desenvolvimento
```bash
python manage.py shell -c "from django.conf import settings; print('DEBUG:', settings.DEBUG); print('CSRF_COOKIE_SECURE:', settings.CSRF_COOKIE_SECURE); print('SESSION_COOKIE_SECURE:', settings.SESSION_COOKIE_SECURE)"
```
**Resultado esperado em desenvolvimento:**
- `DEBUG: True`
- `CSRF_COOKIE_SECURE: False` (normal em desenvolvimento)
- `SESSION_COOKIE_SECURE: False` (normal em desenvolvimento)

#### 6.2 Verificar Configuração de Produção
```bash
# Verificar settings_production.py
# Deve ter USE_HTTPS configurado
```

---

### ✅ 7. TESTES FUNCIONAIS BÁSICOS

#### 7.1 Login e Logout
1. Acesse a página de login
2. Faça login com credenciais válidas
3. Verifique se foi redirecionado para o dashboard
4. Faça logout
5. Verifique se foi redirecionado para login

#### 7.2 Navegação Básica
1. Faça login como admin
2. Navegue pelas principais páginas:
   - Dashboard
   - Listar Notas Fiscais
   - Listar Clientes
   - Listar Motoristas
   - Listar Veículos
3. **Resultado esperado:** Todas as páginas carregam normalmente

#### 7.3 Teste de Permissões por Tipo de Usuário

**Como Cliente:**
1. Faça login como cliente
2. Acesse: `http://localhost:8000/notas/minhas-notas/`
3. **Resultado esperado:** Página carrega normalmente
4. Tente acessar: `http://localhost:8000/notas/usuarios/`
5. **Resultado esperado:** Acesso negado

**Como Funcionário:**
1. Faça login como funcionário
2. Verifique quais páginas tem acesso
3. Tente acessar páginas administrativas
4. **Resultado esperado:** Acesso negado em páginas admin

---

### ✅ 8. TESTES DE SEGURANÇA ADICIONAIS

#### 8.1 Verificar que .env não está no Git
```bash
git check-ignore .env
```
**Resultado esperado:** `.env` (confirmando que está no .gitignore)

#### 8.2 Verificar que não há SECRET_KEY hardcoded
```bash
# Procurar por SECRET_KEY no código (exceto em .env e settings)
grep -r "SECRET_KEY" --exclude="*.pyc" --exclude=".env*" --exclude="*.md" .
```
**Resultado esperado:** Apenas em arquivos de configuração e documentação

#### 8.3 Verificar que não há dados sensíveis expostos
```bash
# Verificar se há senhas ou tokens no código
grep -ri "password.*=" --exclude="*.pyc" --exclude="*.md" . | grep -v "password_field\|password1\|password2"
```

---

## 🎯 TESTES RÁPIDOS (CHECKLIST RESUMIDO)

Execute estes testes na ordem:

- [ ] `python manage.py check` - Sem erros
- [ ] Servidor inicia: `python manage.py runserver`
- [ ] Login funciona com credenciais corretas
- [ ] Rate limiting bloqueia após 5 tentativas erradas
- [ ] Admin acessa `/notas/usuarios/` normalmente
- [ ] Funcionário NÃO acessa `/notas/usuarios/`
- [ ] Cliente NÃO acessa `/notas/usuarios/`
- [ ] Logout funciona corretamente
- [ ] `.env` existe e tem `SECRET_KEY`
- [ ] `.env` está no `.gitignore`

---

## 📊 RESULTADO ESPERADO

Após todos os testes, você deve ter:

✅ **Sistema funcionando normalmente**  
✅ **Rate limiting protegendo o login**  
✅ **Controle de acesso funcionando**  
✅ **SECRET_KEY segura**  
✅ **ALLOWED_HOSTS configurado**  
✅ **Sem erros críticos**

---

## ⚠️ PROBLEMAS COMUNS E SOLUÇÕES

### Problema: "ModuleNotFoundError: No module named 'django_ratelimit'"
**Solução:**
```bash
.\ativar.ps1
pip install django-ratelimit
```

### Problema: "SECRET_KEY not found"
**Solução:**
```bash
python scripts/config/criar_env.py
# Editar .env e adicionar SECRET_KEY gerada
python scripts/config/gerar_secret_key.py
```

### Problema: Rate limiting não funciona
**Solução:**
1. Verificar se o decorator está aplicado: `@ratelimit(key='ip', rate='5/m', method='POST', block=True)`
2. Verificar se `django-ratelimit` está instalado
3. Limpar cache: `python manage.py clear_cache` (se existir)

### Problema: Decorators não funcionam
**Solução:**
1. Verificar se `notas/decorators.py` existe
2. Verificar imports em `views.py`
3. Verificar se o usuário tem os atributos `is_admin`, `is_funcionario`, `is_cliente`

---

## 📝 NOTAS

- Testes devem ser feitos em ambiente de desenvolvimento primeiro
- Após validar, testar em ambiente de staging antes de produção
- Documentar quaisquer problemas encontrados
- Manter este documento atualizado com novos testes

---

**Última Atualização:** 26/11/2025


