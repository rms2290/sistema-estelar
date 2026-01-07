"""
Formulários relacionados a Romaneios
"""
from django import forms
from django.db.models import Q
from datetime import datetime
from ..models import RomaneioViagem, Cliente, Motorista, Veiculo, NotaFiscal
from .base import UpperCaseCharField


class RomaneioViagemForm(forms.ModelForm):
    """Formulário para criar e editar romaneios"""
    notas_fiscais = forms.ModelMultipleChoiceField(
        queryset=NotaFiscal.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
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
        queryset=Veiculo.objects.all().order_by('placa'),
        label='Veículo Principal',
        required=True,
        empty_label="--- Selecione o veículo principal ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reboque_1 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__iexact='Reboque').order_by('placa'),
        label='Reboque 1',
        required=False,
        empty_label="--- Selecione o reboque 1 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reboque_2 = forms.ModelChoiceField(
        queryset=Veiculo.objects.filter(tipo_unidade__iexact='Reboque').order_by('placa'),
        label='Reboque 2',
        required=False,
        empty_label="--- Selecione o reboque 2 ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is None and not self.initial.get('data_romaneio'):
            data_atual = datetime.now().date()
            self.fields['data_romaneio'].initial = data_atual.strftime('%Y-%m-%d')
        
        # Querysets para ModelChoiceFields
        self.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        self.fields['veiculo_principal'].queryset = Veiculo.objects.filter(tipo_unidade__in=['CARRO', 'VAN', 'CAMINHÃO', 'CAVALO']).order_by('placa')
        # Usar iexact para buscar reboques (pode estar em maiúsculas devido ao UpperCaseMixin)
        self.fields['reboque_1'].queryset = Veiculo.objects.filter(tipo_unidade__iexact='Reboque').order_by('placa')
        self.fields['reboque_2'].queryset = Veiculo.objects.filter(tipo_unidade__iexact='Reboque').order_by('placa')

        # Lógica para edição
        if self.instance and self.instance.pk:
            if self.instance.data_emissao:
                if hasattr(self.instance.data_emissao, 'date'):
                    data_emissao = self.instance.data_emissao.date()
                else:
                    data_emissao = self.instance.data_emissao
                self.fields['data_romaneio'].initial = data_emissao.strftime('%Y-%m-%d')

            if self.instance.cliente:
                self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=self.instance.cliente
                ).filter(
                    Q(romaneios_vinculados=self.instance) | Q(status='Depósito')
                ).order_by('nota')
                self.fields['notas_fiscais'].initial = self.instance.notas_fiscais.all()
        
        # Configurar queryset das notas fiscais baseado no cliente dos dados
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
            if field_name != 'notas_fiscais':
                if not isinstance(field.widget, (forms.Select, forms.DateInput)):
                    field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'cliente':
                 field.widget.attrs.update({'onchange': 'loadNotasFiscais(this.value);'})

    class Meta:
        model = RomaneioViagem
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
    
    def clean(self):
        cleaned_data = super().clean()
        
        motorista = cleaned_data.get('motorista')
        veiculo_principal = cleaned_data.get('veiculo_principal')
        reboque_1 = cleaned_data.get('reboque_1')
        reboque_2 = cleaned_data.get('reboque_2')
        
        # Validação de composição veicular
        if motorista and veiculo_principal:
            tipo_composicao_motorista = motorista.tipo_composicao_motorista
            tipo_veiculo_principal = veiculo_principal.tipo_unidade
            
            # Validar se o motorista pode dirigir o tipo de veículo principal
            if tipo_composicao_motorista == 'Carro' and tipo_veiculo_principal not in ['Carro']:
                raise forms.ValidationError(
                    f"O motorista {motorista.nome} está habilitado apenas para dirigir carros, "
                    f"mas foi selecionado um veículo do tipo {tipo_veiculo_principal}."
                )
            elif tipo_composicao_motorista == 'Van' and tipo_veiculo_principal not in ['Van']:
                raise forms.ValidationError(
                    f"O motorista {motorista.nome} está habilitado apenas para dirigir vans, "
                    f"mas foi selecionado um veículo do tipo {tipo_veiculo_principal}."
                )
            elif tipo_composicao_motorista == 'Caminhão' and tipo_veiculo_principal not in ['Caminhão']:
                raise forms.ValidationError(
                    f"O motorista {motorista.nome} está habilitado apenas para dirigir caminhões, "
                    f"mas foi selecionado um veículo do tipo {tipo_veiculo_principal}."
                )
            elif tipo_composicao_motorista == 'Carreta' and tipo_veiculo_principal not in ['Cavalo']:
                raise forms.ValidationError(
                    f"O motorista {motorista.nome} está habilitado para dirigir carretas (cavalo + reboque), "
                    f"mas foi selecionado um veículo do tipo {tipo_veiculo_principal}."
                )
            elif tipo_composicao_motorista == 'Bitrem' and tipo_veiculo_principal not in ['Cavalo']:
                raise forms.ValidationError(
                    f"O motorista {motorista.nome} está habilitado para dirigir bitrens (cavalo + 2 reboques), "
                    f"mas foi selecionado um veículo do tipo {tipo_veiculo_principal}."
                )
            
            # Validar reboques baseado no tipo de composição
            if tipo_composicao_motorista in ['Carro', 'Van', 'Caminhão']:
                if reboque_1 or reboque_2:
                    raise forms.ValidationError(
                        f"O motorista {motorista.nome} está habilitado para dirigir apenas veículos simples "
                        f"({tipo_composicao_motorista}), mas foram selecionados reboques."
                    )
            elif tipo_composicao_motorista == 'Carreta':
                if not reboque_1:
                    raise forms.ValidationError(
                        f"O motorista {motorista.nome} está habilitado para dirigir carretas, "
                        f"mas nenhum reboque foi selecionado."
                    )
                if reboque_2:
                    raise forms.ValidationError(
                        f"O motorista {motorista.nome} está habilitado para dirigir apenas carretas (1 reboque), "
                        f"mas foram selecionados 2 reboques."
                    )
            elif tipo_composicao_motorista == 'Bitrem':
                if not reboque_1 or not reboque_2:
                    raise forms.ValidationError(
                        f"O motorista {motorista.nome} está habilitado para dirigir bitrens, "
                        f"mas é necessário selecionar 2 reboques."
                    )
        
        # Validar reboques (comparação case-insensitive devido ao UpperCaseMixin)
        if reboque_1 and reboque_1.tipo_unidade.upper() != 'REBOQUE':
            raise forms.ValidationError(
                f"O veículo {reboque_1.placa} não é um reboque válido. Tipo atual: {reboque_1.tipo_unidade}"
            )
        
        if reboque_2 and reboque_2.tipo_unidade.upper() != 'REBOQUE':
            raise forms.ValidationError(
                f"O veículo {reboque_2.placa} não é um reboque válido. Tipo atual: {reboque_2.tipo_unidade}"
            )
        
        # Validar se não há reboques duplicados
        if reboque_1 and reboque_2 and reboque_1 == reboque_2:
            raise forms.ValidationError("Não é possível usar o mesmo veículo como reboque 1 e reboque 2.")
        
        # Validar se o veículo principal não é usado como reboque
        if veiculo_principal:
            if reboque_1 and veiculo_principal == reboque_1:
                raise forms.ValidationError("O veículo principal não pode ser usado como reboque 1.")
            if reboque_2 and veiculo_principal == reboque_2:
                raise forms.ValidationError("O veículo principal não pode ser usado como reboque 2.")
        
        return cleaned_data


class RomaneioSearchForm(forms.Form):
    """Formulário de pesquisa para romaneios"""
    codigo = UpperCaseCharField(
        label='Código do Romaneio',
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ROM-001 ou ROM-100-001'})
    )
    tipo_romaneio = forms.ChoiceField(
        label='Tipo de Romaneio',
        choices=[
            ('', 'Todos'),
            ('normal', 'Romaneio Normal'),
            ('generico', 'Romaneio Genérico')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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

