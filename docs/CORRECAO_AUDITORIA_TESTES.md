# 🔧 CORREÇÃO: Auditoria nos Testes de Exclusão e Restauração

**Data:** 27/11/2025  
**Problema Identificado:** Testes de exclusão e restauração não apareciam nos logs de auditoria

---

## 🔍 PROBLEMA

Os testes de exclusão e restauração (`teste_5_excluir_restaurar.py`) estavam chamando diretamente:
- `RomaneioService.excluir_romaneio()` - que não registra na auditoria
- Restauração manual sem chamar `registrar_restauracao()`

**Causa:** O serviço `RomaneioService.excluir_romaneio()` apenas exclui o objeto, mas não registra na auditoria. A auditoria só é registrada quando a exclusão é feita através das views que chamam `registrar_exclusao()`.

---

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. **Registro de Exclusão na Auditoria**

Adicionado registro de auditoria ANTES da exclusão:

```python
# Buscar ou criar usuário para auditoria
usuario_auditoria, _ = Usuario.objects.get_or_create(
    username='sistema_teste',
    defaults={
        'email': 'sistema_teste@teste.com',
        'tipo_usuario': 'admin',
        'is_staff': True,
        'is_superuser': True
    }
)

# Registrar exclusão na auditoria ANTES de excluir
registrar_exclusao(
    usuario=usuario_auditoria,
    instancia=romaneio,
    request=None,
    descricao=f"Exclusao de teste: Romaneio {romaneio.codigo}"
)
```

### 2. **Registro de Restauração na Auditoria**

Adicionado registro de auditoria APÓS a restauração:

```python
# Registrar restauração na auditoria
registrar_restauracao(
    usuario=usuario_auditoria,
    instancia=romaneio,
    request=None,
    descricao=f"Restauracao de teste: Romaneio {romaneio.codigo}"
)
```

---

## 📋 MUDANÇAS REALIZADAS

### Arquivo: `scripts/test/teste_5_excluir_restaurar.py`

1. **Importações adicionadas:**
   - `Usuario` do modelo
   - `registrar_exclusao` e `registrar_restauracao` de `notas.utils.auditoria`

2. **Método `_excluir_dados()` atualizado:**
   - Cria/busca usuário para auditoria
   - Registra exclusão na auditoria ANTES de excluir
   - Mantém a exclusão via `RomaneioService.excluir_romaneio()`

3. **Método `_restaurar_dados()` atualizado:**
   - Cria/busca usuário para auditoria
   - Registra restauração na auditoria APÓS restaurar

---

## 🎯 RESULTADO

Agora os testes de exclusão e restauração:

✅ **Registram exclusões na auditoria** - Antes de excluir o objeto  
✅ **Registram restaurações na auditoria** - Após restaurar o objeto  
✅ **Aparecem nos logs de auditoria** - Visíveis em `/notas/auditoria/logs/`  
✅ **Podem ser restaurados via interface** - Usando a funcionalidade de restauração do sistema

---

## 📝 NOTAS IMPORTANTES

1. **Ordem de Operações:**
   - A exclusão deve ser registrada na auditoria **ANTES** de excluir o objeto
   - A restauração deve ser registrada na auditoria **APÓS** restaurar o objeto

2. **Usuário de Auditoria:**
   - Os testes criam um usuário `sistema_teste` para registrar as ações
   - Este usuário é reutilizado entre execuções do teste

3. **Compatibilidade:**
   - A solução mantém compatibilidade com o código existente
   - Não altera o comportamento do `RomaneioService`
   - Apenas adiciona o registro de auditoria nos testes

---

## 🔄 PRÓXIMOS PASSOS

1. ✅ **Correção aplicada** - Teste 5 atualizado
2. ⏳ **Verificar outros testes** - Se outros testes fazem exclusões, também devem registrar na auditoria
3. ⏳ **Documentar padrão** - Criar guia para testes que fazem exclusões/restaurações

---

**Última Atualização:** 27/11/2025  
**Status:** ✅ CORREÇÃO IMPLEMENTADA


