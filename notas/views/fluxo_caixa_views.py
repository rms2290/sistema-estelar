"""
Views para gerenciamento de Fluxo de Caixa
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta

from django.http import JsonResponse
from ..decorators import admin_required
from ..models import (
    ReceitaEmpresa, CaixaFuncionario, MovimentoCaixaFuncionario,
    MovimentoBancario, ControleSaldoSemanal, CobrancaCarregamento,
    Usuario, Cliente, FuncionarioFluxoCaixa,
    AcertoDiarioCarregamento, CarregamentoCliente,
    DistribuicaoFuncionario, AcumuladoFuncionario,
    MovimentoCaixa, PeriodoMovimentoCaixa
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
    
    # Verificar se deve mostrar o formulário de edição/criação
    mostrar_formulario = request.GET.get('novo') == '1' or request.GET.get('acerto_id')
    acerto_id = request.GET.get('acerto_id')
    novo_acerto = request.GET.get('novo') == '1'
    
    # Se não for para mostrar formulário, mostrar lista com filtros
    if not mostrar_formulario:
        # Filtros de pesquisa
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
            'mostrar_lista': True,
        }
        
        return render(request, 'notas/fluxo_caixa/acerto_diario_carregamento.html', context)
    
    # Se for para mostrar formulário, buscar ou criar acerto
    if acerto_id:
        # Editar acerto existente
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            data_obj = acerto.data
        except AcertoDiarioCarregamento.DoesNotExist:
            acerto = None
            data_obj = timezone.now().date()
    elif novo_acerto:
        # Novo acerto - obter data selecionada (se não informada, não criar ainda)
        data_selecionada = request.GET.get('data', '')
        if data_selecionada:
            try:
                data_obj = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
                # Verificar se já existe acerto para esta data
                acerto_existente = AcertoDiarioCarregamento.objects.filter(data=data_obj).first()
                if acerto_existente:
                    # Se já existe, redirecionar para edição deste acerto (não criar novo)
                    return redirect('{}?acerto_id={}'.format(
                        reverse('notas:acerto_diario_carregamento'),
                        acerto_existente.pk
                    ))
                else:
                    # Criar novo acerto vazio (sem carregamentos ou distribuições)
                    acerto = AcertoDiarioCarregamento.objects.create(
                        data=data_obj,
                        valor_estelar=Decimal('0.00'),
                        observacoes='',
                        usuario_criacao=request.user
                    )
                    # Após criar, redirecionar para edição do novo acerto (garantindo que está vazio)
                    return redirect('{}?acerto_id={}'.format(
                        reverse('notas:acerto_diario_carregamento'),
                        acerto.pk
                    ))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao criar novo acerto: {str(e)}', exc_info=True)
                acerto = None
                data_obj = None
        else:
            # Ainda não escolheu a data - mostrar apenas o seletor de data
            acerto = None
            data_obj = None
    else:
        # Fallback - não deveria chegar aqui
        acerto = None
        data_obj = timezone.now().date()
    
    # Buscar carregamentos e distribuições (apenas se houver acerto)
    # IMPORTANTE: Sempre buscar do acerto específico para garantir que não há dados de outro acerto
    if acerto:
        # Buscar carregamentos APENAS deste acerto específico
        carregamentos = list(CarregamentoCliente.objects.filter(
            acerto_diario_id=acerto.pk  # Usar ID explícito para garantir
        ).select_related('cliente'))
        
        # Ordenar manualmente: clientes primeiro (por nome), depois descargas (por descrição)
        carregamentos.sort(key=lambda x: (
            0 if x.cliente else 1,  # Carregamentos primeiro (0), descargas depois (1)
            x.cliente.razao_social if x.cliente else '',
            x.descricao or ''
        ))
        
        # Buscar distribuições APENAS deste acerto específico
        distribuicoes = list(DistribuicaoFuncionario.objects.filter(
            acerto_diario_id=acerto.pk  # Usar ID explícito para garantir
        ).select_related('funcionario').order_by('funcionario__nome'))
    else:
        carregamentos = []
        distribuicoes = []
    
    # Buscar clientes e funcionários para os selects
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    
    context = {
        'acerto': acerto,
        'data_selecionada': acerto.data if acerto else (data_obj if data_obj else None),
        'carregamentos': carregamentos,
        'distribuicoes': distribuicoes,
        'clientes': clientes,
        'funcionarios': funcionarios,
        'mostrar_formulario': True,
        'novo_acerto': novo_acerto and not acerto,  # Se é novo e ainda não tem acerto
    }
    
    return render(request, 'notas/fluxo_caixa/acerto_diario_carregamento.html', context)


@login_required
@admin_required
def salvar_acerto_diario(request):
    """Salva o acerto diário e cria movimentos de caixa automaticamente"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        data = request.POST.get('data')
        observacoes = request.POST.get('observacoes', '')
        
        acerto, created = AcertoDiarioCarregamento.objects.get_or_create(
            data=data,
            defaults={
                'valor_estelar': Decimal('0.00'),
                'observacoes': observacoes,
                'usuario_criacao': request.user
            }
        )
        
        if not created:
            # Não sobrescrever valor_estelar, pois ele é gerenciado via AJAX
            acerto.observacoes = observacoes
            acerto.save()
        
        # Verificar se há período ativo
        periodo_ativo = PeriodoMovimentoCaixa.objects.filter(status='Aberto').order_by('-criado_em').first()
        if not periodo_ativo:
            return JsonResponse({
                'success': False,
                'message': 'É necessário iniciar um período antes de salvar o acerto. Clique em "Iniciar Período" na página de gerenciamento.'
            })
        
        # Criar movimentos de caixa automaticamente
        # Primeiro, remover movimentos antigos deste acerto (se houver)
        MovimentoCaixa.objects.filter(acerto_diario=acerto).delete()
        
        # NOTA: Carregamentos de clientes NÃO entram na lista de controle
        # Apenas distribuições para funcionários e valor Estelar entram
        
        # 1. Criar saída para valor Estelar (se houver)
        if acerto.valor_estelar and acerto.valor_estelar > 0:
            MovimentoCaixa.objects.create(
                data=acerto.data,
                tipo='Saida',
                valor=acerto.valor_estelar,
                descricao=f"Valor Estelar - Acerto Diário {acerto.data.strftime('%d/%m/%Y')}",
                categoria='Outros',
                acerto_diario=acerto,
                periodo=periodo_ativo,  # Associar ao período ativo
                usuario_criacao=request.user
            )
        
        # 2. Criar ENTRADAS (positivas) para cada distribuição de funcionário
        # As distribuições para funcionários entram como AcertoFuncionario (valor positivo)
        distribuicoes = DistribuicaoFuncionario.objects.filter(acerto_diario=acerto)
        for distribuicao in distribuicoes:
            MovimentoCaixa.objects.create(
                data=acerto.data,
                tipo='AcertoFuncionario',  # Tipo específico para acerto de funcionário (entrada positiva)
                valor=distribuicao.valor,
                descricao=f"Acerto Funcionário: {distribuicao.funcionario.nome} - Acerto Diário {acerto.data.strftime('%d/%m/%Y')}",
                categoria=None,  # AcertoFuncionario não usa categoria
                funcionario=distribuicao.funcionario,
                acerto_diario=acerto,
                periodo=periodo_ativo,  # Associar ao período ativo
                usuario_criacao=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Acerto salvo com sucesso! Movimentos de caixa criados automaticamente.',
            'acerto_id': acerto.pk
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao salvar acerto diário: {str(e)}', exc_info=True)
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


@login_required
@admin_required
def movimento_caixa(request):
    """Lista todos os movimentos de caixa (funcionários e bancários)"""
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    tipo = request.GET.get('tipo', '')  # 'funcionario', 'bancario', ou vazio para todos
    
    # Buscar movimentos de funcionários
    movimentos_funcionarios = MovimentoCaixaFuncionario.objects.all().select_related(
        'caixa_funcionario__funcionario'
    ).order_by('-data', '-id')
    
    # Buscar movimentos bancários
    movimentos_bancarios = MovimentoBancario.objects.all().order_by('-data', '-id')
    
    # Aplicar filtros de data
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentos_funcionarios = movimentos_funcionarios.filter(data__gte=data_inicio_obj)
            movimentos_bancarios = movimentos_bancarios.filter(data__gte=data_inicio_obj)
        except:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentos_funcionarios = movimentos_funcionarios.filter(data__lte=data_fim_obj)
            movimentos_bancarios = movimentos_bancarios.filter(data__lte=data_fim_obj)
        except:
            pass
    
    # Aplicar filtro de tipo
    if tipo == 'funcionario':
        movimentos_bancarios = movimentos_bancarios.none()
    elif tipo == 'bancario':
        movimentos_funcionarios = movimentos_funcionarios.none()
    
    # Combinar e ordenar todos os movimentos
    movimentos_combinados = []
    
    for mov in movimentos_funcionarios:
        movimentos_combinados.append({
            'tipo': 'funcionario',
            'data': mov.data,
            'descricao': mov.descricao,
            'valor': mov.valor,
            'funcionario': mov.caixa_funcionario.funcionario.nome if mov.caixa_funcionario.funcionario else 'N/A',
            'id': mov.id,
            'objeto': mov
        })
    
    for mov in movimentos_bancarios:
        movimentos_combinados.append({
            'tipo': 'bancario',
            'data': mov.data,
            'descricao': mov.descricao,
            'valor': mov.valor if mov.tipo == 'Credito' else -mov.valor,  # Negativo para débitos
            'tipo_movimento': mov.tipo,
            'id': mov.id,
            'objeto': mov
        })
    
    # Ordenar por data (mais recente primeiro)
    movimentos_combinados.sort(key=lambda x: (x['data'], x['id']), reverse=True)
    
    # Calcular total
    total = sum(mov['valor'] for mov in movimentos_combinados)
    
    context = {
        'movimentos': movimentos_combinados,
        'total': total,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo_selecionado': tipo,
    }
    
    return render(request, 'notas/fluxo_caixa/movimento_caixa.html', context)


@login_required
@admin_required
def salvar_valor_estelar_ajax(request):
    """Salva o valor Estelar via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        acerto_id = request.POST.get('acerto_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        
        if valor < 0:
            return JsonResponse({'success': False, 'message': 'Valor não pode ser negativo'})
        
        acerto.valor_estelar = valor
        acerto.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Valor Estelar salvo com sucesso!',
            'valor': str(valor)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao salvar valor Estelar: {str(e)}'
        })


@login_required
@admin_required
def gerenciar_movimento_caixa(request):
    """Tela principal para gerenciar movimentos de caixa"""
    
    # Buscar período ativo (aberto) com contagem de movimentos
    periodo_ativo = PeriodoMovimentoCaixa.objects.filter(status='Aberto').order_by('-criado_em').first()
    if periodo_ativo:
        # Anotar contagem de movimentos para uso no template
        periodo_ativo._movimentos_count = periodo_ativo.movimentos.count()
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    tipo = request.GET.get('tipo', '')
    categoria = request.GET.get('categoria', '')
    periodo_id = request.GET.get('periodo_id', '')
    
    # Se houver período ativo e não foi especificado outro período, usar o ativo
    if periodo_ativo and not periodo_id:
        periodo_id = str(periodo_ativo.pk)
    
    # Buscar movimentos (ordenados do mais antigo para o mais novo)
    if periodo_id:
        try:
            periodo_selecionado = PeriodoMovimentoCaixa.objects.get(pk=periodo_id)
            movimentos = MovimentoCaixa.objects.filter(
                periodo=periodo_selecionado
            ).select_related(
                'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao', 'periodo'
            ).order_by('data', 'criado_em')  # Ordem crescente: mais antigo primeiro
        except PeriodoMovimentoCaixa.DoesNotExist:
            movimentos = MovimentoCaixa.objects.none()
            periodo_selecionado = None
    else:
        movimentos = MovimentoCaixa.objects.none()
        periodo_selecionado = None
    
    # Aplicar filtros adicionais
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            movimentos = movimentos.filter(data__gte=data_inicio_obj)
        except:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            movimentos = movimentos.filter(data__lte=data_fim_obj)
        except:
            pass
    
    if tipo:
        movimentos = movimentos.filter(tipo=tipo)
    
    if categoria:
        movimentos = movimentos.filter(categoria=categoria)
    
    # Se houver período selecionado, calcular saldo considerando valor inicial
    if periodo_selecionado:
        valor_inicial = periodo_selecionado.valor_inicial_caixa
    else:
        valor_inicial = Decimal('0.00')
    
    # Calcular saldo acumulado para cada movimento (para exibição na lista)
    # Movimentos já estão ordenados do mais antigo para o mais novo
    movimentos_lista = list(movimentos)
    
    # Calcular saldo acumulado do mais antigo para o mais recente
    saldo_acumulado = valor_inicial
    movimentos_com_saldo = []
    
    for mov in movimentos_lista:
        if mov.is_entrada:
            saldo_acumulado += mov.valor
        else:
            saldo_acumulado -= mov.valor
        movimentos_com_saldo.append({
            'movimento': mov,
            'saldo_acumulado': saldo_acumulado
        })
    
    # Calcular totais
    total_entradas = sum(mov.valor for mov in movimentos if mov.is_entrada)
    total_saidas = sum(mov.valor for mov in movimentos if mov.is_saida)
    saldo = valor_inicial + total_entradas - total_saidas
    
    # Buscar funcionários e clientes para os selects
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    
    # Buscar todos os períodos para o select
    periodos = PeriodoMovimentoCaixa.objects.all().order_by('-data_inicio', '-criado_em')
    
    context = {
        'periodo_ativo': periodo_ativo,
        'periodo_selecionado': periodo_selecionado,
        'periodos': periodos,
        'movimentos': movimentos,
        'movimentos_com_saldo': movimentos_com_saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'valor_inicial_caixa': valor_inicial,
        'saldo': saldo,
        'funcionarios': funcionarios,
        'clientes': clientes,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'tipo_selecionado': tipo,
        'categoria_selecionada': categoria,
        'periodo_id': periodo_id,
        'tipos': MovimentoCaixa.TIPO_CHOICES,
        'categorias_entrada': MovimentoCaixa.CATEGORIA_ENTRADA_CHOICES,
        'categorias_saida': MovimentoCaixa.CATEGORIA_SAIDA_CHOICES,
    }
    
    return render(request, 'notas/fluxo_caixa/gerenciar_movimento_caixa.html', context)


@login_required
@admin_required
def criar_movimento_caixa_ajax(request):
    """Cria um novo movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        # Verificar se há período ativo
        periodo_ativo = PeriodoMovimentoCaixa.objects.filter(status='Aberto').order_by('-criado_em').first()
        if not periodo_ativo:
            return JsonResponse({
                'success': False,
                'message': 'É necessário iniciar um período antes de criar movimentos. Clique em "Iniciar Período".'
            })
        
        data = request.POST.get('data')
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        categoria = request.POST.get('categoria', '')
        funcionario_id = request.POST.get('funcionario_id', '') or None
        cliente_id = request.POST.get('cliente_id', '') or None
        acerto_diario_id = request.POST.get('acerto_diario_id', '') or None
        
        if not data or not tipo or valor <= 0:
            return JsonResponse({'success': False, 'message': 'Dados inválidos'})
        
        # Validar categoria baseado no tipo
        if tipo == 'Entrada' and categoria and categoria not in [c[0] for c in MovimentoCaixa.CATEGORIA_ENTRADA_CHOICES]:
            return JsonResponse({'success': False, 'message': 'Categoria inválida para entrada'})
        if tipo == 'Saida' and categoria and categoria not in [c[0] for c in MovimentoCaixa.CATEGORIA_SAIDA_CHOICES]:
            return JsonResponse({'success': False, 'message': 'Categoria inválida para saída'})
        
        movimento = MovimentoCaixa.objects.create(
            data=data,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            categoria=categoria or None,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
            acerto_diario_id=acerto_diario_id,
            periodo=periodo_ativo,  # Associar ao período ativo
            usuario_criacao=request.user
        )
        
        # Se for acerto de funcionário, atualizar acumulado
        if tipo == 'AcertoFuncionario' and funcionario_id:
            try:
                acumulado = AcumuladoFuncionario.objects.filter(
                    funcionario_id=funcionario_id
                ).order_by('-data').first()
                
                if acumulado:
                    # Reduzir o acumulado pelo valor acertado
                    acumulado.valor_acumulado = max(Decimal('0.00'), acumulado.valor_acumulado - valor)
                    acumulado.save()
            except Exception as e:
                # Log do erro mas não impede a criação do movimento
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Erro ao atualizar acumulado do funcionário: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': 'Movimento criado com sucesso!',
            'movimento_id': movimento.pk
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao criar movimento: {str(e)}'
        })


@login_required
@admin_required
def editar_movimento_caixa_ajax(request, pk):
    """Edita um movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        
        data = request.POST.get('data')
        tipo = request.POST.get('tipo')
        valor = Decimal(request.POST.get('valor', '0.00'))
        descricao = request.POST.get('descricao', '')
        categoria = request.POST.get('categoria', '')
        funcionario_id = request.POST.get('funcionario_id', '') or None
        cliente_id = request.POST.get('cliente_id', '') or None
        
        if not data or not tipo or valor <= 0:
            return JsonResponse({'success': False, 'message': 'Dados inválidos'})
        
        # Validar categoria
        if tipo == 'Entrada' and categoria and categoria not in [c[0] for c in MovimentoCaixa.CATEGORIA_ENTRADA_CHOICES]:
            return JsonResponse({'success': False, 'message': 'Categoria inválida para entrada'})
        if tipo == 'Saida' and categoria and categoria not in [c[0] for c in MovimentoCaixa.CATEGORIA_SAIDA_CHOICES]:
            return JsonResponse({'success': False, 'message': 'Categoria inválida para saída'})
        
        # Se for acerto de funcionário e o valor mudou, ajustar acumulado
        if tipo == 'AcertoFuncionario' and funcionario_id:
            valor_anterior = movimento.valor
            diferenca = valor - valor_anterior
            
            if diferenca != 0:
                try:
                    acumulado = AcumuladoFuncionario.objects.filter(
                        funcionario_id=funcionario_id
                    ).order_by('-data').first()
                    
                    if acumulado:
                        # Ajustar o acumulado pela diferença
                        acumulado.valor_acumulado = max(Decimal('0.00'), acumulado.valor_acumulado - diferenca)
                        acumulado.save()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Erro ao ajustar acumulado do funcionário: {str(e)}')
        
        movimento.data = data
        movimento.tipo = tipo
        movimento.valor = valor
        movimento.descricao = descricao
        movimento.categoria = categoria or None
        movimento.funcionario_id = funcionario_id
        movimento.cliente_id = cliente_id
        movimento.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Movimento atualizado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao editar movimento: {str(e)}'
        })


@login_required
@admin_required
def excluir_movimento_caixa_ajax(request, pk):
    """Exclui um movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        
        # Se for acerto de funcionário, reverter no acumulado
        if movimento.tipo == 'AcertoFuncionario' and movimento.funcionario:
            try:
                acumulado = AcumuladoFuncionario.objects.filter(
                    funcionario_id=movimento.funcionario_id
                ).order_by('-data').first()
                
                if acumulado:
                    # Reverter o valor no acumulado
                    acumulado.valor_acumulado += movimento.valor
                    acumulado.save()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Erro ao reverter acumulado do funcionário: {str(e)}')
        
        movimento.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Movimento excluído com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir movimento: {str(e)}'
        })


@login_required
@admin_required
def obter_acumulado_funcionario_ajax(request, funcionario_id):
    """Obtém o valor acumulado de um funcionário via AJAX"""
    
    try:
        acumulado = AcumuladoFuncionario.objects.filter(
            funcionario_id=funcionario_id
        ).order_by('-data').first()
        
        valor_acumulado = acumulado.valor_acumulado if acumulado else Decimal('0.00')
        
        return JsonResponse({
            'success': True,
            'valor_acumulado': str(valor_acumulado)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter acumulado: {str(e)}'
        })


@login_required
@admin_required
def obter_movimento_caixa_ajax(request, pk):
    """Obtém dados de um movimento de caixa via AJAX para edição"""
    
    try:
        movimento = get_object_or_404(MovimentoCaixa, pk=pk)
        
        return JsonResponse({
            'success': True,
            'data': movimento.data.strftime('%Y-%m-%d'),
            'tipo': movimento.tipo,
            'valor': str(movimento.valor),
            'descricao': movimento.descricao,
            'categoria': movimento.categoria or '',
            'funcionario_id': movimento.funcionario_id or '',
            'cliente_id': movimento.cliente_id or '',
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter movimento: {str(e)}'
        })


@login_required
@admin_required
def iniciar_periodo_movimento_caixa(request):
    """Inicia um novo período de movimento de caixa"""
    
    if request.method == 'POST':
        try:
            data_inicio = request.POST.get('data_inicio', '')
            valor_inicial = Decimal(request.POST.get('valor_inicial_caixa', '0.00'))
            observacoes = request.POST.get('observacoes', '').strip()
            
            if not data_inicio:
                messages.error(request, 'Data de início é obrigatória.')
                return redirect('notas:gerenciar_movimento_caixa')
            
            # Verificar se já existe período aberto
            periodo_aberto = PeriodoMovimentoCaixa.objects.filter(status='Aberto').first()
            if periodo_aberto:
                from django.utils import formats
                periodo_nome = periodo_aberto.data_inicio.strftime('%d/%m/%Y') if not periodo_aberto.nome else periodo_aberto.nome
                messages.warning(request, f'Já existe um período aberto: {periodo_nome}. Feche-o antes de iniciar um novo.')
                return redirect('notas:gerenciar_movimento_caixa')
            
            # Criar novo período (nome será gerado automaticamente pelo __str__)
            periodo = PeriodoMovimentoCaixa.objects.create(
                nome=None,  # Nome será gerado automaticamente pela data de início
                data_inicio=data_inicio,
                valor_inicial_caixa=valor_inicial,
                observacoes=observacoes or None,
                status='Aberto',
                usuario_criacao=request.user
            )
            
            periodo_nome = periodo.data_inicio.strftime('%d/%m/%Y')
            messages.success(request, f'Período de {periodo_nome} iniciado com sucesso!')
            # Redirecionar para a página de gerenciamento com o período recém-criado selecionado
            return redirect(f"{reverse('notas:gerenciar_movimento_caixa')}?periodo_id={periodo.pk}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro ao iniciar período: {str(e)}', exc_info=True)
            messages.error(request, f'Erro ao iniciar período: {str(e)}')
            return redirect('notas:gerenciar_movimento_caixa')
    
    # GET - mostrar formulário
    return render(request, 'notas/fluxo_caixa/iniciar_periodo_movimento_caixa.html', {
        'data_inicio': timezone.now().date().isoformat()
    })


@login_required
@admin_required
def fechar_periodo_movimento_caixa_ajax(request, pk):
    """Fecha um período de movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        
        if periodo.status == 'Fechado':
            return JsonResponse({'success': False, 'message': 'Período já está fechado'})
        
        periodo.fechar_periodo()
        
        periodo_nome = periodo.data_inicio.strftime('%d/%m/%Y')
        return JsonResponse({
            'success': True,
            'message': f'Período de {periodo_nome} fechado com sucesso!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao fechar período: {str(e)}'
        })


@login_required
@admin_required
def editar_periodo_movimento_caixa_ajax(request, pk):
    """Edita um período de movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        
        # Verificar se o período tem movimentos associados
        if periodo.movimentos.exists():
            return JsonResponse({
                'success': False,
                'message': 'Não é possível editar um período que já possui movimentos cadastrados.'
            })
        
        data_inicio = request.POST.get('data_inicio', '')
        valor_inicial = Decimal(request.POST.get('valor_inicial_caixa', '0.00'))
        observacoes = request.POST.get('observacoes', '').strip()
        
        if not data_inicio:
            return JsonResponse({'success': False, 'message': 'Data de início é obrigatória.'})
        
        periodo.data_inicio = data_inicio
        periodo.valor_inicial_caixa = valor_inicial
        periodo.observacoes = observacoes or None
        periodo.save()
        
        periodo_nome = periodo.data_inicio.strftime('%d/%m/%Y')
        return JsonResponse({
            'success': True,
            'message': f'Período de {periodo_nome} atualizado com sucesso!'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao editar período: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Erro ao editar período: {str(e)}'
        })


@login_required
@admin_required
def obter_periodo_movimento_caixa_ajax(request, pk):
    """Obtém dados de um período de movimento de caixa via AJAX para edição"""
    
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        
        return JsonResponse({
            'success': True,
            'data': {
                'data_inicio': periodo.data_inicio.strftime('%Y-%m-%d'),
                'valor_inicial_caixa': str(periodo.valor_inicial_caixa),
                'observacoes': periodo.observacoes or '',
                'status': periodo.status,
                'tem_movimentos': periodo.movimentos.exists()
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro ao obter período: {str(e)}'
        })


@login_required
@admin_required
def excluir_periodo_movimento_caixa_ajax(request, pk):
    """Exclui um período de movimento de caixa via AJAX"""
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
        
        # Verificar se o período tem movimentos associados
        if periodo.movimentos.exists():
            return JsonResponse({
                'success': False,
                'message': 'Não é possível excluir um período que possui movimentos cadastrados. Primeiro exclua ou mova os movimentos.'
            })
        
        periodo_nome = periodo.data_inicio.strftime('%d/%m/%Y')
        periodo.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Período de {periodo_nome} excluído com sucesso!'
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao excluir período: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Erro ao excluir período: {str(e)}'
        })


@login_required
@admin_required
def pesquisar_periodo_movimento_caixa(request):
    """Página para pesquisar e listar períodos de movimento de caixa"""
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')
    
    # Buscar períodos
    periodos = PeriodoMovimentoCaixa.objects.all()
    
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            periodos = periodos.filter(data_inicio__gte=data_inicio_obj)
        except:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            periodos = periodos.filter(data_inicio__lte=data_fim_obj)
        except:
            pass
    
    if status:
        periodos = periodos.filter(status=status)
    
    # Ordenar por data de início (mais recente primeiro)
    periodos = periodos.order_by('-data_inicio', '-criado_em')
    
    # Anotar contagem de movimentos para cada período
    for periodo in periodos:
        periodo._movimentos_count = periodo.movimentos_caixa.count()
        periodo._total_entradas = periodo.total_entradas
        periodo._total_saidas = periodo.total_saidas
        periodo._saldo_atual = periodo.saldo_atual
    
    context = {
        'periodos': periodos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_selecionado': status,
        'status_choices': PeriodoMovimentoCaixa.STATUS_CHOICES,
    }
    
    return render(request, 'notas/fluxo_caixa/pesquisar_periodos.html', context)


@login_required
@admin_required
def pesquisar_periodo_movimento_caixa(request):
    """Página para pesquisar e listar períodos de movimento de caixa"""
    
    # Filtros
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    status = request.GET.get('status', '')
    
    # Buscar períodos
    periodos = PeriodoMovimentoCaixa.objects.all()
    
    # Aplicar filtros
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            periodos = periodos.filter(data_inicio__gte=data_inicio_obj)
        except:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            periodos = periodos.filter(data_inicio__lte=data_fim_obj)
        except:
            pass
    
    if status:
        periodos = periodos.filter(status=status)
    
    # Ordenar por data de início (mais recente primeiro)
    periodos = periodos.order_by('-data_inicio', '-criado_em')
    
    # Os dados serão acessados via propriedades do modelo
    # Não é necessário anotar, pois o modelo já tem as propriedades
    
    context = {
        'periodos': periodos,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_selecionado': status,
        'status_choices': PeriodoMovimentoCaixa.STATUS_CHOICES,
    }
    
    return render(request, 'notas/fluxo_caixa/pesquisar_periodos.html', context)


@login_required
@admin_required
def visualizar_periodo_movimento_caixa(request, pk):
    """Visualiza detalhes de um período de movimento de caixa"""
    
    periodo = get_object_or_404(PeriodoMovimentoCaixa, pk=pk)
    
    # Buscar movimentos do período
    movimentos = MovimentoCaixa.objects.filter(
        periodo=periodo
    ).select_related(
        'funcionario', 'cliente', 'acerto_diario', 'usuario_criacao'
    ).order_by('data', 'criado_em')
    
    # Calcular saldo acumulado
    movimentos_com_saldo = []
    saldo_acumulado = periodo.valor_inicial_caixa
    
    for mov in movimentos:
        if mov.is_entrada:
            saldo_acumulado += mov.valor
        else:
            saldo_acumulado -= mov.valor
        movimentos_com_saldo.append({
            'movimento': mov,
            'saldo_acumulado': saldo_acumulado
        })
    
    # Calcular totais
    total_entradas = sum(mov.valor for mov in movimentos if mov.is_entrada)
    total_saidas = sum(mov.valor for mov in movimentos if mov.is_saida)
    saldo = periodo.valor_inicial_caixa + total_entradas - total_saidas
    
    context = {
        'periodo': periodo,
        'movimentos_com_saldo': movimentos_com_saldo,
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'valor_inicial_caixa': periodo.valor_inicial_caixa,
        'saldo': saldo,
        'total_movimentos': movimentos.count(),
    }
    
    return render(request, 'notas/fluxo_caixa/visualizar_periodo_movimento_caixa.html', context)

