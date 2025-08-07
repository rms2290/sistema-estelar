from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import re
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, Usuario, TabelaSeguro
from validate_docbr import CNPJ, CPF

# Custom form field that automatically converts text to uppercase
class UpperCaseCharField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            return value.upper()
        return value

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
    # Campo número da nota
    nota = UpperCaseCharField(
        label='Número da Nota',
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da Nota Fiscal'})
    )
    
    # Campo cliente
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campo data
    data = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True,
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']
    )
    
    # Campo fornecedor
    fornecedor = UpperCaseCharField(
        label='Fornecedor',
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Fornecedor'})
    )
    
    # Campo mercadoria
    mercadoria = UpperCaseCharField(
        label='Mercadoria',
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Mercadoria'})
    )

    class Meta:
        model = NotaFiscal
        exclude = ['status', 'romaneios']
        widgets = {
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk is None and not self.initial.get('data'):
            # Formatar a data no formato ISO para input HTML5 date
            data_atual = datetime.now().date()
            self.fields['data'].initial = data_atual.strftime('%Y-%m-%d')

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            return int(peso)
        return peso
    
    # >>> NOVO MÉTODO CLEAN PARA VALIDAR UNICIDADE COMPOSTA E EXIBIR MENSAGEM <<<
    def clean(self):
        cleaned_data = super().clean() # Chama o clean original do ModelForm
        nota = cleaned_data.get('nota')
        cliente = cleaned_data.get('cliente')
        valor = cleaned_data.get('valor')
        
        # Verifica se todos os campos necessários estão presentes
        if nota and cliente and valor is not None:
            # Verifica se já existe uma nota com o mesmo cliente, número da nota e valor
            existing_nota = NotaFiscal.objects.filter(
                nota=nota,
                cliente=cliente,
                valor=valor
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_nota.exists():
                raise ValidationError(
                    f'Já existe uma nota fiscal com o número {nota} para o cliente {cliente} '
                    f'com o valor R$ {valor:.2f}. Não é permitido duplicar notas fiscais.'
                )
        
        return cleaned_data

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
    
    # Sobrescreve campos para adicionar placeholders e estilos consistentes
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
        cnpj = self.cleaned_data.get('cnpj')
        
        # Se o campo não for obrigatório e estiver vazio, retorne imediatamente
        if not cnpj:
            return cnpj
            
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
    # >>> SOBRESCRITA DOS CAMPOS ESTADO E UF_EMISSAO_CNH <<<
    estado = forms.ChoiceField(
        label='Estado',
        choices=[('', '---')] + ESTADOS_CHOICES, # Adiciona opção '---' e as escolhas de estado
        required=False, # Mantém como opcional
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    uf_emissao_cnh = forms.ChoiceField(
        label='UF de Emissão da CNH',
        choices=[('', '---')] + ESTADOS_CHOICES, # Adiciona opção '---' e as escolhas de estado
        required=False, # Mantém como opcional
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # >>> NOVOS CAMPOS NO FORMULARIO <<<
    tipo_composicao_motorista = forms.ChoiceField(
        label='Tipo de Composição que Dirige',
        choices=Motorista.TIPO_COMPOSICAO_MOTORISTA_CHOICES, # Usar as escolhas do modelo
        required=True, # É obrigatório para o motorista definir o tipo
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_tipo_composicao_motorista_select'}) # ID para JS
    )
    veiculo_principal = forms.ModelChoiceField(
        queryset=Veiculo.objects.all().order_by('placa'),  # Inicialmente todos os veículos
        label='Veículo Principal (Placa 1)',
        required=False,
        empty_label="--- Selecione o Veículo Principal ---",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_veiculo_principal_select'})
    )
    reboque_1 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'), # Filtrar por tipo de unidade
        label='Reboque 1 (Placa 2)',
        required=False,
        empty_label="--- Selecione o Reboque 1 ---",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_reboque_1_select'})
    )
    reboque_2 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'), # Filtrar por tipo de unidade
        label='Reboque 2 (Placa 3)',
        required=False,
        empty_label="--- Selecione o Reboque 2 ---",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_reboque_2_select'})
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir os filtros de veículos baseados no tipo de composição
        self.fields['veiculo_principal'].queryset = Veiculo.objects.all().order_by('placa')
        
        # Se temos uma instância (edição), filtrar baseado no tipo de composição atual
        if self.instance and self.instance.pk:
            tipo_composicao = self.instance.tipo_composicao_motorista
            if tipo_composicao in ['Carro']:
                self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade='Carro').order_by('placa')
            elif tipo_composicao in ['Van']:
                self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade='Van').order_by('placa')
            elif tipo_composicao in ['Caminhão']:
                self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade='Caminhão').order_by('placa')
            elif tipo_composicao in ['Carreta', 'Bitrem']:
                self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade='Cavalo').order_by('placa')

    class Meta:
        model = Motorista
        # AJUSTADO: Adicionado os novos campos
        fields = [
            'nome', 'cpf', 'cnh',
            'codigo_seguranca', 'vencimento_cnh', 'uf_emissao_cnh',
            'telefone',
            'endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep',
            'data_nascimento',
            'numero_consulta', # Manter por enquanto
            'tipo_composicao_motorista', # <<< NOVO CAMPO
            'veiculo_principal', # <<< NOVO CAMPO
            'reboque_1', # <<< NOVO CAMPO
            'reboque_2', # <<< NOVO CAMPO
        ]
        widgets = {
            'vencimento_cnh': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'uf_emissao_cnh': forms.Select(attrs={'class': 'form-control'}), 
            'estado': forms.Select(attrs={'class': 'form-control'}), 
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # veiculo_principal, reboque_1, reboque_2 já tem widgets definidos acima
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
        cep = self.cleaned_data.get('cep')
        
        # Se o campo não for obrigatório e estiver vazio, retorne imediatamente
        if not cep:
            return cep
            
        cep_numeros = re.sub(r'[^0-9]', '', cep)
        if len(cep_numeros) != 8:
            raise forms.ValidationError("CEP deve conter 8 dígitos numéricos.")
        return cep_numeros

    def clean(self):
        """
        Validação personalizada para garantir que os veículos sejam diferentes
        """
        cleaned_data = super().clean()
        
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
        
        return cleaned_data

# --------------------------------------------------------------------------------------
# Novo formulário para Veículos
# --------------------------------------------------------------------------------------
class VeiculoForm(forms.ModelForm):
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
    
    # Campo 'modelo' mantido como texto livre para maior flexibilidade
    modelo = UpperCaseCharField(
        label='Modelo',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Lista de anos de fabricação (últimos 30 anos + próximos 5 anos)
    ANOS_CHOICES = [('', '---')] + [(str(ano), str(ano)) for ano in range(2029, 1999, -1)]
    
    # Sobrescreve o campo 'ano_fabricacao' para usar dropdown
    ano_fabricacao = forms.ChoiceField(
        label='Ano de Fabricação',
        choices=ANOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Campo RNTRC com placeholder para formatação
    rntrc = forms.CharField(
        label='RNTRC',
        required=False,
        max_length=12,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000000000000'})
    )
    
    # Sobrescreve o campo 'placa' para padronizar
    placa = forms.CharField(
        label='Placa',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Sobrescreve o campo 'tipo_unidade' para padronizar
    tipo_unidade = forms.ChoiceField(
        label='Tipo da Unidade de Veículo',
        choices=Veiculo.TIPO_UNIDADE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Sobrescreve o campo 'renavam' para padronizar
    renavam = forms.CharField(
        label='Renavam',
        required=False,
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Sobrescreve o campo 'chassi' para padronizar
    chassi = forms.CharField(
        label='Chassi',
        required=False,
        max_length=17,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Sobrescreve o campo 'cidade' para padronizar
    cidade = UpperCaseCharField(
        label='Cidade',
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    
    # Campos de medidas com widgets específicos
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
    
    # Sobrescreve os campos do proprietário para padronizar estilo e placeholder
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
    
    def clean_rntrc(self):
        rntrc = self.cleaned_data.get('rntrc')
        if not rntrc:
            return rntrc
        
        # Remove caracteres não numéricos
        rntrc_numeros = re.sub(r'[^0-9]', '', rntrc)
        
        # Verifica se tem 12 dígitos
        if len(rntrc_numeros) != 12:
            raise forms.ValidationError("RNTRC deve conter 12 dígitos numéricos.")
        
        return rntrc_numeros
    
    # >>> MÉTODO CLEAN PARA CALCULAR CUBAGEM <<<
    def clean(self):
        cleaned_data = super().clean() # Chama o clean original do ModelForm
        
        largura = cleaned_data.get('largura')
        altura = cleaned_data.get('altura')
        comprimento = cleaned_data.get('comprimento')

        # Se todos os campos de medida estão preenchidos, calcula a cubagem
        if largura is not None and altura is not None and comprimento is not None:
            try:
                cubagem_calculada = largura * altura * comprimento
                # Atualiza o campo cubagem no cleaned_data
                cleaned_data['cubagem'] = cubagem_calculada
                
                # Validação: cubagem deve ser positiva
                if cubagem_calculada <= 0:
                    self.add_error(None, "A cubagem calculada deve ser um valor positivo.")
            except TypeError: # Acontece se não forem números válidos
                self.add_error(None, "Valores de largura, altura e comprimento devem ser números válidos.")
        else:
            # Se algum campo estiver vazio, limpa a cubagem
            cleaned_data['cubagem'] = None

        return cleaned_data
    
# --------------------------------------------------------------------------------------
# Novo formulário para Romaneios
# --------------------------------------------------------------------------------------
class RomaneioViagemForm(forms.ModelForm):
    notas_fiscais = forms.ModelMultipleChoiceField(
        queryset=NotaFiscal.objects.none(), # Começa vazio. O JS ou a edição preencherá.
        widget=forms.CheckboxSelectMultiple,
        required=True,  # RESTAURADO COMO OBRIGATÓRIO
        label="Notas Fiscais Associadas"
    )

    data_romaneio = forms.DateField(
        label='Data do Romaneio',
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']
    )

    # Sobrescreve o campo 'cliente' para filtrar por status
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        required=True,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Sobrescreve o campo 'motorista'
    motorista = forms.ModelChoiceField(
        queryset=Motorista.objects.all().order_by('nome'),
        label='Motorista',
        required=True,
        empty_label="--- Selecione um motorista ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Composição veicular
    veiculo_principal = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Carro', 'Van', 'Caminhão', 'Cavalo']).order_by('placa'),
        label='Veículo Principal',
        required=True,
        empty_label="--- Selecione o veículo principal ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reboque_1 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'),
        label='Reboque 1 (Opcional)',
        required=False,
        empty_label="--- Selecione o reboque 1 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reboque_2 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'),
        label='Reboque 2 (Opcional)',
        required=False,
        empty_label="--- Selecione o reboque 2 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is None and not self.initial.get('data_romaneio'):
            # Formatar a data no formato ISO para input HTML5 date
            data_atual = datetime.now().date()
            self.fields['data_romaneio'].initial = data_atual.strftime('%Y-%m-%d')
        
        # Querysets para ModelChoiceFields
        self.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade__in=['Carro', 'Van', 'Caminhão', 'Cavalo']).order_by('placa')
        self.fields['reboque_1'].queryset = Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa')
        self.fields['reboque_2'].queryset = Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa')

        # Lógica para edição (preencher notas_fiscais e data_romaneio)
        if self.instance and self.instance.pk:
            if self.instance.data_emissao:
                 self.fields['data_romaneio'].initial = self.instance.data_emissao.date().strftime('%Y-%m-%d')

            if self.instance.cliente:
                # Filtrar notas para edição: Notas do cliente OU já vinculadas a este romaneio E em status 'Depósito'
                self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=self.instance.cliente
                ).filter(
                    Q(romaneios_vinculados=self.instance) | Q(status='Depósito')
                ).order_by('nota')
                self.fields['notas_fiscais'].initial = self.instance.notas_fiscais.all()
        
        # CORREÇÃO: Configurar queryset das notas fiscais baseado no cliente dos dados
        if self.data and 'cliente' in self.data:
            try:
                cliente_id = self.data.get('cliente')
                if cliente_id:
                    cliente_obj = Cliente.objects.get(pk=cliente_id)
                    self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                        cliente=cliente_obj, status='Depósito' 
                    ).order_by('nota')
            except (Cliente.DoesNotExist, ValueError):
                pass
        
        # Adicionar atributos HTML para estilização
        for field_name, field in self.fields.items():
            if field_name != 'notas_fiscais': # CheckboxSelectMultiple é estilizado diferente
                # Adicionar classes a campos que não são ModelChoiceField sobrescritos ou já tem widget
                if not isinstance(field.widget, (forms.Select, forms.DateInput)):
                    field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'cliente': # Adicionar onchange para o cliente
                 field.widget.attrs.update({'onchange': 'loadNotasFiscais(this.value);'})

    class Meta:
        model = RomaneioViagem
        # 'codigo' e 'status' são controlados pela view e não aparecem no formulário
        fields = ['data_romaneio', 'cliente', 'notas_fiscais', 'motorista', 'veiculo_principal', 'reboque_1', 'reboque_2']
    
    def clean_notas_fiscais(self):
        """Validação customizada para o campo notas_fiscais"""
        notas_fiscais = self.cleaned_data.get('notas_fiscais')
        cliente = self.cleaned_data.get('cliente')
        
        if not notas_fiscais:
            raise forms.ValidationError('Selecione pelo menos uma nota fiscal.')
        
        # Verificar se todas as notas fiscais pertencem ao cliente selecionado
        if cliente:
            notas_invalidas = notas_fiscais.exclude(cliente=cliente)
            if notas_invalidas.exists():
                raise forms.ValidationError('Todas as notas fiscais devem pertencer ao cliente selecionado.')
        
        return notas_fiscais
        
# --------------------------------------------------------------------------------------
# NOVO: Formulário para Histórico de Consulta
# --------------------------------------------------------------------------------------
class HistoricoConsultaForm(forms.ModelForm):
    # Sobrescrever campos de texto para uppercase
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
        # O motorista será preenchido pela view, então não o colocamos aqui
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

# --------------------------------------------------------------------------------------
# Formulários de Pesquisa de notas
# --------------------------------------------------------------------------------------
class NotaFiscalSearchForm(forms.Form):
    nota = UpperCaseCharField(
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

class MotoristaSearchForm(forms.Form):
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'})
    )

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Clientes
# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Motoristas
# --------------------------------------------------------------------------------------

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Veículos
# --------------------------------------------------------------------------------------
class VeiculoSearchForm(forms.Form):
    # Campo para pesquisar por Placa
    placa = forms.CharField(
        label='Placa',
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '---'})
    )
    # Campo para pesquisar por Chassi
    chassi = forms.CharField(
        label='Chassi',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número do Chassi'})
    )
    # Campo para pesquisar por Nome do Proprietário
    proprietario_nome = UpperCaseCharField(
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
# Formulário de Pesquisa para Romaneios
# --------------------------------------------------------------------------------------
class RomaneioSearchForm(forms.Form):
    codigo = UpperCaseCharField(
        label='Código do Romaneio',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ROM-AAAA-MM-NNNN'})
    )
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        required=False,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    motorista = forms.ModelChoiceField(
        queryset=Motorista.objects.all().order_by('nome'),
        label='Motorista',
        required=False,
        empty_label="--- Selecione um motorista ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    veiculo_principal = forms.ModelChoiceField(
        queryset=Veiculo.objects.all().order_by('placa'),
        label='Veículo Principal',
        required=False,
        empty_label="--- Selecione um veículo ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    status = forms.ChoiceField(
        label='Status',
        choices=[('', 'Todos')] + RomaneioViagem.STATUS_ROMANEIO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data_inicio = forms.DateField(
        label='Data de Emissão (Início)',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_fim = forms.DateField(
        label='Data de Emissão (Fim)',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

# --------------------------------------------------------------------------------------
# NOVO: Formulário para Histórico de Consulta
# --------------------------------------------------------------------------------------
class HistoricoConsultaForm(forms.ModelForm):
    class Meta:
        model = HistoricoConsulta
        # O motorista será preenchido pela view, então não o colocamos aqui
        fields = ['numero_consulta', 'data_consulta', 'gerenciadora', 'status_consulta', 'observacoes']
        widgets = {
            'numero_consulta': forms.TextInput(attrs={'class': 'form-control'}),
            'data_consulta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gerenciadora': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da gerenciadora'}),
            'status_consulta': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche a data da consulta com a data atual por padrão
        if self.instance.pk is None and not self.initial.get('data_consulta'):
            self.fields['data_consulta'].initial = datetime.now().date()

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Mercadorias no Depósito
# --------------------------------------------------------------------------------------
class MercadoriaDepositoSearchForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        required=False,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mercadoria = UpperCaseCharField(
        label='Mercadoria',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da mercadoria'})
    )
    fornecedor = UpperCaseCharField(
        label='Fornecedor',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do fornecedor'})
    )
    data_inicio = forms.DateField(
        label='Data de Emissão (Início)',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_fim = forms.DateField(
        label='Data de Emissão (Fim)',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

# --------------------------------------------------------------------------------------
# Formulários de Autenticação
# --------------------------------------------------------------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(
        label='Nome de Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu nome de usuário'
        })
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )

class CadastroUsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha'
        })
    )
    
    # Sobrescrever campos de texto para uppercase
    first_name = UpperCaseCharField(
        label='Nome',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    
    last_name = UpperCaseCharField(
        label='Sobrenome',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'cliente', 'telefone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
            'tipo_usuario': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
        }
    
    # Sobrescrever o campo cliente para ter controle total
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente Vinculado',
        required=False,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Não é mais necessário configurar o campo cliente aqui, pois já foi feito na definição do campo
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("As senhas não coincidem.")
        return password2
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        # Se é uma instância existente (edição) e nenhuma senha foi fornecida, não validar
        if self.instance and self.instance.pk and not password1 and not password2:
            return cleaned_data
        
        # Se é um novo usuário ou senhas foram fornecidas, validar
        if not password1:
            raise forms.ValidationError("A senha é obrigatória para novos usuários.")
        if not password2:
            raise forms.ValidationError("A confirmação de senha é obrigatória para novos usuários.")
        
        # Validação da relação entre tipo de usuário e cliente
        tipo_usuario = cleaned_data.get('tipo_usuario')
        cliente = cleaned_data.get('cliente')
        
        if tipo_usuario == 'cliente' and not cliente:
            raise forms.ValidationError("Usuários do tipo 'Cliente' devem estar vinculados a um cliente.")
        
        if tipo_usuario != 'cliente' and cliente:
            raise forms.ValidationError("Apenas usuários do tipo 'Cliente' podem estar vinculados a um cliente.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Só definir a senha se foi fornecida
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        
        if commit:
            user.save()
        return user

class AlterarSenhaForm(forms.Form):
    senha_atual = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha atual'
        })
    )
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua nova senha'
        })
    )
    confirmar_nova_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua nova senha'
        })
    )
    
    def clean_confirmar_nova_senha(self):
        senha1 = self.cleaned_data.get('nova_senha')
        senha2 = self.cleaned_data.get('confirmar_nova_senha')
        
        if senha1 and senha2 and senha1 != senha2:
            raise ValidationError('As senhas não coincidem.')
        
        return senha2

# --------------------------------------------------------------------------------------
# Formulário para Tabela de Seguros
# --------------------------------------------------------------------------------------
class TabelaSeguroForm(forms.ModelForm):
    percentual_seguro = forms.DecimalField(
        label='Percentual de Seguro (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0.00,
        max_value=100.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.00',
            'max': '100.00',
            'placeholder': '0.00'
        })
    )
    
    class Meta:
        model = TabelaSeguro
        fields = ['estado', 'percentual_seguro']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_percentual_seguro(self):
        percentual = self.cleaned_data.get('percentual_seguro')
        if percentual is not None:
            if percentual < 0:
                raise ValidationError('O percentual não pode ser negativo.')
            if percentual > 100:
                raise ValidationError('O percentual não pode ser maior que 100%.')
        return percentual