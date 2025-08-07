# Restrições de Permissão para Exclusão

## Visão Geral

Este documento descreve as restrições de permissão implementadas para controlar quem pode excluir registros no sistema Estelar.

## Restrições Implementadas

### 1. Exclusão de Clientes
- **Permitido para**: Apenas usuários administradores
- **Bloqueado para**: Usuários funcionários e clientes
- **Mensagem de erro**: "Apenas administradores podem excluir clientes cadastrados."

### 2. Exclusão de Motoristas
- **Permitido para**: Apenas usuários administradores
- **Bloqueado para**: Usuários funcionários e clientes
- **Mensagem de erro**: "Apenas administradores podem excluir motoristas cadastrados."

### 3. Exclusão de Romaneios
- **Romaneios com status 'Salvo'**: Todos os usuários autorizados podem excluir
- **Romaneios com status 'Emitido'**: Apenas usuários administradores podem excluir
- **Mensagem de erro**: "Apenas administradores podem excluir romaneios que já foram emitidos."

## Implementação Técnica

### Views Modificadas

#### `excluir_cliente(request, pk)`
```python
@login_required
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar se o usuário é administrador
    if not request.user.is_admin:
        messages.error(request, 'Apenas administradores podem excluir clientes cadastrados.')
        return redirect('notas:listar_clientes')
    
    # ... resto da lógica de exclusão
```

#### `excluir_motorista(request, pk)`
```python
@login_required
def excluir_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    
    # Verificar se o usuário é administrador
    if not request.user.is_admin:
        messages.error(request, 'Apenas administradores podem excluir motoristas cadastrados.')
        return redirect('notas:listar_motoristas')
    
    # ... resto da lógica de exclusão
```

#### `excluir_romaneio(request, pk)`
```python
@login_required
def excluir_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Verificar se o romaneio foi emitido
    if romaneio.status == 'Emitido':
        # Se foi emitido, apenas administradores podem excluir
        if not request.user.is_admin:
            messages.error(request, 'Apenas administradores podem excluir romaneios que já foram emitidos.')
            return redirect('notas:listar_romaneios')
    
    # ... resto da lógica de exclusão
```

### Templates Modificados

#### `detalhes_cliente.html`
- Botão de exclusão só aparece para usuários administradores
```html
{% if user.is_admin %}
    <form action="{% url 'notas:excluir_cliente' cliente.pk %}" method="post">
        <!-- botão de exclusão -->
    </form>
{% endif %}
```

#### `detalhes_motorista.html`
- Botão de exclusão só aparece para usuários administradores
```html
{% if user.is_admin %}
    <form action="{% url 'notas:excluir_motorista' motorista.pk %}" method="post">
        <!-- botão de exclusão -->
    </form>
{% endif %}
```

#### `detalhes_romaneio.html`
- Botão de exclusão para romaneios emitidos só aparece para administradores
- Botão de exclusão para romaneios salvos aparece para todos os usuários autorizados
```html
{% if romaneio.status == 'Emitido' %}
    {% if user.is_admin %}
        <!-- botão de exclusão apenas para admin -->
    {% endif %}
{% else %}
    <!-- botão de exclusão para todos -->
{% endif %}
```

## Verificação de Permissões

### Propriedades do Modelo Usuario
```python
@property
def is_admin(self):
    return self.tipo_usuario.upper() == 'ADMIN'

@property
def is_funcionario(self):
    return self.tipo_usuario.upper() in ['ADMIN', 'FUNCIONARIO']
```

## Testes

Para testar as restrições implementadas, execute o script:
```bash
python testar_permissoes.py
```

Este script cria usuários de teste e simula tentativas de exclusão para verificar se as restrições estão funcionando corretamente.

## Fluxo de Segurança

1. **Verificação de Login**: Todas as views de exclusão requerem login (`@login_required`)
2. **Verificação de Permissão**: Verifica se o usuário tem o tipo correto
3. **Redirecionamento**: Usuários sem permissão são redirecionados com mensagem de erro
4. **Interface**: Botões de exclusão são ocultados na interface para usuários sem permissão

## Considerações de Segurança

- As verificações são feitas tanto no backend (views) quanto no frontend (templates)
- Mensagens de erro claras informam ao usuário sobre as restrições
- Redirecionamentos seguros evitam acesso direto às URLs de exclusão
- Logs de tentativas de acesso não autorizado podem ser implementados futuramente 