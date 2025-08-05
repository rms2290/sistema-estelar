# Totalizador por Estado

## Descrição
Funcionalidade que permite visualizar o total de valores dos romaneios emitidos por estado, separados por período, incluindo o cálculo automático do valor do seguro baseado na tabela de seguros.

## Funcionalidades

### Filtros
- **Data Inicial**: Define o início do período de análise
- **Data Final**: Define o fim do período de análise

### Informações Exibidas
- **Estado**: Nome completo do estado (UF)
- **Quantidade de Romaneios**: Número de romaneios emitidos no período
- **Valor Total**: Soma dos valores de todas as notas fiscais dos romaneios
- **Percentual de Seguro**: Percentual configurado na tabela de seguros para o estado
- **Valor do Seguro**: Cálculo automático (Valor Total × Percentual de Seguro)

### Resumo
- **Estados com movimentação**: Quantidade de estados que tiveram romaneios no período
- **Valor Total**: Soma de todos os valores por estado
- **Seguro Total**: Soma de todos os valores de seguro calculados

## Acesso
- Apenas usuários administradores podem acessar esta funcionalidade
- Menu: "Totalizador por Estado" (apenas visível para admins)

## URL
```
/notas/totalizador-por-estado/
```

## Como Usar

1. Acesse o menu "Totalizador por Estado"
2. Selecione a data inicial do período desejado
3. Selecione a data final do período desejado
4. Clique em "Filtrar"
5. Visualize os resultados organizados por estado

## Cálculos

### Valor Total por Estado
```
Valor Total = Σ(Valor das Notas Fiscais dos Romaneios Emitidos)
```

### Valor do Seguro
```
Valor Seguro = Valor Total × (Percentual Seguro / 100)
```

## Observações

- Apenas romaneios com status "Emitido" são considerados
- Estados sem movimentação no período não aparecem nos resultados
- Estados sem configuração na tabela de seguros têm percentual 0%
- Os resultados são ordenados por valor total (maior primeiro)

## Arquivos Modificados

- `notas/views.py`: Nova view `totalizador_por_estado`
- `notas/urls.py`: Nova URL para a funcionalidade
- `templates/base.html`: Adicionado link no menu
- `notas/templates/notas/totalizador_por_estado.html`: Template da tela 