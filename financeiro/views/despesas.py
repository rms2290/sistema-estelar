"""
Views dedicadas à tela de Despesas (MovimentoCaixa tipo Saida).
Listagem, criar, editar e excluir em páginas próprias.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from notas.decorators import admin_required
from notas.models import Cliente
from financeiro.models import MovimentoCaixa, PeriodoMovimentoCaixa, FuncionarioFluxoCaixa
from financeiro.services import MovimentoCaixaService, PeriodoCaixaService

logger = logging.getLogger(__name__)


@login_required
@admin_required
def listar_despesas(request):
    """Lista todas as despesas (MovimentoCaixa tipo Saida) com filtros opcionais."""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    categoria = request.GET.get('categoria', '')

    despesas = MovimentoCaixa.objects.filter(tipo='Saida').select_related(
        'funcionario', 'cliente', 'periodo'
    ).order_by('-data', '-criado_em')

    if data_inicio:
        try:
            despesas = despesas.filter(data__gte=datetime.strptime(data_inicio, '%Y-%m-%d').date())
        except ValueError:
            pass
    if data_fim:
        try:
            despesas = despesas.filter(data__lte=datetime.strptime(data_fim, '%Y-%m-%d').date())
        except ValueError:
            pass
    if categoria:
        despesas = despesas.filter(categoria=categoria)

    total = sum(d.valor for d in despesas)

    return render(request, 'financeiro/fluxo_caixa/despesas_listar.html', {
        'despesas': despesas,
        'total': total,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'categoria_selecionada': categoria,
        'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
    })


@login_required
@admin_required
def criar_despesa(request):
    """Página para criar nova despesa (MovimentoCaixa tipo Saida)."""
    periodo_ativo = PeriodoCaixaService.obter_periodo_aberto()
    if not periodo_ativo:
        messages.warning(
            request,
            'É necessário iniciar um período antes de lançar despesas. '
            'Vá em Movimento de Caixa e clique em "Iniciar Período".'
        )
        return redirect('financeiro:gerenciar_movimento_caixa')

    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    if request.method == 'POST':
        data = request.POST.get('data')
        categoria = request.POST.get('categoria', '').strip() or None
        valor_str = request.POST.get('valor', '0')
        descricao = (request.POST.get('descricao') or '').strip()
        destino = request.POST.get('destino', 'nenhum')
        funcionario_id = request.POST.get('funcionario_id', '').strip() or None
        cliente_id = request.POST.get('cliente_id', '').strip() or None

        try:
            valor = Decimal(valor_str)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return render(request, 'financeiro/fluxo_caixa/despesas_criar.html', {
                'periodo_ativo': periodo_ativo,
                'funcionarios': funcionarios,
                'clientes': clientes,
                'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
            })

        if destino == 'estelar':
            funcionario_id = None
            cliente_id = None
            if descricao and 'estelar' not in descricao.lower():
                descricao = 'Estelar ' + descricao
        elif destino == 'funcionario':
            cliente_id = None
        elif destino == 'cliente':
            funcionario_id = None
        else:
            funcionario_id = None
            cliente_id = None

        movimento, erro = MovimentoCaixaService.criar_movimento(
            data=data,
            tipo='Saida',
            valor=valor,
            descricao=descricao or 'Despesa',
            categoria=categoria,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
            acerto_diario_id=None,
            usuario=request.user,
        )
        if erro:
            messages.error(request, erro)
            return render(request, 'financeiro/fluxo_caixa/despesas_criar.html', {
                'periodo_ativo': periodo_ativo,
                'funcionarios': funcionarios,
                'clientes': clientes,
                'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
            })
        messages.success(request, 'Despesa lançada com sucesso.')
        return redirect('financeiro:listar_despesas')

    return render(request, 'financeiro/fluxo_caixa/despesas_criar.html', {
        'periodo_ativo': periodo_ativo,
        'funcionarios': funcionarios,
        'clientes': clientes,
        'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
    })


@login_required
@admin_required
def editar_despesa(request, pk):
    """Página para editar despesa existente (MovimentoCaixa tipo Saida)."""
    movimento = get_object_or_404(MovimentoCaixa, pk=pk, tipo='Saida')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    if request.method == 'POST':
        data = request.POST.get('data')
        categoria = request.POST.get('categoria', '').strip() or None
        valor_str = request.POST.get('valor', '0')
        descricao = (request.POST.get('descricao') or '').strip()
        funcionario_id = request.POST.get('funcionario_id', '').strip() or None
        cliente_id = request.POST.get('cliente_id', '').strip() or None

        try:
            valor = Decimal(valor_str)
        except Exception:
            messages.error(request, 'Valor inválido.')
            return render(request, 'financeiro/fluxo_caixa/despesas_editar.html', {
                'despesa': movimento,
                'funcionarios': funcionarios,
                'clientes': clientes,
                'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
            })

        movimento, erro = MovimentoCaixaService.editar_movimento(
            movimento,
            data=data,
            tipo='Saida',
            valor=valor,
            descricao=descricao or 'Despesa',
            categoria=categoria,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
        )
        if erro:
            messages.error(request, erro)
            return render(request, 'financeiro/fluxo_caixa/despesas_editar.html', {
                'despesa': movimento,
                'funcionarios': funcionarios,
                'clientes': clientes,
                'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
            })
        messages.success(request, 'Despesa atualizada com sucesso.')
        return redirect('financeiro:listar_despesas')

    return render(request, 'financeiro/fluxo_caixa/despesas_editar.html', {
        'despesa': movimento,
        'funcionarios': funcionarios,
        'clientes': clientes,
        'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
    })


@login_required
@admin_required
def excluir_despesa(request, pk):
    """Confirma e exclui despesa (MovimentoCaixa tipo Saida)."""
    despesa = get_object_or_404(MovimentoCaixa, pk=pk, tipo='Saida')

    if request.method == 'POST':
        _, erro = MovimentoCaixaService.excluir_movimento(despesa)
        if erro:
            messages.error(request, erro)
        else:
            messages.success(request, 'Despesa excluída com sucesso.')
        return redirect('financeiro:listar_despesas')

    return render(request, 'financeiro/fluxo_caixa/despesas_excluir.html', {'despesa': despesa})
