"""
Views de totalizador por estado e por cliente (apenas administradores).
"""
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages

from ..models import RomaneioViagem, TabelaSeguro
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso


def _obter_dados_totalizador_estado(data_inicial_str, data_final_str):
    """
    Retorna (resultados, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj)
    para o período informado. Se datas inválidas ou vazias, retorna (None, None, None, None, None).
    """
    data_inicial_obj = parse_date_iso(data_inicial_str or '')
    data_final_obj = parse_date_iso(data_final_str or '')
    if not data_inicial_obj or not data_final_obj:
        return None, None, None, None, None

    romaneios_periodo = RomaneioViagem.objects.filter(
        data_emissao__date__range=[data_inicial_obj, data_final_obj],
        status='Emitido'
    ).select_related('cliente').prefetch_related('notas_fiscais')

    tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
    estados_agrupados = {}

    for romaneio in romaneios_periodo:
        estado_cliente = romaneio.cliente.estado if romaneio.cliente else None
        if not estado_cliente:
            continue
        if estado_cliente not in estados_agrupados:
            estados_agrupados[estado_cliente] = {
                'estado': estado_cliente,
                'nome_estado': dict(TabelaSeguro.ESTADOS_BRASIL).get(estado_cliente, estado_cliente),
                'total_valor': Decimal('0.0'),
                'quantidade_romaneios': 0,
                'romaneios_ids': set()
            }
        for nota in romaneio.notas_fiscais.all():
            estados_agrupados[estado_cliente]['total_valor'] += nota.valor
        estados_agrupados[estado_cliente]['romaneios_ids'].add(romaneio.id)

    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    for estado, dados in estados_agrupados.items():
        total_valor_estado = dados['total_valor']
        quantidade_romaneios = len(dados['romaneios_ids'])
        percentual_seguro = tabelas_seguro.get(estado, Decimal('0.0'))
        valor_seguro_estado = total_valor_estado * (percentual_seguro / Decimal('100.0'))
        if total_valor_estado > 0:
            resultados.append({
                'estado': estado,
                'nome_estado': dados['nome_estado'],
                'total_valor': total_valor_estado,
                'percentual_seguro': percentual_seguro,
                'valor_seguro': valor_seguro_estado,
                'quantidade_romaneios': quantidade_romaneios
            })
            total_geral += total_valor_estado
            total_seguro_geral += valor_seguro_estado
    resultados.sort(key=lambda x: x['total_valor'], reverse=True)
    return resultados, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj


@admin_required
def totalizador_por_estado(request):
    """View para totalizador por estado com filtros de data"""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')

    resultados, total_geral, total_seguro_geral, _di, _df = _obter_dados_totalizador_estado(data_inicial, data_final)
    if resultados is None:
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')
        if data_inicial or data_final:
            messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
    elif not (data_inicial and data_final):
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')

    context = {
        'data_inicial': data_inicial,
        'data_final': data_final,
        'resultados': resultados,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
        'tem_resultados': len(resultados) > 0
    }
    return render(request, 'notas/totalizador_por_estado.html', context)


@admin_required
def totalizador_por_estado_pdf(request):
    """
    Exibe o relatório Totalizador por Estado em página limpa (sem menu/navbar).
    Abre em nova aba para impressão ou salvar como PDF, com o mesmo padrão do relatório por cliente.
    """
    from datetime import datetime

    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_estado')

    resultados, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj = _obter_dados_totalizador_estado(
        data_inicial, data_final
    )
    if resultados is None:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_estado')

    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    context = {
        'titulo_relatorio': 'RELATÓRIO DE TOTAIS POR ESTADO',
        'resultados': resultados,
        'data_inicio': data_inicial_obj.strftime('%d/%m/%Y'),
        'data_fim': data_final_obj.strftime('%d/%m/%Y'),
        'data_geracao': data_geracao,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
    }
    response = render(request, 'notas/relatorio_totalizador_estado_pdf.html', context)
    response['Content-Disposition'] = 'inline'
    return response


@admin_required
def totalizador_por_estado_excel(request):
    """Gera Excel do totalizador por estado."""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_estado')

    resultados, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj = _obter_dados_totalizador_estado(
        data_inicial, data_final
    )
    if resultados is None:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_estado')

    try:
        from ..utils.relatorios import gerar_relatorio_excel_totalizador_estado, gerar_resposta_excel
        excel_content = gerar_relatorio_excel_totalizador_estado(
            resultados, data_inicial_obj, data_final_obj, total_geral, total_seguro_geral
        )
        nome_arquivo = f"totalizador_por_estado_{data_inicial}_{data_final}.xlsx"
        return gerar_resposta_excel(excel_content, nome_arquivo)
    except ImportError:
        messages.error(
            request,
            'Biblioteca openpyxl não encontrada. Instale com: pip install openpyxl'
        )
        return redirect('notas:totalizador_por_estado')


def _obter_dados_totalizador_cliente(data_inicial_str, data_final_str):
    """
    Retorna (resultados, totais_por_estado, total_geral, total_seguro_geral,
             data_inicial_obj, data_final_obj, nomes_estados).
    Se datas inválidas ou vazias, retorna (None, None, None, None, None, None, None).
    """
    data_inicial_obj = parse_date_iso(data_inicial_str or '')
    data_final_obj = parse_date_iso(data_final_str or '')
    if not data_inicial_obj or not data_final_obj:
        return None, None, None, None, None, None, None

    romaneios_periodo = RomaneioViagem.objects.filter(
        data_emissao__date__range=[data_inicial_obj, data_final_obj],
        status='Emitido'
    ).select_related('cliente').prefetch_related('notas_fiscais')

    tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
    clientes_agrupados = {}
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    nomes_estados = dict(TabelaSeguro.ESTADOS_BRASIL)

    for romaneio in romaneios_periodo:
        cliente = romaneio.cliente
        if not cliente:
            continue
        if cliente.id not in clientes_agrupados:
            clientes_agrupados[cliente.id] = {
                'cliente': cliente,
                'total_valor': Decimal('0.0'),
            }
        for nota in romaneio.notas_fiscais.all():
            clientes_agrupados[cliente.id]['total_valor'] += nota.valor

    for cliente_id, dados in clientes_agrupados.items():
        total_valor_cliente = dados['total_valor']
        cliente = dados['cliente']
        percentual_seguro = tabelas_seguro.get(cliente.estado or '', Decimal('0.0'))
        valor_seguro_cliente = total_valor_cliente * (percentual_seguro / Decimal('100.0'))
        if total_valor_cliente > 0:
            resultados.append({
                'cliente': cliente,
                'uf': cliente.estado or '—',
                'valor_mercadoria': total_valor_cliente,
                'valor_seguro': valor_seguro_cliente,
            })
            total_geral += total_valor_cliente
            total_seguro_geral += valor_seguro_cliente

    resultados.sort(key=lambda x: ((x['uf'] or '').upper(), (x['cliente'].razao_social or '').upper()))
    totais_por_estado = {}
    for r in resultados:
        uf = r['uf']
        if uf not in totais_por_estado:
            totais_por_estado[uf] = {'valor_mercadoria': Decimal('0.0'), 'valor_seguro': Decimal('0.0')}
        totais_por_estado[uf]['valor_mercadoria'] += r['valor_mercadoria']
        totais_por_estado[uf]['valor_seguro'] += r['valor_seguro']

    return resultados, totais_por_estado, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj, nomes_estados


@admin_required
def totalizador_por_cliente(request):
    """
    Tela com filtro de período, botão Pesquisar para exibir dados na tela
    e botões para gerar PDF ou Excel.
    """
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    totais_por_estado = {}
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    nomes_estados = {}

    if data_inicial and data_final:
        out = _obter_dados_totalizador_cliente(data_inicial, data_final)
        if out[0] is not None:
            resultados, totais_por_estado, total_geral, total_seguro_geral, _di, _df, nomes_estados = out
        elif data_inicial or data_final:
            messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')

    context = {
        'data_inicial': data_inicial,
        'data_final': data_final,
        'resultados': resultados,
        'totais_por_estado': totais_por_estado,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
        'nomes_estados': nomes_estados,
        'tem_resultados': len(resultados) > 0,
    }
    return render(request, 'notas/totalizador_por_cliente.html', context)


@admin_required
def totalizador_por_cliente_pdf(request):
    """
    Exibe o relatório Totalizador por Cliente em página limpa (sem menu/navbar).
    Abre em nova aba apenas o relatório para impressão ou salvar como PDF.
    """
    from datetime import datetime

    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')

    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_cliente')

    out = _obter_dados_totalizador_cliente(data_inicial, data_final)
    if out[0] is None:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_cliente')

    resultados, totais_por_estado, total_geral, total_seguro_geral, data_inicial_obj, data_final_obj, nomes_estados = out
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    context = {
        'titulo_relatorio': 'RELATÓRIO DE TOTAIS POR CLIENTE',
        'resultados': resultados,
        'totais_por_estado': totais_por_estado,
        'nomes_estados': nomes_estados,
        'data_inicio': data_inicial_obj.strftime('%d/%m/%Y'),
        'data_fim': data_final_obj.strftime('%d/%m/%Y'),
        'data_geracao': data_geracao,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
    }
    response = render(request, 'notas/relatorio_totalizador_cliente_pdf.html', context)
    response['Content-Disposition'] = 'inline'
    return response


@admin_required
def totalizador_por_cliente_excel(request):
    """Gera Excel do totalizador por cliente"""
    messages.info(request, 'Exportação para Excel em desenvolvimento')
    return redirect('notas:totalizador_por_cliente')
