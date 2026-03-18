"""
View de fechamento de caixa.
"""
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.shortcuts import render

import logging
from notas.decorators import admin_required
from notas.models import CobrancaCarregamento
from financeiro.services import PeriodoCaixaService
from financeiro.models import (
    AcertoDiarioCarregamento,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
)

logger = logging.getLogger(__name__)


@login_required
@admin_required
def fechamento_caixa(request):
    """
    Tela para fechamento de caixa.
    Permite visualizar períodos abertos e fechá-los.
    Aceita GET periodo_id=X para exibir o fechamento de um período fechado (vindo da busca).
    """
    periodo_id = request.GET.get('periodo_id')
    periodo_selecionado = None
    if periodo_id:
        try:
            pk = int(periodo_id)
            periodo_selecionado = PeriodoMovimentoCaixa.objects.filter(pk=pk, status='Fechado').first()
        except (ValueError, TypeError):
            periodo_selecionado = None

    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    # Período a exibir: se veio periodo_id e é fechado, usa esse; senão usa o período em aberto
    periodo_exibido = periodo_selecionado if periodo_selecionado else periodo_ativo
    periodos_fechados = PeriodoMovimentoCaixa.objects.filter(
        status='Fechado'
    ).order_by('-data_fim', '-criado_em')[:10]

    funcionarios_acumulados = []
    if periodo_exibido:
        movimentos = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido
        ).select_related(
            'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao'
        )
        # Mesma regra da tela Gerenciar Movimento: AcertoFuncionario sem acerto_diario = saída
        def _eh_saida_na_tela(mov):
            if mov.tipo == 'Saida':
                return True
            if mov.tipo == 'AcertoFuncionario' and not mov.acerto_diario_id:
                return True
            return False
        movimentos_lista = list(movimentos)
        total_entradas = sum(mov.valor for mov in movimentos_lista if not _eh_saida_na_tela(mov))
        total_saidas = sum(mov.valor for mov in movimentos_lista if _eh_saida_na_tela(mov))
        saldo_atual = periodo_exibido.valor_inicial_caixa + total_entradas - total_saidas
        total_movimentos = len(movimentos_lista)

        acertos_periodo = AcertoDiarioCarregamento.objects.filter(
            data__gte=periodo_exibido.data_inicio
        )
        if periodo_exibido.data_fim:
            acertos_periodo = acertos_periodo.filter(data__lte=periodo_exibido.data_fim)

        distribuicoes_agrupadas = DistribuicaoFuncionario.objects.filter(
            acerto_diario__in=acertos_periodo
        ).select_related('funcionario', 'acerto_diario').order_by('funcionario__nome', 'acerto_diario__data')
        distribuicoes_por_funcionario = distribuicoes_agrupadas.values('funcionario').annotate(
            total_distribuicoes=Sum('valor')
        )

        acertos_funcionarios = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='AcertoFuncionario',
            funcionario__isnull=False,
            acerto_diario__isnull=True
        ).select_related('funcionario')
        acertos_agrupados = acertos_funcionarios.values('funcionario').annotate(total_acertos=Sum('valor'))

        saidas_funcionarios = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Saida',
            funcionario__isnull=False
        ).select_related('funcionario')
        saidas_agrupadas = saidas_funcionarios.values('funcionario').annotate(total_saidas=Sum('valor'))

        funcionarios_dict = {}
        for item in distribuicoes_por_funcionario:
            fid = item['funcionario']
            valor_dist = Decimal(str(item['total_distribuicoes'] or '0.00'))
            if fid not in funcionarios_dict:
                funcionarios_dict[fid] = Decimal('0.00')
            funcionarios_dict[fid] += valor_dist
        for item in acertos_agrupados:
            fid = item['funcionario']
            valor_acerto = Decimal(str(item['total_acertos'] or '0.00'))
            if fid not in funcionarios_dict:
                funcionarios_dict[fid] = Decimal('0.00')
            funcionarios_dict[fid] -= valor_acerto
        for item in saidas_agrupadas:
            fid = item['funcionario']
            valor_saida = Decimal(str(item['total_saidas'] or '0.00'))
            if fid not in funcionarios_dict:
                funcionarios_dict[fid] = Decimal('0.00')
            funcionarios_dict[fid] -= valor_saida

        total_acumulado_funcionarios = Decimal('0.00')
        for funcionario_id, valor_acumulado in funcionarios_dict.items():
            if valor_acumulado != 0:
                funcionario = FuncionarioFluxoCaixa.objects.get(pk=funcionario_id)
                funcionarios_acumulados.append({
                    'funcionario': funcionario,
                    'valor_acumulado': valor_acumulado,
                })
                total_acumulado_funcionarios += valor_acumulado
        funcionarios_acumulados.sort(key=lambda x: x['funcionario'].nome)

        entradas_estelar_exato = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Entrada',
            funcionario__isnull=True,
            descricao='Valor Estelar'
        )
        entradas_estelar_icontains = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Entrada',
            funcionario__isnull=True,
            descricao__icontains='Estelar'
        )
        entradas_estelar_categoria = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Entrada',
            funcionario__isnull=True,
            categoria__in=['RecebimentoCliente', 'RecebimentoCarregamento'],
            data__gte=periodo_exibido.data_inicio
        )
        if periodo_exibido.data_fim:
            entradas_estelar_categoria = entradas_estelar_categoria.filter(data__lte=periodo_exibido.data_fim)
        entradas_estelar_categoria = entradas_estelar_categoria.exclude(
            Q(descricao__icontains='Descarga') | Q(descricao__icontains='descarga')
        )
        # Descargas em dinheiro são entradas para a Estelar (categoria RecebimentoDescarga)
        entradas_estelar_descarga = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Entrada',
            funcionario__isnull=True,
            categoria='RecebimentoDescarga',
            data__gte=periodo_exibido.data_inicio
        )
        if periodo_exibido.data_fim:
            entradas_estelar_descarga = entradas_estelar_descarga.filter(data__lte=periodo_exibido.data_fim)

        entradas_estelar_ids = set()
        entradas_estelar_list = []
        for entrada in entradas_estelar_exato:
            if entrada.id not in entradas_estelar_ids:
                entradas_estelar_ids.add(entrada.id)
                entradas_estelar_list.append(entrada)
        for entrada in entradas_estelar_icontains:
            if entrada.id not in entradas_estelar_ids:
                entradas_estelar_ids.add(entrada.id)
                entradas_estelar_list.append(entrada)
        for entrada in entradas_estelar_categoria:
            if entrada.id not in entradas_estelar_ids:
                entradas_estelar_ids.add(entrada.id)
                entradas_estelar_list.append(entrada)
        for entrada in entradas_estelar_descarga:
            if entrada.id not in entradas_estelar_ids:
                entradas_estelar_ids.add(entrada.id)
                entradas_estelar_list.append(entrada)

        total_estelar_entradas = sum(Decimal(str(entrada.valor)) for entrada in entradas_estelar_list)
        if total_estelar_entradas == 0 or len(entradas_estelar_list) == 0:
            valor_dos_acertos = sum(
                Decimal(str(acerto.valor_estelar)) for acerto in acertos_periodo if acerto.valor_estelar
            )
            if valor_dos_acertos > 0:
                total_estelar_entradas = valor_dos_acertos
        if not isinstance(total_estelar_entradas, Decimal):
            total_estelar_entradas = Decimal(str(total_estelar_entradas))

        saidas_estelar = MovimentoCaixa.objects.filter(
            periodo=periodo_exibido,
            tipo='Saida',
            funcionario__isnull=True,
            cliente__isnull=True
        )
        total_estelar_saidas = sum(Decimal(str(saida.valor)) for saida in saidas_estelar)
        if not isinstance(total_estelar_saidas, Decimal):
            total_estelar_saidas = Decimal(str(total_estelar_saidas))
        valor_acumulado_estelar = total_estelar_entradas - total_estelar_saidas
        if not isinstance(valor_acumulado_estelar, Decimal):
            valor_acumulado_estelar = Decimal(str(valor_acumulado_estelar))

        debug_info = {
            'periodo': {
                'data_inicio': periodo_exibido.data_inicio.strftime('%d/%m/%Y') if periodo_exibido.data_inicio else '',
                'data_fim': periodo_exibido.data_fim.strftime('%d/%m/%Y') if periodo_exibido.data_fim else 'Aberto',
            },
            'acertos_diarios': [
                {'id': a.pk, 'data': a.data.strftime('%d/%m/%Y'), 'valor_estelar': str(a.valor_estelar) if a.valor_estelar else '0.00'}
                for a in acertos_periodo
            ],
            'distribuicoes_detalhadas': [
                {'funcionario_id': d.funcionario.pk, 'funcionario_nome': d.funcionario.nome, 'valor': str(d.valor), 'acerto_id': d.acerto_diario.pk, 'acerto_data': d.acerto_diario.data.strftime('%d/%m/%Y')}
                for d in distribuicoes_agrupadas
            ],
            'acertos_diretos_detalhados': [
                {'funcionario_id': a.funcionario.pk, 'funcionario_nome': a.funcionario.nome, 'valor': str(a.valor), 'data': a.data.strftime('%d/%m/%Y'), 'descricao': a.descricao}
                for a in acertos_funcionarios
            ],
            'saidas_funcionarios_detalhadas': [
                {'funcionario_id': s.funcionario.pk, 'funcionario_nome': s.funcionario.nome, 'valor': str(s.valor), 'data': s.data.strftime('%d/%m/%Y'), 'descricao': s.descricao}
                for s in saidas_funcionarios
            ],
        }
    else:
        total_entradas = Decimal('0.00')
        total_saidas = Decimal('0.00')
        saldo_atual = Decimal('0.00')
        total_movimentos = 0
        total_acumulado_funcionarios = Decimal('0.00')
        valor_acumulado_estelar = Decimal('0.00')
        total_estelar_entradas = Decimal('0.00')
        total_estelar_saidas = Decimal('0.00')
        debug_info = None

    cobrancas_pendentes = CobrancaCarregamento.objects.filter(
        status='Pendente'
    ).select_related('cliente').order_by('cliente__razao_social')
    clientes_cobrancas = {}
    for cobranca in cobrancas_pendentes:
        cliente_id = cobranca.cliente.id
        if cliente_id not in clientes_cobrancas:
            clientes_cobrancas[cliente_id] = {
                'cliente': cobranca.cliente,
                'valor_total': Decimal('0.00'),
                'quantidade_cobrancas': 0
            }
        clientes_cobrancas[cliente_id]['valor_total'] += cobranca.valor_carregamento + cobranca.valor_cte_manifesto
        clientes_cobrancas[cliente_id]['quantidade_cobrancas'] += 1
    clientes_cobrancas_lista = sorted(
        clientes_cobrancas.values(),
        key=lambda x: x['cliente'].razao_social
    )
    total_cobrancas_pendentes = sum(item['valor_total'] for item in clientes_cobrancas_lista)

    context = {
        'periodo_ativo': periodo_ativo,
        'periodo_exibido': periodo_exibido,
        'periodo_fechado_selecionado': bool(periodo_selecionado),
        'periodos_fechados': periodos_fechados,
        'total_entradas': total_entradas if periodo_exibido else Decimal('0.00'),
        'total_saidas': total_saidas if periodo_exibido else Decimal('0.00'),
        'valor_inicial_caixa': periodo_exibido.valor_inicial_caixa if periodo_exibido else Decimal('0.00'),
        'saldo_atual': saldo_atual if periodo_exibido else Decimal('0.00'),
        'total_movimentos': total_movimentos if periodo_exibido else 0,
        'funcionarios_acumulados': funcionarios_acumulados,
        'total_acumulado_funcionarios': total_acumulado_funcionarios if periodo_exibido else Decimal('0.00'),
        'valor_acumulado_estelar': valor_acumulado_estelar if periodo_exibido else Decimal('0.00'),
        'total_estelar_entradas': total_estelar_entradas if periodo_exibido else Decimal('0.00'),
        'total_estelar_saidas': total_estelar_saidas if periodo_exibido else Decimal('0.00'),
        'clientes_cobrancas_pendentes': clientes_cobrancas_lista,
        'total_cobrancas_pendentes': total_cobrancas_pendentes,
    }
    if debug_info:
        context['debug_info'] = debug_info
    return render(request, 'financeiro/fluxo_caixa/fechamento_caixa.html', context)
