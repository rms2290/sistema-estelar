"""
Services do Financeiro V2.

Funções que orquestram operações compostas (baixa de cobrança, pagamento, etc.).
Mantidos separados das views para facilitar testes e reuso.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from financeiro.models import (
    AcertoDiarioCarregamento,
    AcumuladoFuncionario,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
)
from notas.models import CobrancaCarregamento, CobrancaCTEAvulsa
from .models import Bolso, Carteira, Lancamento


def semana_da_data(d: date):
    """Retorna (segunda, domingo) da semana ISO da data."""
    weekday = d.weekday()  # segunda=0 ... domingo=6
    inicio = d - timedelta(days=weekday)
    fim = inicio + timedelta(days=6)
    return inicio, fim


def _bolsos_para_baixa():
    """Retorna o trio de bolsos usados na distribuição automática de recebimentos."""
    return {
        'operacional': Bolso.objects.get(codigo='OPERACIONAL'),
        'estelar': Bolso.objects.get(codigo='ESTELAR'),
        'documentacao': Bolso.objects.get(codigo='DOCUMENTACAO'),
    }


def calcular_distribuicao_carregamento(cobranca: CobrancaCarregamento):
    """
    Calcula como o valor da cobrança seria dividido nos bolsos.

    Retorna lista de dicts: {'bolso_codigo', 'bolso_nome', 'valor', 'descricao'}.
    Ordem: Operacional, Estelar, Documentação.
    """
    v_carreg = cobranca.valor_carregamento or Decimal('0.00')
    v_dist = cobranca.valor_distribuicao_trabalhadores
    if v_dist is None:
        v_dist = Decimal('0.00')
    margem = max(Decimal('0.00'), v_carreg - v_dist)
    v_cte = cobranca.valor_cte_manifesto or Decimal('0.00')

    return [
        {
            'bolso_codigo': 'OPERACIONAL',
            'bolso_nome': 'Operacional',
            'valor': v_dist,
            'descricao': 'Parte que vai pagar os chapas',
        },
        {
            'bolso_codigo': 'ESTELAR',
            'bolso_nome': 'Estelar',
            'valor': margem,
            'descricao': 'Margem do carregamento (lucro empresa)',
        },
        {
            'bolso_codigo': 'DOCUMENTACAO',
            'bolso_nome': 'Documentação',
            'valor': v_cte,
            'descricao': 'CTE/Manifesto (paga terceiro + sobra para gerentes)',
        },
    ]


def calcular_distribuicao_cte_avulsa(cobranca: CobrancaCTEAvulsa):
    """Calcula como o valor da CTE avulsa seria dividido nos bolsos."""
    v_cte = cobranca.valor_cte_manifesto or Decimal('0.00')
    return [
        {
            'bolso_codigo': 'DOCUMENTACAO',
            'bolso_nome': 'Documentação',
            'valor': v_cte,
            'descricao': 'CTE/Manifesto avulso (paga terceiro + sobra para gerentes)',
        },
    ]


def aplicar_baixa_carregamento(
    cobranca: CobrancaCarregamento,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """
    Marca CobrancaCarregamento como Baixado e cria lançamentos V2 nos bolsos.

    Os lançamentos só são criados para componentes com valor > 0.
    Tudo dentro de transação atômica.
    """
    if cobranca.status == 'Baixado':
        raise ValueError('Cobrança já está baixada.')

    bolsos = _bolsos_para_baixa()
    distribuicao = calcular_distribuicao_carregamento(cobranca)
    cliente_nome = cobranca.cliente.razao_social if cobranca.cliente else 'Sem cliente'

    lancs = []
    with transaction.atomic():
        cobranca.status = 'Baixado'
        cobranca.data_baixa = data_pagamento
        cobranca.save(update_fields=['status', 'data_baixa', 'atualizado_em'])

        for item in distribuicao:
            valor = item['valor']
            if valor <= 0:
                continue
            bolso_obj = bolsos[item['bolso_codigo'].lower()]
            descricao = (
                f'Recebimento Cobrança #{cobranca.id} - {cliente_nome} '
                f'({item["bolso_nome"]})'
            )
            lancs.append(Lancamento.objects.create(
                data=data_pagamento,
                carteira=carteira,
                bolso=bolso_obj,
                tipo='Entrada',
                valor=valor,
                descricao=descricao,
                categoria='Recebimento Cobrança',
                cliente=cobranca.cliente,
                cobranca_carregamento=cobranca,
                criado_por=usuario,
            ))

    return lancs


def aplicar_baixa_cte_avulsa(
    cobranca: CobrancaCTEAvulsa,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """Marca CobrancaCTEAvulsa como Baixado e cria 1 lançamento em Documentação."""
    if cobranca.status == 'Baixado':
        raise ValueError('Cobrança já está baixada.')

    bolso_doc = Bolso.objects.get(codigo='DOCUMENTACAO')
    valor = cobranca.valor_cte_manifesto or Decimal('0.00')

    lancs = []
    with transaction.atomic():
        cobranca.status = 'Baixado'
        cobranca.data_baixa = data_pagamento
        cobranca.save(update_fields=['status', 'data_baixa', 'atualizado_em'])

        if valor > 0:
            lancs.append(Lancamento.objects.create(
                data=data_pagamento,
                carteira=carteira,
                bolso=bolso_doc,
                tipo='Entrada',
                valor=valor,
                descricao=f'Recebimento CTE Avulsa #{cobranca.id} - {cobranca.nome}',
                categoria='Recebimento CTE Avulsa',
                cobranca_cte_avulsa=cobranca,
                criado_por=usuario,
            ))

    return lancs


# ============================================================================
# A Pagar (Onda 4)
# ============================================================================

def aplicar_pagamento_chapa(
    acumulado: AcumuladoFuncionario,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """
    Marca AcumuladoFuncionario como Depositado e cria Saída no bolso Operacional.
    """
    if acumulado.status == 'Depositado':
        raise ValueError('Acumulado já está pago.')

    valor = acumulado.valor_acumulado or Decimal('0.00')
    if valor <= 0:
        raise ValueError(f'Acumulado tem valor zerado (R$ {valor}).')

    bolso_op = Bolso.objects.get(codigo='OPERACIONAL')

    with transaction.atomic():
        acumulado.status = 'Depositado'
        acumulado.data_deposito = data_pagamento
        acumulado.save(update_fields=['status', 'data_deposito', 'atualizado_em'])

        descricao = (
            f'Pagamento chapa {acumulado.funcionario.nome} - '
            f'semana {acumulado.semana_inicio:%d/%m} a {acumulado.semana_fim:%d/%m}'
        )
        lanc = Lancamento.objects.create(
            data=data_pagamento,
            carteira=carteira,
            bolso=bolso_op,
            tipo='Saida',
            valor=valor,
            descricao=descricao,
            categoria='Pagamento Chapa',
            funcionario=acumulado.funcionario,
            criado_por=usuario,
        )

    return [lanc]


def aplicar_pagamento_terceiro_carregamento(
    cobranca: CobrancaCarregamento,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """Marca status_cte_terceiro=Pago e cria Saída no bolso Documentação."""
    if (cobranca.status_cte_terceiro or '').lower() == 'pago':
        raise ValueError('Pagamento ao terceiro já foi feito.')

    valor = cobranca.valor_cte_terceiro or Decimal('0.00')
    if valor <= 0:
        raise ValueError(f'Cobrança não tem valor para terceiro (R$ {valor}).')

    bolso_doc = Bolso.objects.get(codigo='DOCUMENTACAO')
    cliente_nome = cobranca.cliente.razao_social if cobranca.cliente else 'Sem cliente'

    with transaction.atomic():
        cobranca.status_cte_terceiro = 'Pago'
        cobranca.data_pagamento_cte_terceiro = data_pagamento
        cobranca.save(update_fields=[
            'status_cte_terceiro', 'data_pagamento_cte_terceiro', 'atualizado_em'
        ])

        descricao = (
            f'Pagamento terceiro doc - Cobrança #{cobranca.id} ({cliente_nome})'
        )
        lanc = Lancamento.objects.create(
            data=data_pagamento,
            carteira=carteira,
            bolso=bolso_doc,
            tipo='Saida',
            valor=valor,
            descricao=descricao,
            categoria='Pagamento Terceiro Doc',
            cliente=cobranca.cliente,
            cobranca_carregamento=cobranca,
            criado_por=usuario,
        )

    return [lanc]


def aplicar_pagamento_terceiro_cte_avulsa(
    cobranca: CobrancaCTEAvulsa,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """Marca status_cte_terceiro=Pago e cria Saída no bolso Documentação."""
    if (cobranca.status_cte_terceiro or '').lower() == 'pago':
        raise ValueError('Pagamento ao terceiro já foi feito.')

    valor = cobranca.valor_cte_terceiro or Decimal('0.00')
    if valor <= 0:
        raise ValueError(f'CTE avulsa não tem valor para terceiro (R$ {valor}).')

    bolso_doc = Bolso.objects.get(codigo='DOCUMENTACAO')

    with transaction.atomic():
        cobranca.status_cte_terceiro = 'Pago'
        cobranca.data_pagamento_cte_terceiro = data_pagamento
        cobranca.save(update_fields=[
            'status_cte_terceiro', 'data_pagamento_cte_terceiro', 'atualizado_em'
        ])

        descricao = (
            f'Pagamento terceiro doc - CTE Avulsa #{cobranca.id} ({cobranca.nome})'
        )
        lanc = Lancamento.objects.create(
            data=data_pagamento,
            carteira=carteira,
            bolso=bolso_doc,
            tipo='Saida',
            valor=valor,
            descricao=descricao,
            categoria='Pagamento Terceiro Doc',
            cobranca_cte_avulsa=cobranca,
            criado_por=usuario,
        )

    return [lanc]


# ============================================================================
# Onda 5 - Descarga Avulsa
# ============================================================================

def _adicionar_a_acumulado(funcionario: FuncionarioFluxoCaixa, data_op: date, valor: Decimal):
    """
    Soma `valor` no AcumuladoFuncionario da semana de `data_op` para `funcionario`.

    Se já existir um acumulado dessa semana com status='Depositado', cria um
    novo registro ad-hoc (semana_inicio=fim=data_op) para preservar o histórico.
    """
    inicio, fim = semana_da_data(data_op)

    acumulado, created = AcumuladoFuncionario.objects.get_or_create(
        funcionario=funcionario,
        semana_inicio=inicio,
        semana_fim=fim,
        defaults={
            'valor_acumulado': Decimal('0.00'),
            'status': 'Pendente',
        },
    )

    if acumulado.status == 'Depositado':
        # Já fechada: cria registro ad-hoc para a data específica.
        # Tentar usar a própria data como semana, criando registro distinto.
        # Se já existir um ad-hoc na mesma data, soma nele.
        adhoc, _ = AcumuladoFuncionario.objects.get_or_create(
            funcionario=funcionario,
            semana_inicio=data_op,
            semana_fim=data_op,
            defaults={
                'valor_acumulado': Decimal('0.00'),
                'status': 'Pendente',
                'observacoes': 'Lançamento avulso após semana já fechada',
            },
        )
        adhoc.valor_acumulado = (adhoc.valor_acumulado or Decimal('0.00')) + valor
        adhoc.save(update_fields=['valor_acumulado', 'atualizado_em'])
        return adhoc

    if created:
        acumulado.valor_acumulado = valor
    else:
        acumulado.valor_acumulado = (acumulado.valor_acumulado or Decimal('0.00')) + valor
    acumulado.save(update_fields=['valor_acumulado', 'atualizado_em'])
    return acumulado


def aplicar_descarga_avulsa(
    *,
    data_op: date,
    descricao: str,
    carteira: Carteira,
    valor_cobrado: Decimal,
    chapas_distribuicao: list,  # list of (FuncionarioFluxoCaixa, Decimal)
    usuario,
):
    """
    Registra uma Descarga Avulsa:
    - Cria Lançamento de Entrada (carteira, Operacional) com soma da distribuição.
    - Cria Lançamento de Entrada (carteira, Estelar) com a margem (cobrado - distrib).
    - Para cada chapa, soma valor no AcumuladoFuncionario da semana.
    """
    if not chapas_distribuicao:
        raise ValueError('Adicione pelo menos um chapa.')

    total_distribuido = sum(
        (v for _, v in chapas_distribuicao),
        Decimal('0.00'),
    )
    if total_distribuido > valor_cobrado:
        raise ValueError(
            f'Total distribuído (R$ {total_distribuido}) maior que valor cobrado (R$ {valor_cobrado}).'
        )

    margem = valor_cobrado - total_distribuido

    bolso_op = Bolso.objects.get(codigo='OPERACIONAL')
    bolso_est = Bolso.objects.get(codigo='ESTELAR')

    lancs = []
    acumulados_atualizados = []
    with transaction.atomic():
        if total_distribuido > 0:
            lancs.append(Lancamento.objects.create(
                data=data_op,
                carteira=carteira,
                bolso=bolso_op,
                tipo='Entrada',
                valor=total_distribuido,
                descricao=f'Descarga avulsa - {descricao} (parte chapas)',
                categoria='Descarga Avulsa',
                criado_por=usuario,
            ))
        if margem > 0:
            lancs.append(Lancamento.objects.create(
                data=data_op,
                carteira=carteira,
                bolso=bolso_est,
                tipo='Entrada',
                valor=margem,
                descricao=f'Descarga avulsa - {descricao} (margem Estelar)',
                categoria='Descarga Avulsa',
                criado_por=usuario,
            ))

        for chapa, valor in chapas_distribuicao:
            if valor <= 0:
                continue
            ac = _adicionar_a_acumulado(chapa, data_op, valor)
            acumulados_atualizados.append(ac)

    return {
        'lancamentos': lancs,
        'acumulados': acumulados_atualizados,
        'total_distribuido': total_distribuido,
        'margem': margem,
    }


# ============================================================================
# Onda 6 - Distribuir aos Gerentes + Fundo Gás
# ============================================================================

def aplicar_distribuicao_gerentes(
    *,
    data_op: date,
    carteira: Carteira,
    distribuicoes: list,  # list of (nome:str, valor:Decimal)
    usuario,
):
    """
    Distribui valor entre os gerentes a partir do bolso Documentação.

    Cria 1 Lançamento de Saída por gerente.
    Total não pode exceder o saldo atual do bolso Documentação.
    """
    if not distribuicoes:
        raise ValueError('Adicione pelo menos um gerente.')

    bolso_doc = Bolso.objects.get(codigo='DOCUMENTACAO')
    saldo_doc = bolso_doc.saldo_atual()
    total = sum((v for _, v in distribuicoes), Decimal('0.00'))

    if total <= 0:
        raise ValueError('Total a distribuir deve ser maior que zero.')
    if total > saldo_doc:
        raise ValueError(
            f'Total a distribuir (R$ {total}) excede saldo do bolso '
            f'Documentação (R$ {saldo_doc}).'
        )

    lancs = []
    with transaction.atomic():
        for nome, valor in distribuicoes:
            nome = (nome or '').strip()
            if valor <= 0 or not nome:
                continue
            lancs.append(Lancamento.objects.create(
                data=data_op,
                carteira=carteira,
                bolso=bolso_doc,
                tipo='Saida',
                valor=valor,
                descricao=f'Distribuição aos gerentes - {nome}',
                categoria='Distribuição Gerentes',
                criado_por=usuario,
            ))
    return lancs


def aplicar_fundo_gas(
    *,
    data_op: date,
    carteira: Carteira,
    tipo: str,
    valor: Decimal,
    descricao: str,
    usuario,
):
    """Movimento de Entrada ou Saída no bolso Fundo Gás (terceiros)."""
    if tipo not in ('Entrada', 'Saida'):
        raise ValueError(f'Tipo inválido: {tipo}')
    if valor <= 0:
        raise ValueError('Valor deve ser maior que zero.')

    bolso_gas = Bolso.objects.get(codigo='FUNDO_GAS')

    if tipo == 'Saida':
        saldo = bolso_gas.saldo_atual()
        if valor > saldo:
            raise ValueError(
                f'Saldo insuficiente no Fundo Gás (saldo atual: R$ {saldo}).'
            )

    with transaction.atomic():
        lanc = Lancamento.objects.create(
            data=data_op,
            carteira=carteira,
            bolso=bolso_gas,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            categoria='Fundo Gás',
            criado_por=usuario,
        )

    return [lanc]


def aplicar_pagamento_chapa_em_lote(
    acumulados,
    *,
    carteira: Carteira,
    data_pagamento,
    usuario,
):
    """
    Paga uma lista de AcumuladoFuncionario em uma transação única.

    Cria 1 Lançamento por acumulado para preservar rastreabilidade.
    Retorna lista de lançamentos criados.
    """
    bolso_op = Bolso.objects.get(codigo='OPERACIONAL')
    lancs = []
    with transaction.atomic():
        for acumulado in acumulados:
            if acumulado.status == 'Depositado':
                continue
            valor = acumulado.valor_acumulado or Decimal('0.00')
            if valor <= 0:
                continue
            acumulado.status = 'Depositado'
            acumulado.data_deposito = data_pagamento
            acumulado.save(update_fields=['status', 'data_deposito', 'atualizado_em'])

            descricao = (
                f'Pagamento chapa {acumulado.funcionario.nome} - '
                f'semana {acumulado.semana_inicio:%d/%m} a {acumulado.semana_fim:%d/%m}'
            )
            lancs.append(Lancamento.objects.create(
                data=data_pagamento,
                carteira=carteira,
                bolso=bolso_op,
                tipo='Saida',
                valor=valor,
                descricao=descricao,
                categoria='Pagamento Chapa',
                funcionario=acumulado.funcionario,
                criado_por=usuario,
            ))
    return lancs


# ============================================================================
# Onda 8 - Acerto Diário V2 (substitui MovimentoCaixa por Lancamento)
# ============================================================================

def _recalcular_acumulado_funcionarios_semana_v2(data_referencia: date):
    """
    Recalcula AcumuladoFuncionario da semana de `data_referencia`.

    Mesma regra do serviço antigo: soma DistribuicaoFuncionario da semana
    para cada chapa e atualiza/cria os AcumuladoFuncionario com status
    'Pendente'. Acumulados 'Depositado' não são alterados.
    """
    semana_inicio = data_referencia - timedelta(days=data_referencia.weekday())
    semana_fim = semana_inicio + timedelta(days=6)

    acertos_semana = AcertoDiarioCarregamento.objects.filter(
        data__gte=semana_inicio,
        data__lte=semana_fim,
    )

    totals = dict(
        DistribuicaoFuncionario.objects.filter(
            acerto_diario__in=acertos_semana
        )
        .values('funcionario_id')
        .annotate(total=Sum('valor'))
        .values_list('funcionario_id', 'total')
    )
    totals = {fid: (t or Decimal('0.00')) for fid, t in totals.items()}

    acumulados_existentes = AcumuladoFuncionario.objects.filter(
        semana_inicio=semana_inicio,
        semana_fim=semana_fim,
    )
    for acc in acumulados_existentes:
        if acc.status != 'Pendente':
            continue
        novo = totals.get(acc.funcionario_id, Decimal('0.00'))
        if acc.valor_acumulado != novo:
            acc.valor_acumulado = novo
            acc.save(update_fields=['valor_acumulado'])

    for funcionario_id, total in totals.items():
        if total <= 0:
            continue
        acc, created = AcumuladoFuncionario.objects.get_or_create(
            funcionario_id=funcionario_id,
            semana_inicio=semana_inicio,
            semana_fim=semana_fim,
            defaults={'valor_acumulado': total, 'status': 'Pendente'},
        )
        if not created and acc.status == 'Pendente' and acc.valor_acumulado != total:
            acc.valor_acumulado = total
            acc.save(update_fields=['valor_acumulado'])


def _carteira_padrao_dinheiro():
    return Carteira.objects.get(codigo='DINHEIRO')


def _carteira_padrao_banco():
    return Carteira.objects.get(codigo='BANCO')


def aplicar_acerto_diario_v2(acerto: AcertoDiarioCarregamento, *, usuario):
    """
    Materializa um AcertoDiarioCarregamento como Lançamentos V2.

    Idempotente: apaga todos os Lancamento.acerto_diario=acerto antes e
    recria conforme as linhas atuais (CarregamentoCliente, DistribuicaoFuncionario,
    valor_estelar). Recalcula AcumuladoFuncionario da semana.

    Regras (Opção B - sem dependência de PeriodoMovimentoCaixa):
    - Carregamento COM cliente: NÃO cria lançamento (ficará em A Receber via
      CobrancaCarregamento Pendente quando vinculada).
    - Descarga em Dinheiro (sem cliente): Entrada na Carteira Dinheiro,
      bolso Operacional (valor cheio).
    - Descarga em Depósito (sem cliente): Entrada na Carteira Banco,
      bolso Operacional (valor cheio).
    - Valor Estelar > 0: 1 Saída Operacional + 1 Entrada Estelar (mesma
      Carteira Dinheiro). Reclassifica a margem da empresa para o bolso
      Estelar sem alterar o saldo da carteira.
    - Distribuições aos chapas: NÃO criam lançamento; apenas alimentam
      AcumuladoFuncionario (pago depois via A Pagar V2).

    Returns:
        dict com chaves 'lancamentos', 'descargas_dinheiro', 'descargas_deposito',
        'valor_estelar', 'total_distribuido', 'total_carregamentos'.
    """
    try:
        bolso_op = Bolso.objects.get(codigo='OPERACIONAL')
        bolso_est = Bolso.objects.get(codigo='ESTELAR')
    except Bolso.DoesNotExist as e:
        raise ValueError(
            'Bolsos Operacional/Estelar não encontrados. Verifique o cadastro.'
        ) from e

    try:
        cart_dinheiro = _carteira_padrao_dinheiro()
    except Carteira.DoesNotExist as e:
        raise ValueError(
            'Carteira Dinheiro não encontrada. Verifique o cadastro.'
        ) from e
    try:
        cart_banco = _carteira_padrao_banco()
    except Carteira.DoesNotExist:
        cart_banco = None

    valor_estelar = acerto.valor_estelar or Decimal('0.00')
    descricao_data = acerto.data.strftime('%d/%m/%Y')

    lancs_criados = []
    descargas_dinheiro = Decimal('0.00')
    descargas_deposito = Decimal('0.00')
    total_distribuido = Decimal('0.00')
    total_carregamentos = Decimal('0.00')

    with transaction.atomic():
        Lancamento.objects.filter(acerto_diario=acerto).delete()

        for carreg in CarregamentoCliente.objects.filter(acerto_diario=acerto):
            if carreg.cliente_id:
                total_carregamentos += carreg.valor or Decimal('0.00')
                continue

            valor = carreg.valor or Decimal('0.00')
            if valor <= 0:
                continue
            tipo_pgto = (carreg.tipo_pagamento or 'Dinheiro').upper()
            descricao_desc = (
                f'Descarga {descricao_data}: {carreg.descricao or "sem descrição"}'
            )

            if tipo_pgto in ('DEPOSITO', 'DEPÓSITO'):
                if cart_banco is None:
                    raise ValueError(
                        'Descarga marcada como Depósito mas Carteira Banco '
                        'não está cadastrada.'
                    )
                lanc = Lancamento.objects.create(
                    data=acerto.data,
                    carteira=cart_banco,
                    bolso=bolso_op,
                    tipo='Entrada',
                    valor=valor,
                    descricao=descricao_desc,
                    categoria='Descarga Acerto Diário',
                    acerto_diario=acerto,
                    criado_por=usuario,
                )
                descargas_deposito += valor
            else:
                lanc = Lancamento.objects.create(
                    data=acerto.data,
                    carteira=cart_dinheiro,
                    bolso=bolso_op,
                    tipo='Entrada',
                    valor=valor,
                    descricao=descricao_desc,
                    categoria='Descarga Acerto Diário',
                    acerto_diario=acerto,
                    criado_por=usuario,
                )
                descargas_dinheiro += valor
            lancs_criados.append(lanc)

        if valor_estelar > 0:
            lancs_criados.append(Lancamento.objects.create(
                data=acerto.data,
                carteira=cart_dinheiro,
                bolso=bolso_op,
                tipo='Saida',
                valor=valor_estelar,
                descricao=f'Reclassificação Acerto {descricao_data} (Operacional para Estelar)',
                categoria='Acerto Diário (reclass)',
                acerto_diario=acerto,
                criado_por=usuario,
            ))
            lancs_criados.append(Lancamento.objects.create(
                data=acerto.data,
                carteira=cart_dinheiro,
                bolso=bolso_est,
                tipo='Entrada',
                valor=valor_estelar,
                descricao=f'Margem Estelar - Acerto {descricao_data}',
                categoria='Acerto Diário (margem)',
                acerto_diario=acerto,
                criado_por=usuario,
            ))

        total_distribuido = (
            DistribuicaoFuncionario.objects.filter(acerto_diario=acerto)
            .aggregate(t=Sum('valor'))['t']
            or Decimal('0.00')
        )

        _recalcular_acumulado_funcionarios_semana_v2(acerto.data)

    return {
        'lancamentos': lancs_criados,
        'descargas_dinheiro': descargas_dinheiro,
        'descargas_deposito': descargas_deposito,
        'valor_estelar': valor_estelar,
        'total_distribuido': total_distribuido,
        'total_carregamentos': total_carregamentos,
    }


def excluir_acerto_diario_v2(acerto: AcertoDiarioCarregamento):
    """
    Apaga um AcertoDiarioCarregamento e seus efeitos no V2.

    - Remove Lancamentos vinculados ao acerto (acerto_diario=acerto).
    - Apaga o AcertoDiarioCarregamento (cascade remove CarregamentoCliente
      e DistribuicaoFuncionario).
    - Recalcula AcumuladoFuncionario da semana.

    NOTA: também remove os MovimentoCaixa antigos vinculados ao acerto,
    para manter o sistema legado consistente.
    """
    from financeiro.models import MovimentoCaixa
    data_acerto = acerto.data
    with transaction.atomic():
        Lancamento.objects.filter(acerto_diario=acerto).delete()
        MovimentoCaixa.objects.filter(acerto_diario=acerto).delete()
        acerto.delete()
        _recalcular_acumulado_funcionarios_semana_v2(data_acerto)
