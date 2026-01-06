"""
Formulários relacionados a Fechamento de Frete
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from ..models import FechamentoFrete, ItemFechamentoFrete, DetalheItemFechamento, RomaneioViagem, Cliente, Motorista
from .base import UpperCaseCharField


class FechamentoFreteForm(forms.ModelForm):
    """Formulário para criar e editar fechamento de frete"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estiver editando uma instância existente, inicializar cubagem_total com o valor do cubagem_bau_total
        if self.instance and self.instance.pk and self.instance.cubagem_bau_total:
            self.fields['cubagem_total'].initial = self.instance.cubagem_bau_total
    
    # Campo para seleção múltipla de romaneios
    romaneios_selecionados = forms.ModelMultipleChoiceField(
        queryset=RomaneioViagem.objects.filter(status='Emitido').order_by('-data_emissao'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        label="Romaneios",
        help_text="Selecione os romaneios para este fechamento"
    )
    
    motorista = forms.ModelChoiceField(
        queryset=Motorista.objects.all().order_by('nome'),
        required=True,
        empty_label="--- Selecione um motorista ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Motorista"
    )
    
    data = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Data do Fechamento"
    )
    
    frete_total = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Frete Total (R$)"
    )
    
    ctr_total = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="CTR Total (R$)"
    )
    
    carregamento_total = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Carregamento Total (R$)"
    )
    
    # Campos de cubagem individuais (ocultos, mantidos para compatibilidade)
    cubagem_bau_a = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.HiddenInput(),
        label="Cubagem Baú A (m³)"
    )
    
    cubagem_bau_b = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.HiddenInput(),
        label="Cubagem Baú B (m³)"
    )
    
    cubagem_bau_c = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.HiddenInput(),
        label="Cubagem Baú C (m³)"
    )
    
    # Campo único para cubagem total (não está no modelo, será processado no clean)
    cubagem_total = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_cubagem_total'}),
        label="Cubagem Total (m³)",
        help_text="Cubagem total do baú"
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Observações"
    )
    
    class Meta:
        model = FechamentoFrete
        fields = [
            'motorista', 'data', 'frete_total', 'ctr_total', 'carregamento_total',
            'cubagem_bau_a', 'cubagem_bau_b', 'cubagem_bau_c', 'observacoes'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Se cubagem_total foi preenchida, usar ela para calcular o total
        cubagem_total = cleaned_data.get('cubagem_total')
        if cubagem_total:
            # Preencher o cubagem_bau_total diretamente
            # Os campos A, B, C ficam vazios (null)
            cleaned_data['cubagem_bau_a'] = None
            cleaned_data['cubagem_bau_b'] = None
            cleaned_data['cubagem_bau_c'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sobrescreve save para processar cubagem_total"""
        instance = super().save(commit=False)
        
        # Se cubagem_total foi preenchida, usar ela diretamente
        cubagem_total = self.cleaned_data.get('cubagem_total')
        if cubagem_total:
            instance.cubagem_bau_total = cubagem_total
            instance.cubagem_bau_a = None
            instance.cubagem_bau_b = None
            instance.cubagem_bau_c = None
        else:
            # Se não, calcular normalmente (A + B + C)
            instance.calcular_cubagem_total()
        
        if commit:
            instance.save()
        return instance


class ItemFechamentoFreteForm(forms.ModelForm):
    """Formulário para criar e editar item de fechamento"""
    
    cliente_consolidado = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        required=True,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cliente Consolidado"
    )
    
    peso = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Peso Total (kg)"
    )
    
    cubagem = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Cubagem (m³)"
    )
    
    valor_mercadoria = forms.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Valor Total (R$)"
    )
    
    percentual_ajustado = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        label="Percentual Ajustado Manual (R$)"
    )
    
    usar_ajuste_manual = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Usar Ajuste Manual"
    )
    
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label="Observações"
    )
    
    class Meta:
        model = ItemFechamentoFrete
        fields = [
            'cliente_consolidado', 'peso', 'cubagem', 'valor_mercadoria',
            'percentual_ajustado', 'usar_ajuste_manual', 'observacoes'
        ]

