# 🔧 CORREÇÃO: Import Relativo em models.py

**Data:** 27/11/2025  
**Erro:** `ImportError: attempted relative import beyond top-level package`

---

## 🐛 PROBLEMA IDENTIFICADO

### **Erro:**
```
Exception Type: ImportError at /notas/romaneios/editar/451/
Exception Value: attempted relative import beyond top-level package
```

### **Localização:**
- **Arquivo:** `notas/models.py`
- **Linhas:** 981 e 1028
- **Métodos:** `validar_capacidade_veiculo()` e `get_resumo_romaneio()`

### **Causa:**
O import relativo `from ..utils.constants import CAPACIDADES_VEICULOS` estava causando erro quando executado no contexto do Django, pois tentava ir além do pacote raiz.

---

## ✅ CORREÇÃO APLICADA

### **Antes:**
```python
# Linha 981
from ..utils.constants import CAPACIDADES_VEICULOS

# Linha 1028
from ..utils.constants import CAPACIDADES_VEICULOS
```

### **Depois:**
```python
# Linha 981
from notas.utils.constants import CAPACIDADES_VEICULOS

# Linha 1028
from notas.utils.constants import CAPACIDADES_VEICULOS
```

---

## 📋 DETALHES TÉCNICOS

### **Métodos Afetados:**

1. **`validar_capacidade_veiculo()`** (linha ~975)
   - Valida se o peso total da carga não excede a capacidade dos veículos
   - Usado durante a validação do formulário de romaneio

2. **`get_resumo_romaneio()`** (linha ~1020)
   - Retorna um resumo com totais e capacidades do romaneio
   - Usado para exibição de informações

### **Constante Importada:**
```python
CAPACIDADES_VEICULOS = {
    'Carro': 1000,
    'Van': 1500,
    'Caminhão': 10000,
    'Cavalo': 25000,
    'Reboque': 25000,
    'Semi-reboque': 25000,
}
```

---

## ✅ VERIFICAÇÃO

- ✅ Sistema verificado: `python manage.py check` - OK
- ✅ Imports relativos problemáticos removidos
- ✅ Funcionalidade mantida

---

## 🎯 RESULTADO

O erro de import foi corrigido e o sistema agora pode:
- ✅ Editar romaneios sem erro de import
- ✅ Validar capacidade de veículos corretamente
- ✅ Gerar resumo de romaneios sem problemas

---

## 📝 NOTAS

- **Import Absoluto vs Relativo:**
  - Em Django, imports absolutos são mais seguros e recomendados
  - Imports relativos podem causar problemas em certos contextos de execução

- **Boas Práticas:**
  - Sempre usar imports absolutos quando possível
  - Evitar imports relativos com `..` em métodos de modelos

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ CORRIGIDO


