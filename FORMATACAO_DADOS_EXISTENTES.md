# Formatação de Dados Existentes

## Descrição

Este documento descreve o processo de formatação dos dados existentes no sistema Estelar, aplicando os padrões corretos de CNPJ, telefone, CPF e CEP.

## Comando de Formatação

### Comando Principal
```bash
python manage.py formatar_dados_clientes
```

### Opções Disponíveis

#### Modo Dry-Run (Simulação)
```bash
python manage.py formatar_dados_clientes --dry-run
```
- Executa sem fazer alterações no banco de dados
- Mostra quais alterações seriam feitas
- Útil para verificar antes de aplicar as mudanças

#### Formatar Modelos Específicos
```bash
# Apenas clientes
python manage.py formatar_dados_clientes --model cliente

# Apenas motoristas
python manage.py formatar_dados_clientes --model motorista

# Apenas veículos
python manage.py formatar_dados_clientes --model veiculo

# Todos os modelos (padrão)
python manage.py formatar_dados_clientes --model all
```

## Padrões de Formatação Aplicados

### 1. CNPJ
- **Formato**: `00.000.000/0000-00`
- **Exemplo**: `29954890000233` → `29.954.890/0002-33`

### 2. Telefone
- **Telefone fixo**: `(00) 0000-0000`
- **Celular**: `(00) 00000-0000`
- **Exemplo**: `(81)37220700` → `(81) 3722-0700`

### 3. CPF
- **Formato**: `000.000.000-00`
- **Exemplo**: `12345678901` → `123.456.789-01`

### 4. CEP
- **Formato**: `00000-000`
- **Exemplo**: `55041400` → `55041-400`

## Dados Formatados

### Clientes Atualizados
- **ALLAN MATERIAL DE CONSTRUÇÃO LTDA**
  - CNPJ: `29.954.890/0002-33`
  - CEP: `55041-40`

- **COMERCIAL ALLANE LTDA**
  - CNPJ: `02.302.013/0001-40`
  - Telefone: `(81) 3722-0700`
  - CEP: `55004-130`

### Motoristas
- Nenhum motorista cadastrado no momento

### Veículos
- Nenhum veículo cadastrado no momento

## Script de Verificação

### Executar Verificação
```bash
python verificar_dados_formatados.py
```

### Saída do Script
O script mostra um relatório completo com todos os dados formatados:
- Dados dos clientes (CNPJ, telefone, CEP, email, status)
- Dados dos motoristas (CPF, telefone, CEP, CNH)
- Dados dos veículos (CPF/CNPJ do proprietário, telefone, CEP)

## Arquivos Criados

### 1. Comando Django
- **Arquivo**: `notas/management/commands/formatar_dados_clientes.py`
- **Funcionalidade**: Comando para formatar dados existentes
- **Uso**: `python manage.py formatar_dados_clientes`

### 2. Script de Verificação
- **Arquivo**: `verificar_dados_formatados.py`
- **Funcionalidade**: Relatório dos dados formatados
- **Uso**: `python verificar_dados_formatados.py`

## Segurança

### Transações
- Todas as operações são executadas dentro de transações
- Em caso de erro, todas as alterações são revertidas
- Garante consistência dos dados

### Validação
- Apenas dados válidos são formatados
- Dados inválidos permanecem inalterados
- Verificação de comprimento e formato antes da formatação

## Manutenção

### Adicionar Novos Tipos de Formatação
1. Adicione a função de formatação no comando
2. Atualize a função correspondente no modelo
3. Execute o comando para aplicar as alterações

### Verificar Dados Novos
- Execute o comando periodicamente para novos registros
- Use o modo dry-run para verificar antes de aplicar
- Monitore os logs para identificar problemas

## Benefícios

- **Consistência**: Todos os dados seguem o mesmo padrão
- **Usabilidade**: Formatação visual melhora a experiência
- **Validação**: Dados formatados são mais fáceis de validar
- **Relatórios**: Dados padronizados facilitam relatórios
- **Integração**: Facilita integração com outros sistemas

## Logs de Execução

### Exemplo de Saída
```
Formatando dados dos clientes...
Cliente 'ALLAN MATERIAL DE CONSTRUÇÃO LTDA':
  - CNPJ: 29954890000233 → 29.954.890/0002-33
Cliente 'COMERCIAL ALLANE LTDA':
  - CNPJ: 02302013000140 → 02.302.013/0001-40
  - Telefone: (81)37220700 → (81) 3722-0700
Total de clientes atualizados: 2
Formatação concluída com sucesso!
```

## Próximos Passos

1. **Monitoramento**: Verificar periodicamente novos dados
2. **Automação**: Considerar execução automática do comando
3. **Validação**: Implementar validação adicional se necessário
4. **Relatórios**: Criar relatórios de dados formatados 