# 🧪 TESTE 8: EDITAR ROMANEIO E EMITIR

**Data:** 27/11/2025  
**Objetivo:** Testar o fluxo completo de edição e emissão de romaneio

---

## 📋 DESCRIÇÃO DO TESTE

Este teste valida o processo completo de:
1. **Criar romaneio** com status 'Salvo'
2. **Editar romaneio** (alterar dados e adicionar notas)
3. **Emitir romaneio** (mudar status para 'Emitido')
4. **Imprimir romaneio** emitido

---

## 🔍 CENÁRIOS TESTADOS

### **1. Criação de Dados de Teste**
- ✅ Criar/obter usuário admin
- ✅ Criar/obter cliente
- ✅ Criar/obter motorista
- ✅ Criar/obter veículo principal (Cavalo)
- ✅ Criar/obter reboque
- ✅ Criar 3 notas fiscais

### **2. Criação de Romaneio (Status: Salvo)**
- ✅ Criar romaneio com status 'Salvo'
- ✅ Vincular 2 notas fiscais inicialmente
- ✅ Verificar totais (peso e valor)

### **3. Edição de Romaneio**
- ✅ Alterar origem (São Paulo → Campinas)
- ✅ Alterar destino (Rio de Janeiro → Belo Horizonte)
- ✅ Alterar estado de destino (RJ → MG)
- ✅ Alterar datas (saída e chegada prevista)
- ✅ Adicionar mais notas fiscais (2 → 3)
- ✅ Verificar atualização de totais

### **4. Emissão de Romaneio**
- ✅ Mudar status de 'Salvo' para 'Emitido'
- ✅ Verificar data de emissão preenchida
- ✅ Verificar notas marcadas como 'Enviada'

### **5. Impressão de Romaneio**
- ✅ Acessar rota de impressão
- ✅ Verificar resposta HTTP 200
- ✅ Verificar conteúdo HTML gerado

---

## 📊 VALIDAÇÕES REALIZADAS

### **Após Edição:**
- [x] Origem alterada corretamente
- [x] Destino alterado corretamente
- [x] Estado de destino alterado
- [x] Quantidade de notas atualizada
- [x] Totais recalculados

### **Após Emissão:**
- [x] Status mudado para 'Emitido'
- [x] Data de emissão preenchida
- [x] Todas as notas marcadas como 'Enviada'

### **Após Impressão:**
- [x] Resposta HTTP 200
- [x] Content-Type correto (text/html)
- [x] Contexto do romaneio presente

---

## 🔧 ARQUIVO DE TESTE

**Localização:** `scripts/test/teste_8_editar_emitir_romaneio.py`

**Funcionalidades:**
- Criação automática de dados de teste
- Teste de edição com validações
- Teste de emissão com verificações
- Teste de impressão via Django test client
- Logging detalhado de todas as operações

---

## 📝 COMO EXECUTAR

```powershell
python scripts/test/teste_8_editar_emitir_romaneio.py
```

**Logs:**
- Console: Saída em tempo real
- Arquivo: `logs/teste_8_editar_emitir_romaneio.log`

---

## ✅ RESULTADOS ESPERADOS

| Teste | Status Esperado |
|-------|----------------|
| Criar Dados | ✅ PASSOU |
| Criar Romaneio | ✅ PASSOU |
| Editar Romaneio | ✅ PASSOU |
| Emitir Romaneio | ✅ PASSOU |
| Impressão Romaneio | ✅ PASSOU |

**Total:** 5/5 testes devem passar

---

## 🐛 PROBLEMAS CONHECIDOS

### **Encoding Unicode:**
- ✅ Corrigido: Substituídos símbolos Unicode (✓, ✗) por texto ASCII ([OK], [ERRO])

### **Campo data_romaneio:**
- ✅ Corrigido: Adicionado campo `data_romaneio` obrigatório em todos os formulários

---

## 📚 DEPENDÊNCIAS

- Django 5.2+
- Modelos: `RomaneioViagem`, `Cliente`, `Motorista`, `Veiculo`, `NotaFiscal`
- Serviços: `RomaneioService`
- Formulários: `RomaneioViagemForm`
- Views: `editar_romaneio`, `imprimir_romaneio_novo`

---

## 🎯 OBJETIVO DO TESTE

Garantir que:
1. ✅ Romaneios podem ser editados antes da emissão
2. ✅ Edições atualizam corretamente os dados e totais
3. ✅ Emissão marca corretamente o status e as notas
4. ✅ Romaneios emitidos podem ser impressos
5. ✅ Fluxo completo funciona sem erros

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ TESTE IMPLEMENTADO


