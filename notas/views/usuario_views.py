"""
Views de gerenciamento de usuários (apenas administradores).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..models import Usuario
from ..forms import CadastroUsuarioForm
from ..decorators import admin_required, rate_limit_critical


@admin_required
@rate_limit_critical
def cadastrar_usuario(request):
    """View para cadastrar um novo usuário"""
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário {user.username} cadastrado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao cadastrar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'notas/auth/cadastrar_usuario.html', {'form': form})


@admin_required
def listar_usuarios(request):
    """Lista todos os usuários"""
    usuarios = Usuario.objects.select_related('cliente').order_by('username')
    usuarios_admin = usuarios.filter(tipo_usuario='admin')
    usuarios_funcionario = usuarios.filter(tipo_usuario='funcionario')
    usuarios_cliente = usuarios.filter(tipo_usuario='cliente')
    return render(request, 'notas/auth/listar_usuarios.html', {
        'usuarios': usuarios,
        'usuarios_admin': usuarios_admin,
        'usuarios_funcionario': usuarios_funcionario,
        'usuarios_cliente': usuarios_cliente,
    })


@admin_required
@rate_limit_critical
def editar_usuario(request, pk):
    """View para editar um usuário existente"""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            if form.cleaned_data.get('password1'):
                usuario.set_password(form.cleaned_data['password1'])
            form.save()
            messages.success(request, f'Usuário {usuario.username} atualizado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm(instance=usuario)
    
    return render(request, 'notas/auth/editar_usuario.html', {'form': form, 'usuario': usuario})


@admin_required
@rate_limit_critical
def toggle_status_usuario(request, pk):
    """Alterna o status (ativo/inativo) de um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        if usuario.is_active:
            usuario.is_active = False
            messages.success(request, f'Usuário {usuario.username} foi desativado com sucesso!')
        else:
            usuario.is_active = True
            messages.success(request, f'Usuário {usuario.username} foi ativado com sucesso!')
        
        usuario.save()
        return redirect('notas:listar_usuarios')
    
    return redirect('notas:listar_usuarios')


@admin_required
@rate_limit_critical
def excluir_usuario(request, pk):
    """View para excluir um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if usuario == request.user:
        messages.error(request, 'Você não pode excluir seu próprio usuário.')
        return redirect('notas:listar_usuarios')
    
    if request.method == 'POST':
        try:
            username = usuario.username
            usuario.delete()
            messages.success(request, f'Usuário {username} excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o usuário: {e}')
        return redirect('notas:listar_usuarios')
    
    return render(request, 'notas/auth/confirmar_exclusao_usuario.html', {'usuario': usuario})
