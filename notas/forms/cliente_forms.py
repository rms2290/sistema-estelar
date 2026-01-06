"""
=============================================================================
FORMULÁRIOS DE CLIENTES
=============================================================================

Este módulo contém todos os formulários relacionados ao gerenciamento
de clientes, incluindo formulários de criação/edição e busca.

Formulários:
------------
1. ClienteForm: Formulário principal para criar/editar clientes
2. ClienteSearchForm: Formulário de busca e filtros

Autor: Sistema Estelar
Data: 2025
Versão: 2.0
=============================================================================
"""
from django import forms
import re
from validate_docbr import CNPJ
from ..models import Cliente
from .base import UpperCaseCharField, ESTADOS_CHOICES
from ..utils.constants import TAMANHO_CNPJ


# ============================================================================
# FORMULÁRIO PRINCIPAL
# ============================================================================

class ClienteForm(forms.ModelForm):
    """
    Formulário para criar e editar clientes.
    
    Campos Principais:
        - razao_social: Nome oficial da empresa (obrigatório, maiúsculas)
        - cnpj: CNPJ da empresa (opcional, validado)
        - nome_fantasia: Nome comercial (opcional, maiúsculas)
        - endereco, numero, complemento, bairro, cidade, estado, cep
        - telefone, email
        - status: Ativo ou Inativo
    
    Validações:
        - CNPJ: Valida formato e dígitos verificadores
        - Razão Social: Obrigatório, único no banco
        - Campos de texto: Convertidos automaticamente para maiúsculas
    
    Uso:
        # Criar novo cliente
        form = ClienteForm(data=request.POST)
        if form.is_valid():
            cliente = form.save()
        
        # Editar cliente existente
        form = ClienteForm(data=request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
    
    Exemplo:
        form_data = {
            'razao_social': 'Empresa XYZ LTDA',
            'cnpj': '11.222.333/0001-81',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        if form.is_valid():
            cliente = form.save()
    """
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', '---')] + ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    razao_social = UpperCaseCharField(
        label='Razão Social',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razão Social da Empresa'})
    )
    
    cnpj = forms.CharField(
        label='CNPJ',
        max_length=18,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'})
    )
    
    nome_fantasia = UpperCaseCharField(
        label='Nome Fantasia',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Fantasia (opcional)'})
    )
    
    inscricao_estadual = UpperCaseCharField(
        label='Inscrição Estadual',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Inscrição Estadual'})
    )
    
    endereco = UpperCaseCharField(
        label='Endereço',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Endereço Completo'})
    )
    
    numero = forms.CharField(
        label='Número',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número'})
    )
    
    complemento = UpperCaseCharField(
        label='Complemento',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Complemento (opcional)'})
    )
    
    bairro = UpperCaseCharField(
        label='Bairro',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'})
    )
    
    cidade = UpperCaseCharField(
        label='Cidade',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'})
    )
    
    cep = forms.CharField(
        label='CEP',
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'})
    )
    
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    
    email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'})
    )
    
    status = forms.ChoiceField(
        label='Status',
        choices=Cliente.STATUS_CHOICES,
        initial='Ativo',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Cliente
        fields = '__all__'

    def clean_cnpj(self):
        """
        Valida e limpa o campo CNPJ.
        
        Processo:
        1. Remove caracteres não numéricos (pontos, traços, barras)
        2. Verifica se tem exatamente 14 dígitos
        3. Valida dígitos verificadores usando validate_docbr
        4. Retorna apenas números (sem formatação)
        
        Returns:
            str: CNPJ apenas com números (14 dígitos)
        
        Raises:
            forms.ValidationError: Se CNPJ estiver em formato inválido
                                 ou dígitos verificadores incorretos
        
        Exemplo:
            Input: "11.222.333/0001-81"
            Output: "11222333000181"
        """
        cnpj = self.cleaned_data.get('cnpj')
        
        # Se CNPJ não foi informado, retorna vazio (campo é opcional)
        if not cnpj:
            return cnpj
        
        # Remove todos os caracteres não numéricos
        cnpj_numeros = re.sub(r'[^0-9]', '', cnpj)

        # Valida quantidade de dígitos
        if len(cnpj_numeros) != TAMANHO_CNPJ:
            raise forms.ValidationError(f"CNPJ deve conter {TAMANHO_CNPJ} dígitos numéricos.")
        
        # Valida dígitos verificadores usando biblioteca validate_docbr
        cnpj_validator = CNPJ()
        if not cnpj_validator.validate(cnpj_numeros):
            raise forms.ValidationError("CNPJ inválido. Verifique o número digitado.")

        # Retorna apenas números (sem formatação)
        return cnpj_numeros


# ============================================================================
# FORMULÁRIO DE BUSCA
# ============================================================================

class ClienteSearchForm(forms.Form):
    """
    Formulário de busca e filtros para listagem de clientes.
    
    Todos os campos são opcionais, permitindo buscas flexíveis:
    - Buscar apenas por razão social
    - Buscar apenas por CNPJ
    - Filtrar apenas por status
    - Combinar múltiplos filtros
    
    Campos:
        - razao_social: Busca parcial (case-insensitive, maiúsculas)
        - cnpj: Busca parcial no CNPJ
        - status: Filtro exato (Ativo, Inativo, ou Todos)
    
    Uso:
        form = ClienteSearchForm(data=request.GET)
        if form.is_valid():
            razao_social = form.cleaned_data.get('razao_social')
            # Aplicar filtros na view
    
    Exemplo:
        # Buscar por razão social
        form = ClienteSearchForm({'razao_social': 'XYZ'})
        
        # Filtrar apenas ativos
        form = ClienteSearchForm({'status': 'Ativo'})
        
        # Busca combinada
        form = ClienteSearchForm({
            'razao_social': 'XYZ',
            'status': 'Ativo'
        })
    """
    razao_social = UpperCaseCharField(
        label='Razão Social',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razão Social'})
    )
    cnpj = forms.CharField(
        label='CNPJ',
        required=False,
        max_length=18,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'})
    )
    status = forms.ChoiceField(
        label='Status',
        choices=[('', 'Todos'),] + Cliente.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

