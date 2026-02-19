"""
Views de totalizador por estado e por cliente (apenas administradores).
"""
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages

from ..models import RomaneioViagem, TabelaSeguro
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso


@admin_required
def totalizador_por_estado(request):
    """View para totalizador por estado com filtros de data"""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    data_inicial_obj = parse_date_iso(data_inicial)
    data_final_obj = parse_date_iso(data_final)
    if data_inicial_obj and data_final_obj:
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        estados_agrupados = {}
        
        for romaneio in romaneios_periodo:
            estado_cliente = romaneio.cliente.estado
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
    elif data_inicial or data_final:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
    
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
    """Gera PDF do totalizador por estado"""
    return totalizador_por_estado(request)


@admin_required
def totalizador_por_estado_excel(request):
    """Gera Excel do totalizador por estado"""
    messages.info(request, 'Exportação para Excel em desenvolvimento')
    return redirect('notas:totalizador_por_estado')


@admin_required
def totalizador_por_cliente(request):
    """View para totalizador por cliente com filtros de data"""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    data_inicial_obj = parse_date_iso(data_inicial)
    data_final_obj = parse_date_iso(data_final)
    if data_inicial_obj and data_final_obj:
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        clientes_agrupados = {}
        
        for romaneio in romaneios_periodo:
            cliente = romaneio.cliente
            if cliente.id not in clientes_agrupados:
                clientes_agrupados[cliente.id] = {
                    'cliente': cliente,
                    'total_valor': Decimal('0.0'),
                    'romaneios_ids': set(),
                    'estados_envolvidos': set()
                }
            
            for nota in romaneio.notas_fiscais.all():
                clientes_agrupados[cliente.id]['total_valor'] += nota.valor
            
            clientes_agrupados[cliente.id]['romaneios_ids'].add(romaneio.id)
            if cliente.estado:
                clientes_agrupados[cliente.id]['estados_envolvidos'].add(cliente.estado)
        
        for cliente_id, dados in clientes_agrupados.items():
            total_valor_cliente = dados['total_valor']
            quantidade_romaneios = len(dados['romaneios_ids'])
            cliente = dados['cliente']
            percentual_seguro = tabelas_seguro.get(cliente.estado, Decimal('0.0')) if cliente.estado else Decimal('0.0')
            valor_seguro_cliente = total_valor_cliente * (percentual_seguro / Decimal('100.0'))
            
            if total_valor_cliente > 0:
                resultados.append({
                    'cliente': cliente,
                    'total_valor': total_valor_cliente,
                    'percentual_seguro': percentual_seguro,
                    'valor_seguro': valor_seguro_cliente,
                    'quantidade_romaneios': quantidade_romaneios,
                    'estados_envolvidos': list(dados['estados_envolvidos'])
                })
                total_geral += total_valor_cliente
                total_seguro_geral += valor_seguro_cliente
        
        resultados.sort(key=lambda x: x['total_valor'], reverse=True)
    elif data_inicial or data_final:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
    
    context = {
        'data_inicial': data_inicial,
        'data_final': data_final,
        'resultados': resultados,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
        'tem_resultados': len(resultados) > 0
    }
    return render(request, 'notas/totalizador_por_cliente.html', context)


@admin_required
def totalizador_por_cliente_pdf(request):
    """Gera PDF do totalizador por cliente"""
    return totalizador_por_cliente(request)


@admin_required
def totalizador_por_cliente_excel(request):
    """Gera Excel do totalizador por cliente"""
    messages.info(request, 'Exportação para Excel em desenvolvimento')
    return redirect('notas:totalizador_por_cliente')
