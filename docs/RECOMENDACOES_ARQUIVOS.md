# 📋 RECOMENDAÇÕES: ARQUIVOS DO PROJETO

**Data:** 27/11/2025

---

## ✅ ARQUIVOS ESSENCIAIS (MANTER)

### **Configuração Core:**
- ✅ `manage.py` - Script principal Django
- ✅ `.gitignore` - Configuração Git
- ✅ `requirements.txt` - Dependências principais
- ✅ `requirements_production.txt` - Dependências produção
- ✅ `requirements-dev.txt` - Dependências desenvolvimento
- ✅ `runtime.txt` - Versão Python (Heroku)
- ✅ `Procfile` - Configuração Heroku
- ✅ `pytest.ini` - Configuração testes
- ✅ `.coveragerc` - Configuração cobertura

### **Estrutura:**
- ✅ `sistema_estelar/` - Configurações Django
- ✅ `notas/` - App principal
- ✅ `templates/` - Templates HTML
- ✅ `static/` - Arquivos estáticos
- ✅ `scripts/` - Scripts utilitários
- ✅ `docs/` - Documentação
- ✅ `config/` - Configurações

### **Scripts Úteis:**
- ✅ `scripts/dev/ativar.ps1` / `.bat` - Ativar ambiente
- ✅ `scripts/dev/iniciar_servidor.ps1` / `.bat` - Iniciar servidor
- ✅ Wrappers na raiz (facilitam uso)

---

## ❌ ARQUIVOS TEMPORÁRIOS (REMOVER)

### **Logs de Teste:**
- ❌ `test_server_error.log` - Log de erro temporário
- ❌ `test_server.log` - Log de teste temporário
- ❌ `server_error.txt` - Erro do servidor
- ❌ `server_output.txt` - Saída do servidor

### **Backups Antigos:**
- ❌ `backup_db_20251126_082039.sqlite3` - Backup antigo (se não for mais necessário)

### **Arquivos Gerados:**
- ⚠️ `coverage.xml` - Pode ser regenerado (mas útil manter)
- ⚠️ `db.sqlite3` - Banco de desenvolvimento (já está no .gitignore)

---

## ⚠️ ARQUIVOS DUPLICADOS (CONSOLIDAR)

### **Scripts na Raiz:**
- `ativar.ps1` / `ativar.bat` - Wrappers
- `iniciar_servidor.ps1` / `iniciar_servidor.bat` - Wrappers
- `INICIAR.ps1` / `INICIAR.bat` - Wrappers simples

### **Scripts em `scripts/dev/`:**
- `ativar.ps1` / `ativar.bat` - Versões completas
- `iniciar_servidor.ps1` / `iniciar_servidor.bat` - Versões completas

**Recomendação:** Manter wrappers na raiz (facilitam uso) e scripts completos em `scripts/dev/`

---

## 🧹 COMO LIMPAR

### **Opção 1: Script Automático**
```powershell
.\scripts\limpar_arquivos_temporarios.ps1
```

### **Opção 2: Manual**
```powershell
Remove-Item test_server_error.log, test_server.log, server_error.txt, server_output.txt -ErrorAction SilentlyContinue
Remove-Item backup_db_20251126_082039.sqlite3 -ErrorAction SilentlyContinue
```

### **Opção 3: Limpar Logs Também**
```powershell
Remove-Item logs\*.log, logs\*.txt -Force
```

---

## 📊 RESUMO

| Categoria | Quantidade | Ação |
|-----------|------------|------|
| **Essenciais** | ~20 arquivos | ✅ Manter |
| **Temporários** | ~5 arquivos | ❌ Remover |
| **Duplicados** | ~6 arquivos | ⚠️ Manter (wrappers úteis) |

---

## ✅ AÇÕES RECOMENDADAS

1. ✅ **Remover arquivos temporários** (usar script fornecido)
2. ✅ **Manter estrutura atual** (wrappers na raiz são úteis)
3. ✅ **Verificar .gitignore** (já está configurado corretamente)
4. ✅ **Manter documentação** (útil para referência)

---

**Última Atualização:** 27/11/2025


