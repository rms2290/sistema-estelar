# 🗄️ Guia de Migração: SQLite → PostgreSQL

**Data:** 26/11/2025  
**Versão:** 1.0

---

## 📋 Sumário

Este guia detalha o processo de migração do banco de dados SQLite para PostgreSQL em produção.

---

## ⚠️ AVISOS IMPORTANTES

1. **Faça backup completo** antes de iniciar a migração
2. **Teste em ambiente de staging** primeiro
3. **Execute em horário de baixo tráfego**
4. **Mantenha backup do SQLite** por pelo menos 30 dias
5. **Valide integridade dos dados** após migração

---

## 📦 Pré-requisitos

### 1. PostgreSQL Instalado

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Verificar instalação
psql --version
```

### 2. Criar Banco de Dados

```sql
-- Conectar como usuário postgres
sudo -u postgres psql

-- Criar banco de dados
CREATE DATABASE sistema_estelar;

-- Criar usuário (opcional, pode usar postgres)
CREATE USER estelar_user WITH PASSWORD 'sua_senha_segura';

-- Dar permissões
GRANT ALL PRIVILEGES ON DATABASE sistema_estelar TO estelar_user;

-- Sair
\q
```

### 3. Instalar psycopg2-binary

```bash
# Já está no requirements_production.txt
pip install psycopg2-binary
```

---

## 🔧 Configuração

### 1. Variáveis de Ambiente

Configure as seguintes variáveis no servidor de produção:

```bash
# Arquivo .env ou variáveis de ambiente do sistema
export DB_NAME=sistema_estelar
export DB_USER=estelar_user
export DB_PASSWORD=sua_senha_segura
export DB_HOST=localhost
export DB_PORT=5432
export USE_POSTGRESQL=True
```

### 2. Settings já Configurados

O arquivo `settings_production.py` já está configurado para usar PostgreSQL quando `USE_POSTGRESQL=True`.

---

## 🚀 Processo de Migração

### Opção 1: Usando Script Automatizado

```bash
# 1. Fazer backup manual primeiro
cp db.sqlite3 backups/db_backup_manual_$(date +%Y%m%d_%H%M%S).sqlite3

# 2. Configurar variáveis de ambiente
export DB_NAME=sistema_estelar
export DB_USER=estelar_user
export DB_PASSWORD=sua_senha
export DB_HOST=localhost
export DB_PORT=5432

# 3. Executar script de migração
python scripts/migrate_to_postgresql.py
```

### Opção 2: Migração Manual (Recomendado)

```bash
# 1. Fazer backup do SQLite
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3

# 2. Exportar dados do SQLite
python manage.py dumpdata --indent 2 > data_backup.json

# 3. Configurar PostgreSQL no settings temporariamente
# (ou usar variáveis de ambiente)

# 4. Executar migrations no PostgreSQL
export USE_POSTGRESQL=True
python manage.py migrate

# 5. Importar dados
python manage.py loaddata data_backup.json

# 6. Validar dados
python manage.py check
```

---

## ✅ Validação Pós-Migração

### 1. Verificar Conexão

```python
python manage.py dbshell
# Deve conectar ao PostgreSQL
```

### 2. Contar Registros

```python
python manage.py shell

from notas.models import *
print(f"Clientes: {Cliente.objects.count()}")
print(f"Notas Fiscais: {NotaFiscal.objects.count()}")
print(f"Romaneios: {RomaneioViagem.objects.count()}")
# ... etc
```

### 3. Testar Funcionalidades

- [ ] Login funciona
- [ ] Criar nota fiscal
- [ ] Criar romaneio
- [ ] Listar registros
- [ ] Relatórios funcionam
- [ ] Dashboard carrega

---

## 🔄 Rollback (Se Necessário)

Se houver problemas, você pode voltar ao SQLite:

```bash
# 1. Restaurar backup do SQLite
cp backups/db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3

# 2. Desabilitar PostgreSQL
export USE_POSTGRESQL=False

# 3. Reiniciar aplicação
```

---

## 📊 Comparação de Performance

| Métrica | SQLite | PostgreSQL |
|---------|--------|------------|
| Concorrência | Limitada | Excelente |
| Transações | Básicas | ACID Completo |
| Performance | Boa (pequenos volumes) | Excelente (grandes volumes) |
| Backup | Arquivo único | Ferramentas avançadas |
| Escalabilidade | Limitada | Excelente |

---

## 🛠️ Manutenção PostgreSQL

### Backup Automatizado

```bash
# Criar script de backup
#!/bin/bash
pg_dump -U estelar_user sistema_estelar > backups/pg_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restaurar Backup

```bash
psql -U estelar_user sistema_estelar < backups/pg_backup_YYYYMMDD_HHMMSS.sql
```

---

## 📞 Suporte

Em caso de problemas:

1. Verifique logs: `logs/django.log`
2. Verifique conexão: `python manage.py dbshell`
3. Valide variáveis de ambiente
4. Consulte documentação do PostgreSQL

---

**Última Atualização:** 26/11/2025


