# 📚 Padrões de Documentação do Código

**Sistema Estelar - Guia de Documentação Profissional**

---

## 🎯 Objetivo

Este documento estabelece os padrões de documentação que devem ser seguidos em todo o código do sistema, garantindo que o código seja profissional, bem organizado e fácil de entender para qualquer desenvolvedor que trabalhe no projeto.

---

## 📋 Estrutura de Documentação

### 1. Cabeçalho do Módulo

Todo arquivo Python deve começar com um cabeçalho documentando o módulo:

```python
"""
=============================================================================
NOME DO MÓDULO
=============================================================================

Descrição breve do que o módulo faz e sua responsabilidade principal.

Estrutura:
----------
1. Seção 1: Descrição do que contém
2. Seção 2: Descrição do que contém
3. Seção 3: Descrição do que contém

Autor: Sistema Estelar
Data: 2025
Versão: 2.0
=============================================================================
"""
```

### 2. Documentação de Classes

Toda classe deve ter uma docstring completa:

```python
class MinhaClasse:
    """
    Descrição breve da classe.
    
    Descrição detalhada do propósito e responsabilidades da classe.
    
    Atributos:
        - atributo1: Descrição do atributo
        - atributo2: Descrição do atributo
    
    Métodos Principais:
        - metodo1(): Descrição do método
        - metodo2(): Descrição do método
    
    Exemplo:
        objeto = MinhaClasse(param1, param2)
        resultado = objeto.metodo1()
    """
```

### 3. Documentação de Métodos/Funções

Todos os métodos e funções devem ter docstrings completas:

```python
def meu_metodo(self, param1, param2=None):
    """
    Descrição breve do que o método faz.
    
    Descrição detalhada do comportamento, lógica e propósito.
    
    Args:
        param1 (tipo): Descrição do parâmetro
        param2 (tipo, opcional): Descrição do parâmetro (padrão: None)
    
    Returns:
        tipo: Descrição do valor retornado
    
    Raises:
        TipoErro: Quando e por que este erro é levantado
    
    Exemplo:
        >>> resultado = objeto.meu_metodo('valor1', param2='valor2')
        >>> print(resultado)
        'resultado esperado'
    
    Nota:
        Informações adicionais importantes sobre o método.
    """
```

### 4. Documentação de Modelos Django

Modelos devem ter documentação completa incluindo campos, relacionamentos e exemplos:

```python
class MeuModelo(models.Model):
    """
    Descrição do modelo e sua função no sistema.
    
    Campos Principais:
        - campo1: Descrição (obrigatório/opcional)
        - campo2: Descrição (obrigatório/opcional)
    
    Relacionamentos:
        - relacionamento1: Descrição do relacionamento
        - relacionamento2: Descrição do relacionamento
    
    Ordenação Padrão: Por campo (ascendente/descendente)
    
    Exemplo:
        objeto = MeuModelo.objects.create(
            campo1='valor1',
            campo2='valor2'
        )
    """
```

### 5. Seções e Organização

Use seções bem definidas para organizar o código:

```python
# ============================================================================
# SEÇÃO PRINCIPAL
# ============================================================================

# -----------------------------------------------------------------------------
# SUBSECÇÃO
# -----------------------------------------------------------------------------

# Comentários inline para explicações específicas
```

---

## 📝 Padrões de Comentários

### Comentários Inline

Use comentários inline para explicar lógica complexa:

```python
# Calcular totais com tratamento de valores None
peso_total = sum(nf.peso or 0 for nf in notas_fiscais.all())

# Verificar se os valores mudaram para evitar saves desnecessários
if self.peso_total != peso_total:
    self.peso_total = peso_total
    self.save(update_fields=['peso_total'])
```

### Comentários de Bloco

Use comentários de bloco para seções grandes:

```python
# ============================================================================
# LÓGICA DE VALIDAÇÃO
# ============================================================================
# Esta seção contém toda a lógica de validação de dados antes de salvar.
# As validações são executadas na seguinte ordem:
# 1. Validação de campos obrigatórios
# 2. Validação de formatos
# 3. Validação de regras de negócio
```

---

## 🎨 Convenções de Nomenclatura

### Classes
- **PascalCase**: `ClienteForm`, `RomaneioService`, `NotaFiscal`

### Funções e Métodos
- **snake_case**: `calcular_totais()`, `validar_cnpj()`, `obter_notas_disponiveis()`

### Constantes
- **UPPER_SNAKE_CASE**: `STATUS_CHOICES`, `MAX_TENTATIVAS`, `DEFAULT_STATUS`

### Variáveis
- **snake_case**: `total_peso`, `nota_fiscal`, `cliente_id`

### Privados
- **Prefixo underscore**: `_get_next_codigo()`, `_atualizar_status()`

---

## 📖 Exemplos de Documentação

### Exemplo 1: Modelo Django

```python
class Cliente(UpperCaseMixin, models.Model):
    """
    Modelo que representa uma empresa cliente do sistema.
    
    Armazena informações completas da empresa, incluindo dados cadastrais,
    endereço, contatos e status de ativação.
    
    Campos Principais:
        - razao_social: Nome oficial da empresa (obrigatório, único)
        - cnpj: CNPJ da empresa (opcional, único se informado)
        - status: Ativo ou Inativo
    
    Relacionamentos:
        - notas_fiscais: Notas fiscais do cliente (ForeignKey reverso)
        - romaneios_cliente: Romaneios do cliente (ForeignKey reverso)
    
    Ordenação Padrão: Por razão social (alfabética)
    
    Exemplo:
        cliente = Cliente.objects.create(
            razao_social='Empresa XYZ LTDA',
            cnpj='12345678000190',
            status='Ativo'
        )
    """
```

### Exemplo 2: Serviço

```python
class RomaneioService:
    """
    Serviço centralizado para operações de negócio relacionadas a Romaneios.
    
    Esta classe encapsula toda a lógica complexa de manipulação de romaneios,
    incluindo validações, atualizações de status, cálculos e gerenciamento
    de transações de banco de dados.
    
    Todos os métodos são estáticos (@staticmethod) para facilitar o uso
    sem necessidade de instanciar a classe.
    
    Uso:
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
            form_data, emitir=True, tipo='normal'
        )
    """
    
    @staticmethod
    def criar_romaneio(form_data, emitir=False, tipo='normal'):
        """
        Cria um novo romaneio com validações e atualizações de status.
        
        Args:
            form_data: Dados do formulário validado
            emitir: Se True, cria como 'Emitido', senão 'Salvo'
            tipo: 'normal' ou 'generico'
        
        Returns:
            tuple: (romaneio, sucesso, mensagem_erro)
        """
```

### Exemplo 3: View

```python
def adicionar_cliente(request):
    """
    View para adicionar um novo cliente ao sistema.
    
    Métodos Suportados:
        - GET: Exibe formulário vazio para criação
        - POST: Processa formulário e cria cliente
    
    Fluxo:
        1. Se POST e formulário válido → Cria cliente e redireciona
        2. Se POST e formulário inválido → Exibe erros
        3. Se GET → Exibe formulário vazio
    
    Template:
        notas/adicionar_cliente.html
    
    Exemplo de Uso:
        POST /notas/clientes/adicionar/
    """
```

---

## ✅ Checklist de Documentação

Antes de considerar um arquivo completamente documentado, verifique:

- [ ] Cabeçalho do módulo com descrição completa
- [ ] Todas as classes têm docstrings
- [ ] Todos os métodos/funções têm docstrings
- [ ] Parâmetros documentados com tipos e descrições
- [ ] Valores de retorno documentados
- [ ] Exceções documentadas (quando aplicável)
- [ ] Exemplos de uso incluídos
- [ ] Comentários inline para lógica complexa
- [ ] Seções bem organizadas e separadas
- [ ] Nomenclatura seguindo convenções

---

## 🔍 Ferramentas de Verificação

### Docstring Coverage
```bash
# Verificar cobertura de documentação
pip install interrogate
interrogate notas/
```

### Linting
```bash
# Verificar qualidade do código
pylint notas/
flake8 notas/
```

---

## 📚 Referências

- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Django Coding Style](https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/)

---

**Última Atualização:** 26/11/2025  
**Versão:** 1.0


