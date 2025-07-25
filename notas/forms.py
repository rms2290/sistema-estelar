# Novo formulário para Nota Fiscal

from django import forms
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem
import re

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = '__all__'
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
        }

# Novo formulário para Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'

    def clean_cnpj(self): # Formatação CNPJ
        cnpj = self.cleaned_data['cnpj']
        cnpj_numeros = re.sub(r'[^0-9]', '', cnpj) # Remove tudo que não for número

        if len(cnpj_numeros) != 14:
            raise forms.ValidationError("CNPJ deve conter 14 dígitos numéricos.")
        
        return cnpj_numeros # Retorna o CNPJ limpo (apenas números)
    
    def clean_telefone(self): # Formatação telefone
        telefone = self.cleaned_data.get('telefone') # Use .get() para campos opcionais
        if not telefone: # Se o campo for opcional e não preenchido, retorne None ou string vazia
            return telefone

        telefone_numeros = re.sub(r'[^0-9]', '', telefone)

        # Validações básicas:
        # Pelo menos 10 dígitos (DDD + 8 ou 9 dígitos)
        if not (10 <= len(telefone_numeros) <= 11):
            raise forms.ValidationError("Telefone deve ter entre 10 e 11 dígitos (incluindo DDD).")

        return telefone_numeros # Retorna o telefone limpo (apenas números)
    
    def clean_email(self): # Formatação email
        email = self.cleaned_data.get('email')
        if not email:
            return email

        # O EmailField do Django já faz a validação de formato
        # Aqui, só padronizamos para minúsculas
        return email.lower()


# Novo formulário para Motoristas

class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = '__all__'
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'cnh_vencimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        if len(cpf_numeros) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos numéricos.")
        # Opcional: Adicionar validação de dígito verificador de CPF aqui (mais complexo)
        return cpf_numeros

    def clean_celular(self):
        celular = self.cleaned_data.get('celular')
        if not celular:
            return celular
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

class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        # Lembre-se que 'proprietario' é um ForeignKey.
        # Se você for criar o proprietário na mesma tela, você pode excluí-lo daqui
        # e associá-lo na view. Se for selecionar um proprietário existente,
        # 'fields = '__all__'' vai criar um dropdown automaticamente.
        fields = '__all__' # Por enquanto, vamos manter '__all__' para ver o select box.
                           # Se for implementar o cadastro na mesma tela, mude para:
                           # exclude = ['proprietario']
        widgets = {
            'ano_fabricacao': forms.NumberInput(attrs={'min': 1900, 'max': 2100}), # Exemplo de widget
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
    

# Novo formulário para Romaneios

class RomaneioViagemForm(forms.ModelForm):
    notas_fiscais = forms.ModelMultipleChoiceField(
        queryset=NotaFiscal.objects.none(), # Começa vazio. O JS ou a edição preencherá.
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Notas Fiscais Associadas"
    )

    class Meta:
        model = RomaneioViagem
        fields = ['cliente', 'notas_fiscais', 'motorista', 'veiculo', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Definir o queryset inicial para o campo cliente (todos os clientes)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('razao_social')
        self.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        self.fields['veiculo'].queryset = Veiculo.objects.all().order_by('placa')

        # Se estamos editando um Romaneio existente, pré-popular as notas fiscais
        if self.instance and self.instance.pk: # Verifica se é uma instância existente e salva
            # Popula o queryset de notas_fiscais com base no cliente já associado
            self.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                cliente=self.instance.cliente
            ).order_by('nota')
            
            # Se a instância já existe, preenche as notas_fiscais selecionadas
            # Isso é necessário para que as checkboxes fiquem marcadas corretamente na edição
            self.fields['notas_fiscais'].initial = self.instance.notas_fiscais.all()
        
        # Adicionar atributos HTML para facilitar a estilização com CSS (Bootstrap)
        for field_name, field in self.fields.items():
            if field_name != 'notas_fiscais':
                field.widget.attrs.update({'class': 'form-control'})
            if field_name == 'cliente':
                 # Adiciona evento JS para carregar notas ao mudar o cliente
                 field.widget.attrs.update({'onchange': 'loadNotasFiscais(this.value);'})