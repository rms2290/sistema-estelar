"""
Views do MVP de Caixa Único (diário):
- Caixa do dia (movimentos reais do período aberto)
- A receber (cobranças pendentes) com ação de receber (baixa + entrada no caixa)
- A pagar (acumulados pendentes) com ação de pagar (baixa + saída do caixa)
"""

from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from notas.decorators import admin_required
from notas.models import CobrancaCarregamento, Cliente

from financeiro.models import AcumuladoFuncionario, CarregamentoCliente, MovimentoCaixa, PeriodoMovimentoCaixa
from financeiro.services import MovimentoCaixaService, PeriodoCaixaService


def _eh_saida_caixa_real(mov: MovimentoCaixa) -> bool:
    """
    Regra para saldo do Caixa do Dia (dinheiro real).

    - Saida: sempre saída.
    - AcertoFuncionario sem acerto_diario (pagamento avulso): saída (compatível com telas existentes).
    - Demais: entrada.
    """
    if mov.tipo == 'Saida':
        return True
    if mov.tipo == 'AcertoFuncionario' and not mov.acerto_diario_id:
        return True
    return False


def _marker_descarga_deposito(descarga_id: int) -> str:
    """
    Marcador único para identificar a baixa da "descarga (Depósito)".

    Como CarregamentoCliente não tem campo de status/baixa,
    a gente considera baixado quando existe um MovimentoCaixa de entrada
    com categoria RecebimentoDescarga contendo esse marcador.
    """
    return f"[DESCARGA_DEPOSITO:{descarga_id}]"


@login_required
@admin_required
def caixa_do_dia(request):
    """
    Tela principal do MVP: Caixa do dia baseado no período aberto.
    """
    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()

    if request.method == 'POST' and request.POST.get('acao') == 'iniciar_periodo':
        data_inicio = request.POST.get('data_inicio') or timezone.now().date().isoformat()
        valor_inicial_str = request.POST.get('valor_inicial_caixa', '0.00')
        try:
            valor_inicial = Decimal(valor_inicial_str)
        except Exception:
            messages.error(request, 'Valor inicial inválido.')
            return redirect('financeiro:caixa_do_dia')

        periodo, erro = PeriodoCaixaService.iniciar_periodo(
            data_inicio=data_inicio,
            valor_inicial_caixa=valor_inicial,
            observacoes='Período diário (Caixa do Dia)',
            usuario=request.user,
        )
        if erro:
            messages.warning(request, erro)
            return redirect('financeiro:caixa_do_dia')
        messages.success(request, 'Caixa do dia iniciado com sucesso.')
        return redirect('financeiro:caixa_do_dia')

    movimentos = MovimentoCaixa.objects.none()
    saldo_inicial = Decimal('0.00')
    saldo_atual = Decimal('0.00')
    movimentos_com_saldo = []

    if periodo_ativo:
        saldo_inicial = periodo_ativo.valor_inicial_caixa or Decimal('0.00')
        movimentos = (
            MovimentoCaixa.objects.filter(periodo=periodo_ativo)
            .select_related('funcionario', 'cliente', 'acerto_diario', 'usuario_criacao')
            .order_by('data', 'criado_em')
        )
        saldo = saldo_inicial
        for mov in movimentos:
            if _eh_saida_caixa_real(mov):
                saldo -= mov.valor
                sinal = '-'
            else:
                saldo += mov.valor
                sinal = '+'
            movimentos_com_saldo.append(
                {
                    'movimento': mov,
                    'saldo': saldo,
                    'sinal': sinal,
                    'exibir_como_saida': _eh_saida_caixa_real(mov),
                }
            )
        saldo_atual = saldo

    return render(
        request,
        'financeiro/caixa_unico/caixa_do_dia.html',
        {
            'periodo_ativo': periodo_ativo,
            'saldo_inicial': saldo_inicial,
            'saldo_atual': saldo_atual,
            'movimentos_com_saldo': movimentos_com_saldo,
        },
    )


@login_required
@admin_required
def a_receber(request):
    """
    Lista contas a receber:
    - Cobranças de carregamento (clientes)
    - Descargas lançadas no acerto diário com tipo de pagamento Depósito
    """
    status = request.GET.get('status') or 'Pendente'
    cliente_id = request.GET.get('cliente') or ''
    data_inicio = request.GET.get('data_inicio') or ''
    data_fim = request.GET.get('data_fim') or ''

    qs = CobrancaCarregamento.objects.all().select_related('cliente').prefetch_related('romaneios')
    if status in ('Pendente', 'Baixado'):
        qs = qs.filter(status=status)
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)
    if data_inicio:
        try:
            di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            qs = qs.filter(criado_em__date__gte=di)
        except Exception:
            pass
    if data_fim:
        try:
            df = datetime.strptime(data_fim, '%Y-%m-%d').date()
            qs = qs.filter(criado_em__date__lte=df)
        except Exception:
            pass

    qs = qs.order_by('-criado_em')
    cobrancas_lista = list(qs)

    # Descargas por depósito entram como "a receber" (não transitam no caixa em espécie).
    descargas_deposito = CarregamentoCliente.objects.filter(
        cliente__isnull=True,
        tipo_pagamento='Deposito',
    ).select_related('acerto_diario')
    if data_inicio:
        try:
            di = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            descargas_deposito = descargas_deposito.filter(acerto_diario__data__gte=di)
        except Exception:
            pass
    if data_fim:
        try:
            df = datetime.strptime(data_fim, '%Y-%m-%d').date()
            descargas_deposito = descargas_deposito.filter(acerto_diario__data__lte=df)
        except Exception:
            pass
    descargas_deposito = descargas_deposito.order_by('-acerto_diario__data', '-id')
    descargas_lista = list(descargas_deposito)

    recebiveis = []
    for c in cobrancas_lista:
        recebiveis.append(
            {
                'tipo': 'cobranca_cliente',
                'id': c.id,
                'origem': 'Cobrança de Carregamento',
                'referencia': f'Cobrança #{c.id}',
                'nome': c.cliente.razao_social,
                'valor': c.valor_total or Decimal('0.00'),
                'status': c.status,
                'data': c.criado_em.date() if c.criado_em else None,
                'cobranca': c,
            }
        )

    # Descarga via depósito: considera "baixado" quando houver MovimentoCaixa
    # (Entrada/RecebimentoDescarga) contendo o marcador.
    for d in descargas_lista:
        marker = _marker_descarga_deposito(d.id)
        ja_baixado = MovimentoCaixa.objects.filter(
            tipo='Entrada',
            categoria='RecebimentoDescarga',
            descricao__icontains=marker,
        ).exists()

        item_status = 'Baixado' if ja_baixado else 'Pendente'
        if status in ('Pendente', 'Baixado') and item_status != status:
            continue

        recebiveis.append(
            {
                'tipo': 'descarga_deposito',
                'id': d.id,
                'origem': 'Descarga (Depósito)',
                'referencia': (
                    f'Acerto {d.acerto_diario.data.strftime("%d/%m/%Y")}'
                    if d.acerto_diario
                    else 'Acerto Diário'
                ),
                'nome': d.nome_display,
                'valor': d.valor or Decimal('0.00'),
                'status': item_status,
                'data': d.acerto_diario.data if d.acerto_diario else None,
                'descarga': d,
            }
        )

    recebiveis.sort(key=lambda x: (x['data'] or timezone.now().date(), x['id']), reverse=True)
    total_pendente = (
        sum((item['valor'] or Decimal('0.00')) for item in recebiveis if item['status'] == 'Pendente')
        if status == 'Pendente'
        else Decimal('0.00')
    )
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    return render(
        request,
        'financeiro/caixa_unico/a_receber.html',
        {
            'recebiveis': recebiveis,
            'clientes': clientes,
            'status': status,
            'cliente_id': cliente_id,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'total_pendente': total_pendente,
        },
    )


@login_required
@admin_required
def receber_cobranca(request, cobranca_id: int):
    """
    Recebe (baixa) uma cobrança pendente e registra entrada no caixa do dia (período aberto).
    """
    cobranca = get_object_or_404(CobrancaCarregamento.objects.select_related('cliente'), pk=cobranca_id)
    if request.method != 'POST':
        return redirect('financeiro:a_receber')
    if cobranca.status != 'Pendente':
        messages.info(request, 'Cobrança já está baixada.')
        return redirect('financeiro:a_receber')

    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if not periodo_ativo:
        messages.warning(request, 'Inicie um período no Movimento de Caixa antes de receber cobranças.')
        return redirect('financeiro:gerenciar_movimento_caixa')

    valor = cobranca.valor_total or Decimal('0.00')
    descricao = f"Recebimento Cobrança #{cobranca.id} - {cobranca.cliente.razao_social}"
    movimento, erro = MovimentoCaixaService.criar_movimento(
        data=timezone.now().date().isoformat(),
        tipo='Entrada',
        valor=valor,
        descricao=descricao,
        categoria='RecebimentoCarregamento',
        funcionario_id=None,
        cliente_id=cobranca.cliente_id,
        acerto_diario_id=None,
        usuario=request.user,
    )
    if erro:
        messages.error(request, erro)
        return redirect('financeiro:a_receber')

    cobranca.baixar()
    messages.success(request, f'Cobrança #{cobranca.id} recebida e entrada registrada no caixa.')
    return redirect('financeiro:a_receber')


@login_required
@admin_required
def receber_descarga_deposito(request, carregamento_id: int):
    """
    Dá baixa na descarga registrada como Depósito (CarregamentoCliente):
    - cria um MovimentoCaixa (Entrada/RecebimentoDescarga)
    - marca como baixado para a tela consultando o marcador no descricao
    """
    if request.method != 'POST':
        return redirect('financeiro:a_receber')

    descarga = get_object_or_404(
        CarregamentoCliente.objects.select_related('acerto_diario'),
        pk=carregamento_id,
        cliente__isnull=True,
        tipo_pagamento='Deposito',
    )

    marker = _marker_descarga_deposito(descarga.id)
    ja_baixado = MovimentoCaixa.objects.filter(
        tipo='Entrada',
        categoria='RecebimentoDescarga',
        descricao__icontains=marker,
    ).exists()
    if ja_baixado:
        messages.info(request, 'Descarga (Depósito) já está baixada.')
        return redirect('financeiro:a_receber')

    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if not periodo_ativo:
        messages.warning(
            request,
            'Inicie um período no Movimento de Caixa antes de receber descargas (Depósito).'
        )
        return redirect('financeiro:gerenciar_movimento_caixa')

    valor = descarga.valor or Decimal('0.00')
    texto_descarga = (descarga.descricao or '').strip() or (descarga.nome_display or 'Descarga')
    # Mantemos o marcador no descricao para identificar baixa,
    # mas o texto exibido será limpo em MovimentoCaixa.descricao_exibicao.
    descricao = f"Recebimento de Descarga: {texto_descarga} {marker}"
    movimento, erro = MovimentoCaixaService.criar_movimento(
        data=timezone.now().date().isoformat(),
        tipo='Entrada',
        valor=valor,
        descricao=descricao,
        categoria='RecebimentoDescarga',
        funcionario_id=None,
        cliente_id=None,
        acerto_diario_id=descarga.acerto_diario_id,
        usuario=request.user,
    )
    if erro:
        messages.error(request, erro)
        return redirect('financeiro:a_receber')

    messages.success(request, 'Descarga (Depósito) baixada e entrada registrada no caixa.')
    return redirect('financeiro:a_receber')


@login_required
@admin_required
def a_pagar(request):
    """
    Lista acumulados pendentes por funcionário (contas a pagar).
    """
    pendentes = (
        AcumuladoFuncionario.objects.filter(status='Pendente')
        .select_related('funcionario')
        .order_by('funcionario__nome', '-semana_inicio')
    )
    # Mostrar apenas os que têm valor > 0
    pendentes = [a for a in pendentes if (a.valor_acumulado or Decimal('0.00')) > 0]
    total = sum((a.valor_acumulado or Decimal('0.00')) for a in pendentes)

    return render(
        request,
        'financeiro/caixa_unico/a_pagar.html',
        {'acumulados': pendentes, 'total_pendente': total},
    )


@login_required
@admin_required
def pagar_funcionario(request, acumulado_id: int):
    """
    Marca acumulado como depositado e registra saída no caixa do dia (período aberto).
    """
    acumulado = get_object_or_404(AcumuladoFuncionario.objects.select_related('funcionario'), pk=acumulado_id)
    if request.method != 'POST':
        return redirect('financeiro:a_pagar')
    if acumulado.status != 'Pendente' or (acumulado.valor_acumulado or Decimal('0.00')) <= 0:
        messages.info(request, 'Nada a pagar para este registro.')
        return redirect('financeiro:a_pagar')

    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if not periodo_ativo:
        messages.warning(request, 'Inicie um período no Movimento de Caixa antes de pagar funcionários.')
        return redirect('financeiro:gerenciar_movimento_caixa')

    valor = acumulado.valor_acumulado or Decimal('0.00')
    descricao = (
        f"Pagamento Funcionário {acumulado.funcionario.nome} "
        f"(Semana {acumulado.semana_inicio.strftime('%d/%m/%Y')} a {acumulado.semana_fim.strftime('%d/%m/%Y')})"
    )
    movimento, erro = MovimentoCaixaService.criar_movimento(
        data=timezone.now().date().isoformat(),
        tipo='Saida',
        valor=valor,
        descricao=descricao,
        categoria='Outros',
        funcionario_id=acumulado.funcionario_id,
        cliente_id=None,
        acerto_diario_id=None,
        usuario=request.user,
    )
    if erro:
        messages.error(request, erro)
        return redirect('financeiro:a_pagar')

    acumulado.marcar_depositado(data_deposito=timezone.now().date())
    messages.success(request, 'Pagamento registrado e acumulado baixado.')
    return redirect('financeiro:a_pagar')

