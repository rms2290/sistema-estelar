"""
Views de fechamento de frete (listar, criar, editar, imprimir, detalhes).
"""
import logging
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q, Sum

from ..models import FechamentoFrete, Motorista, Cliente, ItemFechamentoFrete, DetalheItemFechamento, RomaneioViagem
from ..forms import FechamentoFreteForm
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso

logger = logging.getLogger(__name__)


@admin_required
def fechamento_frete(request):
    """View para listar fechamentos de frete com filtros de pesquisa"""
    from decimal import InvalidOperation

    fechamentos = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related('romaneios', 'itens', 'itens__cliente_consolidado')

    motorista_id = request.GET.get('motorista')
    cliente_id = request.GET.get('cliente')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    valor_min = request.GET.get('valor_min')
    valor_max = request.GET.get('valor_max')

    if motorista_id:
        fechamentos = fechamentos.filter(motorista_id=motorista_id)
    if cliente_id:
        fechamentos = fechamentos.filter(itens__cliente_consolidado_id=cliente_id).distinct()

    data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
    if data_inicio_obj:
        fechamentos = fechamentos.filter(data__gte=data_inicio_obj)
    data_fim_obj = parse_date_iso(data_fim) if data_fim else None
    if data_fim_obj:
        fechamentos = fechamentos.filter(data__lte=data_fim_obj)
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

    fechamentos = fechamentos.order_by('-data', '-data_criacao')
    motoristas = Motorista.objects.all().order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    context = {
        'fechamentos': fechamentos,
        'motoristas': motoristas,
        'clientes': clientes,
    }
    return render(request, 'notas/relatorios/fechamento_frete.html', context)


@admin_required
def criar_fechamento_frete(request):
    """View para criar novo fechamento de frete"""
    from django.db import transaction

    if request.method == 'POST':
        form = FechamentoFreteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    fechamento = form.save(commit=False)
                    fechamento.usuario_criacao = request.user
                    fechamento.origem_romaneio = bool(request.POST.getlist('romaneios_selecionados'))
                    fechamento.save()
                    romaneios_ids = request.POST.getlist('romaneios_selecionados')
                    if romaneios_ids:
                        romaneios = RomaneioViagem.objects.filter(pk__in=romaneios_ids)
                        fechamento.romaneios.set(romaneios)
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
                            if romaneios_item:
                                item.romaneios.set(RomaneioViagem.objects.filter(pk__in=romaneios_item))
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
                    messages.success(request, 'Fechamento de frete criado com sucesso!')
                    return redirect('notas:detalhes_fechamento_frete', pk=fechamento.pk)
            except Exception as e:
                logger.error('Erro ao criar fechamento de frete: %s', str(e), exc_info=True)
                messages.error(request, f'Erro ao criar fechamento de frete: {str(e)}')
    else:
        form = FechamentoFreteForm()
    romaneios = RomaneioViagem.objects.filter(status='Emitido').select_related(
        'cliente', 'motorista'
    ).order_by('-data_emissao', '-id')[:10]
    context = {'form': form, 'romaneios': romaneios}
    return render(request, 'notas/relatorios/criar_fechamento_frete.html', context)


@admin_required
def editar_fechamento_frete(request, pk):
    """View para editar fechamento de frete existente"""
    from django.db import transaction

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
                    fechamento = form.save(commit=False)
                    fechamento.origem_romaneio = bool(request.POST.getlist('romaneios_selecionados'))
                    fechamento.save()
                    romaneios_ids = request.POST.getlist('romaneios_selecionados')
                    if romaneios_ids:
                        romaneios = RomaneioViagem.objects.filter(pk__in=romaneios_ids)
                        fechamento.romaneios.set(romaneios)
                    fechamento.itens.all().delete()
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
                            if romaneios_item:
                                item.romaneios.set(RomaneioViagem.objects.filter(pk__in=romaneios_item))
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
                    messages.success(request, 'Fechamento de frete atualizado com sucesso!')
                    return redirect('notas:detalhes_fechamento_frete', pk=fechamento.pk)
            except Exception as e:
                logger.error('Erro ao editar fechamento de frete: %s', str(e), exc_info=True)
                messages.error(request, f'Erro ao editar fechamento de frete: {str(e)}')
    else:
        form = FechamentoFreteForm(instance=fechamento)
        if fechamento.data:
            data_iso = fechamento.data.strftime('%Y-%m-%d')
            form.fields['data'].initial = data_iso
            form.fields['data'].widget.attrs['value'] = data_iso
        romaneios_selecionados = list(fechamento.romaneios.all())
        form.fields['romaneios_selecionados'].initial = romaneios_selecionados
        form.fields['romaneios_selecionados'].queryset = RomaneioViagem.objects.filter(
            Q(status='Emitido') | Q(pk__in=[r.pk for r in romaneios_selecionados])
        ).order_by('-data_emissao', '-id')
    romaneios = RomaneioViagem.objects.filter(status='Emitido').select_related(
        'cliente', 'motorista'
    ).order_by('-data_emissao', '-id')[:10]
    itens_existentes = fechamento.itens.all().select_related('cliente_consolidado').prefetch_related('romaneios', 'detalhes')
    context = {
        'form': form,
        'romaneios': romaneios,
        'fechamento': fechamento,
        'itens_existentes': itens_existentes,
        'editar': True,
    }
    return render(request, 'notas/relatorios/criar_fechamento_frete.html', context)


@admin_required
def imprimir_fechamento_frete(request, pk):
    """View para imprimir fechamento de frete em nova janela"""
    fechamento = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related(
        'romaneios', 'itens__cliente_consolidado',
        'itens__romaneios', 'itens__detalhes__romaneio',
        'itens__detalhes__cliente_original'
    ).get(pk=pk)
    totais = fechamento.itens.aggregate(
        total_peso=Sum('peso'),
        total_cubagem=Sum('cubagem'),
        total_valor=Sum('valor_mercadoria'),
        total_valor_cubagem=Sum('valor_por_cubagem'),
        total_valor_percentual=Sum('valor_por_percentual'),
        total_valor_ideal=Sum('valor_ideal'),
        total_valor_final=Sum('valor_final')
    )
    itens_com_calculos = []
    cubagem_total = fechamento.cubagem_bau_total or Decimal('0')
    for item in fechamento.itens.all():
        proporcao_cubagem = (item.cubagem / cubagem_total) if cubagem_total > 0 and item.cubagem else Decimal('0')
        carregamento_cliente = proporcao_cubagem * (fechamento.carregamento_total or Decimal('0'))
        ctr_cliente = proporcao_cubagem * (fechamento.ctr_total or Decimal('0'))
        total_cliente = carregamento_cliente + ctr_cliente
        itens_com_calculos.append({
            'item': item,
            'carregamento': carregamento_cliente,
            'ctr': ctr_cliente,
            'proporcao_cubagem': proporcao_cubagem * 100,
            'total': total_cliente
        })
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


@admin_required
def detalhes_fechamento_frete(request, pk):
    """View para visualizar detalhes de um fechamento"""
    fechamento = FechamentoFrete.objects.select_related(
        'motorista', 'usuario_criacao'
    ).prefetch_related(
        'romaneios', 'itens__cliente_consolidado',
        'itens__romaneios', 'itens__detalhes__romaneio',
        'itens__detalhes__cliente_original'
    ).get(pk=pk)
    totais = fechamento.itens.aggregate(
        total_peso=Sum('peso'),
        total_cubagem=Sum('cubagem'),
        total_valor=Sum('valor_mercadoria'),
        total_valor_cubagem=Sum('valor_por_cubagem'),
        total_valor_percentual=Sum('valor_por_percentual'),
        total_valor_ideal=Sum('valor_ideal'),
        total_valor_final=Sum('valor_final')
    )
    itens_com_calculos = []
    cubagem_total = fechamento.cubagem_bau_total or Decimal('0')
    for item in fechamento.itens.all():
        proporcao_cubagem = (item.cubagem / cubagem_total) if cubagem_total > 0 and item.cubagem else Decimal('0')
        carregamento_cliente = proporcao_cubagem * (fechamento.carregamento_total or Decimal('0'))
        ctr_cliente = proporcao_cubagem * (fechamento.ctr_total or Decimal('0'))
        total_cliente = carregamento_cliente + ctr_cliente
        itens_com_calculos.append({
            'item': item,
            'carregamento': carregamento_cliente,
            'ctr': ctr_cliente,
            'proporcao_cubagem': proporcao_cubagem * 100,
            'total': total_cliente
        })
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
