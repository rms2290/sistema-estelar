from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db.models import Q
from ..models import TabelaSeguro
from ..forms import CadastroUsuarioForm, TabelaSeguroForm

User = get_user_model()

def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_authenticated and user.tipo_usuario == 'admin'

def is_funcionario(user):
    """Verifica se o usuário é funcionário"""
    return user.is_authenticated and user.tipo_usuario in ['admin', 'funcionario']

def is_cliente(user):
    """Verifica se o usuário é cliente"""
    return user.is_authenticated and user.tipo_usuario in ['admin', 'funcionario', 'cliente']

@login_required
@user_passes_test(is_admin)
def cadastrar_usuario(request):
    """Cadastra um novo usuário"""
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário cadastrado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao cadastrar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'notas/auth/cadastrar_usuario.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def listar_usuarios(request):
    """Lista todos os usuários"""
    usuarios = User.objects.all().order_by('username')
    return render(request, 'notas/auth/listar_usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(is_admin)
def editar_usuario(request, pk):
    """Edita um usuário existente"""
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o usuário.')
    else:
        form = CadastroUsuarioForm(instance=usuario)
    
    return render(request, 'notas/auth/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@user_passes_test(is_admin)
def excluir_usuario(request, pk):
    """Exclui um usuário"""
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        if usuario == request.user:
            messages.error(request, 'Você não pode excluir seu próprio usuário.')
        else:
            usuario.delete()
            messages.success(request, 'Usuário excluído com sucesso!')
        return redirect('notas:listar_usuarios')
    
    return render(request, 'notas/auth/confirmar_exclusao_usuario.html', {'usuario': usuario})

@login_required
@user_passes_test(is_admin)
def listar_tabela_seguros(request):
    """Lista a tabela de seguros"""
    tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    return render(request, 'notas/listar_tabela_seguros.html', {'tabela_seguros': tabela_seguros})

@login_required
@user_passes_test(is_admin)
def editar_tabela_seguro(request, pk):
    """Edita um registro da tabela de seguros"""
    tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
    
    if request.method == 'POST':
        form = TabelaSeguroForm(request.POST, instance=tabela_seguro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tabela de seguro atualizada com sucesso!')
            return redirect('notas:listar_tabela_seguros')
        else:
            messages.error(request, 'Houve um erro ao atualizar a tabela de seguro.')
    else:
        form = TabelaSeguroForm(instance=tabela_seguro)
    
    return render(request, 'notas/editar_tabela_seguro.html', {'form': form, 'tabela_seguro': tabela_seguro})

@login_required
@user_passes_test(is_admin)
def atualizar_tabela_seguro_ajax(request, pk):
    """Atualiza tabela de seguro via AJAX"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
        percentual = request.POST.get('percentual_seguro')
        
        try:
            percentual = float(percentual)
            if 0 <= percentual <= 100:
                tabela_seguro.percentual_seguro = percentual
                tabela_seguro.save()
                return JsonResponse({'success': True, 'message': 'Percentual atualizado com sucesso!'})
            else:
                return JsonResponse({'success': False, 'message': 'Percentual deve estar entre 0 e 100.'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Percentual inválido.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro inesperado: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método não permitido.'})

@login_required
@user_passes_test(is_admin)
def totalizador_por_estado(request):
    """Exibe totalizador por estado"""
    from django.db.models import Sum, Count
    from ..models import NotaFiscal
    
    # Agrupar notas fiscais por estado do cliente
    totalizador = NotaFiscal.objects.values(
        'cliente__estado'
    ).annotate(
        total_notas=Count('id'),
        total_peso=Sum('peso'),
        total_valor=Sum('valor')
    ).order_by('cliente__estado')
    
    # Calcular totais gerais
    totais_gerais = NotaFiscal.objects.aggregate(
        total_notas=Count('id'),
        total_peso=Sum('peso'),
        total_valor=Sum('valor')
    )
    
    context = {
        'totalizador': totalizador,
        'totais_gerais': totais_gerais,
    }
    return render(request, 'notas/totalizador_por_estado.html', context) 