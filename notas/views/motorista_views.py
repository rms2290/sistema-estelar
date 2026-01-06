"""
Views relacionadas a Motoristas
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Motorista, HistoricoConsulta
from ..forms import MotoristaForm, HistoricoConsultaForm
from ..decorators import rate_limit_critical

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
@rate_limit_critical
def adicionar_motorista(request):
    """View para adicionar um novo motorista"""
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            try:
                motorista = form.save()
                # Verificar se os dados foram salvos corretamente
                motorista.refresh_from_db()
                logger.info(
                    f'Motorista {motorista.nome} criado com sucesso',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'motorista_id': motorista.pk,
                        'motorista_cpf': motorista.cpf
                    }
                )
                messages.success(request, 'Motorista adicionado com sucesso!')
                return redirect('notas:listar_motoristas')
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro ao criar motorista',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao salvar motorista: {str(e)}')
        else:
            # Exibir erros do formulário para debug
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f'{field}: {error}')
            messages.error(request, f'Houve um erro ao adicionar o motorista. Verifique os campos. Erros: {", ".join(error_messages)}')
    else:
        form = MotoristaForm()
    
    context = {
        'form': form,
        'historico_consultas': None,  # Não há histórico para motoristas novos
    }
    return render(request, 'notas/adicionar_motorista.html', context)


@login_required
@rate_limit_critical
def editar_motorista(request, pk):
    """View para editar um motorista existente"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]

    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao atualizar o motorista. Verifique os campos.')
    else:
        form = MotoristaForm(instance=motorista)
    
    context = {
        'form': form,
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/editar_motorista.html', context)


def adicionar_historico_consulta(request, pk):
    """View para adicionar histórico de consulta a um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.motorista = motorista
            historico.save()
            
            # Atualizar o campo numero_consulta do motorista com o número da última consulta
            motorista.numero_consulta = historico.numero_consulta
            motorista.save()
            
            messages.success(request, 'Consulta de risco registrada com sucesso!')
            return redirect('notas:editar_motorista', pk=motorista.pk)
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta. Verifique os campos.')
            return redirect('notas:editar_motorista', pk=motorista.pk)
    return redirect('notas:editar_motorista', pk=motorista.pk)


def registrar_consulta_motorista(request, pk):
    """Nova view para registrar consultas diretamente na tela de pesquisa de motoristas"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.motorista = motorista
            historico.save()
            
            # Atualizar o campo numero_consulta do motorista com o número da última consulta
            motorista.numero_consulta = historico.numero_consulta
            motorista.save()
            
            messages.success(request, 'Consulta registrada com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta. Verifique os campos.')
    else:
        form = HistoricoConsultaForm()
    
    # Buscar histórico das últimas 5 consultas
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]
    
    context = {
        'motorista': motorista,
        'form': form,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/registrar_consulta_motorista.html', context)


@login_required
@login_required
@rate_limit_critical
def excluir_motorista(request, pk):
    """View para excluir um motorista (com validação de senha admin)"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
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
            return render(request, 'notas/confirmar_exclusao_motorista.html', {
                'motorista': motorista,
                'erro_senha': True
            })
        
        try:
            # Registrar na auditoria
            from ..utils.auditoria import registrar_exclusao
            observacao = f"Exclusão solicitada por {request.user.username}"
            if admin_autorizador and admin_autorizador != request.user:
                observacao += f", autorizada por {admin_autorizador.username}"
            
            registrar_exclusao(
                usuario=request.user,
                instancia=motorista,
                request=request,
                descricao=observacao
            )
            
            motorista.delete()
            messages.success(request, 'Motorista excluído com sucesso!')
        except IntegrityError as e:
            logger.error(
                'Erro de integridade ao excluir motorista',
                extra={
                    'user': request.user.username,
                    'motorista_id': pk,
                    'error': str(e)
                },
                exc_info=True
            )
            messages.error(
                request,
                'Não foi possível excluir o motorista. '
                'Ele pode estar vinculado a romaneios ou outros registros.'
            )
        except Exception as e:
            logger.error(
                'Erro inesperado ao excluir motorista',
                extra={
                    'user': request.user.username,
                    'motorista_id': pk,
                    'error_type': type(e).__name__,
                    'error': str(e)
                },
                exc_info=True
            )
            messages.error(
                request,
                'Erro inesperado ao excluir motorista. '
                'Tente novamente ou entre em contato com o suporte.'
            )
        return redirect('notas:listar_motoristas')
    
    return render(request, 'notas/confirmar_exclusao_motorista.html', {
        'motorista': motorista,
        'erro_senha': False
    })


@login_required
def detalhes_motorista(request, pk):
    """View para exibir detalhes de um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]
    context = {
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/detalhes_motorista.html', context)


@login_required
def listar_motoristas(request):
    """Lista todos os motoristas com filtros de busca"""
    from ..forms import MotoristaSearchForm
    
    search_form = MotoristaSearchForm(request.GET)
    motoristas = Motorista.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        # Query já otimizada (Motorista não tem ForeignKeys principais para select_related)
        queryset = Motorista.objects.all()
        nome = search_form.cleaned_data.get('nome')
        cpf = search_form.cleaned_data.get('cpf')
        rg = search_form.cleaned_data.get('rg')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        if rg:
            queryset = queryset.filter(rg__icontains=rg)
        
        motoristas = queryset.order_by('nome')
    
    context = {
        'motoristas': motoristas,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_motoristas.html', context)

