# 💡 PROPOSTA FINAL: Fechamento de Frete com Múltiplos Romaneios

**Data:** 27/11/2025  
**Funcionalidade:** Associação de múltiplos romaneios para o mesmo cliente no fechamento

---

## 🎯 NECESSIDADE IDENTIFICADA

### **Cenário Real:**
Grupos empresariais com múltiplas empresas (CNPJs diferentes):
- **Grupo Atacado Tradição:**
  - Atacado Tradição (CNPJ 1) → Romaneio 1
  - Atacado Total (CNPJ 2) → Romaneio 2
  - Tx Mix (CNPJ 3) → Romaneio 3

**No fechamento:** Todos consolidados como "Atacado Tradição" com:
- Peso total = Soma dos 3 romaneios
- Valor total = Soma dos 3 romaneios

---

## 📋 ESTRUTURA PROPOSTA (FINAL)

### **1. SEÇÃO SUPERIOR - Seleção de Romaneios**

```
┌─────────────────────────────────────────────────────────┐
│  [ ] Usar dados de romaneios existentes                │
│                                                         │
│  ROMANEIOS: [Multi-select - Buscar romaneios emitidos]│
│  [Botão: Carregar Dados dos Romaneios]                 │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Romaneios Selecionados:                          │ │
│  │  ✓ ROM-001 - Atacado Tradição                    │ │
│  │  ✓ ROM-002 - Atacado Total                       │ │
│  │  ✓ ROM-003 - Tx Mix                              │ │
│  │                                                   │ │
│  │ Dados Carregados:                                 │ │
│  │  Motorista: [Preenchido]                         │ │
│  │  Data: [Preenchida]                              │ │
│  │  Total Peso: [Soma de todos]                     │ │
│  │  Total Valor: [Soma de todos]                    │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  OU                                                     │
│                                                         │
│  [ ] Criar fechamento manual (sem romaneios)            │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Multi-select de romaneios (pode selecionar vários)
- Lista de romaneios selecionados
- Botão para carregar dados
- Agrupamento automático por cliente

---

### **2. SEÇÃO - Agrupamento de Clientes**

```
┌─────────────────────────────────────────────────────────┐
│  AGRUPAMENTO DE CLIENTES                                │
│                                                         │
│  [ ] Agrupar automaticamente por nome similar          │
│  [ ] Agrupar manualmente                                │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Clientes Encontrados nos Romaneios:              │ │
│  │                                                   │ │
│  │  [ ] Atacado Tradição (ROM-001)                  │ │
│  │  [ ] Atacado Total (ROM-002)                     │ │
│  │  [✓] Tx Mix (ROM-003)                            │ │
│  │                                                   │ │
│  │  Agrupar como: [Dropdown: Atacado Tradição]     │ │
│  │  [Botão: Agrupar]                                │ │
│  │                                                   │ │
│  │  [ ] Cliente B (ROM-004)                         │ │
│  │  [ ] Cliente C (ROM-005)                         │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Lista todos os clientes únicos dos romaneios selecionados
- Permite agrupar clientes diferentes em um único nome
- Mostra qual romaneio cada cliente veio
- Agrupamento manual ou automático (por nome similar)

---

### **3. SEÇÃO - Dados Gerais (Editáveis)**

```
┌─────────────────────────────────────────────────────────┐
│  MOTORISTA: [Preenchido ou Editável]                   │
│  DATA: [Preenchida ou Editável]                        │
│                                                         │
│  FRETE TOTAL: R$ [Input - Obrigatório]                 │
│  CTR: R$ [Input - Obrigatório]                          │
│  CARREGAMENTO: R$ [Input - Obrigatório]                 │
│                                                         │
│  CUBAGEM BAU:                                          │
│    A: [Input]  B: [Input]  C: [Input]  TOTAL: [Auto] │
└─────────────────────────────────────────────────────────┘
```

---

### **4. SEÇÃO PRINCIPAL - Tabela Consolidada**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │ CLIENTE  │ PESO(KG) │ CUB(M³)  │  VALOR   │ VALOR CUB│ % - CUB  │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │ Atacado  │ [Auto]   │ [Input]  │ [Auto]   │ [Auto]   │ [Auto]   │        │
│  │ Tradição │ 7.484    │          │ 242.893  │          │          │        │
│  │          │ (3 rom.) │          │ (3 rom.) │          │          │        │
│  ├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤        │
│  │ Cliente B│ [Auto]   │ [Input]  │ [Auto]   │ [Auto]   │ [Auto]   │        │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘        │
│  TOTAIS: [Auto] [Auto] [Auto] [Auto] [Auto]                                 │
│                                                                              │
│  [Botão: Ver Detalhes] - Mostra romaneios por cliente                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Cliente consolidado (ex: "Atacado Tradição")
- Peso: Soma de todos os romaneios agrupados
- Valor: Soma de todos os romaneios agrupados
- Indicador de quantos romaneios foram agrupados
- Botão para ver detalhes (quais romaneios compõem cada cliente)

---

### **5. MODAL - Detalhes do Agrupamento**

```
┌─────────────────────────────────────────────────────────┐
│  Detalhes: Atacado Tradição                             │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Romaneio: ROM-001                                │   │
│  │ Cliente Original: Atacado Tradição              │   │
│  │ Peso: 4.516 kg                                   │   │
│  │ Valor: R$ 130.286,03                             │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Romaneio: ROM-002                                │   │
│  │ Cliente Original: Atacado Total                 │   │
│  │ Peso: 1.939 kg                                   │   │
│  │ Valor: R$ 50.314,32                             │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Romaneio: ROM-003                                │   │
│  │ Cliente Original: Tx Mix                        │   │
│  │ Peso: 1.029 kg                                   │   │
│  │ Valor: R$ 62.293,57                             │   │
│  └──────────────────────────────────────────────────┘   │
│  ────────────────────────────────────────────────────   │
│  TOTAL: 7.484 kg | R$ 242.893,92                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 LÓGICA DE CÁLCULO (MÚLTIPLOS ROMANEIOS)

### **Função: Carregar Dados de Múltiplos Romaneios**

```python
def carregar_dados_multiplos_romaneios(romaneio_ids):
    """
    Carrega dados de múltiplos romaneios e agrupa por cliente
    
    Args:
        romaneio_ids: Lista de IDs de romaneios
    
    Returns:
        dict: {
            'motorista': motorista (primeiro romaneio),
            'data': data (primeiro romaneio),
            'romaneios': [
                {
                    'romaneio_id': id,
                    'romaneio_codigo': codigo,
                    'cliente_id': id,
                    'cliente_nome': nome,
                    'peso_total': peso,
                    'valor_total': valor
                },
                ...
            ],
            'clientes_agrupados': {
                'cliente_consolidado_id': {
                    'nome_consolidado': nome,
                    'romaneios': [lista de romaneios],
                    'peso_total': soma,
                    'valor_total': soma
                },
                ...
            }
        }
    """
    romaneios = RomaneioViagem.objects.filter(
        pk__in=romaneio_ids,
        status='Emitido'
    ).select_related('motorista', 'cliente').prefetch_related('notas_fiscais')
    
    # Agrupar por cliente (pode ser manual depois)
    clientes_data = {}
    romaneios_data = []
    
    for romaneio in romaneios:
        cliente_id = romaneio.cliente.pk
        cliente_nome = romaneio.cliente.razao_social
        
        # Dados do romaneio
        romaneio_info = {
            'romaneio_id': romaneio.pk,
            'romaneio_codigo': romaneio.codigo,
            'cliente_id': cliente_id,
            'cliente_nome': cliente_nome,
            'peso_total': romaneio.peso_total or 0,
            'valor_total': romaneio.valor_total or 0
        }
        romaneios_data.append(romaneio_info)
        
        # Agrupar por cliente (inicialmente por ID, depois pode ser manual)
        if cliente_id not in clientes_data:
            clientes_data[cliente_id] = {
                'cliente_id': cliente_id,
                'cliente_nome': cliente_nome,
                'romaneios': [],
                'peso_total': 0,
                'valor_total': 0
            }
        
        clientes_data[cliente_id]['romaneios'].append(romaneio_info)
        clientes_data[cliente_id]['peso_total'] += romaneio_info['peso_total']
        clientes_data[cliente_id]['valor_total'] += romaneio_info['valor_total']
    
    return {
        'motorista': romaneios[0].motorista if romaneios else None,
        'data': romaneios[0].data_emissao if romaneios else None,
        'romaneios': romaneios_data,
        'clientes_agrupados': list(clientes_data.values())
    }
```

---

## 📊 FLUXO PROPOSTO

### **1. Seleção de Romaneios**
- Usuário seleciona múltiplos romaneios (multi-select)
- Clica "Carregar Dados"
- Sistema lista todos os clientes encontrados

### **2. Agrupamento de Clientes**
- **Opção A: Automático**
  - Sistema sugere agrupamentos por nome similar
  - Usuário confirma ou ajusta

- **Opção B: Manual**
  - Usuário seleciona quais clientes agrupar
  - Define nome consolidado
  - Pode agrupar quantos quiser

### **3. Consolidação**
- Sistema soma peso e valor dos romaneios agrupados
- Cria linha única na tabela com totais
- Mantém referência aos romaneios originais

### **4. Cálculo do Fechamento**
- Resto igual à proposta original
- Valores calculados sobre os totais consolidados

---

## 💾 ESTRUTURA DE DADOS (ATUALIZADA)

### **Modelo: FechamentoFrete**

```python
class FechamentoFrete(models.Model):
    # Múltiplos romaneios (ManyToMany)
    romaneios = ManyToManyField(
        RomaneioViagem,
        related_name='fechamentos_frete',
        verbose_name="Romaneios Associados"
    )
    
    motorista = ForeignKey(Motorista)
    data = DateField()
    frete_total = DecimalField()
    ctr_total = DecimalField()
    carregamento_total = DecimalField()
    cubagem_bau_a = DecimalField()
    cubagem_bau_b = DecimalField()
    cubagem_bau_c = DecimalField()
    cubagem_bau_total = DecimalField()
    observacoes = TextField()
    usuario_criacao = ForeignKey(Usuario)
    data_criacao = DateTimeField(auto_now_add=True)
    origem_romaneio = BooleanField(default=False)
```

### **Modelo: ItemFechamentoFrete**

```python
class ItemFechamentoFrete(models.Model):
    fechamento = ForeignKey(FechamentoFrete)
    
    # Cliente consolidado (pode ser diferente dos clientes originais)
    cliente_consolidado = ForeignKey(
        Cliente,
        related_name='itens_fechamento_consolidado',
        verbose_name="Cliente Consolidado"
    )
    
    # Valores consolidados
    peso = DecimalField()  # Soma de todos os romaneios
    cubagem = DecimalField()
    valor_mercadoria = DecimalField()  # Soma de todos os romaneios
    
    # Relacionamento com romaneios que compõem este item
    romaneios = ManyToManyField(
        RomaneioViagem,
        related_name='itens_fechamento',
        verbose_name="Romaneios que Compõem"
    )
    
    # Resto igual à proposta original...
```

### **Modelo: DetalheItemFechamento (Opcional)**

```python
class DetalheItemFechamento(models.Model):
    """
    Armazena detalhes de cada romaneio que compõe um item
    """
    item = ForeignKey(ItemFechamentoFrete, related_name='detalhes')
    romaneio = ForeignKey(RomaneioViagem)
    cliente_original = ForeignKey(Cliente)  # Cliente original do romaneio
    peso = DecimalField()
    valor = DecimalField()
```

---

## 🎯 EXEMPLO PRÁTICO

### **Cenário:**
- **ROM-001:** Atacado Tradição → 4.516 kg, R$ 130.286,03
- **ROM-002:** Atacado Total → 1.939 kg, R$ 50.314,32
- **ROM-003:** Tx Mix → 1.029 kg, R$ 62.293,57

### **Fluxo:**
1. Usuário seleciona os 3 romaneios
2. Clica "Carregar Dados"
3. Sistema lista:
   - Atacado Tradição (ROM-001)
   - Atacado Total (ROM-002)
   - Tx Mix (ROM-003)
4. Usuário agrupa os 3 como "Atacado Tradição"
5. Sistema cria linha única:
   - Cliente: Atacado Tradição
   - Peso: 7.484 kg (soma dos 3)
   - Valor: R$ 242.893,92 (soma dos 3)
   - Indicador: "3 romaneios"
6. Resto do cálculo igual à proposta original

---

## ✅ VANTAGENS ESPECÍFICAS

### **1. Flexibilidade:**
- ✅ Pode agrupar quantos clientes quiser
- ✅ Pode agrupar quantos romaneios quiser
- ✅ Nome consolidado editável

### **2. Rastreabilidade:**
- ✅ Mantém referência aos romaneios originais
- ✅ Pode ver detalhes de cada romaneio
- ✅ Histórico completo

### **3. Precisão:**
- ✅ Valores sempre corretos (soma automática)
- ✅ Sem erros de digitação
- ✅ Consistência garantida

---

## 🔄 INTERFACE DE AGRUPAMENTO

### **Tela de Agrupamento:**

```
┌─────────────────────────────────────────────────────────┐
│  AGRUPAR CLIENTES                                       │
│                                                         │
│  Clientes Encontrados:                                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [✓] Atacado Tradição (ROM-001)                   │ │
│  │ [✓] Atacado Total (ROM-002)                      │ │
│  │ [✓] Tx Mix (ROM-003)                             │ │
│  │                                                   │ │
│  │ Nome Consolidado: [Atacado Tradição]            │ │
│  │ [Botão: Agrupar]                                 │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  Clientes Individuais:                                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [ ] Cliente B (ROM-004)                          │ │
│  │ [ ] Cliente C (ROM-005)                          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  [Botão: Confirmar Agrupamento]                        │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 RESUMO DAS MELHORIAS

### **Versão Original:**
- ❌ Um romaneio por fechamento
- ❌ Um cliente por romaneio

### **Versão Melhorada:**
- ✅ Múltiplos romaneios por fechamento
- ✅ Múltiplos clientes agrupados
- ✅ Consolidação automática de valores
- ✅ Rastreabilidade completa

---

**Última Atualização:** 27/11/2025  
**Status:** 💡 PROPOSTA FINAL


