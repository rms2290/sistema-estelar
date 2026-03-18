"""
Formulários administrativos
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from ..models import TabelaSeguro, CobrancaCarregamento, Cliente, RomaneioViagem
from financeiro.models import SetorBancario
from .base import UpperCaseCharField


class TabelaSeguroForm(forms.ModelForm):
    """Formulário para tabela de seguros por estado"""
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


class CobrancaCarregamentoForm(forms.ModelForm):
    """Formulário para criar e editar cobranças de carregamento"""
    
    class Meta:
        model = CobrancaCarregamento
        fields = [
            'cliente',
            'romaneios',
            'tipo_cliente',
            'cubagem',
            'valor_cubagem',
            'valor_carregamento',
            'valor_distribuicao_trabalhadores',
            'valor_cte_manifesto',
            'data_vencimento',
            'observacoes',
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'romaneios': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'valor_carregamento': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'required': True
            }),
            'valor_distribuicao_trabalhadores': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (opcional)',
            }),
            'valor_cte_manifesto': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (opcional)',
            }),
            'data_vencimento': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre esta cobrança (opcional)'
            }),
            'tipo_cliente': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'cubagem': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'valor_cubagem': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
        }
        labels = {
            'cliente': 'Cliente',
            'romaneios': 'Romaneios',
            'tipo_cliente': 'Tipo de Cliente',
            'cubagem': 'Cubagem (m³)',
            'valor_cubagem': 'Valor da Cubagem (R$/m³)',
            'valor_carregamento': 'Valor repassado ao cliente (R$)',
            'valor_distribuicao_trabalhadores': 'Valor para distribuição trabalhadores (R$)',
            'valor_cte_manifesto': 'Valor CTE/Manifesto (R$)',
            'data_vencimento': 'Data de Vencimento',
            'observacoes': 'Observações',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas clientes ativos
        self.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')
        
        # Tornar campo valor_cte_manifesto opcional
        self.fields['valor_cte_manifesto'].required = False
        # Valor distribuição trabalhadores: opcional; ajuda para acerto diário
        self.fields['valor_distribuicao_trabalhadores'].required = False
        self.fields['valor_distribuicao_trabalhadores'].help_text = (
            'Valor que entra no acerto diário para divisão entre trabalhadores. '
            'A diferença (valor ao cliente − este valor) é a margem Estelar.'
        )
        
        # Determinar o cliente para filtrar romaneios
        cliente_para_filtrar = None
        
        # Se for edição, usar o cliente da instância
        if self.instance and self.instance.pk and self.instance.cliente:
            cliente_para_filtrar = self.instance.cliente
        # Se houver dados POST, tentar obter o cliente dos dados
        elif self.data and 'cliente' in self.data:
            try:
                cliente_id = self.data.get('cliente')
                if cliente_id:
                    cliente_para_filtrar = Cliente.objects.get(pk=cliente_id)
            except (Cliente.DoesNotExist, ValueError, TypeError):
                pass
        
        # Definir queryset de romaneios baseado no cliente
        if cliente_para_filtrar:
            self.fields['romaneios'].queryset = RomaneioViagem.objects.filter(
                cliente=cliente_para_filtrar
            ).order_by('-data_emissao')
        else:
            self.fields['romaneios'].queryset = RomaneioViagem.objects.all().order_by('-data_emissao')
        
        # Tornar romaneios opcional visualmente, mas validar depois
        self.fields['romaneios'].required = False
    
    def clean_valor_cte_manifesto(self):
        """Limpa o campo valor_cte_manifesto, convertendo valores vazios para 0.00"""
        valor = self.cleaned_data.get('valor_cte_manifesto')
        
        if valor is None:
            return Decimal('0.00')
        
        if isinstance(valor, str) and valor.strip() == '':
            return Decimal('0.00')
        
        if isinstance(valor, (Decimal, float, int)):
            return Decimal(str(valor))
        
        if isinstance(valor, str):
            try:
                return Decimal(valor.strip()) if valor.strip() else Decimal('0.00')
            except (ValueError, TypeError):
                return Decimal('0.00')
        
        return valor

    def clean_valor_distribuicao_trabalhadores(self):
        """Converte vazio em None; valor não pode ser negativo."""
        valor = self.cleaned_data.get('valor_distribuicao_trabalhadores')
        if valor is None:
            return None
        if isinstance(valor, str) and valor.strip() == '':
            return None
        try:
            v = Decimal(str(valor))
            if v < 0:
                raise ValidationError('Não pode ser negativo.')
            return v
        except (ValueError, TypeError):
            return None

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        romaneios = cleaned_data.get('romaneios')
        valor_carregamento = cleaned_data.get('valor_carregamento') or Decimal('0.00')
        valor_dist = cleaned_data.get('valor_distribuicao_trabalhadores')
        if valor_dist is not None and valor_carregamento is not None and valor_dist > valor_carregamento:
            raise ValidationError(
                {'valor_distribuicao_trabalhadores': 'O valor para distribuição não pode ser maior que o valor repassado ao cliente.'}
            )
        
        # Validar que pelo menos um romaneio foi selecionado
        if not romaneios or romaneios.count() == 0:
            raise ValidationError('Selecione pelo menos um romaneio para esta cobrança.')
        
        # Validar que todos os romaneios selecionados pertencem ao cliente escolhido
        if cliente and romaneios:
            romaneios_invalidos = romaneios.exclude(cliente=cliente)
            if romaneios_invalidos.exists():
                raise ValidationError(
                    f'Os seguintes romaneios não pertencem ao cliente selecionado: '
                    f'{", ".join([str(r.codigo) for r in romaneios_invalidos])}'
                )
        
        return cleaned_data


class SetorBancarioForm(forms.ModelForm):
    """Formulário para dados bancários dos setores"""
    
    class Meta:
        model = SetorBancario
        fields = ['setor', 'nome_responsavel', 'banco', 'agencia', 'conta_corrente', 'chave_pix', 'tipo_chave_pix', 'ativo']
        widgets = {
            'setor': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
            'nome_responsavel': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nome do responsável ou beneficiário'
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: BRADESCO'
            }),
            'agencia': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: 0125'
            }),
            'conta_corrente': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ex: 7715-1'
            }),
            'chave_pix': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Chave PIX'
            }),
            'tipo_chave_pix': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'setor': 'Setor',
            'nome_responsavel': 'Nome do Responsável/Beneficiário',
            'banco': 'Banco',
            'agencia': 'Agência',
            'conta_corrente': 'Conta Corrente',
            'chave_pix': 'Chave PIX',
            'tipo_chave_pix': 'Tipo de Chave PIX',
            'ativo': 'Ativo',
        }
