"""
Forms do Financeiro V2.

Ondas 2-5: lançamento manual, despesa, xerox, baixa, pagamento, doc. avulsa,
descarga avulsa, edição de lançamento.
"""
from decimal import Decimal

from django import forms
from django.forms import formset_factory

from financeiro.models import FuncionarioFluxoCaixa
from notas.models import CobrancaCTEAvulsa
from .models import Bolso, Carteira, Lancamento


CATEGORIAS_DESPESA = [
    ('Material de escritório', 'Material de escritório'),
    ('Limpeza', 'Limpeza'),
    ('Manutenção', 'Manutenção (empilhadeira, equipamentos)'),
    ('Combustível', 'Combustível'),
    ('Vale transporte', 'Vale transporte'),
    ('Serviços terceirizados', 'Serviços terceirizados'),
    ('Outros', 'Outros'),
]


class LancamentoManualForm(forms.ModelForm):
    """Lançamento manual: usuário escolhe tudo."""

    class Meta:
        model = Lancamento
        fields = [
            'data',
            'carteira',
            'bolso',
            'tipo',
            'valor',
            'descricao',
            'categoria',
            'cliente',
            'funcionario',
        ]
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'carteira': forms.Select(attrs={'class': 'form-select'}),
            'bolso': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Recebimento avulso, ajuste de saldo, etc.'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['carteira'].queryset = Carteira.objects.filter(ativa=True)
        self.fields['bolso'].queryset = Bolso.objects.filter(ativo=True)
        self.fields['cliente'].required = False
        self.fields['funcionario'].required = False
        self.fields['categoria'].required = False


class DespesaForm(forms.Form):
    """Despesa avulsa = Lançamento de Saída no bolso Operacional (default)."""

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data',
    )
    categoria = forms.ChoiceField(
        choices=CATEGORIAS_DESPESA,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Categoria',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira (de onde sai)',
    )
    bolso = forms.ModelChoiceField(
        queryset=Bolso.objects.filter(ativo=True, eh_terceiro=False),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Bolso',
        help_text='Em geral é o bolso "Operacional".',
    )
    valor = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Valor (R$)',
    )
    descricao = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Papel A4 - Kalunga'}),
        label='Descrição',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            operacional = Bolso.objects.get(codigo='OPERACIONAL')
            self.fields['bolso'].initial = operacional.pk
        except Bolso.DoesNotExist:
            pass


class XeroxForm(forms.Form):
    """Xerox: quantidade x valor unitário (default R$ 2,00) = entrada de Estelar em Dinheiro."""

    quantidade = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label='Quantidade de impressões',
    )
    valor_unitario = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        initial=Decimal('2.00'),
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Valor unitário (R$)',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira (onde entra)',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass

    @property
    def valor_total(self):
        if self.is_valid():
            return self.cleaned_data['quantidade'] * self.cleaned_data['valor_unitario']
        return Decimal('0.00')


class BaixaCobrancaForm(forms.Form):
    """Formulário de baixa de cobrança (carregamento ou CTE avulsa)."""

    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Como o cliente pagou (carteira que recebe)',
    )
    data_pagamento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data do pagamento',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass


class PagamentoSaidaForm(forms.Form):
    """Formulário de pagamento (chapa ou terceiro doc): carteira de onde sai + data."""

    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira de onde sai o dinheiro',
    )
    data_pagamento = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data do pagamento',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass


# ============================================================================
# Onda 5
# ============================================================================

class CobrancaCTEAvulsaForm(forms.ModelForm):
    """Form para criar uma nova CobrancaCTEAvulsa (doc. avulsa pendente)."""

    class Meta:
        model = CobrancaCTEAvulsa
        fields = ['nome', 'valor_cte_manifesto', 'valor_cte_terceiro', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex.: João Mecânico - 03 CTE',
            }),
            'valor_cte_manifesto': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0',
            }),
            'valor_cte_terceiro': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0',
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Opcional',
            }),
        }
        labels = {
            'nome': 'Nome / Descrição',
            'valor_cte_manifesto': 'Valor cobrado do cliente (R$)',
            'valor_cte_terceiro': 'Valor a pagar ao terceiro (R$)',
            'observacoes': 'Observações',
        }

    def clean(self):
        cd = super().clean()
        cliente = cd.get('valor_cte_manifesto') or Decimal('0.00')
        terceiro = cd.get('valor_cte_terceiro') or Decimal('0.00')
        if terceiro > cliente:
            raise forms.ValidationError(
                'Valor para o terceiro não pode ser maior que o cobrado do cliente.'
            )
        return cd


class DescargaAvulsaForm(forms.Form):
    """Cabeçalho da Descarga Avulsa: data, descrição, valor cobrado, carteira."""

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data',
    )
    descricao = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: Descarga 4 toneladas - Fornecedor X',
        }),
        label='Descrição',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira que recebe',
    )
    valor_cobrado = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.01',
        }),
        label='Valor cobrado (R$)',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass


class ChapaDescargaForm(forms.Form):
    """Linha do formset: chapa que descarregou + valor que vai receber."""

    chapa = forms.ModelChoiceField(
        queryset=FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome'),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm chapa-select'}),
        required=False,
        label='Chapa',
    )
    valor = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm chapa-valor',
            'step': '0.01',
            'placeholder': '0,00',
        }),
        required=False,
        label='Valor',
    )


ChapaDescargaFormSet = formset_factory(
    ChapaDescargaForm,
    extra=3,
    can_delete=False,
)


# ============================================================================
# Onda 6 - Distribuir Gerentes + Fundo Gás
# ============================================================================

class DistribuicaoGerentesForm(forms.Form):
    """Cabeçalho: data + carteira que sai."""

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira de onde sai',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass


class LinhaGerenteForm(forms.Form):
    nome = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm gerente-nome',
            'placeholder': 'Nome do gerente',
        }),
        label='Gerente',
    )
    valor = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm gerente-valor',
            'step': '0.01',
            'placeholder': '0,00',
        }),
        label='Valor',
    )


GerentesFormSet = formset_factory(
    LinhaGerenteForm,
    extra=2,
    can_delete=False,
)


class FundoGasForm(forms.Form):
    """Movimento de entrada ou saída no Fundo Gás (chapas)."""

    TIPO_CHOICES = [
        ('Entrada', 'Entrada (chapas depositam)'),
        ('Saida', 'Saída (chapas retiram)'),
    ]

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data',
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo',
    )
    valor = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Valor (R$)',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Carteira',
        help_text='Em geral o dinheiro do Fundo Gás fica em espécie (Dinheiro).',
    )
    descricao = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: Vaquinha do mês / Compra do botijão',
        }),
        label='Descrição',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            dinheiro = Carteira.objects.get(codigo='DINHEIRO')
            self.fields['carteira'].initial = dinheiro.pk
        except Carteira.DoesNotExist:
            pass


# ============================================================================
# Onda 7 - Filtros de Relatórios
# ============================================================================

class HistoricoFiltroForm(forms.Form):
    """Filtros para a tela de histórico de lançamentos."""

    TIPO_CHOICES = [('', 'Todos'), ('Entrada', 'Entrada'), ('Saida', 'Saída')]

    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='De',
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='Até',
    )
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Tipo',
    )
    carteira = forms.ModelChoiceField(
        queryset=Carteira.objects.filter(ativa=True),
        required=False,
        empty_label='Todas',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Carteira',
    )
    bolso = forms.ModelChoiceField(
        queryset=Bolso.objects.filter(ativo=True),
        required=False,
        empty_label='Todos',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
        label='Bolso',
    )
    categoria = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Contém...',
        }),
        label='Categoria',
    )
    busca = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Descrição contém...',
        }),
        label='Descrição',
    )


class PeriodoForm(forms.Form):
    """Form simples de período (data_inicio + data_fim) para DRE."""

    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='De',
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='Até',
    )


# ============================================================================
# Onda 8 - Acerto Diário V2
# ============================================================================

class AcertoDataForm(forms.Form):
    """Escolhe a data do acerto a abrir (hoje ou retroativa)."""

    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data do acerto',
    )


class AcertoFiltroForm(forms.Form):
    """Filtros da lista de acertos V2."""

    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='De',
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        label='Até',
    )
