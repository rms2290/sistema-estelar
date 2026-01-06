# 🔍 Por Que o PostgreSQL Não Está Ativo?

**Data:** 26/11/2025

---

## 📋 Resumo

O PostgreSQL não está ativo porque o servidor está rodando em **modo de desenvolvimento** usando `settings.py`, que está configurado para usar **SQLite** por padrão.

---

## 🔍 Motivos Detalhados

### 1. **Servidor Rodando com Settings de Desenvolvimento**

O servidor está usando `settings.py` (desenvolvimento), não `settings_production.py` (produção).

**Evidência:**
- `DJANGO_SETTINGS_MODULE` não está definido → Django usa `settings.py` por padrão
- Scripts de inicialização (`iniciar_servidor.ps1`) não especificam `--settings`
- Comando usado: `python manage.py runserver` (usa settings padrão)

### 2. **Variáveis de Ambiente Não Configuradas**

Para usar PostgreSQL, as seguintes variáveis de ambiente precisam estar definidas:

```bash
USE_POSTGRESQL=True
DB_NAME=sistema_estelar
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

**Status Atual:**
- ❌ `USE_POSTGRESQL` - Não definida
- ❌ `DB_NAME` - Não definida
- ❌ `DB_USER` - Não definida
- ❌ `DB_PASSWORD` - Não definida
- ❌ `DB_HOST` - Não definida
- ❌ `DB_PORT` - Não definida

### 3. **Configuração do Settings**

#### `settings.py` (Desenvolvimento - ATUAL):
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # ← SQLite
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
✅ **Sempre usa SQLite** - Não verifica variáveis de ambiente

#### `settings_production.py` (Produção):
```python
USE_POSTGRESQL = os.environ.get('USE_POSTGRESQL', 'True').lower() == 'true'

if USE_POSTGRESQL:
    # Tenta usar PostgreSQL
    if not os.environ.get('DB_NAME'):
        raise ImproperlyConfigured("DB_NAME não encontrada...")  # ← Falha aqui
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # ...
        }
    }
else:
    # Usa SQLite como fallback
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}
```
⚠️ **Tenta usar PostgreSQL por padrão**, mas falha se variáveis não estiverem configuradas

---

## ✅ Como Ativar PostgreSQL

### Opção 1: Configurar Variáveis de Ambiente (Recomendado)

```powershell
# Definir variáveis de ambiente
$env:USE_POSTGRESQL="True"
$env:DB_NAME="sistema_estelar"
$env:DB_USER="postgres"
$env:DB_PASSWORD="sua_senha_aqui"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"

# Iniciar servidor com settings de produção
python manage.py runserver --settings=sistema_estelar.settings_production
```

### Opção 2: Criar Arquivo .env

Criar arquivo `.env` na raiz do projeto:

```env
USE_POSTGRESQL=True
DB_NAME=sistema_estelar
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
DB_HOST=localhost
DB_PORT=5432
```

E usar `python-decouple` para carregar (já está configurado em `settings_production.py`).

### Opção 3: Modificar Scripts de Inicialização

Atualizar `scripts/dev/iniciar_servidor.ps1`:

```powershell
# Adicionar antes de iniciar servidor
if ($env:USE_POSTGRESQL -eq "True") {
    $settings = "sistema_estelar.settings_production"
} else {
    $settings = "sistema_estelar.settings"
}

python manage.py runserver --settings=$settings
```

---

## 📊 Comparação

| Aspecto | SQLite (Atual) | PostgreSQL (Configurado) |
|---------|----------------|--------------------------|
| **Status** | ✅ Ativo | ⚠️ Configurado mas não ativo |
| **Settings** | `settings.py` | `settings_production.py` |
| **Variáveis** | Não necessárias | Obrigatórias |
| **Uso** | Desenvolvimento | Produção |
| **Performance** | Boa (pequenos volumes) | Excelente (grandes volumes) |
| **Concorrência** | Limitada | Excelente |

---

## ⚠️ Importante

1. **SQLite é adequado para desenvolvimento** - Não há problema em usar agora
2. **PostgreSQL é necessário para produção** - Migre antes de colocar em produção
3. **As configurações estão prontas** - Só falta configurar variáveis e usar `settings_production.py`

---

## 🎯 Resumo

**PostgreSQL não está ativo porque:**
1. ✅ Servidor roda com `settings.py` (SQLite)
2. ✅ Variáveis de ambiente não estão configuradas
3. ✅ PostgreSQL só funciona com `settings_production.py` + variáveis

**Para ativar:**
1. Configurar variáveis de ambiente
2. Usar `--settings=sistema_estelar.settings_production`
3. Ter PostgreSQL instalado e rodando

---

**Última Atualização:** 26/11/2025


