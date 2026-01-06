"""
Formulários relacionados a Autenticação e Usuários
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from ..models import Usuario, Cliente
from .base import UpperCaseCharField, ESTADOS_CHOICES


class LoginForm(forms.Form):
    """Formulário de login"""
    username = forms.CharField(
        label='Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário', 'autofocus': True})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )


class CadastroUsuarioForm(forms.ModelForm):
    """Formulário para cadastrar novos usuários"""
    username = forms.CharField(
        label='Nome de Usuário',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'})
    )
    
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'}),
        required=False
    )
    
    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar senha'}),
        required=False
    )
    
    tipo_usuario = forms.ChoiceField(
        label='Tipo de Usuário',
        choices=Usuario.TIPO_USUARIO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(status='Ativo').order_by('razao_social'),
        label='Cliente (se aplicável)',
        required=False,
        empty_label="--- Selecione um cliente ---",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_active = forms.BooleanField(
        label='Usuário Ativo',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'cliente', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        tipo_usuario = cleaned_data.get('tipo_usuario')
        cliente = cleaned_data.get('cliente')
        
        # Se é um novo usuário ou senha foi fornecida, validar senha
        if not self.instance.pk or password1:
            if password1 and password2:
                if password1 != password2:
                    raise forms.ValidationError("As senhas não coincidem.")
                if len(password1) < 8:
                    raise forms.ValidationError("A senha deve ter pelo menos 8 caracteres.")
        
        # Se tipo é cliente, cliente é obrigatório
        if tipo_usuario == 'cliente' and not cliente:
            raise forms.ValidationError("Cliente é obrigatório para usuários do tipo Cliente.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        
        if password1:
            user.set_password(password1)
        
        if commit:
            user.save()
        
        return user


class AlterarSenhaForm(forms.Form):
    """Formulário para alterar senha"""
    senha_atual = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha atual'})
    )
    
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua nova senha'}),
        min_length=8
    )
    
    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme sua nova senha'}),
        min_length=8
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get('nova_senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        
        if nova_senha and confirmar_senha:
            if nova_senha != confirmar_senha:
                raise forms.ValidationError("As novas senhas não coincidem.")
        
        return cleaned_data


