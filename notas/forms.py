from django import forms
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem
import re
from datetime import date
from decimal import Decimal
from validate_docbr import CNPJ

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
    # Sobrescreve o campo 'estado' e 'uf_emissao_cnh'
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
    class Meta:
        model = Motorista
        fields = '__all__'
        widgets = {
            # ... (outros widgets) ...
            # Remova os widgets antigos de 'estado' e 'uf_emissao_cnh' se estiverem aqui
            # 'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
            # 'uf_emissao_cnh': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2, 'placeholder': 'UF'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        if len(cpf_numeros) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        return cpf_numeros

    def clean_celular(self): # <<< ESTE ESTÁ AQUI, MAS LEMBRE-SE QUE O NOME NO MODELO É 'TELEFONE'
        celular = self.cleaned_data.get('celular')
        if not celular: return celular
        celular_numeros = re.sub(r'[^0-9]', '', celular)
        if not (10 <= len(celular_numeros) <= 11):
            raise forms.ValidationError("Celular deve ter entre 10 e 11 dígitos (incluindo DDD).")
        return celular_numeros

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
# Formulários de Pesquisa (mantenha no final do arquivo)
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