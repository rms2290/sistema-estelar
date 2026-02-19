"""
Views de dashboard, receitas, caixa funcionário, movimento bancário e controle de saldo.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.shortcuts import render, get_object_or_404, redirect

from sistema_estelar.api_utils import json_success, json_error
from django.urls import reverse
from django.utils import timezone

from notas.decorators import admin_required
from notas.models import Cliente, CobrancaCarregamento
from financeiro.models import (
    ReceitaEmpresa,
    CaixaFuncionario,
    MovimentoBancario,
    ControleSaldoSemanal,
    FuncionarioFluxoCaixa,
)

logger = logging.getLogger(__name__)


@login_required
@admin_required
def dashboard_fluxo_caixa(request):
    """Dashboard principal de fluxo de caixa semanal"""
    hoje = timezone.now().date()
    dias_para_segunda = hoje.weekday()
    semana_inicio = hoje - timedelta(days=dias_para_segunda)
    semana_fim = semana_inicio + timedelta(days=6)

    semana_selecionada_inicio = request.GET.get('semana_inicio', semana_inicio.isoformat())
    semana_selecionada_fim = request.GET.get('semana_fim', semana_fim.isoformat())

    try:
        semana_inicio_obj = datetime.strptime(semana_selecionada_inicio, '%Y-%m-%d').date()
        semana_fim_obj = datetime.strptime(semana_selecionada_fim, '%Y-%m-%d').date()
    except Exception as e:
        logger.warning('Datas de semana inválidas em dashboard_fluxo_caixa, usando padrão: %s', e)
        semana_inicio_obj = semana_inicio
        semana_fim_obj = semana_fim

    controle_saldo, created = ControleSaldoSemanal.objects.get_or_create(
        semana_inicio=semana_inicio_obj,
        semana_fim=semana_fim_obj,
        defaults={
            'saldo_inicial_caixa': Decimal('0.00'),
            'saldo_inicial_banco': Decimal('0.00'),
        }
    )

    if request.GET.get('calcular') == 'true':
        controle_saldo.calcular_totais()
        messages.success(request, 'Totais calculados com sucesso!')

    if request.method == 'POST' and 'validar' in request.POST:
        try:
            controle_saldo.validar(request.user)
            messages.success(request, 'Saldo validado com sucesso!')
        except ValidationError as e:
            messages.error(request, str(e))

    receitas = ReceitaEmpresa.objects.filter(
        data__gte=semana_inicio_obj,
        data__lte=semana_fim_obj
    ).order_by('-data')

    caixas_funcionarios = CaixaFuncionario.objects.filter(
        Q(
            Q(periodo_tipo='Semanal', semana_inicio__lte=semana_fim_obj, semana_fim__gte=semana_inicio_obj) |
            Q(periodo_tipo='Diario', data__gte=semana_inicio_obj, data__lte=semana_fim_obj)
        ),
        status='Em_Aberto'
    ).select_related('funcionario').order_by('funcionario__nome', '-semana_inicio', '-data')

    movimentos_banco = MovimentoBancario.objects.filter(
        data__gte=semana_inicio_obj,
        data__lte=semana_fim_obj
    ).order_by('-data')

    pendentes_receber = CobrancaCarregamento.objects.filter(
        status='Pendente',
        data_vencimento__lte=semana_fim_obj
    ).order_by('data_vencimento')

    receitas_por_tipo = receitas.values('tipo_receita').annotate(total=Sum('valor')).order_by('-total')

    saldo_banco = controle_saldo.total_entradas_banco - controle_saldo.total_saidas_banco
    saldo_inicial_total = controle_saldo.saldo_inicial_caixa + controle_saldo.saldo_inicial_banco
    saldo_final_real_total = controle_saldo.saldo_final_real_caixa + controle_saldo.saldo_final_real_banco

    context = {
        'controle_saldo': controle_saldo,
        'semana_inicio': semana_inicio_obj,
        'semana_fim': semana_fim_obj,
        'receitas': receitas,
        'receitas_por_tipo': receitas_por_tipo,
        'caixas_funcionarios': caixas_funcionarios,
        'movimentos_banco': movimentos_banco,
        'pendentes_receber': pendentes_receber,
        'saldo_banco': saldo_banco,
        'saldo_inicial_total': saldo_inicial_total,
        'saldo_final_real_total': saldo_final_real_total,
    }
    return render(request, 'financeiro/fluxo_caixa/dashboard_fluxo_caixa.html', context)


@login_required
@admin_required
def criar_receita_empresa(request):
    """Cria uma nova receita da empresa"""
    if request.method == 'POST':
        data = request.POST.get('data')
        tipo_receita = request.POST.get('tipo_receita')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        cliente_id = request.POST.get('cliente', '') or None
        cobranca_id = request.POST.get('cobranca_carregamento', '') or None

        ReceitaEmpresa.objects.create(
            data=data,
            tipo_receita=tipo_receita,
            valor=valor,
            descricao=descricao,
            cliente_id=cliente_id,
            cobranca_carregamento_id=cobranca_id,
            usuario_criacao=request.user
        )
        messages.success(request, 'Receita registrada com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')

    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    cobrancas = CobrancaCarregamento.objects.filter(status='Pendente').order_by('-criado_em')
    context = {
        'clientes': clientes,
        'cobrancas': cobrancas,
        'tipos_receita': ReceitaEmpresa.TIPO_RECEITA_CHOICES,
    }
    return render(request, 'financeiro/fluxo_caixa/criar_receita_empresa.html', context)


@login_required
@admin_required
def editar_receita_empresa(request, pk):
    """Edita uma receita da empresa"""
    receita = get_object_or_404(ReceitaEmpresa, pk=pk)
    if request.method == 'POST':
        receita.data = request.POST.get('data')
        receita.tipo_receita = request.POST.get('tipo_receita')
        receita.valor = Decimal(request.POST.get('valor', '0.00'))
        receita.descricao = request.POST.get('descricao', '')
        receita.cliente_id = request.POST.get('cliente', '') or None
        receita.cobranca_carregamento_id = request.POST.get('cobranca_carregamento', '') or None
        receita.save()
        messages.success(request, 'Receita atualizada com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    cobrancas = CobrancaCarregamento.objects.filter(status='Pendente').order_by('-criado_em')
    context = {
        'receita': receita,
        'clientes': clientes,
        'cobrancas': cobrancas,
        'tipos_receita': ReceitaEmpresa.TIPO_RECEITA_CHOICES,
    }
    return render(request, 'financeiro/fluxo_caixa/editar_receita_empresa.html', context)


@login_required
@admin_required
def excluir_receita_empresa(request, pk):
    """Exclui uma receita da empresa"""
    receita = get_object_or_404(ReceitaEmpresa, pk=pk)
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Receita excluída com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    return render(request, 'financeiro/fluxo_caixa/excluir_receita_empresa.html', {'receita': receita})


@login_required
@admin_required
def criar_caixa_funcionario(request):
    """Cria um novo caixa de funcionário"""
    if request.method == 'POST':
        funcionario_id = request.POST.get('funcionario')
        periodo_tipo = request.POST.get('periodo_tipo')
        valor_coletado = Decimal(request.POST.get('valor_coletado', '0.00'))
        observacoes = request.POST.get('observacoes', '')
        semana_inicio = request.POST.get('semana_inicio') or None
        semana_fim = request.POST.get('semana_fim') or None
        data = request.POST.get('data') or None

        CaixaFuncionario.objects.create(
            funcionario_id=funcionario_id,
            periodo_tipo=periodo_tipo,
            semana_inicio=semana_inicio,
            semana_fim=semana_fim,
            data=data,
            valor_coletado=valor_coletado,
            observacoes=observacoes
        )
        messages.success(request, 'Caixa de funcionário criado com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    return render(request, 'financeiro/fluxo_caixa/criar_caixa_funcionario.html', {'funcionarios': funcionarios})


@login_required
@admin_required
def acertar_caixa_funcionario(request, pk):
    """Acerta o caixa de um funcionário"""
    caixa = get_object_or_404(CaixaFuncionario, pk=pk)
    if request.method == 'POST':
        valor_acertado = Decimal(request.POST.get('valor_acertado', '0.00'))
        data_acerto = request.POST.get('data_acerto')
        observacoes = request.POST.get('observacoes', '')
        caixa.valor_acertado = valor_acertado
        caixa.data_acerto = data_acerto
        caixa.status = 'Acertado'
        if observacoes:
            caixa.observacoes = (caixa.observacoes or '') + '\n' + observacoes
        caixa.save()
        messages.success(request, 'Caixa acertado com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    return render(request, 'financeiro/fluxo_caixa/acertar_caixa_funcionario.html', {'caixa': caixa})


@login_required
@admin_required
def criar_movimento_bancario(request):
    """Cria um novo movimento bancário"""
    if request.method == 'POST':
        MovimentoBancario.objects.create(
            data=request.POST.get('data'),
            tipo=request.POST.get('tipo'),
            valor=Decimal(request.POST.get('valor', '0.00')),
            descricao=request.POST.get('descricao', ''),
            numero_documento=request.POST.get('numero_documento', ''),
            receita_empresa_id=request.POST.get('receita_empresa', '') or None,
            usuario_criacao=request.user
        )
        messages.success(request, 'Movimento bancário registrado com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    receitas = ReceitaEmpresa.objects.all().order_by('-data')[:50]
    return render(request, 'financeiro/fluxo_caixa/criar_movimento_bancario.html', {
        'tipos': MovimentoBancario.TIPO_CHOICES,
        'receitas': receitas,
    })


@login_required
@admin_required
def editar_movimento_bancario(request, pk):
    """Edita um movimento bancário"""
    movimento = get_object_or_404(MovimentoBancario, pk=pk)
    if request.method == 'POST':
        movimento.data = request.POST.get('data')
        movimento.tipo = request.POST.get('tipo')
        movimento.valor = Decimal(request.POST.get('valor', '0.00'))
        movimento.descricao = request.POST.get('descricao', '')
        movimento.numero_documento = request.POST.get('numero_documento', '')
        movimento.receita_empresa_id = request.POST.get('receita_empresa', '') or None
        movimento.save()
        messages.success(request, 'Movimento bancário atualizado com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    receitas = ReceitaEmpresa.objects.all().order_by('-data')[:50]
    return render(request, 'financeiro/fluxo_caixa/editar_movimento_bancario.html', {
        'movimento': movimento,
        'tipos': MovimentoBancario.TIPO_CHOICES,
        'receitas': receitas,
    })


@login_required
@admin_required
def excluir_movimento_bancario(request, pk):
    """Exclui um movimento bancário"""
    movimento = get_object_or_404(MovimentoBancario, pk=pk)
    if request.method == 'POST':
        movimento.delete()
        messages.success(request, 'Movimento bancário excluído com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    return render(request, 'financeiro/fluxo_caixa/excluir_movimento_bancario.html', {'movimento': movimento})


@login_required
@admin_required
def atualizar_controle_saldo(request, pk):
    """Atualiza os saldos iniciais e finais do controle semanal"""
    controle = get_object_or_404(ControleSaldoSemanal, pk=pk)
    if request.method == 'POST':
        controle.saldo_inicial_caixa = Decimal(request.POST.get('saldo_inicial_caixa', '0.00'))
        controle.saldo_inicial_banco = Decimal(request.POST.get('saldo_inicial_banco', '0.00'))
        controle.saldo_final_real_caixa = Decimal(request.POST.get('saldo_final_real_caixa', '0.00'))
        controle.saldo_final_real_banco = Decimal(request.POST.get('saldo_final_real_banco', '0.00'))
        controle.observacoes = request.POST.get('observacoes', '')
        saldo_final_real = controle.saldo_final_real_caixa + controle.saldo_final_real_banco
        controle.diferenca = controle.saldo_final_calculado - saldo_final_real
        controle.save()
        messages.success(request, 'Controle de saldo atualizado com sucesso!')
        return redirect('financeiro:dashboard_fluxo_caixa')
    return render(request, 'financeiro/fluxo_caixa/atualizar_controle_saldo.html', {'controle': controle})


@login_required
@admin_required
def criar_funcionario_ajax(request):
    """Cria um funcionário simples via AJAX (apenas nome, para uso no fluxo de caixa)"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        nome = request.POST.get('nome', '').strip()
        if not nome:
            return json_error('Nome do funcionário é obrigatório')
        if FuncionarioFluxoCaixa.objects.filter(nome__iexact=nome).exists():
            return json_error('Já existe um funcionário com este nome')
        funcionario = FuncionarioFluxoCaixa.objects.create(nome=nome, ativo=True)
        return json_success(
            message='Funcionário criado com sucesso!',
            funcionario_id=funcionario.pk,
            nome=funcionario.nome,
        )
    except Exception as e:
        return json_error(f'Erro ao criar funcionário: {str(e)}')
