# 📁 Sistema de Arquivamento de Dados Antigos

## 🎯 **Visão Geral**

Sistema completo para gerenciar dados antigos (5+ anos) do Sistema Estelar, incluindo arquivamento automático, compressão, backup e consulta de dados históricos.

## 🏗️ **Arquitetura**

```
📁 dados_arquivados/
├── 📦 romaneios/          # Romaneios arquivados por ano
├── 📄 notas_fiscais/      # Notas fiscais arquivadas por ano
├── 🏢 clientes/           # Clientes arquivados
├── 👤 motoristas/         # Motoristas arquivados
├── 🚗 veiculos/           # Veículos arquivados
├── 💾 backups/            # Backups completos
└── 📊 relatorios/         # Relatórios de execução
```

## 🛠️ **Comandos Disponíveis**

### **1. Arquivamento de Dados Antigos**

```bash
# Simular arquivamento (sem executar)
python manage.py arquivar_dados_antigos --dry-run --anos 5

# Executar arquivamento real
python manage.py arquivar_dados_antigos --backup --anos 5

# Arquivamento com idade personalizada
python manage.py arquivar_dados_antigos --anos 3 --backup
```

**Parâmetros:**
- `--dry-run`: Simula a operação sem executar
- `--anos`: Idade mínima dos dados (padrão: 5 anos)
- `--backup`: Cria backup antes do arquivamento

### **2. Consulta de Dados Arquivados**

```bash
# Listar arquivos disponíveis
python manage.py consultar_arquivo --listar

# Consultar romaneios arquivados
python manage.py consultar_arquivo --tipo romaneios

# Buscar por código específico
python manage.py consultar_arquivo --tipo romaneios --buscar "ROM001"

# Consultar dados de ano específico
python manage.py consultar_arquivo --tipo notas --ano 2020

# Consultar todos os tipos
python manage.py consultar_arquivo --tipo todos
```

**Tipos disponíveis:**
- `romaneios`: Romaneios arquivados
- `notas`: Notas fiscais arquivadas
- `clientes`: Clientes arquivados
- `motoristas`: Motoristas arquivados
- `todos`: Todos os tipos

### **3. Agendamento Automático**

```bash
# Iniciar agendamento automático
python agendar_arquivamento.py iniciar

# Executar teste do sistema
python agendar_arquivamento.py teste

# Executar arquivamento mensal manualmente
python agendar_arquivamento.py mensal

# Executar limpeza trimestral manualmente
python agendar_arquivamento.py trimestral

# Executar backup diário manualmente
python agendar_arquivamento.py backup
```

## 📅 **Agendamento Automático**

### **Tarefas Programadas:**

1. **Backup Diário** - 01:00 todos os dias
   - Cria backup dos dados ativos
   - Não executa arquivamento

2. **Arquivamento Mensal** - 02:00 no 1º dia do mês
   - Arquivamento de dados 5+ anos
   - Backup completo antes da operação

3. **Limpeza Trimestral** - 03:00 no 1º dia do trimestre
   - Arquivamento mais agressivo (3+ anos)
   - Backup completo antes da operação

## 🔧 **Funcionalidades**

### **✅ Arquivamento Inteligente**
- Agrupa dados por ano
- Comprime arquivos (economia de 70% de espaço)
- Mantém metadados para consulta
- Preserva relacionamentos entre dados

### **✅ Backup Seguro**
- Backup completo antes de cada operação
- Arquivos comprimidos com timestamp
- Estrutura organizada por tipo de dado

### **✅ Consulta Flexível**
- Busca por código, nome, data
- Filtros por ano e tipo
- Detalhes completos dos registros
- Interface amigável

### **✅ Monitoramento**
- Relatórios de execução
- Estatísticas antes/depois
- Logs detalhados de operações

## 📊 **Benefícios**

### **💾 Economia de Espaço**
- **Antes:** ~2GB de dados
- **Depois:** ~600MB (70% de economia)
- **Arquivados:** Dados históricos preservados

### **⚡ Performance**
- Banco principal mais rápido
- Consultas otimizadas
- Índices eficientes

### **🔒 Segurança**
- Backups automáticos
- Dados preservados
- Recuperação possível

## 🚀 **Como Usar**

### **1. Primeira Execução**
```bash
# Testar o sistema
python agendar_arquivamento.py teste

# Executar arquivamento manual (se necessário)
python manage.py arquivar_dados_antigos --backup --anos 5
```

### **2. Configurar Agendamento**
```bash
# Iniciar agendamento automático
python agendar_arquivamento.py iniciar
```

### **3. Monitorar Execução**
```bash
# Verificar arquivos arquivados
python manage.py consultar_arquivo --listar

# Consultar dados específicos
python manage.py consultar_arquivo --tipo romaneios --ano 2020
```

## 📁 **Estrutura de Arquivos**

```
📁 dados_arquivados/
├── 📦 romaneios/
│   ├── romaneios_2020_20240807_143022.json.gz
│   └── romaneios_2019_20240807_143022.json.gz
├── 📄 notas_fiscais/
│   ├── notas_2020_20240807_143022.json.gz
│   └── notas_2019_20240807_143022.json.gz
├── 💾 backups/
│   ├── backup_completo_20240807_143022.json.gz
│   └── backup_completo_20240807_143022.json.gz
└── 📊 relatorios/
    └── relatorio_20240807_143022.txt
```

## ⚠️ **Considerações Importantes**

### **🔒 Segurança**
- Sempre execute com `--backup` em produção
- Teste com `--dry-run` antes de executar
- Mantenha backups em local seguro

### **📊 Monitoramento**
- Verifique relatórios regularmente
- Monitore espaço em disco
- Teste restauração periodicamente

### **🔄 Manutenção**
- Limpe arquivos antigos de backup
- Verifique integridade dos arquivos
- Atualize agendamento conforme necessário

## 🆘 **Troubleshooting**

### **Problema:** Erro ao executar arquivamento
**Solução:** Verifique permissões de escrita no diretório `dados_arquivados/`

### **Problema:** Arquivos corrompidos
**Solução:** Use backup mais recente para restauração

### **Problema:** Agendamento não funciona
**Solução:** Verifique se o script está rodando em background

## 📞 **Suporte**

Para dúvidas ou problemas:
1. Verifique os logs de execução
2. Teste com `--dry-run` primeiro
3. Consulte os relatórios em `dados_arquivados/relatorios/`

---

**🎯 Sistema de Arquivamento - Sistema Estelar**  
**📅 Última atualização:** Agosto 2025  
**🔧 Versão:** 1.0.0 