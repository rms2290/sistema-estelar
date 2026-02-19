"""
Views de movimento de caixa: listar, gerenciar, CRUD movimento e acumulado.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from sistema_estelar.api_utils import json_success, json_error
from django.utils import timezone

from notas.decorators import admin_required
from notas.models import Cliente
from financeiro.models import (
    MovimentoCaixaFuncionario,
    MovimentoBancario,
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
    FuncionarioFluxoCaixa,
)
from financeiro.services import MovimentoCaixaService, PeriodoCaixaService

logger = logging.getLogger(__name__)


@login_required
@admin_required
def movimento_caixa(request):
    """Lista todos os movimentos de caixa (funcionários e bancários)"""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    tipo = request.GET.get('tipo', '')

    movimentos_funcionarios = MovimentoCaixaFuncionario.objects.all().select_related(
        'caixa_funcionario__funcionario'
    ).order_by('-data', '-id')
    movimentos_bancarios = MovimentoBancario.objects.all().order_by('-data', '-id')

    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentos_funcionarios = movimentos_funcionarios.filter(data__gte=data_inicio_obj)
            movimentos_bancarios = movimentos_bancarios.filter(data__gte=data_inicio_obj)
        except Exception as e:
            logger.warning('Filtro data_inicio inválido em movimento_caixa: %s', e)
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentos_funcionarios = movimentos_funcionarios.filter(data__lte=data_fim_obj)
            movimentos_bancarios = movimentos_bancarios.filter(data__lte=data_fim_obj)
        except Exception as e:
            logger.warning('Filtro data_fim inválido em movimento_caixa: %s', e)
    if tipo == 'funcionario':
        movimentos_bancarios = movimentos_bancarios.none()
    elif tipo == 'bancario':
        movimentos_funcionarios = movimentos_funcionarios.none()

    movimentos_combinados = []
    for mov in movimentos_funcionarios:
        movimentos_combinados.append({
            'tipo': 'funcionario',
            'data': mov.data,
            'descricao': mov.descricao,
            'valor': mov.valor,
            'funcionario': mov.caixa_funcionario.funcionario.nome if mov.caixa_funcionario.funcionario else 'N/A',
            'id': mov.id,
            'objeto': mov
        })
    for mov in movimentos_bancarios:
        movimentos_combinados.append({
            'tipo': 'bancario',
            'data': mov.data,
            'descricao': mov.descricao,
            'valor': mov.valor if mov.tipo == 'Credito' else -mov.valor,
            'tipo_movimento': mov.tipo,
            'id': mov.id,
            'objeto': mov
        })
    movimentos_combinados.sort(key=lambda x: (x['data'], x['id']), reverse=True)
    total = sum(mov['valor'] for mov in movimentos_combinados)

    return render(request, 'financeiro/fluxo_caixa/movimento_caixa.html', {
        'movimentos': movimentos_combinados,
        'total': total,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo_selecionado': tipo,
    })


@login_required
@admin_required
def gerenciar_movimento_caixa(request):
    """Tela principal para gerenciar movimentos de caixa"""
    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if periodo_ativo:
        periodo_ativo._movimentos_count = periodo_ativo.movimentos.count()

    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    tipo = request.GET.get('tipo', '')
    categoria = request.GET.get('categoria', '')
    periodo_id = request.GET.get('periodo_id', '')
    if periodo_ativo and not periodo_id:
        periodo_id = str(periodo_ativo.pk)

    if periodo_id:
        try:
            periodo_selecionado = PeriodoMovimentoCaixa.objects.get(pk=periodo_id)
            movimentos = MovimentoCaixa.objects.filter(
                periodo=periodo_selecionado
            ).select_related(
                'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao', 'periodo'
            ).order_by('data', 'criado_em')
        except PeriodoMovimentoCaixa.DoesNotExist:
            movimentos = MovimentoCaixa.objects.none()
            periodo_selecionado = None
    else:
        movimentos = MovimentoCaixa.objects.none()
        periodo_selecionado = None

    if data_inicio:
        try:
            movimentos = movimentos.filter(data__gte=datetime.strptime(data_inicio, '%Y-%m-%d').date())
        except Exception as e:
            logger.warning('Filtro data_inicio inválido em gerenciar_movimento_caixa: %s', e)
    if data_fim:
        try:
            movimentos = movimentos.filter(data__lte=datetime.strptime(data_fim, '%Y-%m-%d').date())
        except Exception as e:
            logger.warning('Filtro data_fim inválido em gerenciar_movimento_caixa: %s', e)
    if tipo:
        movimentos = movimentos.filter(tipo=tipo)
    if categoria:
        movimentos = movimentos.filter(categoria=categoria)

    valor_inicial = periodo_selecionado.valor_inicial_caixa if periodo_selecionado else Decimal('0.00')
    movimentos_lista = list(movimentos)
    saldo_acumulado = valor_inicial
    movimentos_com_saldo = []
    for mov in movimentos_lista:
        if mov.is_entrada:
            saldo_acumulado += mov.valor
        else:
            saldo_acumulado -= mov.valor
        movimentos_com_saldo.append({'movimento': mov, 'saldo_acumulado': saldo_acumulado})

    total_entradas = sum(mov.valor for mov in movimentos if mov.is_entrada)
    total_saidas = sum(mov.valor for mov in movimentos if mov.is_saida)
    saldo = valor_inicial + total_entradas - total_saidas

    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    periodos = PeriodoMovimentoCaixa.objects.all().order_by('-data_inicio', '-criado_em')

    return render(request, 'financeiro/fluxo_caixa/gerenciar_movimento_caixa.html', {
        'periodo_ativo': periodo_ativo,
        'periodo_selecionado': periodo_selecionado,
        'periodos': periodos,
        'movimentos': movimentos,
        'movimentos_com_saldo': movimentos_com_saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'valor_inicial_caixa': valor_inicial,
        'saldo': saldo,
        'funcionarios': funcionarios,
        'clientes': clientes,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo_selecionado': tipo,
        'categoria_selecionada': categoria,
        'periodo_id': periodo_id,
        'tipos': MovimentoCaixa.TIPO_CHOICES,
        'categorias_entrada': MovimentoCaixa.CATEGORIA_ENTRADA_CHOICES,
        'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
    })


@login_required
@admin_required
def criar_movimento_caixa_ajax(request):
    """Cria um novo movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        data = request.POST.get('data')
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        categoria = request.POST.get('categoria', '')
        funcionario_id = request.POST.get('funcionario_id', '') or None
        cliente_id = request.POST.get('cliente_id', '') or None
        acerto_diario_id = request.POST.get('acerto_diario_id', '') or None
        movimento, erro = MovimentoCaixaService.criar_movimento(
            data=data,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
            acerto_diario_id=acerto_diario_id,
            usuario=request.user,
        )
        if erro:
            return json_error(erro)
        logger.info('Movimento de caixa criado: movimento_id=%s tipo=%s valor=%s usuario=%s', movimento.pk, tipo, valor, request.user.username)
        return json_success(message='Movimento criado com sucesso!', movimento_id=movimento.pk)
    except Exception as e:
        logger.error('Erro ao criar movimento: %s', str(e), exc_info=True)
        return json_error(f'Erro ao criar movimento: {str(e)}')


@login_required
@admin_required
def editar_movimento_caixa_ajax(request, pk):
    """Edita um movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        data = request.POST.get('data')
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        categoria = request.POST.get('categoria', '')
        funcionario_id = request.POST.get('funcionario_id', '') or None
        cliente_id = request.POST.get('cliente_id', '') or None
        movimento, erro = MovimentoCaixaService.editar_movimento(
            movimento,
            data=data,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
        )
        if erro:
            return json_error(erro)
        logger.info('Movimento de caixa editado: movimento_id=%s usuario=%s', pk, request.user.username)
        return json_success(message='Movimento atualizado com sucesso!')
    except Exception as e:
        logger.error('Erro ao editar movimento: %s', str(e), exc_info=True)
        return json_error(f'Erro ao editar movimento: {str(e)}')


@login_required
@admin_required
def excluir_movimento_caixa_ajax(request, pk):
    """Exclui um movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        _, erro = MovimentoCaixaService.excluir_movimento(movimento)
        if erro:
            return json_error(erro)
        logger.info('Movimento de caixa excluído: movimento_id=%s usuario=%s', pk, request.user.username)
        return json_success(message='Movimento excluído com sucesso!')
    except Exception as e:
        logger.error('Erro ao excluir movimento: %s', str(e), exc_info=True)
        return json_error(f'Erro ao excluir movimento: {str(e)}')


@login_required
@admin_required
def obter_acumulado_funcionario_ajax(request, funcionario_id):
    """Obtém o valor acumulado de um funcionário via AJAX"""
    try:
        valor_acumulado = MovimentoCaixaService.obter_acumulado_funcionario(funcionario_id)
        return json_success(valor_acumulado=str(valor_acumulado))
    except Exception as e:
        return json_error(f'Erro ao obter acumulado: {str(e)}')


@login_required
@admin_required
def obter_movimento_caixa_ajax(request, pk):
    """Obtém dados de um movimento de caixa via AJAX para edição"""
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        return json_success(
            data=movimento.data.strftime('%Y-%m-%d'),
            tipo=movimento.tipo,
            valor=str(movimento.valor),
            descricao=movimento.descricao,
            categoria=movimento.categoria or '',
            funcionario_id=movimento.funcionario_id or '',
            cliente_id=movimento.cliente_id or '',
        )
    except Exception as e:
        return json_error(f'Erro ao obter movimento: {str(e)}')
