"""
Views de Relatórios (apenas para administradores)
"""
import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q, Count
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from datetime import datetime, date

from ..models import RomaneioViagem, Cliente, TabelaSeguro
from .base import is_admin

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
@user_passes_test(is_admin)
def totalizador_por_estado(request):
    """View para totalizador por estado com filtros de data"""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    if data_inicial and data_final:
        try:
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
            
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
            
        except ValueError:
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


@login_required
@user_passes_test(is_admin)
def totalizador_por_estado_pdf(request):
    """Gera PDF do totalizador por estado"""
    # Implementação básica - pode ser expandida
    return totalizador_por_estado(request)


@login_required
@user_passes_test(is_admin)
def totalizador_por_estado_excel(request):
    """Gera Excel do totalizador por estado"""
    # Implementação básica - pode ser expandida
    messages.info(request, 'Exportação para Excel em desenvolvimento')
    return redirect('notas:totalizador_por_estado')


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente(request):
    """View para totalizador por cliente com filtros de data"""
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    if data_inicial and data_final:
        try:
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
            
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
                
                percentual_seguro = Decimal('0.0')
                if cliente.estado:
                    percentual_seguro = tabelas_seguro.get(cliente.estado, Decimal('0.0'))
                
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
            
        except ValueError:
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


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente_pdf(request):
    """Gera PDF do totalizador por cliente"""
    # Implementação básica - pode ser expandida
    return totalizador_por_cliente(request)


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente_excel(request):
    """Gera Excel do totalizador por cliente"""
    # Implementação básica - pode ser expandida
    messages.info(request, 'Exportação para Excel em desenvolvimento')
    return redirect('notas:totalizador_por_cliente')


@login_required
@user_passes_test(is_admin)
def fechamento_frete(request):
    """View para listar fechamentos de frete com filtros de pesquisa"""
    from ..models import FechamentoFrete, Motorista, Cliente
    from django.db.models import Q
    
    fechamentos = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related('romaneios', 'itens', 'itens__cliente_consolidado')
    
    # Filtros
    motorista_id = request.GET.get('motorista')
    cliente_id = request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    valor_min = request.GET.get('valor_min')
    valor_max = request.GET.get('valor_max')
    
    # Aplicar filtros
    if motorista_id:
        fechamentos = fechamentos.filter(motorista_id=motorista_id)
    
    if cliente_id:
        # Filtrar por cliente através dos itens
        fechamentos = fechamentos.filter(itens__cliente_consolidado_id=cliente_id).distinct()
    
    if data_inicio:
        try:
            from datetime import datetime
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            fechamentos = fechamentos.filter(data__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            from datetime import datetime
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            fechamentos = fechamentos.filter(data__lte=data_fim_obj)
        except ValueError:
            pass
    
    if valor_min:
        try:
            valor_min_decimal = Decimal(valor_min)
            fechamentos = fechamentos.filter(frete_total__gte=valor_min_decimal)
        except (ValueError, InvalidOperation):
            pass
    
    if valor_max:
        try:
            valor_max_decimal = Decimal(valor_max)
            fechamentos = fechamentos.filter(frete_total__lte=valor_max_decimal)
        except (ValueError, InvalidOperation):
            pass
    
    # Ordenar
    fechamentos = fechamentos.order_by('-data', '-data_criacao')
    
    # Buscar listas para os filtros
    motoristas = Motorista.objects.all().order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    
    context = {
        'fechamentos': fechamentos,
        'motoristas': motoristas,
        'clientes': clientes,
    }
    
    return render(request, 'notas/relatorios/fechamento_frete.html', context)


@login_required
@user_passes_test(is_admin)
def criar_fechamento_frete(request):
    """View para criar novo fechamento de frete"""
    from ..models import FechamentoFrete, ItemFechamentoFrete, DetalheItemFechamento, RomaneioViagem
    from ..forms import FechamentoFreteForm, ItemFechamentoFreteForm
    from django.db import transaction
    from collections import defaultdict
    
    if request.method == 'POST':
        form = FechamentoFreteForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar fechamento
                    fechamento = form.save(commit=False)
                    fechamento.usuario_criacao = request.user
                    fechamento.origem_romaneio = bool(request.POST.getlist('romaneios_selecionados'))
                    fechamento.save()
                    
                    # Adicionar romaneios
                    romaneios_ids = request.POST.getlist('romaneios_selecionados')
                    if romaneios_ids:
                        romaneios = RomaneioViagem.objects.filter(pk__in=romaneios_ids)
                        fechamento.romaneios.set(romaneios)
                    
                    # Processar itens (clientes)
                    # Formato: item_cliente_0, item_peso_0, item_cubagem_0, etc.
                    item_count = 0
                    while f'item_cliente_{item_count}' in request.POST:
                        cliente_id = request.POST.get(f'item_cliente_{item_count}')
                        peso = request.POST.get(f'item_peso_{item_count}')
                        cubagem = request.POST.get(f'item_cubagem_{item_count}')
                        valor = request.POST.get(f'item_valor_{item_count}')
                        romaneios_item_str = request.POST.get(f'item_romaneios_{item_count}', '')
                        percentual_escolhido = request.POST.get(f'item_percentual_escolhido_{item_count}', '6')
                        percentual_ajustado = request.POST.get(f'item_percentual_ajustado_{item_count}', '')
                        usar_ajuste = request.POST.get(f'item_usar_ajuste_{item_count}') == 'on'
                        observacoes = request.POST.get(f'item_observacoes_{item_count}', '')
                        
                        # Processar romaneios (pode vir como string separada por vírgula ou como lista)
                        romaneios_item = []
                        if romaneios_item_str:
                            # Se for string separada por vírgula, converter para lista
                            if ',' in romaneios_item_str:
                                romaneios_item = [int(id.strip()) for id in romaneios_item_str.split(',') if id.strip().isdigit()]
                            else:
                                # Se for um único ID
                                try:
                                    romaneios_item = [int(romaneios_item_str)]
                                except ValueError:
                                    romaneios_item = []
                        
                        if cliente_id and peso and cubagem and valor:
                            item = ItemFechamentoFrete.objects.create(
                                fechamento=fechamento,
                                cliente_consolidado_id=cliente_id,
                                peso=Decimal(peso),
                                cubagem=Decimal(cubagem),
                                valor_mercadoria=Decimal(valor),
                                percentual_escolhido=Decimal(percentual_escolhido),
                                percentual_ajustado=Decimal(percentual_ajustado) if percentual_ajustado else None,
                                usar_ajuste_manual=usar_ajuste,
                                observacoes=observacoes
                            )
                            
                            # Adicionar romaneios ao item
                            if romaneios_item:
                                item.romaneios.set(RomaneioViagem.objects.filter(pk__in=romaneios_item))
                            
                            # Criar detalhes
                            for romaneio_id in romaneios_item:
                                try:
                                    romaneio = RomaneioViagem.objects.get(pk=romaneio_id)
                                    DetalheItemFechamento.objects.create(
                                        item=item,
                                        romaneio=romaneio,
                                        cliente_original=romaneio.cliente,
                                        peso=romaneio.peso_total or 0,
                                        valor=romaneio.valor_total or 0
                                    )
                                except RomaneioViagem.DoesNotExist:
                                    pass
                        
                        item_count += 1
                    
                    messages.success(request, f'Fechamento de frete criado com sucesso!')
                    return redirect('notas:detalhes_fechamento_frete', pk=fechamento.pk)
                    
            except Exception as e:
                logger.error(f'Erro ao criar fechamento de frete: {str(e)}', exc_info=True)
                messages.error(request, f'Erro ao criar fechamento de frete: {str(e)}')
    else:
        form = FechamentoFreteForm()
    
    # Buscar apenas os últimos 10 romaneios emitidos para o formulário
    romaneios = RomaneioViagem.objects.filter(status='Emitido').select_related(
        'cliente', 'motorista'
    ).order_by('-data_emissao', '-id')[:10]
    
    context = {
        'form': form,
        'romaneios': romaneios,
    }
    
    return render(request, 'notas/relatorios/criar_fechamento_frete.html', context)


@login_required
@user_passes_test(is_admin)
def editar_fechamento_frete(request, pk):
    """View para editar fechamento de frete existente"""
    from ..models import FechamentoFrete, ItemFechamentoFrete, DetalheItemFechamento, RomaneioViagem
    from ..forms import FechamentoFreteForm, ItemFechamentoFreteForm
    from django.db import transaction
    from collections import defaultdict
    
    try:
        fechamento = FechamentoFrete.objects.select_related(
            'motorista', 'usuario_criacao'
        ).prefetch_related(
            'romaneios', 'itens__cliente_consolidado', 
            'itens__romaneios', 'itens__detalhes__romaneio',
            'itens__detalhes__cliente_original'
        ).get(pk=pk)
    except FechamentoFrete.DoesNotExist:
        messages.error(request, 'Fechamento de frete não encontrado.')
        return redirect('notas:fechamento_frete')
    
    if request.method == 'POST':
        form = FechamentoFreteForm(request.POST, instance=fechamento)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Atualizar fechamento
                    fechamento = form.save(commit=False)
                    fechamento.origem_romaneio = bool(request.POST.getlist('romaneios_selecionados'))
                    fechamento.save()
                    
                    # Atualizar romaneios
                    romaneios_ids = request.POST.getlist('romaneios_selecionados')
                    if romaneios_ids:
                        romaneios = RomaneioViagem.objects.filter(pk__in=romaneios_ids)
                        fechamento.romaneios.set(romaneios)
                    
                    # Remover itens antigos
                    fechamento.itens.all().delete()
                    
                    # Processar novos itens (clientes)
                    item_count = 0
                    while f'item_cliente_{item_count}' in request.POST:
                        cliente_id = request.POST.get(f'item_cliente_{item_count}')
                        peso = request.POST.get(f'item_peso_{item_count}')
                        cubagem = request.POST.get(f'item_cubagem_{item_count}')
                        valor = request.POST.get(f'item_valor_{item_count}')
                        romaneios_item_str = request.POST.get(f'item_romaneios_{item_count}', '')
                        percentual_escolhido = request.POST.get(f'item_percentual_escolhido_{item_count}', '6')
                        percentual_ajustado = request.POST.get(f'item_percentual_ajustado_{item_count}', '')
                        usar_ajuste = request.POST.get(f'item_usar_ajuste_{item_count}') == 'on'
                        observacoes = request.POST.get(f'item_observacoes_{item_count}', '')
                        
                        # Processar romaneios
                        romaneios_item = []
                        if romaneios_item_str:
                            if ',' in romaneios_item_str:
                                romaneios_item = [int(id.strip()) for id in romaneios_item_str.split(',') if id.strip().isdigit()]
                            else:
                                try:
                                    romaneios_item = [int(romaneios_item_str)]
                                except ValueError:
                                    romaneios_item = []
                        
                        if cliente_id and peso and cubagem and valor:
                            item = ItemFechamentoFrete.objects.create(
                                fechamento=fechamento,
                                cliente_consolidado_id=cliente_id,
                                peso=Decimal(peso),
                                cubagem=Decimal(cubagem),
                                valor_mercadoria=Decimal(valor),
                                percentual_escolhido=Decimal(percentual_escolhido),
                                percentual_ajustado=Decimal(percentual_ajustado) if percentual_ajustado else None,
                                usar_ajuste_manual=usar_ajuste,
                                observacoes=observacoes
                            )
                            
                            # Adicionar romaneios ao item
                            if romaneios_item:
                                item.romaneios.set(RomaneioViagem.objects.filter(pk__in=romaneios_item))
                            
                            # Criar detalhes
                            for romaneio_id in romaneios_item:
                                try:
                                    romaneio = RomaneioViagem.objects.get(pk=romaneio_id)
                                    DetalheItemFechamento.objects.create(
                                        item=item,
                                        romaneio=romaneio,
                                        cliente_original=romaneio.cliente,
                                        peso=romaneio.peso_total or 0,
                                        valor=romaneio.valor_total or 0
                                    )
                                except RomaneioViagem.DoesNotExist:
                                    pass
                        
                        item_count += 1
                    
                    messages.success(request, f'Fechamento de frete atualizado com sucesso!')
                    return redirect('notas:detalhes_fechamento_frete', pk=fechamento.pk)
                    
            except Exception as e:
                logger.error(f'Erro ao editar fechamento de frete: {str(e)}', exc_info=True)
                messages.error(request, f'Erro ao editar fechamento de frete: {str(e)}')
    else:
        form = FechamentoFreteForm(instance=fechamento)
        # Garantir que a data esteja no formato correto para input type="date"
        if fechamento.data:
            # O Django form já deve converter automaticamente, mas vamos garantir
            # Converter para string no formato ISO (yyyy-MM-dd)
            data_iso = fechamento.data.strftime('%Y-%m-%d')
            form.fields['data'].initial = data_iso
            # Também definir o valor do widget diretamente
            form.fields['data'].widget.attrs['value'] = data_iso
        # Inicializar romaneios selecionados
        romaneios_selecionados = list(fechamento.romaneios.all())
        form.fields['romaneios_selecionados'].initial = romaneios_selecionados
        form.fields['romaneios_selecionados'].queryset = RomaneioViagem.objects.filter(
            Q(status='Emitido') | Q(pk__in=[r.pk for r in romaneios_selecionados])
        ).order_by('-data_emissao', '-id')
    
    # Buscar romaneios para o formulário
    romaneios = RomaneioViagem.objects.filter(status='Emitido').select_related(
        'cliente', 'motorista'
    ).order_by('-data_emissao', '-id')[:10]
    
    # Preparar dados dos itens existentes para o template
    itens_existentes = fechamento.itens.all().select_related('cliente_consolidado').prefetch_related('romaneios', 'detalhes')
    
    context = {
        'form': form,
        'romaneios': romaneios,
        'fechamento': fechamento,
        'itens_existentes': itens_existentes,
        'editar': True,
    }
    
    return render(request, 'notas/relatorios/criar_fechamento_frete.html', context)


@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
def imprimir_fechamento_frete(request, pk):
    """View para imprimir fechamento de frete em nova janela"""
    from ..models import FechamentoFrete
    from django.db.models import Sum
    from decimal import Decimal
    
    fechamento = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related(
        'romaneios', 'itens__cliente_consolidado', 
        'itens__romaneios', 'itens__detalhes__romaneio',
        'itens__detalhes__cliente_original'
    ).get(pk=pk)
    
    # Calcular totais dos itens
    totais = fechamento.itens.aggregate(
        total_peso=Sum('peso'),
        total_cubagem=Sum('cubagem'),
        total_valor=Sum('valor_mercadoria'),
        total_valor_cubagem=Sum('valor_por_cubagem'),
        total_valor_percentual=Sum('valor_por_percentual'),
        total_valor_ideal=Sum('valor_ideal'),
        total_valor_final=Sum('valor_final')
    )
    
    # Calcular carregamento e CTR por cliente baseado na cubagem
    itens_com_calculos = []
    cubagem_total = fechamento.cubagem_bau_total or Decimal('0')
    
    for item in fechamento.itens.all():
        # Calcular proporção da cubagem
        if cubagem_total > 0 and item.cubagem:
            proporcao_cubagem = item.cubagem / cubagem_total
        else:
            proporcao_cubagem = Decimal('0')
        
        # Calcular carregamento proporcional
        carregamento_cliente = proporcao_cubagem * (fechamento.carregamento_total or Decimal('0'))
        
        # Calcular CTR proporcional
        ctr_cliente = proporcao_cubagem * (fechamento.ctr_total or Decimal('0'))
        
        # Calcular total (apenas carregamento + CTR, sem frete)
        total_cliente = carregamento_cliente + ctr_cliente
        
        itens_com_calculos.append({
            'item': item,
            'carregamento': carregamento_cliente,
            'ctr': ctr_cliente,
            'proporcao_cubagem': proporcao_cubagem * 100,  # Em percentual (mantido para possível uso futuro)
            'total': total_cliente
        })
    
    # Calcular totais de carregamento e CTR
    total_carregamento_calculado = sum([i['carregamento'] for i in itens_com_calculos])
    total_ctr_calculado = sum([i['ctr'] for i in itens_com_calculos])
    total_carregamento_ctr = total_carregamento_calculado + total_ctr_calculado
    
    context = {
        'fechamento': fechamento,
        'totais': totais,
        'itens_com_calculos': itens_com_calculos,
        'total_carregamento_calculado': total_carregamento_calculado,
        'total_ctr_calculado': total_ctr_calculado,
        'total_carregamento_ctr': total_carregamento_ctr,
    }
    
    return render(request, 'notas/relatorios/visualizar_fechamento_frete_para_impressao.html', context)


@login_required
@user_passes_test(is_admin)
def detalhes_fechamento_frete(request, pk):
    """View para visualizar detalhes de um fechamento"""
    from ..models import FechamentoFrete
    from django.db.models import Sum
    
    fechamento = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related(
        'romaneios', 'itens__cliente_consolidado', 
        'itens__romaneios', 'itens__detalhes__romaneio',
        'itens__detalhes__cliente_original'
    ).get(pk=pk)
    
    # Calcular totais dos itens
    totais = fechamento.itens.aggregate(
        total_peso=Sum('peso'),
        total_cubagem=Sum('cubagem'),
        total_valor=Sum('valor_mercadoria'),
        total_valor_cubagem=Sum('valor_por_cubagem'),
        total_valor_percentual=Sum('valor_por_percentual'),
        total_valor_ideal=Sum('valor_ideal'),
        total_valor_final=Sum('valor_final')
    )
    
    # Calcular carregamento e CTR por cliente baseado na cubagem
    itens_com_calculos = []
    cubagem_total = fechamento.cubagem_bau_total or Decimal('0')
    
    for item in fechamento.itens.all():
        # Calcular proporção da cubagem
        if cubagem_total > 0 and item.cubagem:
            proporcao_cubagem = item.cubagem / cubagem_total
        else:
            proporcao_cubagem = Decimal('0')
        
        # Calcular carregamento proporcional
        carregamento_cliente = proporcao_cubagem * (fechamento.carregamento_total or Decimal('0'))
        
        # Calcular CTR proporcional
        ctr_cliente = proporcao_cubagem * (fechamento.ctr_total or Decimal('0'))
        
        # Calcular total (apenas carregamento + CTR, sem frete)
        total_cliente = carregamento_cliente + ctr_cliente
        
        itens_com_calculos.append({
            'item': item,
            'carregamento': carregamento_cliente,
            'ctr': ctr_cliente,
            'proporcao_cubagem': proporcao_cubagem * 100,  # Em percentual (mantido para possível uso futuro)
            'total': total_cliente
        })
    
    # Calcular totais de carregamento e CTR
    total_carregamento_calculado = sum([i['carregamento'] for i in itens_com_calculos])
    total_ctr_calculado = sum([i['ctr'] for i in itens_com_calculos])
    total_carregamento_ctr = total_carregamento_calculado + total_ctr_calculado
    
    context = {
        'fechamento': fechamento,
        'totais': totais,
        'itens_com_calculos': itens_com_calculos,
        'total_carregamento_calculado': total_carregamento_calculado,
        'total_ctr_calculado': total_ctr_calculado,
        'total_carregamento_ctr': total_carregamento_ctr,
    }
    
    return render(request, 'notas/relatorios/detalhes_fechamento_frete.html', context)


@login_required
@user_passes_test(is_admin)
def cobranca_mensal(request):
    """View para cobrança mensal"""
    messages.info(request, 'Funcionalidade de cobrança mensal em desenvolvimento')
    return render(request, 'notas/relatorios/cobranca_mensal.html')


@login_required
@user_passes_test(is_admin)
def cobranca_carregamento(request):
    """View para listar cobranças de carregamento"""
    from datetime import datetime
    from ..models import Cliente, CobrancaCarregamento
    
    cobrancas = CobrancaCarregamento.objects.all().select_related('cliente').prefetch_related('romaneios')
    
    # Filtros
    cliente_id = request.GET.get('cliente')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if cliente_id:
        cobrancas = cobrancas.filter(cliente_id=cliente_id)
    if status:
        cobrancas = cobrancas.filter(status=status)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio_obj)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            cobrancas = cobrancas.filter(criado_em__date__lte=data_fim_obj)
        except ValueError:
            pass
    
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    
    context = {
        'cobrancas': cobrancas,
        'clientes': clientes,
    }
    
    return render(request, 'notas/relatorios/cobranca_carregamento.html', context)

