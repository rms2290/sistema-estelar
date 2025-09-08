# Formatação Automática de Campos

## Descrição

Este sistema implementa formatação automática para campos de entrada de dados, aplicando máscaras específicas durante a digitação e ao perder o foco.

## Campos Suportados

### 1. CNPJ
- **Formato**: `00.000.000/0000-00`
- **Detecção**: Campos com `cnpj` no nome, id ou placeholder
- **Exemplo**: `12345678000123` → `12.345.678/0001-23`

### 2. Telefone
- **Formato**: 
  - Telefone fixo: `(00) 0000-0000`
  - Celular: `(00) 00000-0000`
- **Detecção**: Campos com `telefone` no nome, id ou placeholder
- **Exemplo**: `11987654321` → `(11) 98765-4321`

### 3. CPF
- **Formato**: `000.000.000-00`
- **Detecção**: Campos com `cpf` no nome, id ou placeholder
- **Exemplo**: `12345678901` → `123.456.789-01`

### 4. CEP
- **Formato**: `00000-000`
- **Detecção**: Campos com `cep` no nome, id ou placeholder
- **Exemplo**: `12345678` → `12345-678`

## Funcionalidades

### Formatação em Tempo Real
- A formatação é aplicada durante a digitação
- Apenas números são aceitos
- Caracteres especiais são automaticamente inseridos

### Formatação ao Perder Foco
- Garante que o campo esteja formatado corretamente
- Útil para campos carregados dinamicamente

### Detecção Automática
- Identifica o tipo de campo baseado no nome, id ou placeholder
- Funciona com qualquer campo que contenha as palavras-chave

### Suporte a Conteúdo Dinâmico
- Observa mudanças no DOM
- Aplica formatação a novos campos carregados via AJAX
- Funciona com formulários carregados dinamicamente

## Arquivos

### JavaScript
- **Localização**: `static/js/formatters.js`
- **Inclusão**: Automática via `templates/base.html`

### Templates Afetados
- `adicionar_cliente.html`
- `editar_cliente.html`
- `adicionar_motorista.html`
- `editar_motorista.html`
- `adicionar_veiculo.html`
- `editar_veiculo.html`
- `auth/cadastrar_usuario.html`

## Como Funciona

1. **Carregamento**: O script é carregado automaticamente em todas as páginas
2. **Detecção**: Identifica campos baseado em nome, id ou placeholder
3. **Formatação**: Aplica máscaras específicas para cada tipo de campo
4. **Observação**: Monitora mudanças no DOM para novos campos
5. **Compatibilidade**: Funciona com formulários existentes e novos

## Benefícios

- **Experiência do Usuário**: Formatação automática melhora a usabilidade
- **Consistência**: Padronização dos formatos em todo o sistema
- **Validação Visual**: Usuário vê imediatamente se o formato está correto
- **Redução de Erros**: Menos erros de digitação e formatação

## Manutenção

Para adicionar novos tipos de formatação:

1. Adicione a função de formatação no arquivo `formatters.js`
2. Atualize a função `detectarTipoCampo()` para incluir a nova detecção
3. Atualize a função `aplicarFormatacao()` para incluir o novo tipo
4. Execute `python manage.py collectstatic --noinput`

## Compatibilidade

- Funciona em todos os navegadores modernos
- Compatível com Bootstrap e outros frameworks CSS
- Não interfere com validações do Django
- Preserva funcionalidades existentes dos formulários 