"""
Views para gerenciamento de Fluxo de Caixa
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta

from django.http import JsonResponse
from ..decorators import admin_required
from ..models import (
    ReceitaEmpresa, CaixaFuncionario, MovimentoCaixaFuncionario,
    MovimentoBancario, ControleSaldoSemanal, CobrancaCarregamento,
    Usuario, Cliente, FuncionarioFluxoCaixa,
    AcertoDiarioCarregamento, CarregamentoCliente,
    DistribuicaoFuncionario, AcumuladoFuncionario
)


@login_required
@admin_required
def dashboard_fluxo_caixa(request):
    """Dashboard principal de fluxo de caixa semanal"""
    
    # Obter semana atual (segunda a domingo)
    hoje = timezone.now().date()
    dias_para_segunda = hoje.weekday()  # 0 = segunda, 6 = domingo
    semana_inicio = hoje - timedelta(days=dias_para_segunda)
    semana_fim = semana_inicio + timedelta(days=6)
    
    # Permitir seleção de semana via GET
    semana_selecionada_inicio = request.GET.get('semana_inicio', semana_inicio.isoformat())
    semana_selecionada_fim = request.GET.get('semana_fim', semana_fim.isoformat())
    
    try:
        semana_inicio_obj = datetime.strptime(semana_selecionada_inicio, '%Y-%m-%d').date()
        semana_fim_obj = datetime.strptime(semana_selecionada_fim, '%Y-%m-%d').date()
    except:
        semana_inicio_obj = semana_inicio
        semana_fim_obj = semana_fim
    
    # Buscar ou criar controle de saldo semanal
    controle_saldo, created = ControleSaldoSemanal.objects.get_or_create(
        semana_inicio=semana_inicio_obj,
        semana_fim=semana_fim_obj,
        defaults={
            'saldo_inicial_caixa': Decimal('0.00'),
            'saldo_inicial_banco': Decimal('0.00'),
        }
    )
    
    # Calcular totais se solicitado
    if request.GET.get('calcular') == 'true':
        controle_saldo.calcular_totais()
        messages.success(request, 'Totais calculados com sucesso!')
    
    # Validar se solicitado
    if request.method == 'POST' and 'validar' in request.POST:
        try:
            controle_saldo.validar(request.user)
            messages.success(request, 'Saldo validado com sucesso!')
        except ValidationError as e:
            messages.error(request, str(e))
    
    # Buscar dados para exibição
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
    
    # Totais por tipo de receita
    receitas_por_tipo = receitas.values('tipo_receita').annotate(
        total=Sum('valor')
    ).order_by('-total')
    
    # Calcular saldo do banco (entradas - saídas)
    saldo_banco = controle_saldo.total_entradas_banco - controle_saldo.total_saidas_banco
    
    # Calcular totais para exibição
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
    
    return render(request, 'notas/fluxo_caixa/dashboard_fluxo_caixa.html', context)


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
        
        receita = ReceitaEmpresa.objects.create(
            data=data,
            tipo_receita=tipo_receita,
            valor=valor,
            descricao=descricao,
            cliente_id=cliente_id,
            cobranca_carregamento_id=cobranca_id,
            usuario_criacao=request.user
        )
        
        messages.success(request, 'Receita registrada com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    cobrancas = CobrancaCarregamento.objects.filter(status='Pendente').order_by('-criado_em')
    
    context = {
        'clientes': clientes,
        'cobrancas': cobrancas,
        'tipos_receita': ReceitaEmpresa.TIPO_RECEITA_CHOICES,
    }
    
    return render(request, 'notas/fluxo_caixa/criar_receita_empresa.html', context)


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
        return redirect('notas:dashboard_fluxo_caixa')
    
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    cobrancas = CobrancaCarregamento.objects.filter(status='Pendente').order_by('-criado_em')
    
    context = {
        'receita': receita,
        'clientes': clientes,
        'cobrancas': cobrancas,
        'tipos_receita': ReceitaEmpresa.TIPO_RECEITA_CHOICES,
    }
    
    return render(request, 'notas/fluxo_caixa/editar_receita_empresa.html', context)


@login_required
@admin_required
def excluir_receita_empresa(request, pk):
    """Exclui uma receita da empresa"""
    
    receita = get_object_or_404(ReceitaEmpresa, pk=pk)
    
    if request.method == 'POST':
        receita.delete()
        messages.success(request, 'Receita excluída com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    return render(request, 'notas/fluxo_caixa/excluir_receita_empresa.html', {'receita': receita})


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
        
        caixa = CaixaFuncionario.objects.create(
            funcionario_id=funcionario_id,
            periodo_tipo=periodo_tipo,
            semana_inicio=semana_inicio,
            semana_fim=semana_fim,
            data=data,
            valor_coletado=valor_coletado,
            observacoes=observacoes
        )
        
        messages.success(request, 'Caixa de funcionário criado com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'funcionarios': funcionarios,
    }
    
    return render(request, 'notas/fluxo_caixa/criar_caixa_funcionario.html', context)


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
        return redirect('notas:dashboard_fluxo_caixa')
    
    return render(request, 'notas/fluxo_caixa/acertar_caixa_funcionario.html', {'caixa': caixa})


@login_required
@admin_required
def criar_movimento_bancario(request):
    """Cria um novo movimento bancário"""
    
    if request.method == 'POST':
        data = request.POST.get('data')
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        numero_documento = request.POST.get('numero_documento', '')
        receita_id = request.POST.get('receita_empresa', '') or None
        
        movimento = MovimentoBancario.objects.create(
            data=data,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            numero_documento=numero_documento,
            receita_empresa_id=receita_id,
            usuario_criacao=request.user
        )
        
        messages.success(request, 'Movimento bancário registrado com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    receitas = ReceitaEmpresa.objects.all().order_by('-data')[:50]
    
    context = {
        'tipos': MovimentoBancario.TIPO_CHOICES,
        'receitas': receitas,
    }
    
    return render(request, 'notas/fluxo_caixa/criar_movimento_bancario.html', context)


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
        return redirect('notas:dashboard_fluxo_caixa')
    
    receitas = ReceitaEmpresa.objects.all().order_by('-data')[:50]
    
    context = {
        'movimento': movimento,
        'tipos': MovimentoBancario.TIPO_CHOICES,
        'receitas': receitas,
    }
    
    return render(request, 'notas/fluxo_caixa/editar_movimento_bancario.html', context)


@login_required
@admin_required
def excluir_movimento_bancario(request, pk):
    """Exclui um movimento bancário"""
    
    movimento = get_object_or_404(MovimentoBancario, pk=pk)
    
    if request.method == 'POST':
        movimento.delete()
        messages.success(request, 'Movimento bancário excluído com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    return render(request, 'notas/fluxo_caixa/excluir_movimento_bancario.html', {'movimento': movimento})


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
        
        # Recalcular diferença
        saldo_final_real = controle.saldo_final_real_caixa + controle.saldo_final_real_banco
        controle.diferenca = controle.saldo_final_calculado - saldo_final_real
        
        controle.save()
        
        messages.success(request, 'Controle de saldo atualizado com sucesso!')
        return redirect('notas:dashboard_fluxo_caixa')
    
    return render(request, 'notas/fluxo_caixa/atualizar_controle_saldo.html', {'controle': controle})


@login_required
@admin_required
def criar_funcionario_ajax(request):
    """Cria um funcionário simples via AJAX (apenas nome, para uso no fluxo de caixa)"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        nome = request.POST.get('nome', '').strip()
        
        # Validações
        if not nome:
            return JsonResponse({'success': False, 'message': 'Nome do funcionário é obrigatório'})
        
        # Verificar se nome já existe
        if FuncionarioFluxoCaixa.objects.filter(nome__iexact=nome).exists():
            return JsonResponse({'success': False, 'message': 'Já existe um funcionário com este nome'})
        
        # Criar funcionário simples
        funcionario = FuncionarioFluxoCaixa.objects.create(
            nome=nome,
            ativo=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Funcionário criado com sucesso!',
            'funcionario_id': funcionario.pk,
            'nome': funcionario.nome
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar funcionário: {str(e)}'
        })


@login_required
@admin_required
def listar_acertos_diarios(request):
    """Lista todos os acertos diários com opção de pesquisa"""
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Buscar acertos
    acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')
    
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            acertos = acertos.filter(data__gte=data_inicio_obj)
        except:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            acertos = acertos.filter(data__lte=data_fim_obj)
        except:
            pass
    
    context = {
        'acertos': acertos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
    }
    
    return render(request, 'notas/fluxo_caixa/listar_acertos_diarios.html', context)


@login_required
@admin_required
def acerto_diario_carregamento(request):
    """Tela principal de acerto diário de carregamento"""
    
    # Verificar se é requisição AJAX para detalhes
    if request.GET.get('ajax') == '1' and request.GET.get('acerto_id'):
        acerto_id = request.GET.get('acerto_id')
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            carregamentos = list(CarregamentoCliente.objects.filter(
                acerto_diario=acerto
            ).select_related('cliente'))
            carregamentos.sort(key=lambda x: (
                0 if x.cliente else 1,
                x.cliente.razao_social if x.cliente else '',
                x.descricao or ''
            ))
            distribuicoes = DistribuicaoFuncionario.objects.filter(
                acerto_diario=acerto
            ).select_related('funcionario').order_by('funcionario__nome')
            
            from django.template.loader import render_to_string
            from django.utils.safestring import mark_safe
            # Calcular diferença para o template
            diferenca = abs(acerto.total_carregamentos - acerto.total_distribuido)
            html = render_to_string('notas/fluxo_caixa/detalhes_acerto_diario.html', {
                'acerto': acerto,
                'carregamentos': carregamentos,
                'distribuicoes': distribuicoes,
                'diferenca': diferenca,
            }, request=request)
            # Marcar como seguro para evitar escape
            return JsonResponse({'html': mark_safe(html)})
        except AcertoDiarioCarregamento.DoesNotExist:
            return JsonResponse({'error': 'Acerto não encontrado'}, status=404)
    
    # Obter data selecionada (hoje por padrão)
    data_selecionada = request.GET.get('data', timezone.now().date().isoformat())
    
    try:
        data_obj = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
    except:
        data_obj = timezone.now().date()
    
    # Buscar ou criar acerto do dia
    acerto, created = AcertoDiarioCarregamento.objects.get_or_create(
        data=data_obj,
        defaults={
            'valor_estelar': Decimal('0.00'),
            'usuario_criacao': request.user
        }
    )
    
    # Buscar carregamentos e distribuições
    # Ordenar: primeiro carregamentos (com cliente), depois descargas (sem cliente)
    carregamentos = list(CarregamentoCliente.objects.filter(
        acerto_diario=acerto
    ).select_related('cliente'))
    
    # Ordenar manualmente: clientes primeiro (por nome), depois descargas (por descrição)
    carregamentos.sort(key=lambda x: (
        0 if x.cliente else 1,  # Carregamentos primeiro (0), descargas depois (1)
        x.cliente.razao_social if x.cliente else '',
        x.descricao or ''
    ))
    
    distribuicoes = DistribuicaoFuncionario.objects.filter(
        acerto_diario=acerto
    ).select_related('funcionario').order_by('funcionario__nome')
    
    # Buscar clientes e funcionários para os selects
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'acerto': acerto,
        'data_selecionada': data_obj,
        'carregamentos': carregamentos,
        'distribuicoes': distribuicoes,
        'clientes': clientes,
        'funcionarios': funcionarios,
    }
    
    return render(request, 'notas/fluxo_caixa/acerto_diario_carregamento.html', context)


@login_required
@admin_required
def salvar_acerto_diario(request):
    """Salva o acerto diário (via AJAX)"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = request.POST.get('data')
        valor_estelar = Decimal(request.POST.get('valor_estelar', '0.00'))
        observacoes = request.POST.get('observacoes', '')
        
        acerto, created = AcertoDiarioCarregamento.objects.get_or_create(
            data=data,
            defaults={
                'valor_estelar': valor_estelar,
                'observacoes': observacoes,
                'usuario_criacao': request.user
            }
        )
        
        if not created:
            acerto.valor_estelar = valor_estelar
            acerto.observacoes = observacoes
            acerto.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Acerto salvo com sucesso!',
            'acerto_id': acerto.pk
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao salvar acerto: {str(e)}'
        })


@login_required
@admin_required
def adicionar_carregamento_cliente_ajax(request):
    """Adiciona um carregamento de cliente ou descarga via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        acerto_id = request.POST.get('acerto_id')
        cliente_id = request.POST.get('cliente_id', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        valor = Decimal(request.POST.get('valor', '0.00'))
        observacoes = request.POST.get('observacoes', '')
        
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        
        if valor <= 0:
            return JsonResponse({'success': False, 'message': 'Valor deve ser maior que zero'})
        
        # Validar: deve ter cliente OU descrição
        if not cliente_id and not descricao:
            return JsonResponse({'success': False, 'message': 'Informe um cliente ou a descrição da descarga'})
        
        if cliente_id and descricao:
            return JsonResponse({'success': False, 'message': 'Informe apenas cliente OU descrição, não ambos'})
        
        # Buscar cliente se informado
        cliente = None
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
        
        # Criar ou atualizar carregamento
        carregamento, created = CarregamentoCliente.objects.get_or_create(
            acerto_diario=acerto,
            cliente=cliente,
            defaults={
                'descricao': descricao if not cliente else '',
                'valor': valor,
                'observacoes': observacoes
            }
        )
        
        if not created:
            carregamento.cliente = cliente
            carregamento.descricao = descricao if not cliente else ''
            carregamento.valor = valor
            carregamento.observacoes = observacoes
            carregamento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Registro adicionado com sucesso!',
            'carregamento_id': carregamento.pk,
            'nome_display': carregamento.nome_display,
            'tipo': carregamento.tipo,
            'valor': str(carregamento.valor)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar registro: {str(e)}'
        })


@login_required
@admin_required
def remover_carregamento_cliente_ajax(request, pk):
    """Remove um carregamento de cliente via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        carregamento = get_object_or_404(CarregamentoCliente, pk=pk)
        carregamento.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Carregamento removido com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover carregamento: {str(e)}'
        })


@login_required
@admin_required
def adicionar_distribuicao_funcionario_ajax(request):
    """Adiciona uma distribuição para funcionário via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        acerto_id = request.POST.get('acerto_id')
        funcionario_id = request.POST.get('funcionario_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        funcionario = get_object_or_404(FuncionarioFluxoCaixa, pk=funcionario_id)
        
        if valor <= 0:
            return JsonResponse({'success': False, 'message': 'Valor deve ser maior que zero'})
        
        distribuicao, created = DistribuicaoFuncionario.objects.get_or_create(
            acerto_diario=acerto,
            funcionario=funcionario,
            defaults={'valor': valor}
        )
        
        if not created:
            distribuicao.valor = valor
            distribuicao.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Distribuição adicionada com sucesso!',
            'distribuicao_id': distribuicao.pk,
            'funcionario_nome': funcionario.nome,
            'valor': str(distribuicao.valor)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao adicionar distribuição: {str(e)}'
        })


@login_required
@admin_required
def remover_distribuicao_funcionario_ajax(request, pk):
    """Remove uma distribuição de funcionário via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        distribuicao = get_object_or_404(DistribuicaoFuncionario, pk=pk)
        distribuicao.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Distribuição removida com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao remover distribuição: {str(e)}'
        })

