# Configurações do Sistema Estelar

Esta pasta contém arquivos de configuração do projeto.

## 📁 Estrutura

```
config/
├── gunicorn.conf.py              # Configuração do Gunicorn (servidor WSGI)
├── nginx_sistema_estelar.conf    # Configuração do Nginx (proxy reverso)
├── examples/                     # Exemplos de configuração
│   ├── env_example.txt          # Exemplo de variáveis de ambiente
│   └── crontab_example.txt      # Exemplo de configuração de cron
└── README.md                     # Este arquivo
```

## 📝 Arquivos de Configuração

### `gunicorn.conf.py`
Configuração otimizada do Gunicorn para produção com baixo consumo de memória.

**Uso:**
```bash
gunicorn --config config/gunicorn.conf.py sistema_estelar.wsgi:application
```

### `nginx_sistema_estelar.conf`
Configuração do Nginx como proxy reverso para o Gunicorn.

**Uso:**
Copie este arquivo para o diretório de configuração do Nginx e ajuste conforme necessário.

## 📝 Exemplos

### `examples/env_example.txt`
Template de variáveis de ambiente. Copie para `.env` na raiz do projeto e preencha com seus valores.

### `examples/crontab_example.txt`
Exemplo de configuração de tarefas agendadas (cron). Use como referência para configurar tarefas automáticas.

## ⚠️ Nota de Segurança

- **NUNCA** commite arquivos `.env` ou configurações com senhas no Git
- Use `env_example.txt` como template e mantenha valores reais em `.env` (que está no `.gitignore`)



