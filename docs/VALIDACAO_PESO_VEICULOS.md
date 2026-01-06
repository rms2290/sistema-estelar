# ✅ VALIDAÇÃO DE PESO POR VEÍCULO

**Data:** 27/11/2025  
**Status:** ✅ IMPLEMENTADO E CORRIGIDO

---

## 📋 RESUMO

O sistema **SIM, está fazendo validação de peso para cada veículo**, verificando se o peso total da carga não excede a capacidade total da composição veicular.

---

## 🔍 COMO FUNCIONA

### **1. Capacidades Definidas**

As capacidades de cada tipo de veículo estão definidas em `notas/utils/constants.py`:

```python
CAPACIDADES_VEICULOS = {
    'Carro': 1000,        # 1.000 kg
    'Van': 1500,          # 1.500 kg
    'Caminhão': 10000,    # 10.000 kg
    'Cavalo': 25000,      # 25.000 kg
    'Reboque': 25000,     # 25.000 kg
    'Semi-reboque': 25000, # 25.000 kg
}
```

### **2. Método de Validação**

O método `validar_capacidade_veiculo()` está no modelo `RomaneioViagem`:

```python
def validar_capacidade_veiculo(self):
    """
    Valida se o peso total da carga não excede a capacidade dos veículos.
    
    Calcula a capacidade total somando:
    - Capacidade do veículo principal
    - Capacidade do reboque 1 (se houver)
    - Capacidade do reboque 2 (se houver)
    
    Returns:
        tuple: (valido: bool, mensagem_erro: str)
    """
```

**Lógica:**
1. Obtém a capacidade de cada veículo baseado no tipo
2. Soma todas as capacidades (principal + reboques)
3. Compara com o peso total da carga
4. Retorna erro se peso exceder capacidade

### **3. Onde é Validado**

A validação é executada no formulário `RomaneioViagemForm`, no método `clean()`:

- ✅ **Na CRIAÇÃO** de romaneio (após correção)
- ✅ **Na EDIÇÃO** de romaneio

**Antes da correção:**
- ❌ Validação só funcionava na edição
- ❌ Não validava na criação

**Depois da correção:**
- ✅ Validação funciona na criação e edição
- ✅ Calcula peso baseado nas notas fiscais selecionadas
- ✅ Valida antes de salvar

---

## 📊 EXEMPLOS DE VALIDAÇÃO

### **Exemplo 1: Composição Simples (Cavalo)**
- **Veículo:** Cavalo (25.000 kg)
- **Carga:** 30.000 kg
- **Resultado:** ❌ ERRO - "Peso total da carga (30.000,00 kg) excede a capacidade total dos veículos (25.000 kg)."

### **Exemplo 2: Carreta (Cavalo + Reboque)**
- **Veículo Principal:** Cavalo (25.000 kg)
- **Reboque 1:** Reboque (25.000 kg)
- **Capacidade Total:** 50.000 kg
- **Carga:** 45.000 kg
- **Resultado:** ✅ OK

### **Exemplo 3: Bi-trem (Cavalo + 2 Reboques)**
- **Veículo Principal:** Cavalo (25.000 kg)
- **Reboque 1:** Reboque (25.000 kg)
- **Reboque 2:** Semi-reboque (25.000 kg)
- **Capacidade Total:** 75.000 kg
- **Carga:** 70.000 kg
- **Resultado:** ✅ OK

---

## 🔧 CORREÇÃO APLICADA

### **Problema Identificado:**
A validação só funcionava na edição, não na criação de novos romaneios.

### **Solução:**
Modificado o método `clean()` do formulário para:

1. **Calcular peso total** baseado nas notas fiscais selecionadas
2. **Validar tanto na criação quanto na edição**
3. **Usar peso do instance na edição** (se disponível) ou peso calculado

**Código corrigido:**
```python
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
```

---

## ✅ VERIFICAÇÃO

- ✅ Validação implementada no modelo
- ✅ Validação chamada no formulário
- ✅ Funciona na criação e edição
- ✅ Capacidades definidas corretamente
- ✅ Mensagens de erro claras

---

## 📝 NOTAS TÉCNICAS

### **Quando a Validação é Executada:**
1. **No formulário** (`clean()`): Antes de salvar
2. **Automaticamente**: Quando o peso total é calculado

### **O que é Validado:**
- ✅ Peso total da carga vs capacidade total da composição
- ✅ Considera veículo principal + reboques
- ✅ Retorna mensagem de erro clara se exceder

### **O que NÃO é Validado:**
- ❌ Distribuição de peso entre veículos (apenas total)
- ❌ Peso individual por nota fiscal
- ❌ Limites legais de trânsito (apenas capacidades técnicas)

---

## 🎯 RESULTADO

O sistema agora:
- ✅ **Valida peso na criação** de romaneios
- ✅ **Valida peso na edição** de romaneios
- ✅ **Calcula capacidade total** corretamente
- ✅ **Exibe mensagens de erro** claras
- ✅ **Previne romaneios** com carga acima da capacidade

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ FUNCIONANDO CORRETAMENTE


