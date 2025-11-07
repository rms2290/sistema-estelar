# Sistema Estelar 🌟

Sistema de gerenciamento de transporte e logística para a empresa Estelar.

## 📁 Estrutura do Projeto

```
sistema-estelar/
├── 📂 notas/                    # Aplicação principal Django
│   ├── management/              # Comandos personalizados
│   ├── templates/               # Templates HTML
│   ├── utils/                   # Utilitários
│   └── views.py                 # Views da aplicação
│
├── 📂 sistema_estelar/          # Configurações do projeto
│   ├── settings.py              # Configurações de desenvolvimento
│   ├── settings_production.py  # Configurações de produção
│   └── urls.py                  # URLs principais
│
├── 📂 static/                   # Arquivos estáticos (CSS, JS, imagens)
├── 📂 templates/                # Templates base
│
├── 📂 scripts/                  # Scripts auxiliares organizados
│   ├── deploy/                  # Scripts de deploy e manutenção
│   ├── teste/                   # Scripts para criar dados de teste
│   └── config/                  # Scripts de configuração e monitoramento
│
├── 📂 docs/                     # Documentação do projeto
│   ├── README_ARQUIVAMENTO.md   # Guia do sistema de arquivamento
│   └── GUIA_DEPLOY_LOCAWEB.md   # Guia de deploy na Locaweb
│
├── 📂 examples/                 # Exemplos de configuração
│   ├── crontab_example.txt      # Exemplo de crontab
│   ├── env_example.txt          # Exemplo de variáveis de ambiente
│   └── nginx_sistema_estelar.conf  # Exemplo de configuração nginx
│
├── 📂 dados_arquivados/         # Dados antigos arquivados
│   ├── backups/
│   ├── clientes/
│   ├── motoristas/
│   ├── notas_fiscais/
│   ├── romaneios/
│   └── veiculos/
│
├── 📂 logs/                     # Logs da aplicação
├── 📂 cache/                    # Cache da aplicação
│
├── 📄 manage.py                 # Comando principal Django
├── 📄 db.sqlite3                # Banco de dados SQLite
├── 📄 requirements.txt          # Dependências Python (desenvolvimento)
├── 📄 requirements_production.txt  # Dependências Python (produção)
├── 📄 gunicorn.conf.py          # Configuração do Gunicorn
├── 📄 agendar_arquivamento.py   # Script de arquivamento automático
└── 📄 backup_database.py        # Script de backup do banco de dados
```

## 🚀 Como Usar

### Desenvolvimento Local

1. **Ativar ambiente virtual:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Instalar dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar migrações:**
   ```bash
   python manage.py migrate
   ```

4. **Iniciar servidor:**
   ```bash
   python manage.py runserver
   ```

5. **Acessar aplicação:**
   ```
   http://localhost:8000
   ```

### Criar Usuário Administrador

```bash
python scripts/teste/create_admin.py
```

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

### Criar Dados de Teste

```bash
python scripts/teste/criar_dados_teste.py
```

## 📦 Deploy em Produção

### Opção 1: Deploy Automático na Locaweb
```bash
# No servidor
bash scripts/deploy/deploy_servidor_locaweb.sh
```

### Opção 2: Deploy Manual
Consulte o guia completo em: [`docs/GUIA_DEPLOY_LOCAWEB.md`](docs/GUIA_DEPLOY_LOCAWEB.md)

## 🔧 Scripts Úteis

### Deploy e Manutenção
- **`scripts/deploy/deploy_servidor_locaweb.sh`** - Deploy completo no servidor
- **`scripts/deploy/instalar_servidor.sh`** - Instalação inicial do servidor
- **`scripts/deploy/restart_sistema.sh`** - Reiniciar sistema
- **`scripts/deploy/resolver_problema.sh`** - Corrigir problemas comuns
- **`scripts/deploy/configurar_servidor.py`** - Configurar servidor Python

### Testes e Desenvolvimento
- **`scripts/teste/create_admin.py`** - Criar usuário administrador
- **`scripts/teste/criar_dados_teste.py`** - Criar dados de teste

### Configuração e Monitoramento
- **`scripts/config/monitor_memoria.sh`** - Monitorar uso de memória

## 📚 Documentação

- **[Guia de Arquivamento](docs/README_ARQUIVAMENTO.md)** - Sistema de arquivamento de dados antigos
- **[Guia de Deploy Locaweb](docs/GUIA_DEPLOY_LOCAWEB.md)** - Como fazer deploy na Locaweb

## 🔐 Segurança

Para produção, configure as seguintes variáveis de ambiente (veja `examples/env_example.txt`):

- `SECRET_KEY` - Chave secreta do Django
- `DEBUG` - Desabilitar em produção (False)
- `ALLOWED_HOSTS` - Domínios permitidos
- `DB_*` - Configurações do banco de dados (se usar PostgreSQL)

## 📊 Sistema de Arquivamento

O sistema possui arquivamento automático de dados antigos (5+ anos):

```bash
# Executar arquivamento manual
python manage.py arquivar_dados_antigos --backup --anos 5

# Consultar dados arquivados
python manage.py consultar_arquivo --listar

# Agendar arquivamento automático
python agendar_arquivamento.py iniciar
```

Mais detalhes em: [`docs/README_ARQUIVAMENTO.md`](docs/README_ARQUIVAMENTO.md)

## 🔄 Backup

### Backup Manual do Banco de Dados
```bash
python backup_database.py
```

### Backup Automático (Crontab)
Consulte o exemplo em: [`examples/crontab_example.txt`](examples/crontab_example.txt)

## 🛠️ Tecnologias

- **Backend:** Django 4.2+
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Servidor:** Gunicorn + Nginx
- **Frontend:** HTML, CSS, JavaScript

## 📝 Licença

Sistema proprietário da Estelar Transportes.

---

**🌟 Sistema Estelar** - Gestão de Transporte e Logística





