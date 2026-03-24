"""View de fechamento de caixa (painel consolidado)."""
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from notas.decorators import admin_required
from notas.models import CobrancaCarregamento, CobrancaCTEAvulsa
from financeiro.models import AcumuladoFuncionario, MovimentoCaixa, ReceitaEmpresa
from financeiro.services import PeriodoCaixaService


def _eh_saida_caixa_real(mov: MovimentoCaixa) -> bool:
    """Regra de cálculo do saldo real do caixa (mesma usada no caixa do dia)."""
    if mov.tipo == 'Saida':
        return True
    if mov.tipo == 'AcertoFuncionario' and not mov.acerto_diario_id:
        return True
    return False


def _parse_decimal_br(valor):
    """Converte valor monetário (pt-BR/en) para Decimal."""
    if valor is None:
        return Decimal('0.00')
    texto = str(valor).strip()
    if not texto:
        return Decimal('0.00')
    texto = texto.replace(' ', '').replace('R$', '').replace('r$', '')
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    return Decimal(texto)


@login_required
@admin_required
def fechamento_caixa(request):
    """
    Painel de fechamento em 3 seções:
    - Saldo
    - A Pagar (acumulados pendentes de funcionários)
    - A Receber (cobranças de carregamento pendentes)
    """
    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()

    saldo_movimento = Decimal('0.00')
    total_entradas = Decimal('0.00')
    total_saidas = Decimal('0.00')
    total_movimentos = 0
    total_estelar = Decimal('0.00')
    total_cte = Decimal('0.00')
    receitas_personalizadas_agrupadas = []
    total_receitas_personalizadas = Decimal('0.00')

    if periodo_ativo:
        movimentos = list(
            MovimentoCaixa.objects.filter(periodo=periodo_ativo).select_related('acerto_diario')
        )
        total_movimentos = len(movimentos)
        saldo_movimento = periodo_ativo.valor_inicial_caixa or Decimal('0.00')
        for mov in movimentos:
            if _eh_saida_caixa_real(mov):
                total_saidas += mov.valor or Decimal('0.00')
                saldo_movimento -= mov.valor or Decimal('0.00')
            else:
                total_entradas += mov.valor or Decimal('0.00')
                saldo_movimento += mov.valor or Decimal('0.00')

        # Totais por tipo de receita dentro do período ativo
        data_inicio_periodo = periodo_ativo.data_inicio
        data_fim_periodo = periodo_ativo.data_fim or timezone.now().date()
        receitas_periodo = ReceitaEmpresa.objects.filter(
            data__gte=data_inicio_periodo,
            data__lte=data_fim_periodo,
        )
        receitas_estelar = sum(
            (r.valor or Decimal('0.00'))
            for r in receitas_periodo.filter(tipo_receita__iexact='Estelar')
        )
        receitas_cte = sum(
            (r.valor or Decimal('0.00'))
            for r in receitas_periodo.filter(
                Q(tipo_receita__iexact='CTE') | Q(tipo_receita__iexact='Manifesto')
            )
        )

        # Cobranças do período:
        # - Margem Estelar compõe o campo Estelar no fechamento
        # - Lucro CTE compõe o campo CTE no fechamento
        cobrancas_periodo = CobrancaCarregamento.objects.filter(
            criado_em__date__gte=data_inicio_periodo,
            criado_em__date__lte=data_fim_periodo,
        )
        margem_estelar_baixada = sum(
            (c.margem_carregamento or Decimal('0.00'))
            for c in cobrancas_periodo
        )
        lucro_cte_baixado = sum(
            (c.lucro_cte or Decimal('0.00'))
            for c in cobrancas_periodo
        )
        lucro_cte_avulso_periodo = sum(
            (c.lucro_cte or Decimal('0.00'))
            for c in CobrancaCTEAvulsa.objects.filter(
                criado_em__date__gte=data_inicio_periodo,
                criado_em__date__lte=data_fim_periodo,
            )
        )

        # Estelar:
        # - Receitas registradas como Estelar
        # - Margem das cobranças de carregamento
        # - Apenas movimentos de caixa direcionados à Estelar
        #   (categoria Estelar ou descrição contendo "estelar")
        impacto_movimento_estelar = sum(
            (mov.valor or Decimal('0.00')) if mov.tipo == 'Entrada' else -(mov.valor or Decimal('0.00'))
            for mov in movimentos
            if mov.tipo in ('Entrada', 'Saida')
            and (
                (mov.categoria or '') == 'Estelar'
                or 'estelar' in (mov.descricao or '').lower()
            )
        )
        total_estelar = receitas_estelar + margem_estelar_baixada + impacto_movimento_estelar
        total_cte = receitas_cte + lucro_cte_baixado + lucro_cte_avulso_periodo

        grupos_pers = defaultdict(
            lambda: {
                'total': Decimal('0.00'),
                'ids': [],
                'data_ref': None,
                '_last_em': None,
            }
        )
        for r in (
            receitas_periodo.filter(tipo_receita__iexact='Outro')
            .filter(rotulo_personalizado__isnull=False)
            .exclude(rotulo_personalizado='')
            .order_by('criado_em')
        ):
            rot = (r.rotulo_personalizado or '').strip()
            if not rot:
                continue
            g = grupos_pers[rot]
            g['total'] += r.valor or Decimal('0.00')
            g['ids'].append(r.pk)
            if g['_last_em'] is None or r.criado_em >= g['_last_em']:
                g['data_ref'] = r.data
                g['_last_em'] = r.criado_em
        receitas_personalizadas_agrupadas = sorted(
            (
                {
                    'rotulo': k,
                    'total': v['total'],
                    'ids': v['ids'],
                    'data_ref': v['data_ref'],
                }
                for k, v in grupos_pers.items()
            ),
            key=lambda x: x['rotulo'].lower(),
        )
        total_receitas_personalizadas = sum(
            (x['total'] for x in receitas_personalizadas_agrupadas),
            Decimal('0.00'),
        )

    # Saldo (card verde no topo): soma dos indicadores da seção 1)
    saldo_consolidado = (
        saldo_movimento + total_estelar + total_cte + total_receitas_personalizadas
    )

    acumulados_pendentes = list(
        AcumuladoFuncionario.objects.filter(status='Pendente')
        .select_related('funcionario')
        .order_by('funcionario__nome', '-semana_inicio')
    )
    acumulados_pendentes = [
        a for a in acumulados_pendentes if (a.valor_acumulado or Decimal('0.00')) > 0
    ]
    total_a_pagar_funcionarios = sum((a.valor_acumulado or Decimal('0.00')) for a in acumulados_pendentes)
    cte_terceiro_pendentes = list(
        CobrancaCarregamento.objects.filter(
            status_cte_terceiro__iexact='Pendente',
            valor_cte_terceiro__gt=0,
        )
        .select_related('cliente')
        .order_by('-data_baixa', '-criado_em')
    )
    cte_terceiro_avulso_pendentes = list(
        CobrancaCTEAvulsa.objects.filter(
            status_cte_terceiro__iexact='Pendente',
            valor_cte_terceiro__gt=0,
        ).order_by('-criado_em')
    )
    cte_terceiro_pendentes.extend(cte_terceiro_avulso_pendentes)
    total_a_pagar_cte_terceiro = sum(
        (c.valor_cte_terceiro or Decimal('0.00'))
        for c in cte_terceiro_pendentes
    )
    total_a_pagar = total_a_pagar_funcionarios + total_a_pagar_cte_terceiro

    cobrancas_pendentes = list(
        CobrancaCarregamento.objects.filter(status='Pendente')
        .select_related('cliente')
        .order_by('cliente__razao_social', '-criado_em')
    )
    cobrancas_cte_avulsa_pendentes = list(
        CobrancaCTEAvulsa.objects.filter(status='Pendente').order_by('-criado_em')
    )
    total_a_receber = (
        sum((c.valor_total or Decimal('0.00')) for c in cobrancas_pendentes)
        + sum((c.valor_cte_manifesto or Decimal('0.00')) for c in cobrancas_cte_avulsa_pendentes)
    )

    saldo_projetado = saldo_consolidado + total_a_receber - total_a_pagar

    saldo_banco_informado = ''
    estelar_saldo_anterior = ''
    cte_manifesto_saldo_anterios = ''
    if request.method == 'POST':
        saldo_banco_informado = request.POST.get('saldo_banco_informado', '').strip()
        estelar_saldo_anterior = request.POST.get('estelar_saldo_anterior', '').strip()
        cte_manifesto_saldo_anterios = request.POST.get('cte_manifesto_saldo_anterios', '').strip()
    else:
        saldo_banco_informado = request.session.get('fechamento_saldo_banco_informado', '')
        estelar_saldo_anterior = request.session.get('fechamento_estelar_saldo_anterior', '')
        cte_manifesto_saldo_anterios = request.session.get('fechamento_cte_manifesto_saldo_anterios', '')

    saldo_banco_decimal = None
    divergencia_conciliacao = None

    if request.method == 'POST':
        acao = request.POST.get('acao')
        try:
            if saldo_banco_informado:
                saldo_banco_decimal = _parse_decimal_br(saldo_banco_informado)
                divergencia_conciliacao = saldo_banco_decimal - saldo_movimento
        except (InvalidOperation, ValueError):
            messages.error(request, 'Saldo do banco inválido. Informe um valor numérico válido.')
            return redirect('financeiro:fechamento_caixa')

        if acao == 'fechar_caixa':
            if not periodo_ativo:
                messages.warning(request, 'Não há período aberto para fechar.')
                return redirect('financeiro:fechamento_caixa')

            ok, erro = PeriodoCaixaService.fechar_periodo(periodo_ativo)
            if erro:
                messages.error(request, erro)
            elif not ok:
                messages.warning(request, 'Não foi possível fechar o período.')
            else:
                if divergencia_conciliacao is not None and divergencia_conciliacao != Decimal('0.00'):
                    messages.warning(
                        request,
                        f'Período fechado com divergência de conciliação: R$ {divergencia_conciliacao:.2f}.'
                    )
                else:
                    messages.success(request, 'Período fechado com sucesso.')
            return redirect('financeiro:fechamento_caixa')

    context = {
        'periodo_ativo': periodo_ativo,
        'saldo_movimento': saldo_movimento,
        'saldo_consolidado': saldo_consolidado,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'total_movimentos': total_movimentos,
        'total_estelar': total_estelar,
        'total_cte': total_cte,
        'receitas_personalizadas_agrupadas': receitas_personalizadas_agrupadas,
        'total_receitas_personalizadas': total_receitas_personalizadas,
        'acumulados_pendentes': acumulados_pendentes,
        'total_a_pagar_funcionarios': total_a_pagar_funcionarios,
        'total_a_pagar_cte_terceiro': total_a_pagar_cte_terceiro,
        'cte_terceiro_pendentes': cte_terceiro_pendentes,
        'total_a_pagar': total_a_pagar,
        'cobrancas_pendentes': cobrancas_pendentes,
        'cobrancas_cte_avulsa_pendentes': cobrancas_cte_avulsa_pendentes,
        'total_a_receber': total_a_receber,
        'saldo_projetado': saldo_projetado,
        'saldo_banco_informado': saldo_banco_informado,
        'estelar_saldo_anterior': estelar_saldo_anterior,
        'cte_manifesto_saldo_anterios': cte_manifesto_saldo_anterios,
        'saldo_banco_decimal': saldo_banco_decimal,
        'divergencia_conciliacao': divergencia_conciliacao,
    }
    return render(request, 'financeiro/fluxo_caixa/fechamento_caixa.html', context)


def _data_lancamento_fechamento(data_str, periodo_ativo):
    """Retorna date dentro do período ou (None, mensagem_erro)."""
    if not periodo_ativo:
        return None, 'Não há período aberto.'
    texto = (data_str or '').strip()
    d = parse_date(texto) if texto else timezone.now().date()
    if not d:
        return None, 'Data inválida.'
    ini = periodo_ativo.data_inicio
    fim = periodo_ativo.data_fim or timezone.now().date()
    if d < ini or d > fim:
        return None, 'Informe uma data dentro do período aberto.'
    return d, None


def _parse_receita_ids_post(raw):
    if not raw or not str(raw).strip():
        return []
    out = []
    for x in str(raw).split(','):
        x = x.strip()
        if x.isdigit():
            out.append(int(x))
    return out


def _validar_receitas_outro_periodo(ids, periodo_ativo):
    """Receitas tipo Outro do período (campos personalizados do fechamento)."""
    if not ids:
        return None, 'Nenhum registro informado.'
    if len(set(ids)) != len(ids):
        return None, 'Lista de registros inválida.'
    qs = ReceitaEmpresa.objects.filter(pk__in=ids)
    if qs.count() != len(ids):
        return None, 'Registro não encontrado.'
    data_ini = periodo_ativo.data_inicio
    data_fim = periodo_ativo.data_fim or timezone.now().date()
    rotulos = set()
    for r in qs:
        tr = (r.tipo_receita or '').strip().lower()
        if tr != 'outro':
            return None, 'Somente lançamentos de campo personalizado podem ser alterados ou excluídos.'
        rd = r.data
        if rd < data_ini or rd > data_fim:
            return None, 'Data do lançamento fora do período aberto.'
        rot = (r.rotulo_personalizado or '').strip()
        if not rot:
            return None, 'Lançamento inválido (sem rótulo).'
        rotulos.add(rot)
    if len(rotulos) != 1:
        return None, 'Lote de lançamentos inválido.'
    return qs, None


@login_required
@admin_required
@require_POST
def fechamento_receita_entrada(request):
    """Registra receita (Estelar/CTE ou campo nomeado) a partir do botão Criar entrada."""
    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if not periodo_ativo:
        return JsonResponse({'ok': False, 'error': 'Não há período aberto.'}, status=400)

    operacao = (request.POST.get('operacao') or 'salvar').strip().lower()
    rec_ids = _parse_receita_ids_post(request.POST.get('receita_ids', ''))

    if operacao == 'excluir':
        if not rec_ids:
            return JsonResponse({'ok': False, 'error': 'Nenhum registro para excluir.'}, status=400)
        qs, verr = _validar_receitas_outro_periodo(rec_ids, periodo_ativo)
        if verr:
            return JsonResponse({'ok': False, 'error': verr}, status=400)
        qs.delete()
        return JsonResponse({'ok': True})

    modo = (request.POST.get('modo') or '').strip()
    descricao_extra = (request.POST.get('descricao') or '').strip()

    d, err = _data_lancamento_fechamento(request.POST.get('data'), periodo_ativo)
    if err:
        return JsonResponse({'ok': False, 'error': err}, status=400)

    desc_base = 'Entrada registrada no fechamento de caixa.'
    desc_full = f'{desc_base} {descricao_extra}'.strip()[:2000]

    try:
        if modo == 'campos_existentes':
            if rec_ids:
                return JsonResponse(
                    {'ok': False, 'error': 'Edição de receitas não se aplica a Estelar/CTE neste fluxo.'},
                    status=400,
                )
            ve = _parse_decimal_br(request.POST.get('valor_estelar'))
            vc = _parse_decimal_br(request.POST.get('valor_cte'))
            if ve <= 0 and vc <= 0:
                return JsonResponse(
                    {'ok': False, 'error': 'Informe valor em Estelar e/ou CTE/Manifesto.'},
                    status=400,
                )
            if ve > 0:
                ReceitaEmpresa.objects.create(
                    data=d,
                    tipo_receita='Estelar',
                    valor=ve,
                    descricao=desc_full,
                    usuario_criacao=request.user,
                )
            if vc > 0:
                ReceitaEmpresa.objects.create(
                    data=d,
                    tipo_receita='CTE',
                    valor=vc,
                    descricao=desc_full,
                    usuario_criacao=request.user,
                )
        elif modo == 'novo_campo':
            nome = (request.POST.get('nome_campo') or '').strip()
            vp = _parse_decimal_br(request.POST.get('valor_personalizado'))
            if not nome:
                return JsonResponse({'ok': False, 'error': 'Informe o nome do campo.'}, status=400)
            if vp <= 0:
                return JsonResponse({'ok': False, 'error': 'Informe um valor maior que zero.'}, status=400)
            if rec_ids:
                qs, verr = _validar_receitas_outro_periodo(rec_ids, periodo_ativo)
                if verr:
                    return JsonResponse({'ok': False, 'error': verr}, status=400)
                qs.delete()
            ReceitaEmpresa.objects.create(
                data=d,
                tipo_receita='Outro',
                valor=vp,
                rotulo_personalizado=nome[:120],
                descricao=desc_full,
                usuario_criacao=request.user,
            )
        else:
            return JsonResponse({'ok': False, 'error': 'Modo inválido.'}, status=400)
    except (InvalidOperation, ValueError):
        return JsonResponse({'ok': False, 'error': 'Valor ou data inválidos.'}, status=400)

    return JsonResponse({'ok': True})
