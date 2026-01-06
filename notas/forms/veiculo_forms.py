"""
Formulários relacionados a Veículos
"""
from django import forms
import re
from ..models import Veiculo
from .base import UpperCaseCharField, ESTADOS_CHOICES


class VeiculoForm(forms.ModelForm):
    """Formulário para criar e editar veículos"""
    # Lista de países comuns
    PAISES_CHOICES = [
        ('', '---'),
        ('Brasil', 'Brasil'),
        ('Argentina', 'Argentina'),
        ('Paraguai', 'Paraguai'),
        ('Uruguai', 'Uruguai'),
        ('Bolívia', 'Bolívia'),
        ('Chile', 'Chile'),
        ('Peru', 'Peru'),
        ('Colômbia', 'Colômbia'),
        ('Venezuela', 'Venezuela'),
        ('Equador', 'Equador'),
        ('Guiana', 'Guiana'),
        ('Suriname', 'Suriname'),
        ('Guiana Francesa', 'Guiana Francesa'),
    ]
    
    # Campo 'pais' sobrescrito para usar dropdown
    pais = forms.ChoiceField(
        label='País',
        choices=PAISES_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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
    
    # Lista de marcas comuns de veículos
    MARCAS_CHOICES = [
        ('', '---'),
        ('FORD', 'FORD'),
        ('CHEVROLET', 'CHEVROLET'),
        ('VOLKSWAGEN', 'VOLKSWAGEN'),
        ('FIAT', 'FIAT'),
        ('MERCEDES-BENZ', 'MERCEDES-BENZ'),
        ('SCANIA', 'SCANIA'),
        ('VOLVO', 'VOLVO'),
        ('IVECO', 'IVECO'),
        ('MAN', 'MAN'),
        ('DAF', 'DAF'),
        ('RENAULT', 'RENAULT'),
        ('PEUGEOT', 'PEUGEOT'),
        ('CITROEN', 'CITROEN'),
        ('HYUNDAI', 'HYUNDAI'),
        ('TOYOTA', 'TOYOTA'),
        ('NISSAN', 'NISSAN'),
        ('HONDA', 'HONDA'),
        ('MITSUBISHI', 'MITSUBISHI'),
        ('MAZDA', 'MAZDA'),
        ('SUBARU', 'SUBARU'),
        ('AUDI', 'AUDI'),
        ('BMW', 'BMW'),
        ('OUTROS', 'OUTROS'),
    ]
    
    # Sobrescreve o campo 'marca' para usar dropdown
    marca = forms.ChoiceField(
        label='Marca',
        choices=MARCAS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campo 'modelo' mantido como texto livre
    modelo = UpperCaseCharField(
        label='Modelo',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Lista de anos de fabricação
    ANOS_CHOICES = [('', '---')] + [(str(ano), str(ano)) for ano in range(2029, 1999, -1)]
    
    # Sobrescreve o campo 'ano_fabricacao' para usar dropdown
    ano_fabricacao = forms.ChoiceField(
        label='Ano de Fabricação',
        choices=ANOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campos específicos
    rntrc = forms.CharField(
        label='RNTRC',
        required=False,
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000000000000'})
    )
    
    placa = forms.CharField(
        label='Placa',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    tipo_unidade = forms.ChoiceField(
        label='Tipo da Unidade de Veículo',
        choices=Veiculo.TIPO_UNIDADE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    renavam = forms.CharField(
        label='Renavam',
        required=False,
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    chassi = forms.CharField(
        label='Chassi',
        required=False,
        max_length=17,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    cidade = UpperCaseCharField(
        label='Cidade',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Campos de medidas
    largura = forms.DecimalField(
        label='Largura (m)',
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    altura = forms.DecimalField(
        label='Altura (m)',
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    comprimento = forms.DecimalField(
        label='Comprimento (m)',
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    cubagem = forms.DecimalField(
        label='Cubagem (m³)',
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': 'readonly'})
    )
    
    # Campos do proprietário
    proprietario_nome_razao_social = UpperCaseCharField(
        label='Nome/Razão Social do Proprietário',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_cpf_cnpj = forms.CharField(
        label='CPF/CNPJ do Proprietário',
        required=False,
        max_length=18,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00 ou 00.000.000/0000-00'})
    )
    proprietario_rg_ie = UpperCaseCharField(
        label='RG/IE do Proprietário',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_endereco = UpperCaseCharField(
        label='Endereço do Proprietário',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_bairro = UpperCaseCharField(
        label='Bairro do Proprietário',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_numero = forms.CharField(
        label='Número do Proprietário',
        required=False,
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_cep = forms.CharField(
        label='CEP do Proprietário',
        required=False,
        max_length=9,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_telefone = forms.CharField(
        label='Telefone do Proprietário',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    proprietario_placa = forms.CharField(
        label='Placa do Proprietário',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    proprietario_cidade = UpperCaseCharField(
        label='Cidade do Proprietário',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )

    class Meta:
        model = Veiculo
        fields = '__all__'

    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if not placa:
            return placa
        # Remove caracteres especiais para padronização
        placa_limpa = re.sub(r'[^a-zA-Z0-9]', '', placa).upper()
        if len(placa_limpa) != 7:
            raise forms.ValidationError("Placa deve conter 7 caracteres alfanuméricos.")
        return placa_limpa

    def clean_chassi(self):
        chassi = self.cleaned_data.get('chassi')
        if not chassi:
            return chassi
        # Chassi tem 17 caracteres alfanuméricos
        chassi_limpo = re.sub(r'[^a-zA-Z0-9]', '', chassi).upper()
        if len(chassi_limpo) != 17:
            raise forms.ValidationError("Chassi deve conter 17 caracteres alfanuméricos.")
        return chassi_limpo

    def clean_renavam(self):
        renavam = self.cleaned_data.get('renavam')
        if not renavam:
            return renavam
        renavam_numeros = re.sub(r'[^0-9]', '', renavam)
        if len(renavam_numeros) != 11:
            raise forms.ValidationError("RENAVAM deve conter 11 dígitos numéricos.")
        return renavam_numeros
    
    def clean_rntrc(self):
        rntrc = self.cleaned_data.get('rntrc')
        if not rntrc:
            return rntrc
        # Remove caracteres não numéricos (mantém apenas números)
        # Não valida quantidade mínima/máxima de dígitos
        rntrc_numeros = re.sub(r'[^0-9]', '', rntrc)
        return rntrc_numeros
    
    def clean(self):
        """Calcula a cubagem automaticamente"""
        cleaned_data = super().clean()
        
        largura = cleaned_data.get('largura')
        altura = cleaned_data.get('altura')
        comprimento = cleaned_data.get('comprimento')

        # Se todos os campos de medida estão preenchidos, calcula a cubagem
        if largura is not None and altura is not None and comprimento is not None:
            try:
                cubagem_calculada = largura * altura * comprimento
                cleaned_data['cubagem'] = cubagem_calculada
                
                if cubagem_calculada <= 0:
                    self.add_error(None, "A cubagem calculada deve ser um valor positivo.")
            except TypeError:
                self.add_error(None, "Valores de largura, altura e comprimento devem ser números válidos.")
        else:
            cleaned_data['cubagem'] = None

        return cleaned_data


class VeiculoSearchForm(forms.Form):
    """Formulário de pesquisa para veículos"""
    placa = forms.CharField(
        label='Placa',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    chassi = forms.CharField(
        label='Chassi',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do Chassi'})
    )
    proprietario_nome = UpperCaseCharField(
        label='Nome do Proprietário',
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome/Razão Social do Proprietário'})
    )
    tipo_unidade = forms.ChoiceField(
        label='Tipo de Unidade',
        choices=[('', 'Todos')] + Veiculo.TIPO_UNIDADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

