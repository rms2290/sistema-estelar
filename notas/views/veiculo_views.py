"""
Views relacionadas a Veículos
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Veiculo
from ..forms import VeiculoForm, VeiculoSearchForm
from ..decorators import rate_limit_critical

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
@rate_limit_critical
def adicionar_veiculo(request):
    """View para adicionar UMA UNIDADE de Veículo"""
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            try:
                veiculo = form.save()
                logger.info(
                    f'Veículo {veiculo.placa} criado com sucesso',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'veiculo_id': veiculo.pk,
                        'veiculo_placa': veiculo.placa
                    }
                )
                messages.success(request, 'Unidade de Veículo cadastrada com sucesso!')
                return redirect('notas:listar_veiculos')  # Redireciona para a pesquisa de unidades
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro ao criar veículo',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao cadastrar veículo: {str(e)}')
        else:
            logger.warning(
                f'Formulário de veículo inválido',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'errors': form.errors
                }
            )
            messages.error(request, 'Houve um erro ao cadastrar a unidade de veículo. Verifique os campos.')
    else:
        form = VeiculoForm()
    
    context = {
        'form': form,
    }
    return render(request, 'notas/adicionar_veiculo.html', context)


@login_required
@rate_limit_critical
def editar_veiculo(request, pk):
    """View para editar uma unidade de veículo existente"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        form = VeiculoForm(request.POST, instance=veiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidade de Veículo atualizada com sucesso!')
            return redirect('notas:detalhes_veiculo', pk=veiculo.pk)
        else:
            messages.error(request, 'Houve um erro ao atualizar a unidade de veículo. Verifique os campos.')
    else:
        form = VeiculoForm(instance=veiculo)
    return render(request, 'notas/editar_veiculo.html', {'form': form, 'veiculo': veiculo})


@login_required
@login_required
@rate_limit_critical
def excluir_veiculo(request, pk):
    """View para excluir uma unidade de veículo (com validação de senha admin)"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    if request.method == 'POST':
        # Verificar credenciais de administrador
        from ..utils.validacao_exclusao import validar_exclusao_com_senha_admin
        
        username_admin = request.POST.get('username_admin', '')
        senha_admin = request.POST.get('senha_admin', '')
        valido, admin_autorizador, mensagem_erro = validar_exclusao_com_senha_admin(
            username_admin=username_admin,
            senha_admin=senha_admin,
            usuario_solicitante=request.user
        )
        
        if not valido:
            messages.error(request, mensagem_erro)
            return render(request, 'notas/confirmar_exclusao_veiculo.html', {
                'veiculo': veiculo,
                'erro_senha': True
            })
        
        try:
            # Verificar se o veículo está sendo usado em romaneios
            romaneios_principal = veiculo.romaneios_veiculo_principal.all()
            romaneios_reboque1 = veiculo.romaneios_reboque_1.all()
            romaneios_reboque2 = veiculo.romaneios_reboque_2.all()
            
            total_romaneios = romaneios_principal.count() + romaneios_reboque1.count() + romaneios_reboque2.count()
            
            if total_romaneios > 0:
                # Desvincular o veículo dos romaneios
                for romaneio in romaneios_principal:
                    romaneio.veiculo_principal = None
                    romaneio.save()
                for romaneio in romaneios_reboque1:
                    romaneio.reboque_1 = None
                    romaneio.save()
                for romaneio in romaneios_reboque2:
                    romaneio.reboque_2 = None
                    romaneio.save()
                messages.warning(request, f'Veículo desvinculado de {total_romaneios} romaneio(s) antes da exclusão.')
            
            # Registrar na auditoria
            from ..utils.auditoria import registrar_exclusao
            observacao = f"Exclusão solicitada por {request.user.username}"
            if admin_autorizador and admin_autorizador != request.user:
                observacao += f", autorizada por {admin_autorizador.username}"
            
            registrar_exclusao(
                usuario=request.user,
                instancia=veiculo,
                request=request,
                descricao=observacao
            )
            
            veiculo.delete()
            logger.info(
                f'Veículo {veiculo.placa} excluído com sucesso',
                extra={
                    'user': request.user.username,
                    'veiculo_id': veiculo.pk,
                    'veiculo_placa': veiculo.placa,
                    'admin_autorizador': admin_autorizador.username if admin_autorizador else None
                }
            )
            messages.success(request, 'Unidade de Veículo excluída com sucesso!')
        except (IntegrityError, ValidationError) as e:
            logger.error(
                f'Erro ao excluir veículo {veiculo.pk}',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'veiculo_id': veiculo.pk,
                    'error': str(e),
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            messages.error(request, f'Não foi possível excluir o veículo: {str(e)}')
        return redirect('notas:listar_veiculos')
    return render(request, 'notas/confirmar_exclusao_veiculo.html', {
        'veiculo': veiculo,
        'erro_senha': False
    })


@login_required
def detalhes_veiculo(request, pk):
    """View para exibir detalhes de uma unidade de veículo"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    context = {
        'veiculo': veiculo,
    }
    return render(request, 'notas/detalhes_veiculo.html', context)


@login_required
def listar_veiculos(request):
    """Lista todos os veículos com filtros de busca"""
    search_form = VeiculoSearchForm(request.GET)
    veiculos = Veiculo.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = Veiculo.objects.all()
        placa = search_form.cleaned_data.get('placa')
        tipo_unidade = search_form.cleaned_data.get('tipo_unidade')

        if placa:
            queryset = queryset.filter(placa__icontains=placa)
        if tipo_unidade:
            queryset = queryset.filter(tipo_unidade=tipo_unidade)
        
        veiculos = queryset.order_by('placa')
    
    context = {
        'veiculos': veiculos,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_veiculos.html', context)

