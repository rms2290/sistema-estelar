# Scripts Auxiliares 🔧

Esta pasta contém todos os scripts auxiliares do Sistema Estelar, organizados por categoria.

## 📁 Estrutura

```
scripts/
├── deploy/     # Scripts de deploy e manutenção do servidor
├── teste/      # Scripts para criar dados de teste
└── config/     # Scripts de configuração e monitoramento
```

## 🚀 Deploy e Manutenção (`deploy/`)

### Scripts de Deploy

#### `deploy_servidor_locaweb.sh` ⭐ **RECOMENDADO**
Script completo e atualizado para deploy no servidor Locaweb.

**Uso:**
```bash
bash scripts/deploy/deploy_servidor_locaweb.sh
```

**Funcionalidades:**
- Atualiza código do repositório
- Instala dependências
- Coleta arquivos estáticos
- Aplica migrações
- Reinicia serviços (Gunicorn + Nginx)

---

#### `instalar_servidor.sh`
Script para primeira instalação do servidor (configuração inicial).

**Uso:**
```bash
bash scripts/deploy/instalar_servidor.sh
```

**Funcionalidades:**
- Configura nginx
- Configura supervisor
- Cria estrutura de diretórios
- Configura permissões

---

### Scripts de Manutenção

#### `restart_sistema.sh`
Reinicia todos os serviços do sistema.

**Uso:**
```bash
bash scripts/deploy/restart_sistema.sh
```

---

#### `resolver_problema.sh`
Resolve problemas comuns de configuração do servidor.

**Uso:**
```bash
bash scripts/deploy/resolver_problema.sh
```

**O que faz:**
- Para processos antigos
- Reconfigura nginx
- Reinicia gunicorn
- Testa conectividade

---

#### `corrigir_servidor_completo.sh`
Script completo de correção e reconfiguração do servidor.

**Uso:**
```bash
bash scripts/deploy/corrigir_servidor_completo.sh
```

**Funcionalidades:**
- Recria arquivos de configuração
- Reconfigura nginx e supervisor
- Aplica permissões
- Reinicia todos os serviços

---

### Scripts Python de Deploy

#### `deploy_locaweb.py`
Script Python automatizado para deploy.

**Uso:**
```bash
python scripts/deploy/deploy_locaweb.py
```

---

#### `deploy_simples.py`
Versão simplificada do script de deploy.

**Uso:**
```bash
python scripts/deploy/deploy_simples.py
```

---

#### `configurar_servidor.py`
Script Python para configuração do servidor.

**Uso:**
```bash
python scripts/deploy/configurar_servidor.py
```

---

### Scripts Windows

#### `deploy_manual.bat`
Script para deploy manual no Windows (preparação local).

**Uso:**
```batch
scripts\deploy\deploy_manual.bat
```

---

#### `configurar_acesso_externo.bat`
Gera arquivos de configuração para acesso externo.

**Uso:**
```batch
scripts\deploy\configurar_acesso_externo.bat
```

---

## 🧪 Testes (`teste/`)

### `create_admin.py` ⭐
Cria usuário administrador do sistema.

**Uso:**
```bash
python scripts/teste/create_admin.py
```

**Credenciais criadas:**
- Usuário: `admin`
- Senha: `admin123`
- Email: `admin@estelar.com`

Também cria usuários de teste:
- Funcionário: `funcionario` / `func123`
- Cliente: `cliente` / `cliente123`

---

### `criar_dados_teste.py` ⭐
Popula o banco de dados com dados de teste.

**Uso:**
```bash
python scripts/teste/criar_dados_teste.py
```

**O que cria:**
- 10 clientes
- 10 motoristas
- 10 veículos
- 100 notas fiscais (70 para o primeiro cliente)

---

## ⚙️ Configuração (`config/`)

### `monitor_memoria.sh`
Monitora o uso de memória do sistema e dos processos.

**Uso:**
```bash
bash scripts/config/monitor_memoria.sh
```

**Funcionalidades:**
- Mostra uso de memória RAM
- Lista processos Python rodando
- Monitora uso de disco
- Pode ser agendado via crontab

---

## 📋 Notas Importantes

### Scripts Recomendados para Uso Regular

1. **Deploy no servidor:** `deploy_servidor_locaweb.sh`
2. **Criar admin:** `create_admin.py`
3. **Criar dados teste:** `criar_dados_teste.py`
4. **Monitorar sistema:** `monitor_memoria.sh`

### Scripts para Situações Específicas

- **Primeira instalação:** `instalar_servidor.sh`
- **Problemas de configuração:** `resolver_problema.sh`
- **Correção completa:** `corrigir_servidor_completo.sh`

### Scripts Legados (Mantidos para Compatibilidade)

Os seguintes scripts são versões antigas mantidas para compatibilidade:
- `deploy_simples.py`
- `deploy_locaweb.py`
- `configurar_acesso_externo.bat`

**Recomendação:** Use os scripts shell (`.sh`) mais recentes que são mais robustos e testados.

---

## 🔧 Permissões

Para executar scripts shell no Linux/Mac, você pode precisar dar permissão de execução:

```bash
chmod +x scripts/deploy/*.sh
chmod +x scripts/config/*.sh
```

---

## 📞 Suporte

Se algum script apresentar problemas:

1. Verifique os logs em `logs/django.log`
2. Consulte a documentação em `docs/`
3. Execute o script de correção: `resolver_problema.sh`

---

**🌟 Sistema Estelar** - Scripts Auxiliares





