# 🔧 ALTERAÇÃO: Validação do Campo RNTRC

**Data:** 27/11/2025  
**Alteração:** Remoção da validação de quantidade mínima/máxima de dígitos do RNTRC

---

## 📋 ALTERAÇÃO REALIZADA

### **Arquivo Modificado:**
- `notas/forms/veiculo_forms.py`

### **Método Alterado:**
- `clean_rntrc()` - Método de validação do campo RNTRC

---

## 🔄 MUDANÇA

### **Antes:**
```python
def clean_rntrc(self):
    rntrc = self.cleaned_data.get('rntrc')
    if not rntrc:
        return rntrc
    # Remove caracteres não numéricos
    rntrc_numeros = re.sub(r'[^0-9]', '', rntrc)
    if len(rntrc_numeros) != 12:  # ❌ Validação de quantidade exata
        raise forms.ValidationError("RNTRC deve conter 12 dígitos numéricos.")
    return rntrc_numeros
```

### **Depois:**
```python
def clean_rntrc(self):
    rntrc = self.cleaned_data.get('rntrc')
    if not rntrc:
        return rntrc
    # Remove caracteres não numéricos (mantém apenas números)
    # Não valida quantidade mínima/máxima de dígitos
    rntrc_numeros = re.sub(r'[^0-9]', '', rntrc)
    return rntrc_numeros  # ✅ Sem validação de quantidade
```

---

## ✅ RESULTADO

Agora o campo RNTRC:
- ✅ **Aceita qualquer quantidade de dígitos** (sem validação de mínimo/máximo)
- ✅ **Remove caracteres não numéricos** automaticamente
- ✅ **Mantém apenas números** no valor final
- ✅ **Permite campo vazio** (se não informado)

---

## 📝 OBSERVAÇÕES

1. **Limpeza Automática:**
   - O sistema ainda remove caracteres não numéricos (pontos, traços, espaços, etc.)
   - Apenas números são mantidos no valor final

2. **Sem Validação de Tamanho:**
   - Não há mais validação de quantidade mínima ou máxima
   - Aceita qualquer quantidade de dígitos numéricos

3. **Compatibilidade:**
   - O campo no modelo ainda tem `max_length=12`
   - Mas a validação do formulário não força mais exatamente 12 dígitos
   - Se necessário, pode-se ajustar o `max_length` no modelo também

---

## 🎯 CASOS DE USO

Agora é possível cadastrar:
- ✅ RNTRC com menos de 12 dígitos
- ✅ RNTRC com mais de 12 dígitos (até o limite do campo)
- ✅ RNTRC vazio (opcional)
- ✅ RNTRC com formatação (será limpo automaticamente)

**Exemplos:**
- `123456` → Aceito (6 dígitos)
- `123456789012` → Aceito (12 dígitos)
- `123.456.789-01` → Limpo para `12345678901` (11 dígitos)
- `""` (vazio) → Aceito

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ ALTERAÇÃO IMPLEMENTADA


