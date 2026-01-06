"""
Formulários relacionados a Motoristas
"""
from django import forms
from django.core.exceptions import ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import re
from validate_docbr import CPF

from ..models import Motorista, HistoricoConsulta
from .base import UpperCaseCharField, ESTADOS_CHOICES


class MotoristaForm(forms.ModelForm):
    """Formulário para criar e editar motoristas"""
    # >>> SOBRESCRITA DOS CAMPOS ESTADO E UF_EMISSAO_CNH <<<
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', '---')] + ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    uf_emissao_cnh = forms.ChoiceField(
        label='UF de Emissão da CNH',
        choices=[('', '---')] + ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Sobrescrever campos de texto para uppercase
    nome = UpperCaseCharField(
        label='Nome Completo',
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '000.000.000-00',
            'data-format': 'cpf'
        })
    )
    
    cnh = forms.CharField(
        label='CNH',
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000'})
    )
    
    codigo_seguranca = UpperCaseCharField(
        label='Código de Segurança CNH',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    
    endereco = UpperCaseCharField(
        label='Endereço',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    numero = forms.CharField(
        label='Número',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    complemento = UpperCaseCharField(
        label='Complemento',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    bairro = UpperCaseCharField(
        label='Bairro',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    cidade = UpperCaseCharField(
        label='Cidade',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    cep = forms.CharField(
        label='CEP',
        max_length=9,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'})
    )
    
    numero_consulta = UpperCaseCharField(
        label='Número da Última Consulta',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Digite observações sobre o motorista...'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Garantir que os campos de data sejam formatados corretamente quando há uma instância
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'data_nascimento') and self.instance.data_nascimento:
                data_nasc_str = self.instance.data_nascimento.strftime('%Y-%m-%d')
                self.fields['data_nascimento'].initial = data_nasc_str
                if 'data_nascimento' not in self.initial:
                    self.initial['data_nascimento'] = data_nasc_str
            
            if hasattr(self.instance, 'vencimento_cnh') and self.instance.vencimento_cnh:
                vencimento_str = self.instance.vencimento_cnh.strftime('%Y-%m-%d')
                self.fields['vencimento_cnh'].initial = vencimento_str
                if 'vencimento_cnh' not in self.initial:
                    self.initial['vencimento_cnh'] = vencimento_str

    class Meta:
        model = Motorista
        fields = [
            'nome', 'cpf', 'rg', 'cnh',
            'codigo_seguranca', 'vencimento_cnh', 'uf_emissao_cnh',
            'telefone',
            'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep',
            'data_nascimento',
            'numero_consulta',
            'observacoes',
        ]
        widgets = {
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'vencimento_cnh': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'uf_emissao_cnh': forms.Select(attrs={'class': 'form-control'}), 
            'estado': forms.Select(attrs={'class': 'form-control'}), 
            'data_nascimento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        
        if not cpf:
            return cpf

        cpf_numeros = re.sub(r'[^0-9]', '', cpf)

        if len(cpf_numeros) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        
        cpf_validator = CPF()
        if not cpf_validator.validate(cpf_numeros):
            raise forms.ValidationError("CPF inválido. Verifique o número digitado.")

        return cpf_numeros

    def clean_telefone(self): 
        telefone = self.cleaned_data.get('telefone') 
        if not telefone: 
            return telefone
        telefone_numeros = re.sub(r'[^0-9]', '', telefone)
        if not (10 <= len(telefone_numeros) <= 11):
            raise forms.ValidationError("Telefone deve ter entre 10 e 11 dígitos (incluindo DDD).")
        return telefone_numeros

    def clean_cep(self):
        cep = self.cleaned_data.get('cep')
        
        if not cep:
            return cep
            
        cep_numeros = re.sub(r'[^0-9]', '', cep)
        if len(cep_numeros) != 8:
            raise forms.ValidationError("CEP deve conter 8 dígitos numéricos.")
        return cep_numeros

    def clean(self):
        """Validação personalizada para garantir que os veículos sejam diferentes e validar conflitos entre datas"""
        cleaned_data = super().clean()
        
        # Validações de veículos
        veiculo_principal = cleaned_data.get('veiculo_principal')
        reboque_1 = cleaned_data.get('reboque_1')
        reboque_2 = cleaned_data.get('reboque_2')
        tipo_composicao = cleaned_data.get('tipo_composicao_motorista')
        
        # Lista para armazenar veículos únicos
        veiculos_selecionados = []
        
        if veiculo_principal:
            veiculos_selecionados.append(veiculo_principal)
        
        if reboque_1:
            if reboque_1 in veiculos_selecionados:
                raise forms.ValidationError("O Reboque 1 não pode ser o mesmo que o Veículo Principal.")
            veiculos_selecionados.append(reboque_1)
        
        if reboque_2:
            if reboque_2 in veiculos_selecionados:
                raise forms.ValidationError("O Reboque 2 não pode ser o mesmo que o Veículo Principal ou Reboque 1.")
            veiculos_selecionados.append(reboque_2)
        
        # Validação baseada no tipo de composição
        if tipo_composicao == 'Simples':
            if reboque_1 or reboque_2:
                raise forms.ValidationError("Para composição Simples, não é permitido selecionar reboques.")
        elif tipo_composicao == 'Carreta':
            if not reboque_1:
                raise forms.ValidationError("Para composição Carreta, é obrigatório selecionar o Reboque 1.")
            if reboque_2:
                raise forms.ValidationError("Para composição Carreta, não é permitido selecionar o Reboque 2.")
        elif tipo_composicao == 'Bi-trem':
            if not reboque_1 or not reboque_2:
                raise forms.ValidationError("Para composição Bi-trem, é obrigatório selecionar tanto o Reboque 1 quanto o Reboque 2.")
        
        # Validações de datas
        data_nascimento = cleaned_data.get('data_nascimento')
        vencimento_cnh = cleaned_data.get('vencimento_cnh')
        
        # Se estamos editando e o campo não foi preenchido, usar o valor existente
        if self.instance and self.instance.pk:
            if not data_nascimento and self.instance.data_nascimento:
                data_nascimento = self.instance.data_nascimento
                cleaned_data['data_nascimento'] = data_nascimento
            if not vencimento_cnh and self.instance.vencimento_cnh:
                vencimento_cnh = self.instance.vencimento_cnh
                cleaned_data['vencimento_cnh'] = vencimento_cnh
        
        hoje = date.today()
        
        # Validar data de nascimento
        if data_nascimento:
            if data_nascimento > hoje:
                raise forms.ValidationError({
                    'data_nascimento': 'A data de nascimento não pode ser no futuro.'
                })
            
            idade_minima_absoluta = hoje - relativedelta(years=16)
            if data_nascimento > idade_minima_absoluta:
                raise forms.ValidationError({
                    'data_nascimento': 'A data de nascimento indica que a pessoa tem menos de 16 anos. Verifique os dados.'
                })
        
        # Validar vencimento da CNH
        if vencimento_cnh:
            if data_nascimento and vencimento_cnh < data_nascimento:
                raise forms.ValidationError({
                    'vencimento_cnh': 'A data de vencimento da CNH não pode ser anterior à data de nascimento.'
                })
            
            if data_nascimento:
                idade_na_vencimento = relativedelta(vencimento_cnh, data_nascimento)
                anos_na_vencimento = idade_na_vencimento.years
                
                if anos_na_vencimento < 18:
                    raise forms.ValidationError({
                        'vencimento_cnh': f'O motorista teria apenas {anos_na_vencimento} anos na data de vencimento da CNH. É necessário ter pelo menos 18 anos para dirigir.'
                    })
        
        return cleaned_data

    def save(self, commit=True):
        """Sobrescreve o método save para garantir que campos vazios sejam salvos como None"""
        motorista = super().save(commit=False)
        
        # Preservar valores de data se não foram alterados
        if self.instance and self.instance.pk:
            if not self.cleaned_data.get('data_nascimento') and self.instance.data_nascimento:
                motorista.data_nascimento = self.instance.data_nascimento
            if not self.cleaned_data.get('vencimento_cnh') and self.instance.vencimento_cnh:
                motorista.vencimento_cnh = self.instance.vencimento_cnh
        
        # Garantir que campos vazios sejam None
        campos_opcionais = ['rg', 'cnh', 'codigo_seguranca', 'telefone', 'endereco', 
                           'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep',
                           'numero_consulta', 'observacoes', 'uf_emissao_cnh']
        
        for campo in campos_opcionais:
            valor = getattr(motorista, campo, None)
            if valor == '' or valor == '---' or (isinstance(valor, str) and valor.strip() == ''):
                setattr(motorista, campo, None)
        
        if commit:
            motorista.save()
        return motorista


class MotoristaSearchForm(forms.Form):
    """Formulário de pesquisa para motoristas"""
    nome = UpperCaseCharField(
        label='Nome do Motorista',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Motorista'})
    )
    cpf = forms.CharField(
        label='CPF',
        required=False,
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '000.000.000-00',
            'data-format': 'cpf'
        })
    )
    rg = forms.CharField(
        label='RG/RNE',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RG/RNE'})
    )


class HistoricoConsultaForm(forms.ModelForm):
    """Formulário para histórico de consultas de motoristas"""
    numero_consulta = UpperCaseCharField(
        label='Número da Consulta',
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da consulta'})
    )
    
    gerenciadora = UpperCaseCharField(
        label='Gerenciadora',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da gerenciadora'})
    )
    
    observacoes = forms.CharField(
        label='Observações da Consulta',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = HistoricoConsulta
        fields = ['numero_consulta', 'data_consulta', 'gerenciadora', 'status_consulta', 'observacoes']
        widgets = {
            'data_consulta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status_consulta': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche a data da consulta com a data atual por padrão
        if self.instance.pk is None and not self.initial.get('data_consulta'):
            self.fields['data_consulta'].initial = datetime.now().date()

