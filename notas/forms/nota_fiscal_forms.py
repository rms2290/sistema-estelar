"""
Formulários relacionados a Notas Fiscais
"""
from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime
from ..models import NotaFiscal, Cliente
from .base import UpperCaseCharField


class NotaFiscalForm(forms.ModelForm):
    """Formulário para criar/editar notas fiscais"""
    nota = UpperCaseCharField(
        label='Número da Nota',
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da Nota Fiscal'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente',
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    data = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'tabindex': '-1'}),
        required=True,
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y']
    )
    
    fornecedor = UpperCaseCharField(
        label='Fornecedor',
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Fornecedor'})
    )
    
    mercadoria = UpperCaseCharField(
        label='Mercadoria',
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Mercadoria'})
    )
    
    local = forms.ChoiceField(
        label='Local',
        choices=[('', '--- Selecione o galpão ---')] + NotaFiscal.LOCAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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
            data_atual = datetime.now().date()
            self.fields['data'].initial = data_atual.strftime('%Y-%m-%d')

    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso is not None:
            return int(peso)
        return peso
    
    def clean(self):
        cleaned_data = super().clean()
        nota = cleaned_data.get('nota')
        cliente = cleaned_data.get('cliente')
        valor = cleaned_data.get('valor')
        
        if nota and cliente and valor is not None:
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


class NotaFiscalSearchForm(forms.Form):
    """Formulário de busca de notas fiscais"""
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
    local = forms.ChoiceField(
        label='Local',
        choices=[('', 'Todos os galpões')] + NotaFiscal.LOCAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class MercadoriaDepositoSearchForm(forms.Form):
    """Formulário de busca de mercadorias em depósito"""
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
    fornecedor = UpperCaseCharField(
        label='Fornecedor',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Fornecedor'})
    )
    mercadoria = UpperCaseCharField(
        label='Mercadoria',
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Mercadoria'})
    )
    local = forms.ChoiceField(
        label='Local/Galpão',
        required=False,
        choices=[('', '--- Todos os galpões ---')] + NotaFiscal.LOCAL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


