"""
=============================================================================
Views do Financeiro V2
=============================================================================

Onda 1: Painel.
Onda 2: Caixa do Dia + Lançamento manual + Despesa avulsa + Xerox.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from notas.decorators import admin_required
from notas.models import Cliente, CobrancaCarregamento, CobrancaCTEAvulsa
from financeiro.models import (
    AcertoDiarioCarregamento,
    AcumuladoFuncionario,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
)

from sistema_estelar.api_utils import json_success, json_error

from . import services
from .forms import (
    AcertoDataForm,
    AcertoFiltroForm,
    BaixaCobrancaForm,
    ChapaDescargaFormSet,
    CobrancaCTEAvulsaForm,
    DescargaAvulsaForm,
    DespesaForm,
    DistribuicaoGerentesForm,
    FundoGasForm,
    GerentesFormSet,
    HistoricoFiltroForm,
    LancamentoManualForm,
    PagamentoSaidaForm,
    PeriodoForm,
    XeroxForm,
)
from .models import Bolso, Carteira, Lancamento


# ============================================================================
# Helpers
# ============================================================================

def _classifica_idade(dias):
    """Classifica idade da cobrança em verde / amarelo / laranja / vermelho."""
    if dias <= 7:
        return 'verde'
    if dias <= 15:
        return 'amarelo'
    if dias <= 30:
        return 'laranja'
    return 'vermelho'


def _parse_date(text, default=None):
    """Converte 'YYYY-MM-DD' em date, ou retorna default."""
    if not text:
        return default
    try:
        return datetime.strptime(text, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return default


def _saldo_carteira_ate(carteira, data_limite):
    """Saldo da carteira somando lançamentos com data <= data_limite (exclusiva no início do dia)."""
    agg = carteira.lancamentos.filter(data__lt=data_limite).aggregate(
        entradas=Sum('valor', filter=Q(tipo='Entrada')),
        saidas=Sum('valor', filter=Q(tipo='Saida')),
    )
    entradas = agg['entradas'] or Decimal('0.00')
    saidas = agg['saidas'] or Decimal('0.00')
    return (carteira.saldo_inicial or Decimal('0.00')) + entradas - saidas


# ============================================================================
# Painel (Onda 1)
# ============================================================================

@login_required
@admin_required
def painel(request):
    """Painel V2: saldo, bolsos, a receber por antiguidade, a pagar e projetado."""
    hoje = date.today()

    carteiras = []
    saldo_real_total = Decimal('0.00')
    for c in Carteira.objects.filter(ativa=True).order_by('nome'):
        saldo = c.saldo_atual()
        carteiras.append({'obj': c, 'saldo': saldo})
        saldo_real_total += saldo

    bolsos_empresa = []
    bolsos_terceiros = []
    fundo_terceiros_total = Decimal('0.00')
    for b in Bolso.objects.filter(ativo=True).order_by('ordem', 'nome'):
        saldo = b.saldo_atual()
        item = {'obj': b, 'saldo': saldo}
        if b.eh_terceiro:
            bolsos_terceiros.append(item)
            fundo_terceiros_total += saldo
        else:
            bolsos_empresa.append(item)

    saldo_empresa = saldo_real_total - fundo_terceiros_total

    # A Receber
    a_receber_buckets = {
        'verde': Decimal('0.00'),
        'amarelo': Decimal('0.00'),
        'laranja': Decimal('0.00'),
        'vermelho': Decimal('0.00'),
    }
    total_a_receber = Decimal('0.00')

    for c in CobrancaCarregamento.objects.filter(status='Pendente').select_related('cliente'):
        valor = c.valor_total or Decimal('0.00')
        ref_data = c.criado_em.date() if c.criado_em else hoje
        idade = (hoje - ref_data).days
        a_receber_buckets[_classifica_idade(idade)] += valor
        total_a_receber += valor

    for c in CobrancaCTEAvulsa.objects.filter(status='Pendente'):
        valor = c.valor_cte_manifesto or Decimal('0.00')
        ref_data = c.criado_em.date() if c.criado_em else hoje
        idade = (hoje - ref_data).days
        a_receber_buckets[_classifica_idade(idade)] += valor
        total_a_receber += valor

    # A Pagar
    total_chapas = (
        AcumuladoFuncionario.objects.filter(status='Pendente').aggregate(
            total=Sum('valor_acumulado')
        )['total']
        or Decimal('0.00')
    )
    cte_terceiro_carreg = (
        CobrancaCarregamento.objects.filter(
            status_cte_terceiro__iexact='Pendente', valor_cte_terceiro__gt=0
        ).aggregate(total=Sum('valor_cte_terceiro'))['total']
        or Decimal('0.00')
    )
    cte_terceiro_avulso = (
        CobrancaCTEAvulsa.objects.filter(
            status_cte_terceiro__iexact='Pendente', valor_cte_terceiro__gt=0
        ).aggregate(total=Sum('valor_cte_terceiro'))['total']
        or Decimal('0.00')
    )
    total_terceiro_doc = cte_terceiro_carreg + cte_terceiro_avulso
    total_a_pagar = total_chapas + total_terceiro_doc

    saldo_projetado = saldo_empresa + total_a_receber - total_a_pagar

    context = {
        'hoje': hoje,
        'carteiras': carteiras,
        'saldo_real_total': saldo_real_total,
        'saldo_empresa': saldo_empresa,
        'fundo_terceiros_total': fundo_terceiros_total,
        'bolsos_empresa': bolsos_empresa,
        'bolsos_terceiros': bolsos_terceiros,
        'a_receber': a_receber_buckets,
        'total_a_receber': total_a_receber,
        'total_chapas': total_chapas,
        'total_terceiro_doc': total_terceiro_doc,
        'total_a_pagar': total_a_pagar,
        'saldo_projetado': saldo_projetado,
    }
    return render(request, 'financeiro_v2/painel.html', context)


# ============================================================================
# Caixa do Dia (Onda 2)
# ============================================================================

@login_required
@admin_required
def caixa_do_dia(request):
    """Lista lançamentos do dia (ou período) com saldo corrente."""
    data_str = request.GET.get('data', '')
    carteira_id = request.GET.get('carteira', '')

    data_filtro = _parse_date(data_str, default=date.today())

    qs = Lancamento.objects.filter(data=data_filtro).select_related(
        'carteira', 'bolso', 'cliente', 'funcionario', 'criado_por'
    ).order_by('carteira_id', 'criado_em')

    carteiras = list(Carteira.objects.filter(ativa=True).order_by('nome'))
    carteira_obj = None
    if carteira_id:
        try:
            carteira_obj = Carteira.objects.get(pk=carteira_id, ativa=True)
            qs = qs.filter(carteira=carteira_obj)
        except Carteira.DoesNotExist:
            carteira_obj = None

    # Saldo inicial do dia (saldo das carteiras antes da data filtrada)
    if carteira_obj:
        saldo_inicial_do_dia = _saldo_carteira_ate(carteira_obj, data_filtro)
    else:
        saldo_inicial_do_dia = Decimal('0.00')
        for c in carteiras:
            saldo_inicial_do_dia += _saldo_carteira_ate(c, data_filtro)

    saldo_corrente = saldo_inicial_do_dia
    total_entradas = Decimal('0.00')
    total_saidas = Decimal('0.00')
    linhas = []
    for lanc in qs:
        if lanc.tipo == 'Entrada':
            saldo_corrente += lanc.valor
            total_entradas += lanc.valor
        else:
            saldo_corrente -= lanc.valor
            total_saidas += lanc.valor
        linhas.append({'lanc': lanc, 'saldo': saldo_corrente})

    context = {
        'data_filtro': data_filtro,
        'carteiras': carteiras,
        'carteira_obj': carteira_obj,
        'linhas': linhas,
        'saldo_inicial_do_dia': saldo_inicial_do_dia,
        'saldo_atual': saldo_corrente,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
    }
    return render(request, 'financeiro_v2/caixa_do_dia.html', context)


# ============================================================================
# Lançamento manual (Onda 2)
# ============================================================================

@login_required
@admin_required
def criar_lancamento(request):
    """Cria um lançamento manual (entrada/saída livre)."""
    if request.method == 'POST':
        form = LancamentoManualForm(request.POST)
        if form.is_valid():
            lanc = form.save(commit=False)
            lanc.criado_por = request.user
            lanc.save()
            messages.success(request, f'Lançamento criado: {lanc}')
            return redirect('financeiro_v2:caixa_do_dia')
    else:
        form = LancamentoManualForm(initial={'data': date.today(), 'tipo': 'Entrada'})

    return render(
        request,
        'financeiro_v2/lancamento_form.html',
        {'form': form, 'titulo': 'Novo Lançamento Manual', 'icone': 'fa-pen'},
    )


# ============================================================================
# Despesa avulsa (Onda 2)
# ============================================================================

@login_required
@admin_required
def criar_despesa(request):
    """Cria uma despesa = Lançamento de Saída."""
    if request.method == 'POST':
        form = DespesaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            Lancamento.objects.create(
                data=cd['data'],
                carteira=cd['carteira'],
                bolso=cd['bolso'],
                tipo='Saida',
                valor=cd['valor'],
                descricao=cd['descricao'],
                categoria=cd['categoria'],
                criado_por=request.user,
            )
            messages.success(
                request,
                f"Despesa lançada: {cd['descricao']} - R$ {cd['valor']:.2f}"
            )
            return redirect('financeiro_v2:caixa_do_dia')
    else:
        form = DespesaForm(initial={'data': date.today()})

    return render(
        request,
        'financeiro_v2/despesa_form.html',
        {'form': form},
    )


# ============================================================================
# Xerox (Onda 2)
# ============================================================================

@login_required
@admin_required
def criar_xerox(request):
    """Cria um Lançamento de Entrada de Xerox no bolso Estelar.

    Suporta dois modos:
    - Pagina full: renderiza `xerox_form.html` (uso por bookmark/legado).
    - Modal AJAX: detectado pelo header `X-Requested-With: XMLHttpRequest`.
      GET retorna apenas o partial do form; POST retorna JSON.
    """
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = XeroxForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            qtd = cd['quantidade']
            unit = cd['valor_unitario']
            total = qtd * unit
            try:
                bolso_estelar = Bolso.objects.get(codigo='ESTELAR')
            except Bolso.DoesNotExist:
                msg = 'Bolso "Estelar" não encontrado. Verifique o cadastro.'
                if is_ajax:
                    return JsonResponse({'success': False, 'message': msg}, status=400)
                messages.error(request, msg)
                return redirect('financeiro_v2:painel')

            descricao = (
                f'Xerox ({qtd} {"impressão" if qtd == 1 else "impressões"} '
                f'x R$ {unit:.2f})'
            )
            Lancamento.objects.create(
                data=date.today(),
                carteira=cd['carteira'],
                bolso=bolso_estelar,
                tipo='Entrada',
                valor=total,
                descricao=descricao,
                categoria='Xerox',
                criado_por=request.user,
            )
            success_msg = f'Xerox lançado: R$ {total:.2f}'.replace('.', ',')
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'reload': True,
                })
            messages.success(request, success_msg)
            return redirect('financeiro_v2:caixa_do_dia')
        elif is_ajax:
            html = render_to_string(
                'financeiro_v2/partials/_xerox_form_inner.html',
                {'form': form},
                request=request,
            )
            return JsonResponse({'success': False, 'form_html': html}, status=400)
    else:
        form = XeroxForm()

    if is_ajax:
        html = render_to_string(
            'financeiro_v2/partials/_xerox_form_inner.html',
            {'form': form},
            request=request,
        )
        return JsonResponse({'success': True, 'form_html': html})

    return render(
        request,
        'financeiro_v2/xerox_form.html',
        {'form': form},
    )


# ============================================================================
# A Receber (Onda 3)
# ============================================================================

@login_required
@admin_required
def a_receber_lista(request):
    """Lista cobranças pendentes agrupadas por cliente, com antiguidade."""
    hoje = date.today()
    filtro_cor = request.GET.get('cor', '')

    cobs_carreg = (
        CobrancaCarregamento.objects.filter(status='Pendente')
        .select_related('cliente')
        .order_by('cliente__razao_social', 'criado_em')
    )
    cobs_cte = CobrancaCTEAvulsa.objects.filter(status='Pendente').order_by('criado_em')

    grupos = {}
    avulsas = []
    buckets = {
        'verde': Decimal('0.00'),
        'amarelo': Decimal('0.00'),
        'laranja': Decimal('0.00'),
        'vermelho': Decimal('0.00'),
    }
    contagem_buckets = {'verde': 0, 'amarelo': 0, 'laranja': 0, 'vermelho': 0}
    total_geral = Decimal('0.00')

    for c in cobs_carreg:
        ref = c.criado_em.date() if c.criado_em else hoje
        idade = (hoje - ref).days
        cor = _classifica_idade(idade)
        valor = c.valor_total or Decimal('0.00')
        item = {
            'tipo': 'carregamento',
            'obj': c,
            'pk': c.pk,
            'idade': idade,
            'cor': cor,
            'valor': valor,
            'origem': c.get_origem_cobranca_display(),
        }
        if filtro_cor and cor != filtro_cor:
            continue
        cli = c.cliente
        chave = cli.pk if cli else 0
        nome = cli.razao_social if cli else 'Sem cliente'
        g = grupos.setdefault(
            chave,
            {'cliente': cli, 'cliente_nome': nome, 'itens': [], 'total': Decimal('0.00')},
        )
        g['itens'].append(item)
        g['total'] += valor
        total_geral += valor
        buckets[cor] += valor
        contagem_buckets[cor] += 1

    for c in cobs_cte:
        ref = c.criado_em.date() if c.criado_em else hoje
        idade = (hoje - ref).days
        cor = _classifica_idade(idade)
        valor = c.valor_cte_manifesto or Decimal('0.00')
        item = {
            'tipo': 'cte',
            'obj': c,
            'pk': c.pk,
            'idade': idade,
            'cor': cor,
            'valor': valor,
            'nome': c.nome,
        }
        if filtro_cor and cor != filtro_cor:
            continue
        avulsas.append(item)
        total_geral += valor
        buckets[cor] += valor
        contagem_buckets[cor] += 1

    grupos_list = sorted(grupos.values(), key=lambda x: x['cliente_nome'])

    context = {
        'grupos': grupos_list,
        'avulsas': avulsas,
        'buckets': buckets,
        'contagem_buckets': contagem_buckets,
        'total_geral': total_geral,
        'filtro_cor': filtro_cor,
        'qtd_clientes': len(grupos_list),
        'qtd_avulsas': len(avulsas),
    }
    return render(request, 'financeiro_v2/a_receber_lista.html', context)


def _get_cobranca(tipo, pk):
    """Retorna (cobranca, distribuicao_callable) de acordo com o tipo."""
    if tipo == 'carregamento':
        cobranca = get_object_or_404(CobrancaCarregamento, pk=pk)
        return cobranca, services.calcular_distribuicao_carregamento
    if tipo == 'cte':
        cobranca = get_object_or_404(CobrancaCTEAvulsa, pk=pk)
        return cobranca, services.calcular_distribuicao_cte_avulsa
    raise Http404('Tipo de cobrança inválido.')


@login_required
@admin_required
def a_receber_baixar(request, tipo, pk):
    """Tela de confirmação de baixa: mostra distribuição automática e aplica."""
    cobranca, calc_distribuicao = _get_cobranca(tipo, pk)

    if cobranca.status == 'Baixado':
        messages.warning(request, 'Esta cobrança já foi baixada anteriormente.')
        return redirect('financeiro_v2:a_receber_lista')

    if request.method == 'POST':
        form = BaixaCobrancaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                if tipo == 'carregamento':
                    lancs = services.aplicar_baixa_carregamento(
                        cobranca,
                        carteira=cd['carteira'],
                        data_pagamento=cd['data_pagamento'],
                        usuario=request.user,
                    )
                else:
                    lancs = services.aplicar_baixa_cte_avulsa(
                        cobranca,
                        carteira=cd['carteira'],
                        data_pagamento=cd['data_pagamento'],
                        usuario=request.user,
                    )
                messages.success(
                    request,
                    f'Cobrança baixada com sucesso. {len(lancs)} '
                    f'lançamento{"s" if len(lancs) != 1 else ""} criado'
                    f'{"s" if len(lancs) != 1 else ""} no V2.'
                )
                return redirect('financeiro_v2:a_receber_lista')
            except ValueError as e:
                messages.error(request, str(e))
            except Bolso.DoesNotExist:
                messages.error(
                    request,
                    'Bolso não encontrado. Verifique o cadastro do Financeiro V2.'
                )
    else:
        form = BaixaCobrancaForm(initial={'data_pagamento': date.today()})

    distribuicao = calc_distribuicao(cobranca)
    valor_total_distribuicao = sum((d['valor'] for d in distribuicao), Decimal('0.00'))

    if tipo == 'carregamento':
        titulo = f'Baixar Cobrança #{cobranca.id} - {cobranca.cliente.razao_social}'
        valor_cobranca = cobranca.valor_total or Decimal('0.00')
    else:
        titulo = f'Baixar CTE Avulsa #{cobranca.id} - {cobranca.nome}'
        valor_cobranca = cobranca.valor_cte_manifesto or Decimal('0.00')

    context = {
        'cobranca': cobranca,
        'tipo': tipo,
        'titulo': titulo,
        'form': form,
        'distribuicao': distribuicao,
        'valor_total_distribuicao': valor_total_distribuicao,
        'valor_cobranca': valor_cobranca,
    }
    return render(request, 'financeiro_v2/a_receber_baixar.html', context)


# ============================================================================
# A Pagar (Onda 4)
# ============================================================================

@login_required
@admin_required
def a_pagar_lista(request):
    """Lista combinada de pagamentos pendentes (chapas + terceiro doc)."""
    hoje = date.today()

    # ----- Chapas -----
    acumulados = (
        AcumuladoFuncionario.objects
        .filter(status='Pendente', valor_acumulado__gt=0)
        .select_related('funcionario')
        .order_by('funcionario__nome', 'semana_inicio')
    )
    grupos_chapas = {}
    total_chapas = Decimal('0.00')
    for ac in acumulados:
        idade = (hoje - ac.semana_fim).days if ac.semana_fim else 0
        item = {'obj': ac, 'idade': idade, 'valor': ac.valor_acumulado or Decimal('0.00')}
        f = ac.funcionario
        g = grupos_chapas.setdefault(
            f.pk,
            {'funcionario': f, 'itens': [], 'total': Decimal('0.00')},
        )
        g['itens'].append(item)
        g['total'] += item['valor']
        total_chapas += item['valor']

    grupos_chapas_list = sorted(grupos_chapas.values(), key=lambda x: x['funcionario'].nome)

    # ----- Terceiro doc -----
    cobs_carreg_terc = (
        CobrancaCarregamento.objects
        .filter(status_cte_terceiro__iexact='Pendente', valor_cte_terceiro__gt=0)
        .select_related('cliente')
        .order_by('-criado_em')
    )
    cobs_avulsa_terc = (
        CobrancaCTEAvulsa.objects
        .filter(status_cte_terceiro__iexact='Pendente', valor_cte_terceiro__gt=0)
        .order_by('-criado_em')
    )

    terceiros = []
    total_terceiros = Decimal('0.00')
    for c in cobs_carreg_terc:
        valor = c.valor_cte_terceiro or Decimal('0.00')
        terceiros.append({
            'tipo': 'carregamento',
            'pk': c.pk,
            'obj': c,
            'descricao': (
                c.cliente.razao_social if c.cliente else 'Sem cliente'
            ),
            'subdescricao': f'Cobrança #{c.id}',
            'valor': valor,
            'criado_em': c.criado_em,
        })
        total_terceiros += valor
    for c in cobs_avulsa_terc:
        valor = c.valor_cte_terceiro or Decimal('0.00')
        terceiros.append({
            'tipo': 'cte',
            'pk': c.pk,
            'obj': c,
            'descricao': c.nome,
            'subdescricao': f'CTE Avulsa #{c.id}',
            'valor': valor,
            'criado_em': c.criado_em,
        })
        total_terceiros += valor

    terceiros.sort(key=lambda x: x['criado_em'] or datetime.min, reverse=True)

    context = {
        'grupos_chapas': grupos_chapas_list,
        'total_chapas': total_chapas,
        'qtd_chapas': len(grupos_chapas_list),
        'qtd_acumulados': sum(len(g['itens']) for g in grupos_chapas_list),
        'terceiros': terceiros,
        'total_terceiros': total_terceiros,
        'qtd_terceiros': len(terceiros),
        'total_geral': total_chapas + total_terceiros,
        'aba_inicial': request.GET.get('aba', 'chapas'),
    }
    return render(request, 'financeiro_v2/a_pagar_lista.html', context)


@login_required
@admin_required
def a_pagar_chapa(request, pk):
    """Pagar 1 acumulado individual de chapa."""
    acumulado = get_object_or_404(
        AcumuladoFuncionario.objects.select_related('funcionario'), pk=pk
    )

    if acumulado.status == 'Depositado':
        messages.warning(request, 'Este acumulado já foi pago anteriormente.')
        return redirect('financeiro_v2:a_pagar_lista')

    if request.method == 'POST':
        form = PagamentoSaidaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                services.aplicar_pagamento_chapa(
                    acumulado,
                    carteira=cd['carteira'],
                    data_pagamento=cd['data_pagamento'],
                    usuario=request.user,
                )
                messages.success(
                    request,
                    f'Pagamento de R$ {acumulado.valor_acumulado:.2f} '
                    f'para {acumulado.funcionario.nome} registrado.'
                )
                return redirect('financeiro_v2:a_pagar_lista')
            except ValueError as e:
                messages.error(request, str(e))
            except Bolso.DoesNotExist:
                messages.error(
                    request,
                    'Bolso "Operacional" não encontrado. Verifique o cadastro.'
                )
    else:
        form = PagamentoSaidaForm(initial={'data_pagamento': date.today()})

    context = {
        'acumulado': acumulado,
        'form': form,
    }
    return render(request, 'financeiro_v2/a_pagar_chapa.html', context)


@login_required
@admin_required
def a_pagar_chapa_lote(request, funcionario_pk):
    """Paga TODOS os acumulados pendentes de um funcionário em uma operação."""
    from financeiro.models import FuncionarioFluxoCaixa
    funcionario = get_object_or_404(FuncionarioFluxoCaixa, pk=funcionario_pk)

    acumulados = list(
        AcumuladoFuncionario.objects
        .filter(funcionario=funcionario, status='Pendente', valor_acumulado__gt=0)
        .order_by('semana_inicio')
    )
    total = sum((a.valor_acumulado or Decimal('0.00') for a in acumulados), Decimal('0.00'))

    if not acumulados:
        messages.warning(request, f'Nenhum acumulado pendente para {funcionario.nome}.')
        return redirect('financeiro_v2:a_pagar_lista')

    if request.method == 'POST':
        form = PagamentoSaidaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                lancs = services.aplicar_pagamento_chapa_em_lote(
                    acumulados,
                    carteira=cd['carteira'],
                    data_pagamento=cd['data_pagamento'],
                    usuario=request.user,
                )
                messages.success(
                    request,
                    f'Pagamento total de R$ {total:.2f} para {funcionario.nome} '
                    f'registrado ({len(lancs)} lançamento{"s" if len(lancs) != 1 else ""}).'
                )
                return redirect('financeiro_v2:a_pagar_lista')
            except Bolso.DoesNotExist:
                messages.error(request, 'Bolso "Operacional" não encontrado.')
    else:
        form = PagamentoSaidaForm(initial={'data_pagamento': date.today()})

    context = {
        'funcionario': funcionario,
        'acumulados': acumulados,
        'total': total,
        'form': form,
    }
    return render(request, 'financeiro_v2/a_pagar_chapa_lote.html', context)


def _get_cobranca_terceiro(tipo, pk):
    if tipo == 'carregamento':
        return get_object_or_404(CobrancaCarregamento, pk=pk)
    if tipo == 'cte':
        return get_object_or_404(CobrancaCTEAvulsa, pk=pk)
    raise Http404('Tipo de cobrança inválido.')


@login_required
@admin_required
def a_pagar_terceiro(request, tipo, pk):
    """Pagar o terceiro de documentação de uma cobrança."""
    cobranca = _get_cobranca_terceiro(tipo, pk)

    if (cobranca.status_cte_terceiro or '').lower() == 'pago':
        messages.warning(request, 'Este pagamento ao terceiro já foi feito.')
        return redirect('financeiro_v2:a_pagar_lista')

    if request.method == 'POST':
        form = PagamentoSaidaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                if tipo == 'carregamento':
                    services.aplicar_pagamento_terceiro_carregamento(
                        cobranca,
                        carteira=cd['carteira'],
                        data_pagamento=cd['data_pagamento'],
                        usuario=request.user,
                    )
                else:
                    services.aplicar_pagamento_terceiro_cte_avulsa(
                        cobranca,
                        carteira=cd['carteira'],
                        data_pagamento=cd['data_pagamento'],
                        usuario=request.user,
                    )
                valor = cobranca.valor_cte_terceiro or Decimal('0.00')
                messages.success(
                    request,
                    f'Pagamento ao terceiro de R$ {valor:.2f} registrado.'
                )
                return redirect('financeiro_v2:a_pagar_lista')
            except ValueError as e:
                messages.error(request, str(e))
            except Bolso.DoesNotExist:
                messages.error(
                    request,
                    'Bolso "Documentação" não encontrado. Verifique o cadastro.'
                )
    else:
        form = PagamentoSaidaForm(initial={'data_pagamento': date.today()})

    if tipo == 'carregamento':
        identificacao = (
            f'Cobrança #{cobranca.id} - '
            f'{cobranca.cliente.razao_social if cobranca.cliente else "Sem cliente"}'
        )
        valor = cobranca.valor_cte_terceiro or Decimal('0.00')
        valor_cliente = cobranca.valor_cte_manifesto or Decimal('0.00')
    else:
        identificacao = f'CTE Avulsa #{cobranca.id} - {cobranca.nome}'
        valor = cobranca.valor_cte_terceiro or Decimal('0.00')
        valor_cliente = cobranca.valor_cte_manifesto or Decimal('0.00')

    margem = max(Decimal('0.00'), valor_cliente - valor)

    context = {
        'cobranca': cobranca,
        'tipo': tipo,
        'identificacao': identificacao,
        'valor': valor,
        'valor_cliente': valor_cliente,
        'margem': margem,
        'form': form,
    }
    return render(request, 'financeiro_v2/a_pagar_terceiro.html', context)


# ============================================================================
# Onda 5 - Criar Doc. Avulsa (CobrancaCTEAvulsa)
# ============================================================================

@login_required
@admin_required
def criar_cte_avulsa(request):
    """Cria uma CobrancaCTEAvulsa pendente; aparecerá em A Receber e A Pagar."""
    if request.method == 'POST':
        form = CobrancaCTEAvulsaForm(request.POST)
        if form.is_valid():
            cob = form.save(commit=False)
            cob.status = 'Pendente'
            cob.status_cte_terceiro = 'Pendente'
            cob.save()
            messages.success(
                request,
                f'Doc. Avulsa #{cob.id} criada: {cob.nome} - '
                f'R$ {cob.valor_cte_manifesto}'
            )
            return redirect('financeiro_v2:a_receber_lista')
    else:
        form = CobrancaCTEAvulsaForm()

    return render(
        request,
        'financeiro_v2/cte_avulsa_form.html',
        {'form': form},
    )


# ============================================================================
# Onda 5 - Editar / Excluir Lançamento
# ============================================================================

@login_required
@admin_required
def editar_lancamento(request, pk):
    """Edita um Lancamento manual existente."""
    lanc = get_object_or_404(Lancamento, pk=pk)

    if request.method == 'POST':
        form = LancamentoManualForm(request.POST, instance=lanc)
        if form.is_valid():
            form.save()
            messages.success(request, f'Lançamento #{lanc.id} atualizado.')
            return redirect(
                request.GET.get('next') or 'financeiro_v2:caixa_do_dia'
            )
    else:
        form = LancamentoManualForm(instance=lanc)

    return render(
        request,
        'financeiro_v2/lancamento_form.html',
        {
            'form': form,
            'titulo': f'Editar Lançamento #{lanc.id}',
            'icone': 'fa-pen',
            'lanc': lanc,
            'editando': True,
        },
    )


@login_required
@admin_required
def excluir_lancamento(request, pk):
    """Exclui um Lancamento (com confirmação)."""
    lanc = get_object_or_404(Lancamento, pk=pk)

    if request.method == 'POST':
        descricao = lanc.descricao
        valor = lanc.valor
        lanc.delete()
        messages.success(
            request,
            f'Lançamento excluído: {descricao} (R$ {valor:.2f}).'
        )
        return redirect(
            request.GET.get('next') or 'financeiro_v2:caixa_do_dia'
        )

    return render(
        request,
        'financeiro_v2/lancamento_excluir.html',
        {'lanc': lanc},
    )


# ============================================================================
# Onda 5 - Descarga Avulsa
# ============================================================================

@login_required
@admin_required
def criar_descarga_avulsa(request):
    """
    Tela de Descarga Avulsa.

    Cabeçalho (data, descrição, valor cobrado, carteira) + formset de chapas.
    Ao salvar:
    - Cria 2 Lançamentos (Entrada Operacional + Entrada Estelar)
    - Soma valor no AcumuladoFuncionario da semana de cada chapa
    """
    if request.method == 'POST':
        form = DescargaAvulsaForm(request.POST)
        formset = ChapaDescargaFormSet(request.POST, prefix='chapas')

        if form.is_valid() and formset.is_valid():
            chapas_distribuicao = []
            chapas_vistos = set()
            erro_formset = None
            for sub in formset:
                if not sub.cleaned_data:
                    continue
                chapa = sub.cleaned_data.get('chapa')
                valor = sub.cleaned_data.get('valor') or Decimal('0.00')
                if chapa is None or valor <= 0:
                    continue
                if chapa.pk in chapas_vistos:
                    erro_formset = f'Chapa {chapa.nome} aparece mais de uma vez.'
                    break
                chapas_vistos.add(chapa.pk)
                chapas_distribuicao.append((chapa, valor))

            if erro_formset:
                messages.error(request, erro_formset)
            elif not chapas_distribuicao:
                messages.error(request, 'Adicione pelo menos um chapa com valor maior que zero.')
            else:
                cd = form.cleaned_data
                try:
                    resultado = services.aplicar_descarga_avulsa(
                        data_op=cd['data'],
                        descricao=cd['descricao'],
                        carteira=cd['carteira'],
                        valor_cobrado=cd['valor_cobrado'],
                        chapas_distribuicao=chapas_distribuicao,
                        usuario=request.user,
                    )
                    qtd_chapas = len(resultado['acumulados'])
                    messages.success(
                        request,
                        f'Descarga registrada: R$ {cd["valor_cobrado"]:.2f} '
                        f'(margem R$ {resultado["margem"]:.2f}, {qtd_chapas} '
                        f'chapa{"s" if qtd_chapas != 1 else ""} atualizado'
                        f'{"s" if qtd_chapas != 1 else ""}).'
                    )
                    return redirect('financeiro_v2:caixa_do_dia')
                except ValueError as e:
                    messages.error(request, str(e))
                except Bolso.DoesNotExist:
                    messages.error(
                        request,
                        'Bolsos Operacional/Estelar não encontrados. Verifique o cadastro.'
                    )
    else:
        form = DescargaAvulsaForm(initial={'data': date.today()})
        formset = ChapaDescargaFormSet(prefix='chapas')

    return render(
        request,
        'financeiro_v2/descarga_avulsa_form.html',
        {'form': form, 'formset': formset},
    )


# ============================================================================
# Onda 6 - Cliente Extrato
# ============================================================================

@login_required
@admin_required
def cliente_extrato(request, pk):
    """Extrato de movimentações de um cliente: cobranças + lançamentos V2."""
    cliente = get_object_or_404(Cliente, pk=pk)

    cobs = (
        CobrancaCarregamento.objects.filter(cliente=cliente)
        .order_by('-criado_em')
    )
    lancs = (
        Lancamento.objects.filter(cliente=cliente)
        .select_related('carteira', 'bolso', 'cobranca_carregamento')
        .order_by('-data', '-criado_em')
    )

    total_pendente = (
        cobs.filter(status='Pendente').aggregate(
            total=Sum('valor_carregamento') + Sum('valor_cte_manifesto')
        )
    )
    pendente_carreg = (
        cobs.filter(status='Pendente').aggregate(
            total=Sum('valor_carregamento')
        )['total'] or Decimal('0.00')
    )
    pendente_cte = (
        cobs.filter(status='Pendente').aggregate(
            total=Sum('valor_cte_manifesto')
        )['total'] or Decimal('0.00')
    )
    total_pendente = pendente_carreg + pendente_cte

    pago_carreg = (
        cobs.filter(status='Baixado').aggregate(
            total=Sum('valor_carregamento')
        )['total'] or Decimal('0.00')
    )
    pago_cte = (
        cobs.filter(status='Baixado').aggregate(
            total=Sum('valor_cte_manifesto')
        )['total'] or Decimal('0.00')
    )
    total_pago = pago_carreg + pago_cte

    # Linha do tempo unificada
    eventos = []
    for c in cobs:
        valor = c.valor_total or Decimal('0.00')
        eventos.append({
            'data': c.criado_em.date() if c.criado_em else date.today(),
            'tipo': 'cobranca',
            'icone': 'fa-file-invoice-dollar',
            'cor': 'success' if c.status == 'Baixado' else 'warning',
            'titulo': f'Cobrança #{c.id}',
            'subtitulo': c.get_origem_cobranca_display(),
            'valor': valor,
            'sentido': '+',  # cliente deve esses valores
            'status': c.get_status_display(),
            'extra': (
                f'Baixada em {c.data_baixa:%d/%m/%Y}'
                if c.status == 'Baixado' and c.data_baixa
                else None
            ),
            'obj': c,
        })

    for l in lancs:
        eventos.append({
            'data': l.data,
            'tipo': 'lancamento',
            'icone': 'fa-cash-register',
            'cor': 'info',
            'titulo': f'Lançamento V2 #{l.id}',
            'subtitulo': l.descricao,
            'valor': l.valor,
            'sentido': '+' if l.tipo == 'Entrada' else '−',
            'status': f'{l.bolso.nome} / {l.carteira.nome}',
            'extra': l.categoria,
            'obj': l,
        })

    eventos.sort(key=lambda e: (e['data'], 0), reverse=True)

    context = {
        'cliente': cliente,
        'eventos': eventos,
        'qtd_cobrancas': cobs.count(),
        'qtd_pendentes': cobs.filter(status='Pendente').count(),
        'qtd_lancamentos': lancs.count(),
        'pendente_carreg': pendente_carreg,
        'pendente_cte': pendente_cte,
        'total_pendente': total_pendente,
        'pago_carreg': pago_carreg,
        'pago_cte': pago_cte,
        'total_pago': total_pago,
    }
    return render(request, 'financeiro_v2/cliente_extrato.html', context)


# ============================================================================
# Onda 6 - Distribuir aos Gerentes
# ============================================================================

@login_required
@admin_required
def distribuir_gerentes(request):
    """Distribui o saldo do bolso Documentação entre os gerentes."""
    try:
        bolso_doc = Bolso.objects.get(codigo='DOCUMENTACAO')
        saldo_doc = bolso_doc.saldo_atual()
    except Bolso.DoesNotExist:
        messages.error(request, 'Bolso Documentação não encontrado.')
        return redirect('financeiro_v2:painel')

    if request.method == 'POST':
        form = DistribuicaoGerentesForm(request.POST)
        formset = GerentesFormSet(request.POST, prefix='gerentes')

        if form.is_valid() and formset.is_valid():
            distribuicoes = []
            for sub in formset:
                if not sub.cleaned_data:
                    continue
                nome = (sub.cleaned_data.get('nome') or '').strip()
                valor = sub.cleaned_data.get('valor') or Decimal('0.00')
                if nome and valor > 0:
                    distribuicoes.append((nome, valor))

            if not distribuicoes:
                messages.error(request, 'Adicione pelo menos um gerente com nome e valor > 0.')
            else:
                cd = form.cleaned_data
                try:
                    lancs = services.aplicar_distribuicao_gerentes(
                        data_op=cd['data'],
                        carteira=cd['carteira'],
                        distribuicoes=distribuicoes,
                        usuario=request.user,
                    )
                    total = sum((v for _, v in distribuicoes), Decimal('0.00'))
                    messages.success(
                        request,
                        f'Distribuição registrada: R$ {total:.2f} entre '
                        f'{len(lancs)} gerente{"s" if len(lancs) != 1 else ""}.'
                    )
                    return redirect('financeiro_v2:painel')
                except ValueError as e:
                    messages.error(request, str(e))
    else:
        form = DistribuicaoGerentesForm(initial={'data': date.today()})
        formset = GerentesFormSet(prefix='gerentes')

    return render(
        request,
        'financeiro_v2/distribuir_gerentes.html',
        {'form': form, 'formset': formset, 'saldo_doc': saldo_doc},
    )


# ============================================================================
# Onda 6 - Fundo Gás
# ============================================================================

@login_required
@admin_required
def fundo_gas(request):
    """Movimentação de entrada/saída no Fundo Gás (terceiros)."""
    try:
        bolso_gas = Bolso.objects.get(codigo='FUNDO_GAS')
        saldo_gas = bolso_gas.saldo_atual()
    except Bolso.DoesNotExist:
        messages.error(request, 'Bolso Fundo Gás não encontrado.')
        return redirect('financeiro_v2:painel')

    if request.method == 'POST':
        form = FundoGasForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                services.aplicar_fundo_gas(
                    data_op=cd['data'],
                    carteira=cd['carteira'],
                    tipo=cd['tipo'],
                    valor=cd['valor'],
                    descricao=cd['descricao'],
                    usuario=request.user,
                )
                tipo_label = 'Entrada' if cd['tipo'] == 'Entrada' else 'Saída'
                messages.success(
                    request,
                    f'{tipo_label} no Fundo Gás registrada: R$ {cd["valor"]:.2f}.'
                )
                return redirect('financeiro_v2:fundo_gas')
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = FundoGasForm(initial={'data': date.today(), 'tipo': 'Entrada'})

    movimentos = (
        Lancamento.objects.filter(bolso=bolso_gas)
        .select_related('carteira', 'criado_por')
        .order_by('-data', '-criado_em')[:30]
    )

    return render(
        request,
        'financeiro_v2/fundo_gas.html',
        {'form': form, 'saldo_gas': saldo_gas, 'movimentos': movimentos},
    )


# ============================================================================
# Onda 7 - Histórico/Relatórios
# ============================================================================

@login_required
@admin_required
def historico_lancamentos(request):
    """Lista paginada de lançamentos com filtros."""
    form = HistoricoFiltroForm(request.GET or None)

    qs = Lancamento.objects.all().select_related(
        'carteira', 'bolso', 'cliente', 'funcionario', 'criado_por'
    ).order_by('-data', '-criado_em')

    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('data_inicio'):
            qs = qs.filter(data__gte=cd['data_inicio'])
        if cd.get('data_fim'):
            qs = qs.filter(data__lte=cd['data_fim'])
        if cd.get('tipo'):
            qs = qs.filter(tipo=cd['tipo'])
        if cd.get('carteira'):
            qs = qs.filter(carteira=cd['carteira'])
        if cd.get('bolso'):
            qs = qs.filter(bolso=cd['bolso'])
        if cd.get('categoria'):
            qs = qs.filter(categoria__icontains=cd['categoria'])
        if cd.get('busca'):
            qs = qs.filter(descricao__icontains=cd['busca'])

    # Totais agregados (sobre o filtro completo, não a página)
    totais = qs.aggregate(
        total_entradas=Sum('valor', filter=Q(tipo='Entrada')),
        total_saidas=Sum('valor', filter=Q(tipo='Saida')),
    )
    total_entradas = totais['total_entradas'] or Decimal('0.00')
    total_saidas = totais['total_saidas'] or Decimal('0.00')
    saldo_periodo = total_entradas - total_saidas

    # Quebra por bolso (top 8)
    por_bolso = (
        qs.values('bolso__nome', 'bolso__codigo')
        .annotate(
            entradas=Sum('valor', filter=Q(tipo='Entrada')),
            saidas=Sum('valor', filter=Q(tipo='Saida')),
        )
        .order_by('bolso__ordem', 'bolso__nome')
    )

    paginator = Paginator(qs, 50)
    pagina = request.GET.get('page')
    page_obj = paginator.get_page(pagina)

    # Querystring sem o param "page" para preservar nos links
    qs_sem_page = request.GET.copy()
    qs_sem_page.pop('page', None)
    querystring_extra = qs_sem_page.urlencode()

    context = {
        'form': form,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo_periodo': saldo_periodo,
        'por_bolso': por_bolso,
        'querystring_extra': querystring_extra,
    }
    return render(request, 'financeiro_v2/historico_lancamentos.html', context)


# ============================================================================
# Onda 7 - DRE Simplificado
# ============================================================================

def _periodo_padrao_mes_atual():
    hoje = date.today()
    inicio = hoje.replace(day=1)
    if hoje.month == 12:
        prox_mes = hoje.replace(year=hoje.year + 1, month=1, day=1)
    else:
        prox_mes = hoje.replace(month=hoje.month + 1, day=1)
    fim = prox_mes - timedelta(days=1)
    return inicio, fim


@login_required
@admin_required
def dre_periodo(request):
    """
    Demonstrativo de Resultados simplificado do período.

    Apresenta 2 visões:
    - Fluxo de Caixa: entradas vs saídas brutas no período.
    - Resultado Operacional: margem real da empresa.
    """
    if request.GET.get('data_inicio'):
        form = PeriodoForm(request.GET)
    else:
        ini_padrao, fim_padrao = _periodo_padrao_mes_atual()
        form = PeriodoForm(initial={'data_inicio': ini_padrao, 'data_fim': fim_padrao})

    if form.is_valid():
        data_inicio = form.cleaned_data['data_inicio']
        data_fim = form.cleaned_data['data_fim']
    else:
        data_inicio, data_fim = _periodo_padrao_mes_atual()

    qs = Lancamento.objects.filter(data__gte=data_inicio, data__lte=data_fim)

    # ----- Fluxo de Caixa (visão A) -----
    por_bolso = (
        qs.values('bolso__nome', 'bolso__codigo')
        .annotate(
            entradas=Sum('valor', filter=Q(tipo='Entrada')),
            saidas=Sum('valor', filter=Q(tipo='Saida')),
        )
        .order_by('bolso__ordem', 'bolso__nome')
    )
    fluxo_lista = []
    total_entradas = Decimal('0.00')
    total_saidas = Decimal('0.00')
    for item in por_bolso:
        ent = item['entradas'] or Decimal('0.00')
        sai = item['saidas'] or Decimal('0.00')
        fluxo_lista.append({
            'nome': item['bolso__nome'],
            'codigo': item['bolso__codigo'],
            'entradas': ent,
            'saidas': sai,
            'saldo': ent - sai,
        })
        total_entradas += ent
        total_saidas += sai
    fluxo_liquido = total_entradas - total_saidas

    # ----- Resultado Operacional (visão B) -----
    def _agg_bolso(codigo, tipo):
        return qs.filter(bolso__codigo=codigo, tipo=tipo).aggregate(
            t=Sum('valor')
        )['t'] or Decimal('0.00')

    estelar_in = _agg_bolso('ESTELAR', 'Entrada')
    estelar_out = _agg_bolso('ESTELAR', 'Saida')
    margem_estelar = estelar_in - estelar_out

    doc_in = _agg_bolso('DOCUMENTACAO', 'Entrada')
    doc_pagamento_terceiro = (
        qs.filter(bolso__codigo='DOCUMENTACAO', tipo='Saida',
                  categoria__icontains='Terceiro').aggregate(t=Sum('valor'))['t']
        or Decimal('0.00')
    )
    doc_distrib_gerentes = (
        qs.filter(bolso__codigo='DOCUMENTACAO', tipo='Saida',
                  categoria__icontains='Gerentes').aggregate(t=Sum('valor'))['t']
        or Decimal('0.00')
    )
    margem_doc_apos_terceiro = doc_in - doc_pagamento_terceiro

    # Despesas operacionais = saídas no Operacional com categoria não-pagamento
    despesas_op = (
        qs.filter(bolso__codigo='OPERACIONAL', tipo='Saida')
        .exclude(categoria__icontains='Pagamento Chapa')
        .aggregate(t=Sum('valor'))['t'] or Decimal('0.00')
    )

    receita_operacional = margem_estelar + margem_doc_apos_terceiro
    deducoes = despesas_op + doc_distrib_gerentes
    lucro_operacional = receita_operacional - deducoes

    context = {
        'form': form,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'fluxo_lista': fluxo_lista,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'fluxo_liquido': fluxo_liquido,
        'margem_estelar': margem_estelar,
        'doc_in': doc_in,
        'doc_pagamento_terceiro': doc_pagamento_terceiro,
        'margem_doc_apos_terceiro': margem_doc_apos_terceiro,
        'despesas_op': despesas_op,
        'doc_distrib_gerentes': doc_distrib_gerentes,
        'receita_operacional': receita_operacional,
        'deducoes': deducoes,
        'lucro_operacional': lucro_operacional,
    }
    return render(request, 'financeiro_v2/dre_periodo.html', context)


# ============================================================================
# Onda 7 - Inadimplência por Cliente
# ============================================================================

@login_required
@admin_required
def inadimplencia_lista(request):
    """Lista clientes com cobranças pendentes acima de N dias."""
    hoje = date.today()
    try:
        dias_min = int(request.GET.get('dias_min', '30'))
    except ValueError:
        dias_min = 30
    if dias_min < 0:
        dias_min = 0

    limite = hoje - timedelta(days=dias_min)

    cobs = (
        CobrancaCarregamento.objects
        .filter(status='Pendente', criado_em__date__lte=limite)
        .select_related('cliente')
        .order_by('cliente__razao_social', 'criado_em')
    )

    grupos = {}
    total_geral = Decimal('0.00')
    for c in cobs:
        valor = c.valor_total or Decimal('0.00')
        ref = c.criado_em.date() if c.criado_em else hoje
        idade = (hoje - ref).days
        cli = c.cliente
        if not cli:
            continue
        g = grupos.setdefault(
            cli.pk,
            {
                'cliente': cli,
                'total': Decimal('0.00'),
                'qtd': 0,
                'idade_max': 0,
            },
        )
        g['total'] += valor
        g['qtd'] += 1
        if idade > g['idade_max']:
            g['idade_max'] = idade
        total_geral += valor

    grupos_list = sorted(grupos.values(), key=lambda x: -x['idade_max'])

    context = {
        'dias_min': dias_min,
        'grupos': grupos_list,
        'total_geral': total_geral,
        'qtd_clientes': len(grupos_list),
    }
    return render(request, 'financeiro_v2/inadimplencia_lista.html', context)


# ============================================================================
# Onda 8 - Acerto Diário V2
# ============================================================================

def _carregamentos_ordenados(acerto):
    """Carregamentos do acerto: clientes primeiro (alfabético), descargas depois."""
    qs = list(
        CarregamentoCliente.objects.filter(acerto_diario=acerto)
        .select_related('cliente')
    )
    qs.sort(key=lambda x: (
        0 if x.cliente else 1,
        (x.cliente.razao_social if x.cliente else '') or '',
        x.descricao or '',
    ))
    return qs


@login_required
@admin_required
def acerto_diario_v2_lista(request):
    """Lista de acertos com filtros de período + botão para abrir acerto do dia."""
    form = AcertoFiltroForm(request.GET or None)
    acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')

    data_inicio = ''
    data_fim = ''
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('data_inicio'):
            data_inicio = cd['data_inicio'].strftime('%Y-%m-%d')
            acertos = acertos.filter(data__gte=cd['data_inicio'])
        if cd.get('data_fim'):
            data_fim = cd['data_fim'].strftime('%Y-%m-%d')
            acertos = acertos.filter(data__lte=cd['data_fim'])

    paginator = Paginator(acertos, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    qs_extra = request.GET.copy()
    qs_extra.pop('page', None)
    querystring_extra = qs_extra.urlencode()

    context = {
        'form': form,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_count': paginator.count,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'querystring_extra': querystring_extra,
        'hoje': date.today(),
    }
    return render(request, 'financeiro_v2/acerto_diario_v2_lista.html', context)


@login_required
@admin_required
def acerto_diario_v2_abrir(request):
    """Abre/cria um acerto pela data informada (?data=YYYY-MM-DD) e redireciona ao detalhe."""
    data_str = request.GET.get('data', '') or request.POST.get('data', '')
    data_obj = _parse_date(data_str, default=date.today())

    acerto, _ = AcertoDiarioCarregamento.objects.get_or_create(
        data=data_obj,
        defaults={
            'valor_estelar': Decimal('0.00'),
            'observacoes': '',
            'usuario_criacao': request.user,
        },
    )
    return redirect('financeiro_v2:acerto_diario_v2_detalhe', pk=acerto.pk)


@login_required
@admin_required
def acerto_diario_v2_detalhe(request, pk):
    """
    Tela de edição do acerto diário V2:
    - Cabeçalho (data, valor estelar, observações)
    - Lista de carregamentos (clientes + descargas)
    - Lista de distribuições aos chapas
    - Modais para adicionar carregamento, descarga, distribuição
    - Botão "Salvar" que materializa em Lancamento V2 + recalcula AcumuladoFuncionario
    """
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    carregamentos = _carregamentos_ordenados(acerto)
    distribuicoes = list(
        DistribuicaoFuncionario.objects.filter(acerto_diario=acerto)
        .select_related('funcionario')
        .order_by('funcionario__nome')
    )

    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    cobrancas_pendentes_qs = (
        CobrancaCarregamento.objects.filter(status='Pendente')
        .select_related('cliente')
        .order_by('-criado_em')
    )
    ja_no_acerto = set(
        CarregamentoCliente.objects.filter(acerto_diario=acerto)
        .exclude(cobranca_carregamento__isnull=True)
        .values_list('cobranca_carregamento_id', flat=True)
    )
    cobrancas_pendentes = [c for c in cobrancas_pendentes_qs if c.pk not in ja_no_acerto][:200]

    diferenca = (acerto.total_carregamentos - acerto.total_distribuido).quantize(Decimal('0.01'))
    ja_aplicado_v2 = Lancamento.objects.filter(acerto_diario=acerto).exists()

    context = {
        'acerto': acerto,
        'carregamentos': carregamentos,
        'distribuicoes': distribuicoes,
        'funcionarios': funcionarios,
        'cobrancas_pendentes': cobrancas_pendentes,
        'diferenca': diferenca,
        'ja_aplicado_v2': ja_aplicado_v2,
        'qtd_lancamentos_v2': Lancamento.objects.filter(acerto_diario=acerto).count(),
    }
    return render(request, 'financeiro_v2/acerto_diario_v2_detalhe.html', context)


@login_required
@admin_required
@require_POST
def acerto_diario_v2_salvar(request, pk):
    """Salva o cabeçalho (valor_estelar + observações) e aplica no V2."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)

    valor_estelar_str = request.POST.get('valor_estelar', '0').strip().replace(',', '.')
    observacoes = request.POST.get('observacoes', '') or ''

    try:
        valor_estelar = Decimal(valor_estelar_str or '0')
        if valor_estelar < 0:
            return json_error('Valor Estelar não pode ser negativo.')
    except Exception:
        return json_error('Valor Estelar inválido.')

    acerto.valor_estelar = valor_estelar
    acerto.observacoes = observacoes
    acerto.save(update_fields=['valor_estelar', 'observacoes', 'atualizado_em'])

    try:
        resultado = services.aplicar_acerto_diario_v2(acerto, usuario=request.user)
    except ValueError as e:
        return json_error(str(e))
    except Exception as e:
        return json_error(f'Erro ao aplicar acerto V2: {e}')

    return json_success(
        message='Acerto salvo e aplicado no Financeiro V2.',
        acerto_id=acerto.pk,
        qtd_lancamentos=len(resultado['lancamentos']),
        descargas_dinheiro=str(resultado['descargas_dinheiro']),
        descargas_deposito=str(resultado['descargas_deposito']),
        valor_estelar=str(resultado['valor_estelar']),
        total_distribuido=str(resultado['total_distribuido']),
        total_carregamentos=str(resultado['total_carregamentos']),
    )


@login_required
@admin_required
@require_POST
def acerto_diario_v2_excluir(request, pk):
    """Exclui um acerto e seus efeitos no V2."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    try:
        services.excluir_acerto_diario_v2(acerto)
    except Exception as e:
        return json_error(f'Erro ao excluir acerto: {e}')
    return json_success(message='Acerto excluído com sucesso.')


# ----------------------------------------------------------------------------
# AJAX endpoints (Acerto V2)
# ----------------------------------------------------------------------------

@login_required
@admin_required
@require_POST
def acerto_v2_add_carregamento_cliente(request, pk):
    """Adiciona um carregamento de cliente ao acerto (vinculando cobrança pendente)."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    cobranca_id = request.POST.get('cobranca_id', '').strip()
    if not cobranca_id:
        return json_error('Informe a cobrança.')
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id, status='Pendente')

    if CarregamentoCliente.objects.filter(
        acerto_diario=acerto, cobranca_carregamento=cobranca
    ).exists():
        return json_error('Esta cobrança já foi adicionada a este acerto.')

    valor = cobranca.valor_carregamento or Decimal('0.00')
    if valor <= 0:
        return json_error('Cobrança sem valor de carregamento.')

    carreg = CarregamentoCliente.objects.create(
        acerto_diario=acerto,
        cliente=cobranca.cliente,
        valor=valor,
        descricao='',
        observacoes=f'Cobrança #{cobranca.pk}',
        cobranca_carregamento=cobranca,
    )
    return json_success(
        message='Carregamento adicionado.',
        carregamento_id=carreg.pk,
        cliente=cobranca.cliente.razao_social,
        valor=str(carreg.valor),
        valor_distribuicao=str(cobranca.valor_distribuicao_trabalhadores or ''),
        margem=str(cobranca.margem_carregamento or ''),
    )


@login_required
@admin_required
@require_POST
def acerto_v2_add_descarga(request, pk):
    """Adiciona uma descarga (sem cliente) ao acerto."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    descricao = (request.POST.get('descricao') or '').strip()
    valor_str = (request.POST.get('valor') or '').strip().replace(',', '.')
    tipo_pagamento = (request.POST.get('tipo_pagamento') or 'Dinheiro').strip().capitalize()

    if not descricao:
        return json_error('Descrição é obrigatória para descarga.')
    if tipo_pagamento not in ('Dinheiro', 'Deposito', 'Depósito'):
        return json_error('Tipo de pagamento inválido.')
    if tipo_pagamento == 'Depósito':
        tipo_pagamento = 'Deposito'

    try:
        valor = Decimal(valor_str or '0')
    except Exception:
        return json_error('Valor inválido.')
    if valor <= 0:
        return json_error('Valor deve ser maior que zero.')

    carreg = CarregamentoCliente.objects.create(
        acerto_diario=acerto,
        cliente=None,
        descricao=descricao,
        valor=valor,
        tipo_pagamento=tipo_pagamento,
    )
    return json_success(
        message='Descarga adicionada.',
        carregamento_id=carreg.pk,
        descricao=carreg.descricao,
        valor=str(carreg.valor),
        tipo_pagamento=carreg.tipo_pagamento or 'Dinheiro',
    )


@login_required
@admin_required
@require_POST
def acerto_v2_remove_carregamento(request, pk, carreg_pk):
    """Remove um carregamento/descarga do acerto."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    carreg = get_object_or_404(CarregamentoCliente, pk=carreg_pk, acerto_diario=acerto)
    carreg.delete()
    return json_success(message='Item removido.')


@login_required
@admin_required
@require_POST
def acerto_v2_add_distribuicao(request, pk):
    """Adiciona/atualiza uma distribuição aos chapas."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    funcionario_id = request.POST.get('funcionario_id', '').strip()
    valor_str = (request.POST.get('valor') or '').strip().replace(',', '.')
    if not funcionario_id:
        return json_error('Selecione o chapa.')
    funcionario = get_object_or_404(FuncionarioFluxoCaixa, pk=funcionario_id, ativo=True)

    try:
        valor = Decimal(valor_str or '0')
    except Exception:
        return json_error('Valor inválido.')
    if valor <= 0:
        return json_error('Valor deve ser maior que zero.')

    distrib, created = DistribuicaoFuncionario.objects.get_or_create(
        acerto_diario=acerto,
        funcionario=funcionario,
        defaults={'valor': valor},
    )
    if not created:
        distrib.valor = valor
        distrib.save(update_fields=['valor'])
    return json_success(
        message='Distribuição salva.',
        distribuicao_id=distrib.pk,
        funcionario_nome=funcionario.nome,
        valor=str(distrib.valor),
        criado=created,
    )


@login_required
@admin_required
@require_POST
def acerto_v2_remove_distribuicao(request, pk, distrib_pk):
    """Remove uma distribuição."""
    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=pk)
    distrib = get_object_or_404(DistribuicaoFuncionario, pk=distrib_pk, acerto_diario=acerto)
    distrib.delete()
    return json_success(message='Distribuição removida.')
