from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
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
    
    # >>> NOVO MÉTODO CLEAN PARA VALIDAR UNICIDADE COMPOSTA E EXIBIR MENSAGEM <<<
    def clean(self):
        cleaned_data = super().clean() # Chama o clean original do ModelForm
        nota = cleaned_data.get('nota')
        cliente = cleaned_data.get('cliente')
        mercadoria = cleaned_data.get('mercadoria')
        quantidade = cleaned_data.get('quantidade')
        peso = cleaned_data.get('peso')

        # Se todos os campos chave estão presentes
        if nota and cliente and mercadoria and quantidade is not None and peso is not None:
            # Queryset para buscar notas que são "iguais" pela sua regra de negócio
            qs = NotaFiscal.objects.filter(
                nota=nota,
                cliente=cliente,
                mercadoria=mercadoria,
                quantidade=quantidade,
                peso=peso
            )
            # Se estamos editando uma nota, excluímos a nota atual da busca por duplicatas
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError(
                    "Já existe uma nota fiscal com o mesmo Número, Cliente, Mercadoria, Quantidade e Peso.",
                    code='duplicate_nota_fiscal'
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
        queryset=Veiculo.objects.all().order_by('placa'),
        label='Veículo Principal (Placa 1)',
        required=False,
        empty_label="--- Selecione o Veículo Principal ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reboque_1 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'), # Filtrar por tipo de unidade
        label='Reboque 1 (Placa 2)',
        required=False,
        empty_label="--- Selecione o Reboque 1 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    reboque_2 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__in=['Reboque', 'Semi-reboque']).order_by('placa'), # Filtrar por tipo de unidade
        label='Reboque 2 (Placa 3)',
        required=False,
        empty_label="--- Selecione o Reboque 2 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

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
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'cnh': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000000000'}),

            'codigo_seguranca': forms.TextInput(attrs={'class': 'form-control'}),
            'vencimento_cnh': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'uf_emissao_cnh': forms.Select(attrs={'class': 'form-control'}), 
            
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}), 
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_consulta': forms.TextInput(attrs={'class': 'form-control'}),
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
    
    # >>> NOVO MÉTODO CLEAN PARA CALCULAR CUBAGEM <<<
    def clean(self):
        cleaned_data = super().clean() # Chama o clean original do ModelForm
        
        largura = cleaned_data.get('largura')
        altura = cleaned_data.get('altura')
        comprimento = cleaned_data.get('comprimento')

        # Se todos os campos de medida estão preenchidos, calcula a cubagem
        if largura is not None and altura is not None and comprimento is not None:
            try:
                cubagem_calculada = largura * altura * comprimento
                # A cubagem não é um campo do formulário, mas um campo do modelo
                # Nós a salvamos no método save() do modelo.
                # Aqui no clean, podemos apenas validar que a cubagem seria positiva, se quiser.
                if cubagem_calculada <= 0:
                    self.add_error(None, "A cubagem calculada deve ser um valor positivo.") # Erro geral
            except TypeError: # Acontece se não forem números válidos
                self.add_error(None, "Valores de largura, altura e comprimento devem ser números válidos.")
        else:
            # Se algum campo estiver vazio, garante que não há cálculo e pode adicionar um erro
            # se quiser que sejam obrigatórios para o cálculo.
            # No nosso save() do modelo, já tratamos o caso de ser None.
            pass

        return cleaned_data
    
# --------------------------------------------------------------------------------------
# Novo formulário para Romaneios
# --------------------------------------------------------------------------------------
class RomaneioViagemForm(forms.ModelForm):
    notas_fiscais = forms.ModelMultipleChoiceField(
        queryset=NotaFiscal.objects.none(), # Começa vazio. O JS ou a edição preencherá.
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Notas Fiscais Associadas"
    )

    data_romaneio = forms.DateField(
        label='Data do Romaneio',
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
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

    # Sobrescreve o campo 'veiculo' para apontar para Veiculo (unidade)
    veiculo = forms.ModelChoiceField(
        queryset=Veiculo.objects.all().order_by('placa'),
        label='Unidade de Veículo', # Ajustado o label
        required=True,
        empty_label="--- Selecione uma unidade ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is None and not self.initial.get('data_romaneio'):
            self.fields['data_romaneio'].initial = date.today()
        
        # Querysets para ModelChoiceFields
        self.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        self.fields['veiculo'].queryset = Veiculo.objects.all().order_by('placa')

        # Lógica para edição (preencher notas_fiscais e data_romaneio)
        if self.instance and self.instance.pk:
            if self.instance.data_emissao:
                 self.fields['data_romaneio'].initial = self.instance.data_emissao.date()

            if self.instance.cliente:
                # Filtrar notas para edição: Notas do cliente OU já vinculadas a este romaneio E em status 'Depósito'
                self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=self.instance.cliente
                ).filter(
                    Q(romaneios_vinculados=self.instance) | Q(status='Depósito')
                ).order_by('nota')
                self.fields['notas_fiscais'].initial = self.instance.notas_fiscais.all()
        
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
        fields = ['data_romaneio', 'cliente', 'notas_fiscais', 'motorista', 'veiculo']
        
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

# --------------------------------------------------------------------------------------
# Formulário de Pesquisa para Mercadorias no Depósito
# --------------------------------------------------------------------------------------
class MercadoriaDepositoSearchForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        required=True,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mercadoria = forms.CharField(
        label='Mercadoria',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da mercadoria'})
    )
    fornecedor = forms.CharField(
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