# 💡 PROPOSTA: Tela de Fechamento de Frete

**Data:** 27/11/2025  
**Objetivo:** Criar interface para análise e distribuição de frete por cliente

---

## 📋 ESTRUTURA PROPOSTA

### **1. SEÇÃO SUPERIOR - Dados Gerais**

```
┌─────────────────────────────────────────────────────────┐
│  MOTORISTA: [Dropdown ou Input]                        │
│  DATA: [DatePicker]                                    │
│                                                         │
│  FRETE TOTAL: R$ [Input numérico]                     │
│  CTR: R$ [Input numérico]                              │
│  CARREGAMENTO: R$ [Input numérico]                     │
│                                                         │
│  CUBAGEM BAU:                                          │
│    A: [Input]  B: [Input]  C: [Input]  TOTAL: [Auto] │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Dropdown de motoristas (buscar do banco)
- Data padrão: hoje
- Campos numéricos com formatação brasileira (R$)
- Cálculo automático do total de cubagem (A + B + C)

---

### **2. SEÇÃO PRINCIPAL - Tabela de Clientes**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [Botão: + Adicionar Cliente]                                               │
│                                                                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │ CLIENTE  │ PESO(KG) │ CUB(M³)  │  VALOR   │ VALOR CUB│ % - CUB  │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │ [Select] │ [Input]  │ [Input]  │ [Input]  │ [Auto]   │ [Auto]   │        │
│  │ [Select] │ [Input]  │ [Input]  │ [Input]  │ [Auto]   │ [Auto]   │        │
│  │ [Select] │ [Input]  │ [Input]  │ [Input]  │ [Auto]   │ [Auto]   │        │
│  │ ...      │ ...      │ ...      │ ...      │ ...      │ ...      │        │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘        │
│                                                                              │
│  TOTAIS: [Auto] [Auto] [Auto] [Auto] [Auto]                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Adicionar/remover linhas dinamicamente
- Dropdown de clientes (buscar do banco)
- Cálculos automáticos:
  - **VALOR CUB:** `(Cubagem do Cliente / Total Cubagem) * Frete Total`
  - **% - CUB:** `(Valor Cub / Valor Cliente) * 100`
- Totais calculados automaticamente

---

### **3. SEÇÃO DE ANÁLISE - Percentuais e Distribuições**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANÁLISE POR PERCENTUAL SOBRE VALOR                                        │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐                  │
│  │ CLIENTE   │   6,00%  │   6,50%  │   7,00%  │  [Ajuste]│                  │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┤                  │
│  │ Cliente 1 │ [Auto]   │ [Auto]   │ [Auto]   │ [Editável]│                  │
│  │ Cliente 2 │ [Auto]   │ [Auto]   │ [Auto]   │ [Editável]│                  │
│  │ ...       │ ...      │ ...      │ ...      │ ...      │                  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘                  │
│  TOTAIS: [Auto] [Auto] [Auto] [Auto]                                       │
│                                                                              │
│  DISTRIBUIÇÃO DE CUSTOS (Proporcional à Cubagem)                           │
│  ┌──────────┬──────────┬──────────┬──────────┐                             │
│  │ CLIENTE   │  FRETE   │   CTR    │ CARREG.  │                             │
│  ├──────────┼──────────┼──────────┼──────────┤                             │
│  │ Cliente 1 │ [Auto]   │ [Auto]   │ [Auto]   │                             │
│  │ Cliente 2 │ [Auto]   │ [Auto]   │ [Auto]   │                             │
│  │ ...       │ ...      │ ...      │ ...      │                             │
│  └──────────┴──────────┴──────────┴──────────┘                             │
│  TOTAIS: [Auto] [Auto] [Auto]                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Percentuais calculados automaticamente: `Valor Cliente * Percentual`
- Coluna "Ajuste" editável para ajustes manuais
- Distribuição proporcional à cubagem:
  - **Frete Cliente:** `(Cubagem Cliente / Total Cubagem) * Frete Total`
  - **CTR Cliente:** `(Cubagem Cliente / Total Cubagem) * CTR Total`
  - **Carregamento Cliente:** `(Cubagem Cliente / Total Cubagem) * Carregamento Total`

---

### **4. SEÇÃO DE COMPARAÇÃO E AJUSTES**

```
┌─────────────────────────────────────────────────────────┐
│  COMPARAÇÃO DE MÉTODOS                                  │
│                                                          │
│  Para cada cliente, exibir:                             │
│  - Valor por Cubagem: R$ X,XX                           │
│  - Percentual sobre Valor (6%): R$ X,XX                 │
│  - Percentual sobre Valor (7%): R$ X,XX                 │
│  - Valor Ajustado Manual: R$ [Editável]                 │
│                                                          │
│  [Checkbox] Usar valor ajustado manual                  │
│                                                          │
│  OBSERVAÇÕES: [Textarea]                                │
│  (Ex: "Cliente mais distante", "Carga mais pesada")     │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Comparação lado a lado dos diferentes métodos
- Campo de observações para justificar ajustes
- Opção de usar valor ajustado manualmente

---

### **5. BOTÕES DE AÇÃO**

```
┌─────────────────────────────────────────────────────────┐
│  [Calcular] [Salvar] [Exportar Excel] [Imprimir]       │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- **Calcular:** Recalcula todos os valores
- **Salvar:** Salva o fechamento no banco
- **Exportar Excel:** Gera planilha similar à atual
- **Imprimir:** Gera PDF do fechamento

---

## 🎯 FLUXO DE USO PROPOSTO

### **1. Seleção Inicial**
- Usuário seleciona motorista e data
- Informa valores de frete, CTR e carregamento
- Informa cubagem do baú (A, B, C)

### **2. Adição de Clientes**
- Clica em "+ Adicionar Cliente"
- Seleciona cliente do dropdown
- Informa peso, cubagem e valor
- Sistema calcula automaticamente:
  - Valor por cubagem
  - Percentual sobre cubagem
  - Percentuais sobre valor (6%, 6.5%, 7%)

### **3. Análise e Ajustes**
- Visualiza comparação entre métodos
- Pode ajustar manualmente valores
- Adiciona observações (distância, peso, etc.)
- Escolhe qual método usar para cada cliente

### **4. Finalização**
- Revisa totais
- Salva o fechamento
- Exporta ou imprime

---

## 💾 ESTRUTURA DE DADOS PROPOSTA

### **Modelo: FechamentoFrete**

```python
class FechamentoFrete(models.Model):
    motorista = ForeignKey(Motorista)
    data = DateField()
    frete_total = DecimalField()
    ctr_total = DecimalField()
    carregamento_total = DecimalField()
    cubagem_bau_a = DecimalField()
    cubagem_bau_b = DecimalField()
    cubagem_bau_c = DecimalField()
    cubagem_bau_total = DecimalField()  # Calculado
    observacoes = TextField()
    usuario_criacao = ForeignKey(Usuario)
    data_criacao = DateTimeField(auto_now_add=True)
```

### **Modelo: ItemFechamentoFrete**

```python
class ItemFechamentoFrete(models.Model):
    fechamento = ForeignKey(FechamentoFrete)
    cliente = ForeignKey(Cliente)
    peso = DecimalField()
    cubagem = DecimalField()
    valor_mercadoria = DecimalField()
    
    # Calculados automaticamente
    valor_por_cubagem = DecimalField()
    percentual_cubagem = DecimalField()
    percentual_6 = DecimalField()
    percentual_6_5 = DecimalField()
    percentual_7 = DecimalField()
    percentual_ajustado = DecimalField()  # Editável
    
    # Distribuição proporcional
    frete_proporcional = DecimalField()
    ctr_proporcional = DecimalField()
    carregamento_proporcional = DecimalField()
    
    # Valor final escolhido
    valor_final = DecimalField()
    usar_ajuste_manual = BooleanField(default=False)
    observacoes = TextField()
```

---

## 🔧 FUNCIONALIDADES TÉCNICAS

### **1. Cálculos Automáticos (JavaScript + Backend)**

**Frontend (JavaScript):**
- Cálculos em tempo real conforme usuário digita
- Validação de valores
- Formatação brasileira (R$, vírgulas, pontos)

**Backend (Python):**
- Validação de dados
- Cálculos precisos com Decimal
- Persistência no banco

### **2. Validações**

- Totais devem bater (soma dos itens = totais gerais)
- Cubagem total = A + B + C
- Valores não podem ser negativos
- Clientes não podem ser duplicados

### **3. Recursos Adicionais**

- **Histórico:** Ver fechamentos anteriores
- **Comparação:** Comparar diferentes fechamentos
- **Templates:** Salvar configurações de percentuais
- **Relatórios:** Gerar relatórios consolidados

---

## 🎨 INTERFACE PROPOSTA

### **Layout:**
- Design responsivo (Bootstrap)
- Tabelas com scroll horizontal se necessário
- Cores diferentes para valores calculados vs editáveis
- Indicadores visuais de ajustes manuais

### **UX:**
- Auto-save opcional
- Confirmação antes de salvar
- Mensagens de sucesso/erro claras
- Tooltips explicando cálculos

---

## 📊 EXEMPLO DE CÁLCULOS

### **Cenário:**
- Frete Total: R$ 15.000,00
- Total Cubagem: 88,29 m³
- Cliente COPA:
  - Peso: 1.939 kg
  - Cubagem: 20,74 m³
  - Valor: R$ 50.314,32

### **Cálculos:**
1. **Valor por Cubagem:**
   - `(20,74 / 88,29) * 15.000 = R$ 3.523,62`

2. **Percentual sobre Cubagem:**
   - `(3.523,62 / 50.314,32) * 100 = 7,00%`

3. **Percentuais sobre Valor:**
   - 6%: `50.314,32 * 0,06 = R$ 3.018,86`
   - 6,5%: `50.314,32 * 0,065 = R$ 3.270,43`
   - 7%: `50.314,32 * 0,07 = R$ 3.522,00`

4. **Distribuição Proporcional:**
   - Frete: `(20,74 / 88,29) * 15.000 = R$ 3.523,62`
   - CTR: `(20,74 / 88,29) * 650 = R$ 152,69`
   - Carregamento: `(20,74 / 88,29) * 500 = R$ 117,46`

---

## ✅ VANTAGENS DA PROPOSTA

1. **Automação:** Cálculos automáticos eliminam erros manuais
2. **Flexibilidade:** Permite ajustes manuais quando necessário
3. **Rastreabilidade:** Histórico de fechamentos
4. **Análise:** Comparação entre diferentes métodos
5. **Integração:** Pode buscar dados de romaneios existentes
6. **Exportação:** Gera Excel/PDF para compartilhamento

---

## 🔄 PRÓXIMOS PASSOS (SE APROVADO)

1. Criar modelos no banco
2. Criar formulários Django
3. Implementar view com lógica de cálculo
4. Criar template HTML com JavaScript
5. Implementar exportação Excel/PDF
6. Testes e ajustes

---

**Última Atualização:** 27/11/2025  
**Status:** 📋 PROPOSTA


