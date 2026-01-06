# 🚀 Sistema Estelar

Sistema de gestão de notas fiscais, romaneios e logística desenvolvido em Django.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Melhorias Implementadas](#melhorias-implementadas)
- [Documentação](#documentação)

## 📖 Sobre o Projeto

O Sistema Estelar é uma aplicação web completa para gestão de:
- **Notas Fiscais**: Cadastro, consulta e controle de status
- **Romaneios de Viagem**: Criação e gerenciamento de romaneios
- **Clientes**: Cadastro e gestão de empresas clientes
- **Motoristas**: Cadastro de motoristas e suas composições veiculares
- **Veículos**: Gestão de frota (caminhões, reboques, etc.)
- **Agenda de Entregas**: Controle de entregas agendadas
- **Cobrança e Carregamento**: Gestão financeira

## 🛠 Tecnologias

- **Backend**: Django 5.2.5
- **Python**: 3.13.5
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Segurança**: django-ratelimit, autenticação customizada

## 📦 Requisitos

- Python 3.13+
- pip
- PostgreSQL (para produção)
- Git

## 🚀 Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd sistema-estelar
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
```

### 3. Ativar ambiente virtual

**Windows:**
```powershell
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependências

```bash
pip install -r requirements.txt
```

### 5. Configurar variáveis de ambiente

Copie o arquivo de exemplo e configure:

```bash
cp config/examples/env_example.txt .env
```

Edite o arquivo `.env` com suas configurações.

### 6. Executar migrações

```bash
python manage.py migrate
```

### 7. Criar superusuário

```bash
python manage.py createsuperuser
```

### 8. Iniciar servidor

```bash
python manage.py runserver
```

Acesse: http://127.0.0.1:8000

## ⚙️ Configuração

### Desenvolvimento

O sistema usa `settings.py` por padrão, que configura:
- SQLite como banco de dados
- Debug ativado
- Logging em console

### Produção

Para usar configurações de produção:

```bash
python manage.py runserver --settings=sistema_estelar.settings_production
```

Configure as variáveis de ambiente:
- `USE_POSTGRESQL=True`
- `DB_NAME=sistema_estelar`
- `DB_USER=postgres`
- `DB_PASSWORD=sua_senha`
- `DB_HOST=localhost`
- `DB_PORT=5432`

## 📁 Estrutura do Projeto

```
sistema-estelar/
├── notas/                    # App principal
│   ├── models.py            # Modelos de dados
│   ├── views/               # Views modularizadas
│   │   ├── auth_views.py
│   │   ├── cliente_views.py
│   │   ├── nota_fiscal_views.py
│   │   ├── romaneio_views.py
│   │   └── ...
│   ├── forms/               # Formulários
│   ├── services/            # Lógica de negócio
│   ├── utils/               # Utilitários
│   └── decorators.py        # Decorators customizados
├── sistema_estelar/         # Configurações do projeto
│   ├── settings.py         # Desenvolvimento
│   └── settings_production.py  # Produção
├── scripts/                 # Scripts utilitários
├── docs/                    # Documentação
└── templates/               # Templates HTML
```

## ✅ Melhorias Implementadas

### 🔴 Críticas (Concluídas)
- ✅ Remoção de arquivos backup
- ✅ Rate limiting implementado (25+ endpoints)
- ✅ PostgreSQL configurado (pronto para migração)

### 🟡 Importantes (Concluídas)
- ✅ Otimização de queries (select_related/prefetch_related)
- ✅ @login_required explícito em todas as views
- ✅ Validação de permissões granulares
- ✅ Índices no banco de dados
- ✅ Tratamento de exceções específicas

### 🟢 Desejáveis (Em Progresso)
- ⚠️ Type hints (parcial)
- ⚠️ Logging estruturado (parcial)
- ⚠️ Cache estratégico (configurado)
- ⚠️ Documentação (este README)

## 📚 Documentação

Documentação completa disponível em `docs/`:

- `RELATORIO_ANALISE_MELHORIAS.md` - Análise completa do projeto
- `IMPLEMENTACAO_MELHORIAS_CRITICAS.md` - Melhorias críticas implementadas
- `MELHORIAS_IMPORTANTES_IMPLEMENTADAS.md` - Melhorias importantes
- `MELHORIAS_PENDENTES.md` - Melhorias ainda pendentes
- `MIGRACAO_POSTGRESQL.md` - Guia de migração para PostgreSQL
- `CHECKLIST_SEGURANCA.md` - Checklist de segurança

## 🔒 Segurança

O sistema implementa:

- **Rate Limiting**: Proteção contra brute force e abuso
- **Autenticação**: Sistema customizado com tipos de usuário
- **Permissões Granulares**: Clientes só veem seus próprios dados
- **Validação de Exclusão**: Requer senha de admin para exclusões
- **Auditoria**: Log de todas as operações críticas
- **HTTPS Ready**: Configurado para produção

## 🧪 Testes

Executar testes:

```bash
python manage.py test
```

## 📝 Licença

Este projeto é proprietário.

## 👥 Contribuidores

Sistema Estelar - Desenvolvimento Interno

## 📞 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.

---

**Última Atualização:** 26/11/2025  
**Versão:** 2.0


