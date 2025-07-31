from django import forms
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta 
import re
from datetime import date
from decimal import Decimal     
from validate_docbr import CNPJ, CPF

ESTADOS_CHOICES = [
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
    ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
    ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
    ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
    ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
]


# --------------------------------------------------------------------------------------
# Novo formulário para Nota Fiscal
# --------------------------------------------------------------------------------------
class NotaFiscalForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )

    class Meta:
        model = NotaFiscal
        exclude = ['status', 'romaneios']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None and not self.initial.get('data'):
            self.fields['data'].initial = date.today()

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            return int(peso)
        return peso

# --------------------------------------------------------------------------------------
# Novo formulário para Cliente
# --------------------------------------------------------------------------------------
class ClienteForm(forms.ModelForm):
    # Sobrescreve o campo 'estado'
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', '---')] + ESTADOS_CHOICES, # Adiciona opção '---' para vazio
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Cliente
        fields = '__all__' # Ou liste os campos que você quer que apareçam
        widgets = {
            # ... (outros widgets) ...
            # Remova o widget antigo de 'estado' se ele estiver aqui
            # 'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        cnpj_numeros = re.sub(r'[^0-9]', '', cnpj) # Remove tudo que não for número

        # Validação de comprimento (básica)
        if len(cnpj_numeros) != 14:
            raise forms.ValidationError("CNPJ deve conter 14 dígitos numéricos.")
        
        # >>> NOVO: Validação do dígito verificador usando validate_docbr <<<
        cnpj_validator = CNPJ()
        if not cnpj_validator.validate(cnpj_numeros):
            raise forms.ValidationError("CNPJ inválido. Verifique o número digitado.")

        return cnpj_numeros

# --------------------------------------------------------------------------------------
# Novo formulário para Motoristas
# --------------------------------------------------------------------------------------
class MotoristaForm(forms.ModelForm):
    # Sobrescreve o campo veiculo_principal para ser um dropdown de Veiculos
    veiculo_principal = forms.ModelChoiceField(
        queryset=Veiculo.objects.all().order_by('placa'), # Puxa todos os veículos existentes
        label='Veículo Principal',
        required=False, # É opcional
        empty_label="--- Selecione um veículo ---", # Opção para não selecionar
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Motorista
        # AJUSTADO: Adicionado 'veiculo_principal'
        fields = [
            'nome', 'cpf', 'cnh',
            'codigo_seguranca', 'vencimento_cnh', 'uf_emissao_cnh',
            'telefone',
            'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep',
            'data_nascimento',
            'numero_consulta', # Mantido por enquanto
            'veiculo_principal' # <<< NOVO CAMPO NO FORMULÁRIO
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'cnh': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000'}),

            'codigo_seguranca': forms.TextInput(attrs={'class': 'form-control'}),
            'vencimento_cnh': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'uf_emissao_cnh': forms.Select(attrs={'class': 'form-control'}), # Usar Select aqui
            
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}), # Usar Select aqui
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_consulta': forms.TextInput(attrs={'class': 'form-control'}),
            # 'veiculo_principal' não precisa de widget aqui, pois foi sobrescrito acima
        }

    # MÉTODO CLEAN_CPF (VERSÃO ÚNICA E CORRETA)
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf') # Use .get() para pegar o valor do campo
        
        # Se o campo não for obrigatório e estiver vazio, retorne imediatamente
        if not cpf:
            return cpf

        cpf_numeros = re.sub(r'[^0-9]', '', cpf) # Remove tudo que não for número

        if len(cpf_numeros) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        
        cpf_validator = CPF() # Instancia o validador de CPF
        if not cpf_validator.validate(cpf_numeros): # Valida o CPF numérico
            raise forms.ValidationError("CPF inválido. Verifique o número digitado.")

        return cpf_numeros

    # clean_telefone (CORRIGIDO: renomeado de clean_celular)
    def clean_telefone(self): 
        telefone = self.cleaned_data.get('telefone') 
        if not telefone: return telefone
        telefone_numeros = re.sub(r'[^0-9]', '', telefone)
        if not (10 <= len(telefone_numeros) <= 11):
            raise forms.ValidationError("Telefone deve ter entre 10 e 11 dígitos (incluindo DDD).")
        return telefone_numeros

    def clean_cep(self):
        cep = self.cleaned_data['cep']
        cep_numeros = re.sub(r'[^0-9]', '', cep)
        if len(cep_numeros) != 8:
            raise forms.ValidationError("CEP deve conter 8 dígitos numéricos.")
        return cep_numeros

# --------------------------------------------------------------------------------------
# Novo formulário para Veículos
# --------------------------------------------------------------------------------------
class VeiculoForm(forms.ModelForm):
    # Campo 'pais' sobrescrito para garantir required=False
    pais = forms.CharField(
        label='País',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    # Sobrescreve o campo 'estado' do veículo
    estado = forms.ChoiceField(
        label='Estado (UF)',
        choices=[('', '---')] + ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # Sobrescreve o campo 'proprietario_estado'
    proprietario_estado = forms.ChoiceField(
        label='Estado do Proprietário (UF)',
        choices=[('', '---')] + ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Veiculo
        fields = '__all__'
        widgets = {
            # ... (outros widgets) ...
            # Remova os widgets antigos de 'estado' e 'proprietario_estado' se estiverem aqui
            # 'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
            # 'proprietario_estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
        }

    def clean_placa(self):
        placa = self.cleaned_data['placa']
        # Remove caracteres especiais para padronização (formato MERCOSUL ou antigo)
        placa_limpa = re.sub(r'[^a-zA-Z0-9]', '', placa).upper()

        # Validação básica de comprimento para placa Mercosul (7 caracteres alfanuméricos)
        # ou placas antigas (7 caracteres, 3 letras e 4 números)
        if len(placa_limpa) != 7:
            raise forms.ValidationError("Placa deve conter 7 caracteres alfanuméricos.")
        # Validação mais complexa de formato de placa exigiria regex específicos
        return placa_limpa

    def clean_chassi(self):
        chassi = self.cleaned_data['chassi']
        # Chassi tem 17 caracteres alfanuméricos (letras maiúsculas e números)
        chassi_limpo = re.sub(r'[^a-zA-Z0-9]', '', chassi).upper()
        if len(chassi_limpo) != 17:
            raise forms.ValidationError("Chassi deve conter 17 caracteres alfanuméricos.")
        return chassi_limpo

    def clean_renavam(self):
        renavam = self.cleaned_data['renavam']
        renavam_numeros = re.sub(r'[^0-9]', '', renavam)
        if len(renavam_numeros) != 11:
            raise forms.ValidationError("RENAVAM deve conter 11 dígitos numéricos.")
        # Opcional: Adicionar validação de dígito verificador de RENAVAM (complexo)
        return renavam_numeros
    
# --------------------------------------------------------------------------------------
# Novo formulário para Romaneios (AGORA COM __INIT__ CONSOLIDADO)
# --------------------------------------------------------------------------------------
class RomaneioViagemForm(forms.ModelForm):
    notas_fiscais = forms.ModelMultipleChoiceField(
        queryset=NotaFiscal.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Notas Fiscais Associadas"
    )

    data_romaneio = forms.DateField(
        label='Data do Romaneio',
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is None and not self.initial.get('data_romaneio'):
            self.fields['data_romaneio'].initial = date.today()
        
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('razao_social')
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        self.fields['veiculo'].queryset = Veiculo.objects.all().order_by('placa')

        # >>> AQUI: INDENTAÇÃO CORRIGIDA <<<
        if self.instance and self.instance.pk: 
            if self.instance.data_emissao:
                 self.fields['data_romaneio'].initial = self.instance.data_emissao.date()

            if self.instance.cliente:
                self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=self.instance.cliente
                ).order_by('nota')
                self.fields['notas_fiscais'].initial = self.instance.notas_fiscais.all()
        
        # >>> AQUI: INDENTAÇÃO CORRIGIDA <<<
        for field_name, field in self.fields.items(): 
            if field_name != 'notas_fiscais':
                field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'cliente':
                 field.widget.attrs.update({'onchange': 'loadNotasFiscais(this.value);'})

    class Meta:
        model = RomaneioViagem
        fields = ['cliente', 'notas_fiscais', 'motorista', 'veiculo', 'observacoes', 'data_romaneio']
        widgets = {
            # ... (widgets) ...
        }

# --------------------------------------------------------------------------------------
# NOVO: Formulário para Histórico de Consulta
# --------------------------------------------------------------------------------------
class HistoricoConsultaForm(forms.ModelForm):
    class Meta:
        model = HistoricoConsulta
        # O motorista será preenchido pela view, então não o colocamos aqui
        fields = ['numero_consulta', 'data_consulta', 'status_consulta', 'observacoes']
        widgets = {
            'numero_consulta': forms.TextInput(attrs={'class': 'form-control'}),
            'data_consulta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status_consulta': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche a data da consulta com a data atual por padrão
        if self.instance.pk is None and not self.initial.get('data_consulta'):
            self.fields['data_consulta'].initial = date.today()

# --------------------------------------------------------------------------------------
# Formulários de Pesquisa de notas
# --------------------------------------------------------------------------------------
class NotaFiscalSearchForm(forms.Form):
    nota = forms.CharField(
        label='Número da Nota',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da Nota'})
    )
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        required=False,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data = forms.DateField(
        label='Data de Emissão',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class ClienteSearchForm(forms.Form):
    razao_social = forms.CharField(
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

class MotoristaSearchForm(forms.Form):
    nome = forms.CharField(
        label='Nome do Motorista',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Motorista'})
    )
    cpf = forms.CharField(
        label='CPF',
        required=False,
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Clientes
# --------------------------------------------------------------------------------------
class ClienteSearchForm(forms.Form):
    # Campo para pesquisar por Razão Social
    razao_social = forms.CharField(
        label='Razão Social',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razão Social'})
    )
    # Campo para pesquisar por CNPJ
    cnpj = forms.CharField(
        label='CNPJ',
        required=False,
        max_length=18,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'})
    )
    # Campo para filtrar por Status (Ativo/Inativo)
    status = forms.ChoiceField(
        label='Status',
        # Adiciona 'Todos' como opção inicial, e depois as escolhas do modelo Cliente
        choices=[('', 'Todos'),] + Cliente.STATUS_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Motoristas
# --------------------------------------------------------------------------------------
class MotoristaSearchForm(forms.Form):
    # Campo para pesquisar por Nome do Motorista
    nome = forms.CharField(
        label='Nome do Motorista',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Motorista'})
    )
    # Campo para pesquisar por CPF
    cpf = forms.CharField(
        label='CPF',
        required=False,
        max_length=14, # 11 dígitos + pontos e traços
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Veículos
# --------------------------------------------------------------------------------------
class VeiculoSearchForm(forms.Form):
    # Campo para pesquisar por Placa
    placa = forms.CharField(
        label='Placa',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC-1234 ou ABC1D23'})
    )
    # Campo para pesquisar por Chassi
    chassi = forms.CharField(
        label='Chassi',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do Chassi'})
    )
    # Campo para pesquisar por Nome do Proprietário
    proprietario_nome = forms.CharField(
        label='Nome do Proprietário',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome/Razão Social do Proprietário'})
    )
    # Campo para filtrar por Tipo de Unidade de Veículo (Carro, Van, Truck, etc.)
    tipo_unidade = forms.ChoiceField(
        label='Tipo de Unidade',
        choices=[('', 'Todos')] + Veiculo.TIPO_UNIDADE_CHOICES, # Adiciona 'Todos' como opção inicial
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# --------------------------------------------------------------------------------------
# NOVO: Formulário para Histórico de Consulta
# --------------------------------------------------------------------------------------
class HistoricoConsultaForm(forms.ModelForm):
    class Meta:
        model = HistoricoConsulta
        # O motorista será preenchido pela view, então não o colocamos aqui
        fields = ['numero_consulta', 'data_consulta', 'status_consulta', 'observacoes']
        widgets = {
            'numero_consulta': forms.TextInput(attrs={'class': 'form-control'}),
            'data_consulta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status_consulta': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche a data da consulta com a data atual por padrão
        if self.instance.pk is None and not self.initial.get('data_consulta'):
            self.fields['data_consulta'].initial = date.today()