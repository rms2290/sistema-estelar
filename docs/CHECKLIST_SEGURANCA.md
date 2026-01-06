# ✅ CHECKLIST DE SEGURANÇA - FASE 1

Use este checklist para verificar se todas as melhorias de segurança foram implementadas corretamente.

---

## 🔴 CRÍTICO - Verificar Antes de Deploy

### Configuração de Ambiente
- [ ] Arquivo `.env` criado na raiz do projeto
- [ ] `SECRET_KEY` configurada no `.env` (chave longa e aleatória)
- [ ] Arquivo `.env` está no `.gitignore` (verificado)
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado com domínios reais (não `*`)

### Verificação de Código
- [ ] Nenhuma chave secreta hardcoded no código
- [ ] Nenhuma senha hardcoded no código
- [ ] Configurações sensíveis apenas em variáveis de ambiente

---

## 🟡 IMPORTANTE - Verificar Regularmente

### Rate Limiting
- [ ] Rate limiting ativo no login (5 tentativas/minuto)
- [ ] Testar bloqueio após muitas tentativas
- [ ] Mensagem de erro clara quando bloqueado

### Controle de Acesso
- [ ] Views administrativas protegidas com `@admin_required`
- [ ] Views de funcionários protegidas com `@funcionario_required`
- [ ] Testar acesso negado para usuários não autorizados
- [ ] Mensagens de erro apropriadas

### HTTPS (Quando Configurado)
- [ ] `USE_HTTPS=True` no `.env` de produção
- [ ] Certificado SSL válido
- [ ] Redirecionamento HTTP → HTTPS funcionando
- [ ] Cookies seguros habilitados

---

## 🟢 RECOMENDADO - Boas Práticas

### Auditoria
- [ ] Logs de auditoria funcionando
- [ ] Logs de acesso sendo registrados
- [ ] Rotação de logs configurada

### Backup
- [ ] Backup do banco de dados automatizado
- [ ] Backup de arquivos de configuração
- [ ] Teste de restauração realizado

### Monitoramento
- [ ] Logs de erro sendo monitorados
- [ ] Alertas configurados para falhas críticas

---

## 🧪 TESTES DE SEGURANÇA

### Teste 1: SECRET_KEY Obrigatória
```bash
# Remover SECRET_KEY do .env temporariamente
# A aplicação deve FALHAR ao iniciar
python manage.py check
# Esperado: Erro sobre SECRET_KEY não encontrada
```

### Teste 2: Rate Limiting
```bash
# Tentar fazer login 6 vezes seguidas com senha errada
# Esperado: Bloqueio após 5 tentativas
```

### Teste 3: Controle de Acesso
```bash
# Fazer login como cliente
# Tentar acessar /notas/usuarios/
# Esperado: Redirecionamento com mensagem de acesso negado
```

### Teste 4: ALLOWED_HOSTS
```bash
# Acessar aplicação com Host header diferente
# Esperado: Erro 400 Bad Request
```

---

## 📝 COMANDOS ÚTEIS

### Gerar SECRET_KEY
```bash
python scripts/config/gerar_secret_key.py
```

### Criar .env
```bash
python scripts/config/criar_env.py
```

### Verificar Configurações
```bash
python manage.py check --deploy
```

### Verificar Segurança Django
```bash
python manage.py check --deploy
```

---

## ⚠️ AVISOS IMPORTANTES

1. **NUNCA** commite o arquivo `.env` no Git
2. **SEMPRE** use SECRET_KEY diferente em desenvolvimento e produção
3. **VERIFIQUE** que `.env` está no `.gitignore` antes de fazer commit
4. **TESTE** todas as configurações antes de fazer deploy

---

**Última Atualização:** 26/11/2025


