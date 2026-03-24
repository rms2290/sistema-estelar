"""
Views de período de caixa: iniciar, pesquisar, visualizar, imprimir, fechar/editar/obter/excluir.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from sistema_estelar.api_utils import json_success, json_error
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from notas.decorators import admin_required
from financeiro.models import MovimentoCaixa, PeriodoMovimentoCaixa
from financeiro.services import PeriodoCaixaService

logger = logging.getLogger(__name__)


def _format_data_periodo(data):
    """Formata data de período aceitando date ou string ISO."""
    if hasattr(data, 'strftime'):
        return data.strftime('%d/%m/%Y')
    if isinstance(data, str):
        data_obj = parse_date(data)
        if data_obj:
            return data_obj.strftime('%d/%m/%Y')
    return str(data)


def _parse_decimal_br(valor_str):
    """
    Converte string monetária em Decimal aceitando formato brasileiro.
    Exemplos aceitos: "1000", "1000.50", "1.000,50", "1000,50".
    """
    if valor_str is None:
        return Decimal('0.00')
    texto = str(valor_str).strip()
    if not texto:
        return Decimal('0.00')
    texto = texto.replace(' ', '').replace('R$', '').replace('r$', '')

    # Casos com vírgula decimal (pt-BR): "1.234,56" / "1000,50"
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
        return Decimal(texto)

    # Casos apenas com ponto:
    # - "1000.50" (decimal com ponto) -> mantém
    # - "1.000" / "12.345.678" (milhar pt-BR) -> remove separadores
    if '.' in texto:
        partes = texto.split('.')
        if all(parte.isdigit() for parte in partes):
            # Se último grupo tem 3 dígitos e os grupos intermediários também,
            # tratamos como separador de milhar.
            if len(partes[-1]) == 3 and all(len(parte) == 3 for parte in partes[1:]):
                texto = ''.join(partes)

    return Decimal(texto)


@login_required
@admin_required
def iniciar_periodo_movimento_caixa(request):
    """Inicia um novo período de movimento de caixa"""
    if request.method == 'POST':
        try:
            data_inicio = request.POST.get('data_inicio', '')
            valor_inicial = _parse_decimal_br(request.POST.get('valor_inicial_caixa', '0.00'))
            observacoes = request.POST.get('observacoes', '').strip()
            periodo, erro = PeriodoCaixaService.iniciar_periodo(
                data_inicio=data_inicio,
                valor_inicial_caixa=valor_inicial,
                observacoes=observacoes,
                usuario=request.user,
            )
            if erro:
                if 'Data de início' in erro:
                    messages.error(request, erro)
                else:
                    messages.warning(request, erro)
                return redirect('financeiro:gerenciar_movimento_caixa')
            periodo_nome = _format_data_periodo(periodo.data_inicio)
            logger.info('Período de caixa iniciado: periodo_id=%s data=%s usuario=%s', periodo.pk, periodo_nome, request.user.username)
            messages.success(request, f'Período de {periodo_nome} iniciado com sucesso!')
            return redirect(f"{reverse('financeiro:gerenciar_movimento_caixa')}?periodo_id={periodo.pk}")
        except Exception as e:
            logger.error(f'Erro ao iniciar período: {str(e)}', exc_info=True)
            messages.error(request, f'Erro ao iniciar período: {str(e)}')
            return redirect('financeiro:gerenciar_movimento_caixa')
    return render(request, 'financeiro/fluxo_caixa/iniciar_periodo_movimento_caixa.html', {
        'data_inicio': timezone.now().date().isoformat()
    })


@login_required
@admin_required
def fechar_periodo_movimento_caixa_ajax(request, pk):
    """Fecha um período de movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        ok, erro = PeriodoCaixaService.fechar_periodo(periodo)
        if erro:
            return json_error(erro)
        periodo_nome = _format_data_periodo(periodo.data_inicio)
        logger.info('Período de caixa fechado: periodo_id=%s data=%s usuario=%s', periodo.pk, periodo_nome, request.user.username)
        return json_success(message=f'Período de {periodo_nome} fechado com sucesso!')
    except Exception as e:
        logger.error('Erro ao fechar período: %s', str(e), exc_info=True)
        return json_error(f'Erro ao fechar período: {str(e)}')


@login_required
@admin_required
def editar_periodo_movimento_caixa_ajax(request, pk):
    """Edita um período de movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        data_inicio = request.POST.get('data_inicio', '')
        valor_inicial = _parse_decimal_br(request.POST.get('valor_inicial_caixa', '0.00'))
        observacoes = request.POST.get('observacoes', '').strip()
        periodo, erro = PeriodoCaixaService.editar_periodo(
            periodo, data_inicio, valor_inicial, observacoes
        )
        if erro:
            return json_error(erro)
        periodo_nome = _format_data_periodo(periodo.data_inicio)
        return json_success(message=f'Período de {periodo_nome} atualizado com sucesso!')
    except Exception as e:
        logger.error(f'Erro ao editar período: {str(e)}', exc_info=True)
        return json_error(f'Erro ao editar período: {str(e)}')


@login_required
@admin_required
def obter_periodo_movimento_caixa_ajax(request, pk):
    """Obtém dados de um período de movimento de caixa via AJAX para edição"""
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        return json_success(
            data={
                'data_inicio': periodo.data_inicio.strftime('%Y-%m-%d'),
                'valor_inicial_caixa': str(periodo.valor_inicial_caixa),
                'observacoes': periodo.observacoes or '',
                'status': periodo.status,
                'tem_movimentos': periodo.movimentos.exists()
            }
        )
    except Exception as e:
        return json_error(f'Erro ao obter período: {str(e)}')


@login_required
@admin_required
def excluir_periodo_movimento_caixa_ajax(request, pk):
    """Exclui um período de movimento de caixa via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        periodo_nome = _format_data_periodo(periodo.data_inicio)
        movimentos_count, erro = PeriodoCaixaService.excluir_periodo(periodo)
        if erro:
            return json_error(erro)
        if movimentos_count > 0:
            return json_success(
                message=f'Período de {periodo_nome} e seus {movimentos_count} movimento(s) foram excluídos com sucesso!'
            )
        return json_success(message=f'Período de {periodo_nome} excluído com sucesso!')
    except Exception as e:
        logger.error(f'Erro ao excluir período: {str(e)}', exc_info=True)
        return json_error(f'Erro ao excluir período: {str(e)}')


@login_required
@admin_required
def pesquisar_periodo_movimento_caixa(request):
    """Página para pesquisar e listar períodos de movimento de caixa. Para uso no fechamento, use ?status=Fechado."""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')
    periodos = PeriodoMovimentoCaixa.objects.all()
    if data_inicio:
        try:
            periodos = periodos.filter(data_inicio__gte=datetime.strptime(data_inicio, '%Y-%m-%d').date())
        except Exception as e:
            logger.warning('Filtro data_inicio inválido em pesquisar_periodos: %s', e)
    if data_fim:
        try:
            periodos = periodos.filter(data_inicio__lte=datetime.strptime(data_fim, '%Y-%m-%d').date())
        except Exception as e:
            logger.warning('Filtro data_fim inválido em pesquisar_periodos: %s', e)
    if status:
        periodos = periodos.filter(status=status)
    periodos = periodos.order_by('-data_inicio', '-criado_em')
    periodos_com_totais = []
    for periodo in periodos:
        periodos_com_totais.append({
            'periodo': periodo,
            'movimentos_count': periodo.movimentos.count(),
            'total_entradas': getattr(periodo, 'total_entradas', Decimal('0')),
            'total_saidas': getattr(periodo, 'total_saidas', Decimal('0')),
            'saldo_atual': getattr(periodo, 'saldo_atual', Decimal('0')),
        })
    return render(request, 'financeiro/fluxo_caixa/pesquisar_periodos.html', {
        'periodos': periodos_com_totais,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_selecionado': status,
        'status_choices': PeriodoMovimentoCaixa.STATUS_CHOICES,
    })


@login_required
@admin_required
def visualizar_periodo_movimento_caixa(request, pk):
    """Visualiza detalhes de um período de movimento de caixa"""
    periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
    movimentos = MovimentoCaixa.objects.filter(
        periodo=periodo
    ).select_related(
        'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao'
    ).order_by('data', 'criado_em')
    # Mesma regra da tela Gerenciar Movimento: AcertoFuncionario sem acerto_diario = saída
    def _eh_saida_na_tela(mov):
        if mov.tipo == 'Saida':
            return True
        if mov.tipo == 'AcertoFuncionario' and not mov.acerto_diario_id:
            return True
        return False
    movimentos_lista = list(movimentos)
    movimentos_com_saldo = []
    saldo_acumulado = periodo.valor_inicial_caixa
    for mov in movimentos_lista:
        if _eh_saida_na_tela(mov):
            saldo_acumulado -= mov.valor
        else:
            saldo_acumulado += mov.valor
        movimentos_com_saldo.append({
            'movimento': mov,
            'saldo_acumulado': saldo_acumulado,
            'exibir_como_saida': _eh_saida_na_tela(mov),
        })
    total_entradas = sum(mov.valor for mov in movimentos_lista if not _eh_saida_na_tela(mov))
    total_saidas = sum(mov.valor for mov in movimentos_lista if _eh_saida_na_tela(mov))
    saldo = periodo.valor_inicial_caixa + total_entradas - total_saidas
    return render(request, 'financeiro/fluxo_caixa/visualizar_periodo_movimento_caixa.html', {
        'periodo': periodo,
        'movimentos_com_saldo': movimentos_com_saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'valor_inicial_caixa': periodo.valor_inicial_caixa,
        'saldo': saldo,
        'total_movimentos': len(movimentos_lista),
    })


@login_required
@admin_required
def imprimir_periodo_movimento_caixa(request, pk):
    """Gera relatório de impressão do período de movimento de caixa"""
    periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
    movimentos = MovimentoCaixa.objects.filter(
        periodo=periodo
    ).select_related(
        'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao'
    ).order_by('data', 'criado_em')
    # Mesma regra da tela Gerenciar Movimento: AcertoFuncionario sem acerto_diario = saída
    def _eh_saida_na_tela(mov):
        if mov.tipo == 'Saida':
            return True
        if mov.tipo == 'AcertoFuncionario' and not mov.acerto_diario_id:
            return True
        return False
    movimentos_lista = list(movimentos)
    movimentos_com_saldo = []
    saldo_acumulado = periodo.valor_inicial_caixa
    for mov in movimentos_lista:
        if _eh_saida_na_tela(mov):
            saldo_acumulado -= mov.valor
        else:
            saldo_acumulado += mov.valor
        movimentos_com_saldo.append({
            'movimento': mov,
            'saldo_acumulado': saldo_acumulado,
            'exibir_como_saida': _eh_saida_na_tela(mov),
        })
    total_entradas = sum(mov.valor for mov in movimentos_lista if not _eh_saida_na_tela(mov))
    total_saidas = sum(mov.valor for mov in movimentos_lista if _eh_saida_na_tela(mov))
    saldo = periodo.valor_inicial_caixa + total_entradas - total_saidas
    return render(request, 'financeiro/fluxo_caixa/imprimir_periodo_movimento_caixa.html', {
        'periodo': periodo,
        'movimentos_com_saldo': movimentos_com_saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'valor_inicial_caixa': periodo.valor_inicial_caixa,
        'saldo': saldo,
        'total_movimentos': len(movimentos_lista),
    })
