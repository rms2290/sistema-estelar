from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from ..forms import LoginForm, CadastroUsuarioForm, AlterarSenhaForm

def login_view(request):
    """View para login de usuários"""
    if request.user.is_authenticated:
        return redirect('notas:listar_notas_fiscais')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.get_full_name()}!')
                return redirect('notas:listar_notas_fiscais')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'notas/auth/login.html', {'form': form})

def logout_view(request):
    """View para logout de usuários"""
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('notas:login')

@login_required
def alterar_senha(request):
    """View para alterar senha do usuário logado"""
    if request.method == 'POST':
        form = AlterarSenhaForm(request.POST)
        if form.is_valid():
            user = request.user
            if user.check_password(form.cleaned_data['senha_atual']):
                user.set_password(form.cleaned_data['nova_senha'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('notas:perfil')
            else:
                messages.error(request, 'Senha atual incorreta.')
    else:
        form = AlterarSenhaForm()
    
    return render(request, 'notas/auth/alterar_senha.html', {'form': form})

@login_required
def perfil_usuario(request):
    """View para exibir perfil do usuário"""
    return render(request, 'notas/auth/perfil.html')

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente')
def minhas_notas_fiscais(request):
    """View para clientes verem suas próprias notas fiscais"""
    from ..models import NotaFiscal
    
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        notas_fiscais = NotaFiscal.objects.filter(cliente=request.user.cliente)
    else:
        notas_fiscais = NotaFiscal.objects.none()
    
    context = {
        'notas_fiscais': notas_fiscais,
    }
    return render(request, 'notas/auth/minhas_notas.html', context)

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente')
def imprimir_nota_fiscal(request, pk):
    """View para clientes imprimirem suas notas fiscais"""
    from ..models import NotaFiscal
    from django.shortcuts import get_object_or_404
    
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk, cliente=request.user.cliente)
    else:
        nota_fiscal = get_object_or_404(NotaFiscal, pk=pk)
    
    return render(request, 'notas/auth/imprimir_nota_fiscal.html', {'nota_fiscal': nota_fiscal})

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente')
def meus_romaneios(request):
    """View para clientes verem seus próprios romaneios"""
    from ..models import RomaneioViagem
    
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        romaneios = RomaneioViagem.objects.filter(cliente=request.user.cliente)
    else:
        romaneios = RomaneioViagem.objects.none()
    
    context = {
        'romaneios': romaneios,
    }
    return render(request, 'notas/auth/meus_romaneios.html', context) 