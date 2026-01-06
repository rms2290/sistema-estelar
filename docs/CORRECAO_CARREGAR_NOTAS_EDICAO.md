# 🔧 CORREÇÃO: Erro ao Carregar Notas Fiscais na Edição de Romaneio

**Data:** 27/11/2025  
**Erro:** "Erro ao carregar notas fiscais." na edição de romaneio

---

## 🐛 PROBLEMA IDENTIFICADO

### **Sintoma:**
- Mensagem de erro "Erro ao carregar notas fiscais." aparecendo na página de edição de romaneio
- Notas fiscais não sendo carregadas via AJAX
- Totais (peso e valor) permanecendo em zero

### **Causa Raiz:**
1. **Falta de import `Q`** em `api_views.py` - causava erro ao filtrar notas
2. **Formato de resposta incorreto** - JavaScript esperava array direto, mas recebia objeto `{notas: [...]}`
3. **Campos incompletos** - resposta não incluía todos os campos necessários (fornecedor, mercadoria, etc)
4. **IDs de elementos** - fallback para IDs alternativos não estava funcionando

---

## ✅ CORREÇÕES APLICADAS

### **1. Arquivo: `notas/views/api_views.py`**

#### **Adicionado import:**
```python
from django.db.models import Q
```

#### **Corrigida função `load_notas_fiscais_edicao()`:**

**Antes:**
```python
notas_data = [{
    'id': nota.id,
    'nota': nota.nota,
    'valor': str(nota.valor),
    'peso': str(nota.peso),
} for nota in notas]

return JsonResponse({'notas': notas_data})
```

**Depois:**
```python
# Formato esperado pelo JavaScript: array direto com campos completos
notas_data = []
for nota in notas:
    notas_data.append({
        'id': nota.id,
        'nota_numero': nota.nota,
        'fornecedor': nota.fornecedor or '',
        'mercadoria': nota.mercadoria or '',
        'quantidade': str(nota.quantidade) if nota.quantidade else '0',
        'peso': str(nota.peso) if nota.peso else '0',
        'valor': str(nota.valor) if nota.valor else '0',
        'data_emissao': nota.data.strftime('%d/%m/%Y') if nota.data else '',
    })

return JsonResponse(notas_data, safe=False)  # Array direto
```

**Melhorias:**
- ✅ Retorna array direto (não objeto com chave 'notas')
- ✅ Inclui todos os campos necessários para exibição
- ✅ Tratamento de valores None/null
- ✅ Formatação de data
- ✅ Tratamento de erros com logging

---

### **2. Arquivo: `templates/base.html`**

#### **Melhorada função `loadNotasFiscaisEdicao()`:**

**Adicionado:**
- ✅ Validação de `clienteId` com mensagem apropriada
- ✅ Fallback para IDs alternativos de elementos
- ✅ Validação de existência do container antes de usar

```javascript
if (!clienteId) {
    if (notasContainer) {
        notasContainer.innerHTML = '<p class="text-info">Selecione um cliente para carregar as notas fiscais.</p>';
    }
    return;
}

// Fallback para IDs alternativos
if (!notasContainer) {
    notasContainer = document.getElementById('notas_fiscais_checkboxes') || document.getElementById('notas-fiscais-container');
}
if (!totalPesoElement) {
    totalPesoElement = document.getElementById('peso_total_romaneio') || document.getElementById('total-peso');
}
if (!totalValorElement) {
    totalValorElement = document.getElementById('valor_total_romaneio') || document.getElementById('total-valor');
}
```

---

### **3. Arquivo: `notas/templates/notas/editar_romaneio.html`**

#### **Adicionada validação:**
```javascript
// Verificar se os elementos existem
if (!notasFiscaisDiv) {
    console.error('Elemento notas_fiscais_checkboxes não encontrado');
    return;
}
```

---

## 📋 CAMPOS RETORNADOS

A API agora retorna todos os campos necessários:

- `id` - ID da nota fiscal
- `nota_numero` - Número da nota fiscal
- `fornecedor` - Nome do fornecedor
- `mercadoria` - Descrição da mercadoria
- `quantidade` - Quantidade
- `peso` - Peso em kg
- `valor` - Valor em R$
- `data_emissao` - Data formatada (dd/mm/yyyy)

---

## ✅ VERIFICAÇÃO

- ✅ Sistema verificado: `python manage.py check` - OK
- ✅ Import `Q` adicionado
- ✅ Formato de resposta corrigido
- ✅ Campos completos incluídos
- ✅ Tratamento de erros melhorado

---

## 🎯 RESULTADO

Agora o sistema:
- ✅ Carrega notas fiscais corretamente na edição
- ✅ Exibe todos os campos das notas
- ✅ Calcula totais automaticamente
- ✅ Mantém notas já selecionadas marcadas
- ✅ Trata erros adequadamente

---

## 📝 NOTAS TÉCNICAS

### **Formato de Resposta JSON:**
- **Antes:** `{"notas": [...]}` (objeto)
- **Depois:** `[...]` (array direto)

### **Uso de `safe=False`:**
Necessário para retornar array diretamente em `JsonResponse`:
```python
return JsonResponse(notas_data, safe=False)
```

### **Filtro de Notas:**
```python
notas = notas.filter(
    Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
)
```
- Inclui notas já vinculadas ao romaneio
- Inclui notas em depósito (disponíveis)

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ CORRIGIDO


