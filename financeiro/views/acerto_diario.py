"""
Views de acerto diário: listar, salvar, carregamento/distribuição, valor Estelar.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from sistema_estelar.api_utils import json_success, json_error
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from notas.decorators import admin_required
from notas.models import Cliente
from financeiro.models import (
    AcertoDiarioCarregamento,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
)

logger = logging.getLogger(__name__)


@login_required
@admin_required
def listar_acertos_diarios(request):
    """Lista todos os acertos diários com opção de pesquisa"""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            acertos = acertos.filter(data__gte=data_inicio_obj)
        except Exception as e:
            logger.warning('Filtro data_inicio inválido em listar_acertos_diarios: %s', e)
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            acertos = acertos.filter(data__lte=data_fim_obj)
        except Exception as e:
            logger.warning('Filtro data_fim inválido em listar_acertos_diarios: %s', e)
    context = {'acertos': acertos, 'data_inicio': data_inicio, 'data_fim': data_fim}
    return render(request, 'financeiro/fluxo_caixa/listar_acertos_diarios.html', context)


@login_required
@admin_required
def acerto_diario_carregamento(request):
    """Tela principal de acerto diário de carregamento"""
    if request.GET.get('ajax') == '1' and request.GET.get('acerto_id'):
        acerto_id = request.GET.get('acerto_id')
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            carregamentos = list(CarregamentoCliente.objects.filter(
                acerto_diario=acerto
            ).select_related('cliente'))
            carregamentos.sort(key=lambda x: (
                0 if x.cliente else 1,
                x.cliente.razao_social if x.cliente else '',
                x.descricao or ''
            ))
            distribuicoes = DistribuicaoFuncionario.objects.filter(
                acerto_diario=acerto
            ).select_related('funcionario').order_by('funcionario__nome')
            diferenca = abs(acerto.total_carregamentos - acerto.total_distribuido)
            html = render_to_string('financeiro/fluxo_caixa/detalhes_acerto_diario.html', {
                'acerto': acerto,
                'carregamentos': carregamentos,
                'distribuicoes': distribuicoes,
                'diferenca': diferenca,
            }, request=request)
            return json_success(html=mark_safe(html))
        except AcertoDiarioCarregamento.DoesNotExist:
            return json_error('Acerto não encontrado', status=404)

    mostrar_formulario = request.GET.get('novo') == '1' or request.GET.get('acerto_id')
    acerto_id = request.GET.get('acerto_id')
    novo_acerto = request.GET.get('novo') == '1'

    if not mostrar_formulario:
        data_inicio = request.GET.get('data_inicio', '')
        data_fim = request.GET.get('data_fim', '')
        acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')
        if data_inicio:
            try:
                acertos = acertos.filter(data__gte=datetime.strptime(data_inicio, '%Y-%m-%d').date())
            except Exception as e:
                logger.warning('Filtro data_inicio inválido em acerto_diario_carregamento: %s', e)
        if data_fim:
            try:
                acertos = acertos.filter(data__lte=datetime.strptime(data_fim, '%Y-%m-%d').date())
            except Exception as e:
                logger.warning('Filtro data_fim inválido em acerto_diario_carregamento: %s', e)
        return render(request, 'financeiro/fluxo_caixa/acerto_diario_carregamento.html', {
            'acertos': acertos,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'mostrar_lista': True,
        })

    if acerto_id:
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            data_obj = acerto.data
        except AcertoDiarioCarregamento.DoesNotExist:
            acerto = None
            data_obj = timezone.now().date()
    elif novo_acerto:
        data_selecionada = request.GET.get('data', '')
        if data_selecionada:
            try:
                data_obj = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
                acerto_existente = AcertoDiarioCarregamento.objects.filter(data=data_obj).first()
                if acerto_existente:
                    return redirect('{}?acerto_id={}'.format(
                        reverse('financeiro:acerto_diario_carregamento'), acerto_existente.pk
                    ))
                acerto = AcertoDiarioCarregamento.objects.create(
                    data=data_obj,
                    valor_estelar=Decimal('0.00'),
                    observacoes='',
                    usuario_criacao=request.user
                )
                return redirect('{}?acerto_id={}'.format(
                    reverse('financeiro:acerto_diario_carregamento'), acerto.pk
                ))
            except Exception as e:
                logger.error(f'Erro ao criar novo acerto: {str(e)}', exc_info=True)
                acerto = None
                data_obj = None
        else:
            acerto = None
            data_obj = None
    else:
        acerto = None
        data_obj = timezone.now().date()

    if acerto:
        carregamentos = list(CarregamentoCliente.objects.filter(
            acerto_diario_id=acerto.pk
        ).select_related('cliente'))
        carregamentos.sort(key=lambda x: (
            0 if x.cliente else 1,
            x.cliente.razao_social if x.cliente else '',
            x.descricao or ''
        ))
        distribuicoes = list(DistribuicaoFuncionario.objects.filter(
            acerto_diario_id=acerto.pk
        ).select_related('funcionario').order_by('funcionario__nome'))
    else:
        carregamentos = []
        distribuicoes = []

    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    context = {
        'acerto': acerto,
        'data_selecionada': acerto.data if acerto else (data_obj if data_obj else None),
        'carregamentos': carregamentos,
        'distribuicoes': distribuicoes,
        'clientes': clientes,
        'funcionarios': funcionarios,
        'mostrar_formulario': True,
        'novo_acerto': novo_acerto and not acerto,
    }
    return render(request, 'financeiro/fluxo_caixa/acerto_diario_carregamento.html', context)


@login_required
@admin_required
def salvar_acerto_diario(request):
    """Salva o acerto diário e cria movimentos de caixa automaticamente"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        data = request.POST.get('data')
        observacoes = request.POST.get('observacoes', '')
        from financeiro.services import AcertoDiarioService
        acerto, erro = AcertoDiarioService.salvar_acerto_e_criar_movimentos(
            data=data,
            observacoes=observacoes,
            usuario=request.user,
        )
        if erro:
            return json_error(erro)
        return json_success(
            message='Acerto salvo com sucesso! Movimentos de caixa criados automaticamente.',
            acerto_id=acerto.pk,
        )
    except Exception as e:
        logger.error(f'Erro ao salvar acerto diário: {str(e)}', exc_info=True)
        return json_error(f'Erro ao salvar acerto: {str(e)}')


@login_required
@admin_required
def adicionar_carregamento_cliente_ajax(request):
    """Adiciona um carregamento de cliente ou descarga via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id')
        cliente_id = request.POST.get('cliente_id', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        valor = Decimal(request.POST.get('valor', '0.00'))
        observacoes = request.POST.get('observacoes', '')
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        if valor <= 0:
            return json_error('Valor deve ser maior que zero')
        if not cliente_id and not descricao:
            return json_error('Informe um cliente ou a descrição da descarga')
        if cliente_id and descricao:
            return json_error('Informe apenas cliente OU descrição, não ambos')
        cliente = None
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
        tipo_pagamento = request.POST.get('tipo_pagamento', 'Dinheiro') if not cliente else None
        carregamento, created = CarregamentoCliente.objects.get_or_create(
            acerto_diario=acerto,
            cliente=cliente,
            defaults={
                'descricao': descricao if not cliente else '',
                'valor': valor,
                'observacoes': observacoes,
                'tipo_pagamento': tipo_pagamento
            }
        )
        if not created:
            carregamento.cliente = cliente
            carregamento.descricao = descricao if not cliente else ''
            carregamento.valor = valor
            carregamento.observacoes = observacoes
            if not cliente:
                carregamento.tipo_pagamento = tipo_pagamento
            carregamento.save()
        return json_success(
            message='Registro adicionado com sucesso!',
            carregamento_id=carregamento.pk,
            nome_display=carregamento.nome_display,
            tipo=carregamento.tipo,
            valor=str(carregamento.valor),
        )
    except Exception as e:
        return json_error(f'Erro ao adicionar registro: {str(e)}')


@login_required
@admin_required
def remover_carregamento_cliente_ajax(request, pk):
    """Remove um carregamento de cliente via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        carregamento = get_object_or_404(CarregamentoCliente, pk=pk)
        carregamento.delete()
        return json_success(message='Carregamento removido com sucesso!')
    except Exception as e:
        return json_error(f'Erro ao remover carregamento: {str(e)}')


@login_required
@admin_required
def adicionar_distribuicao_funcionario_ajax(request):
    """Adiciona uma distribuição para funcionário via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id')
        funcionario_id = request.POST.get('funcionario_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        funcionario = get_object_or_404(FuncionarioFluxoCaixa, pk=funcionario_id)
        if valor <= 0:
            return json_error('Valor deve ser maior que zero')
        distribuicao, created = DistribuicaoFuncionario.objects.get_or_create(
            acerto_diario=acerto,
            funcionario=funcionario,
            defaults={'valor': valor}
        )
        if not created:
            distribuicao.valor = valor
            distribuicao.save()
        return json_success(
            message='Distribuição adicionada com sucesso!',
            distribuicao_id=distribuicao.pk,
            funcionario_nome=funcionario.nome,
            valor=str(distribuicao.valor),
        )
    except Exception as e:
        return json_error(f'Erro ao adicionar distribuição: {str(e)}')


@login_required
@admin_required
def remover_distribuicao_funcionario_ajax(request, pk):
    """Remove uma distribuição de funcionário via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        distribuicao = get_object_or_404(DistribuicaoFuncionario, pk=pk)
        distribuicao.delete()
        return json_success(message='Distribuição removida com sucesso!')
    except Exception as e:
        return json_error(f'Erro ao remover distribuição: {str(e)}')


@login_required
@admin_required
def salvar_valor_estelar_ajax(request):
    """Salva o valor Estelar via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        if valor < 0:
            return json_error('Valor não pode ser negativo')
        acerto.valor_estelar = valor
        acerto.save()
        return json_success(message='Valor Estelar salvo com sucesso!', valor=str(valor))
    except Exception as e:
        return json_error(f'Erro ao salvar valor Estelar: {str(e)}')
