"""
Views de autenticação e perfil de usuário
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# Importação opcional de django_ratelimit
try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    # Se django_ratelimit não estiver instalado, criar um decorator dummy
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

from ..forms import LoginForm, AlterarSenhaForm


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """
    View de login com rate limiting:
    - Máximo 5 tentativas por minuto por IP
    - Proteção contra brute force
    """
    if request.user.is_authenticated:
        return redirect('notas:dashboard')
    
    error_message = None
    
    # Verificar se foi bloqueado por rate limit
    if getattr(request, 'limited', False):
        error_message = 'Muitas tentativas de login. Aguarde 1 minuto antes de tentar novamente.'
        form = LoginForm()
        return render(request, 'notas/auth/login.html', {'form': form, 'error_message': error_message})
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_active:
                login(request, user)
                # Atualizar último acesso
                user.ultimo_acesso = timezone.now()
                user.save()
                
                messages.success(request, f'Bem-vindo, {user.get_full_name()}!')
                return redirect('notas:dashboard')
            else:
                error_message = 'Nome de usuário ou senha inválidos.'
    else:
        form = LoginForm()
    
    return render(request, 'notas/auth/login.html', {'form': form, 'error_message': error_message})


def logout_view(request):
    """View para fazer logout do usuário"""
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('notas:login')


@login_required
def alterar_senha(request):
    """View para alterar senha do usuário"""
    if request.method == 'POST':
        form = AlterarSenhaForm(request.POST)
        if form.is_valid():
            senha_atual = form.cleaned_data['senha_atual']
            nova_senha = form.cleaned_data['nova_senha']
            
            # Verificar senha atual
            if not request.user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
            else:
                # Alterar senha
                request.user.set_password(nova_senha)
                request.user.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('notas:dashboard')
    else:
        form = AlterarSenhaForm()
    
    return render(request, 'notas/auth/alterar_senha.html', {'form': form})


@login_required
def perfil_usuario(request):
    """View para exibir perfil do usuário"""
    return render(request, 'notas/auth/perfil.html')

