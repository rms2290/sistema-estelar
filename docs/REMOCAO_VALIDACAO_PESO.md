# 🗑️ REMOÇÃO: Validação de Peso por Veículo

**Data:** 27/11/2025  
**Ação:** Remoção da validação de capacidade de peso dos veículos

---

## 📋 O QUE FOI REMOVIDO

### **Validação no Formulário:**
- ❌ Cálculo de peso total para validação
- ❌ Validação de capacidade do veículo
- ❌ Mensagens de erro de capacidade excedida
- ❌ Bloqueio de criação/edição por excesso de peso

---

## ✅ O QUE FOI MANTIDO

### **Métodos e Constantes (para uso futuro):**
- ✅ Método `validar_capacidade_veiculo()` no modelo `RomaneioViagem`
- ✅ Constantes `CAPACIDADES_VEICULOS` em `notas/utils/constants.py`
- ✅ Método `get_resumo_carga()` que calcula capacidade

**Motivo:** Mantidos caso seja necessário reativar a validação no futuro.

---

## 🔧 ARQUIVO MODIFICADO

**Arquivo:** `notas/forms/romaneio_forms.py`  
**Método:** `clean()` da classe `RomaneioViagemForm`

### **Antes:**
```python
# Validação de capacidade do veículo
# Calcular peso total baseado nas notas fiscais selecionadas
notas_fiscais_selecionadas = cleaned_data.get('notas_fiscais', [])
peso_total_calculado = sum(nota.peso for nota in notas_fiscais_selecionadas if nota.peso) if notas_fiscais_selecionadas else 0

# Se for edição, usar o peso_total do instance se disponível, senão usar o calculado
if self.instance and self.instance.pk:
    peso_total_validar = self.instance.peso_total if self.instance.peso_total else peso_total_calculado
else:
    peso_total_validar = peso_total_calculado

# Validar capacidade apenas se houver veículo principal e peso
if veiculo_principal and peso_total_validar > 0:
    temp_romaneio = RomaneioViagem(
        veiculo_principal=veiculo_principal,
        reboque_1=reboque_1,
        reboque_2=reboque_2,
        peso_total=peso_total_validar
    )
    capacidade_ok, mensagem_erro = temp_romaneio.validar_capacidade_veiculo()
    if not capacidade_ok:
        raise forms.ValidationError(mensagem_erro)

return cleaned_data
```

### **Depois:**
```python
return cleaned_data
```

---

## 📊 COMPORTAMENTO ATUAL

### **Antes da Remoção:**
- ❌ Sistema bloqueava criação/edição se peso excedesse capacidade
- ❌ Exibia mensagem de erro: "Peso total da carga (X kg) excede a capacidade total dos veículos (Y kg)."

### **Depois da Remoção:**
- ✅ Sistema permite criar/editar romaneios sem validar peso
- ✅ Não há bloqueio por excesso de peso
- ✅ Usuário pode criar romaneios com qualquer peso

---

## 🔄 COMO REATIVAR (SE NECESSÁRIO)

Se precisar reativar a validação no futuro:

1. **Adicionar no método `clean()` do formulário:**
```python
# Calcular peso total
notas_fiscais_selecionadas = cleaned_data.get('notas_fiscais', [])
peso_total = sum(nota.peso for nota in notas_fiscais_selecionadas if nota.peso) if notas_fiscais_selecionadas else 0

# Validar capacidade
if veiculo_principal and peso_total > 0:
    temp_romaneio = RomaneioViagem(
        veiculo_principal=veiculo_principal,
        reboque_1=reboque_1,
        reboque_2=reboque_2,
        peso_total=peso_total
    )
    capacidade_ok, mensagem_erro = temp_romaneio.validar_capacidade_veiculo()
    if not capacidade_ok:
        raise forms.ValidationError(mensagem_erro)
```

2. **Métodos e constantes já estão disponíveis:**
   - `RomaneioViagem.validar_capacidade_veiculo()`
   - `CAPACIDADES_VEICULOS` em `notas.utils.constants`

---

## ✅ VERIFICAÇÃO

- ✅ Validação removida do formulário
- ✅ Sistema verificado: `python manage.py check` - OK
- ✅ Código limpo e funcional
- ✅ Métodos mantidos para uso futuro

---

## 📝 NOTAS

- A remoção foi feita apenas no formulário
- Os métodos de validação no modelo foram mantidos
- As constantes de capacidade foram mantidas
- É possível reativar facilmente se necessário

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ VALIDAÇÃO REMOVIDA


