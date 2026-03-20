"""
Views de cobrança de carregamento (apenas administradores).
"""
import logging
from datetime import datetime
from decimal import Decimal
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from ..models import CobrancaCarregamento, Cliente, RomaneioViagem
from ..forms import CobrancaCarregamentoForm
from ..decorators import admin_required, rate_limit_critical
from ..utils.date_utils import parse_date_iso

logger = logging.getLogger(__name__)


@admin_required
@rate_limit_critical
def criar_cobranca_carregamento(request):
    """View para criar uma nova cobrança de carregamento"""
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    romaneios = RomaneioViagem.objects.none()
    cliente_selecionado_id = None
    
    if request.method == 'POST':
        form = CobrancaCarregamentoForm(request.POST)
        if form.is_valid():
            cobranca = form.save()
            messages.success(request, f'Cobrança #{cobranca.id} criada com sucesso!')
            return redirect('notas:cobranca_carregamento')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            if error_messages:
                messages.error(request, 'Erro ao criar cobrança: ' + ' | '.join(error_messages))
            else:
                messages.error(request, 'Erro ao criar cobrança. Verifique os campos.')
            
            cliente_id = request.POST.get('cliente')
            if cliente_id:
                try:
                    cliente_obj = Cliente.objects.get(pk=cliente_id)
                    romaneios = (
                        RomaneioViagem.objects
                        .filter(cliente=cliente_obj, cobrancas_vinculadas__isnull=True)
                        .order_by('-data_emissao')
                    )
                    form.fields['romaneios'].queryset = romaneios
                    cliente_selecionado_id = cliente_id
                except (Cliente.DoesNotExist, ValueError):
                    pass
    else:
        form = CobrancaCarregamentoForm()
        cliente_selecionado_id = request.GET.get('cliente')
        if cliente_selecionado_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_selecionado_id)
                romaneios = (
                    RomaneioViagem.objects
                    .filter(cliente=cliente_obj, cobrancas_vinculadas__isnull=True)
                    .order_by('-data_emissao')
                )
                form.fields['romaneios'].queryset = romaneios
            except Cliente.DoesNotExist:
                pass
    
    context = {
        'form': form,
        'clientes': clientes,
        'romaneios': romaneios,
        'cliente_selecionado_id': cliente_selecionado_id,
    }
    return render(request, 'notas/criar_cobranca_carregamento.html', context)


@admin_required
def visualizar_cobranca_carregamento(request, cobranca_id):
    """View para visualizar uma cobrança de carregamento (somente leitura), com opções Editar e Excluir."""
    cobranca = get_object_or_404(
        CobrancaCarregamento.objects.select_related('cliente').prefetch_related('romaneios'),
        pk=cobranca_id
    )
    context = {'cobranca': cobranca}
    return render(request, 'notas/visualizar_cobranca_carregamento.html', context)


@admin_required
@rate_limit_critical
def editar_cobranca_carregamento(request, cobranca_id):
    """View para editar uma cobrança de carregamento"""
    cobranca = get_object_or_404(
        CobrancaCarregamento.objects.select_related('cliente').prefetch_related('romaneios'),
        pk=cobranca_id
    )
    
    if request.method == 'POST':
        form = CobrancaCarregamentoForm(request.POST, instance=cobranca)
        if form.is_valid():
            cobranca = form.save()
            messages.success(request, f'Cobrança #{cobranca.id} atualizada com sucesso!')
            return redirect('notas:cobranca_carregamento')
        else:
            messages.error(request, 'Erro ao atualizar cobrança. Verifique os campos.')
    else:
        form = CobrancaCarregamentoForm(instance=cobranca)
    
    # Romaneios do cliente (para exibir na tabela de seleção)
    romaneios = (
        RomaneioViagem.objects
        .filter(cliente=cobranca.cliente)
        .filter(Q(cobrancas_vinculadas__isnull=True) | Q(cobrancas_vinculadas=cobranca))
        .distinct()
        .order_by('-data_emissao')
    )
    # IDs dos romaneios selecionados: no POST use o que veio do formulário; no GET use os já vinculados
    if request.method == 'POST' and request.POST.getlist('romaneios'):
        romaneios_selecionados = [int(x) for x in request.POST.getlist('romaneios') if x.isdigit()]
    else:
        romaneios_selecionados = list(cobranca.romaneios.values_list('id', flat=True))
    
    context = {
        'form': form,
        'cobranca': cobranca,
        'romaneios': romaneios,
        'romaneios_selecionados': romaneios_selecionados,
    }
    return render(request, 'notas/editar_cobranca_carregamento.html', context)


@admin_required
@rate_limit_critical
def excluir_cobranca_carregamento(request, cobranca_id):
    """View para excluir uma cobrança de carregamento"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        from ..utils.validacao_exclusao import validar_exclusao_com_senha_admin
        from ..utils.auditoria import registrar_exclusao
        
        username_admin = request.POST.get('username_admin', '')
        senha_admin = request.POST.get('senha_admin', '')
        valido, admin_autorizador, mensagem_erro = validar_exclusao_com_senha_admin(
            username_admin=username_admin,
            senha_admin=senha_admin,
            usuario_solicitante=request.user
        )
        
        if not valido:
            messages.error(request, mensagem_erro)
            return render(request, 'notas/confirmar_exclusao_cobranca.html', {
                'cobranca': cobranca,
                'erro_senha': True
            })
        
        observacao = f"Exclusão solicitada por {request.user.username}"
        if admin_autorizador and admin_autorizador != request.user:
            observacao += f", autorizada por {admin_autorizador.username}"
        
        registrar_exclusao(
            usuario=request.user,
            instancia=cobranca,
            request=request,
            descricao=observacao
        )
        
        cobranca_id_temp = cobranca.id
        cobranca.delete()
        messages.success(request, f'Cobrança #{cobranca_id_temp} excluída com sucesso!')
        return redirect('notas:cobranca_carregamento')
    
    context = {
        'cobranca': cobranca,
        'erro_senha': False,
    }
    return render(request, 'notas/confirmar_exclusao_cobranca.html', context)


@admin_required
def baixar_cobranca_carregamento(request, cobranca_id):
    """View para baixar (marcar como paga) uma cobrança"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        cobranca.baixar()
        messages.success(request, f'Cobrança #{cobranca.id} baixada com sucesso!')
        return redirect('notas:cobranca_carregamento')
    
    context = {
        'cobranca': cobranca,
    }
    return render(request, 'notas/confirmar_baixa_cobranca.html', context)


@admin_required
def gerar_relatorio_cobranca_carregamento_pdf(request, cobranca_id):
    """Exibe relatório individual de cobrança no layout padrão de impressão."""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    romaneios = cobranca.romaneios.all().order_by('codigo')

    data_ref = cobranca.criado_em.date() if cobranca.criado_em else None
    data_ref_fmt = data_ref.strftime('%d/%m/%Y') if data_ref else '-'

    context = {
        'titulo_relatorio': 'RELATÓRIO DE COBRANÇA DE CARREGAMENTO',
        'cobranca': cobranca,
        'romaneios': romaneios,
        'data_inicio': data_ref_fmt,
        'data_fim': data_ref_fmt,
        'data_geracao': datetime.now().strftime('%d/%m/%Y às %H:%M'),
    }
    response = render(request, 'notas/relatorio_cobranca_carregamento_pdf.html', context)
    response['Content-Disposition'] = 'inline'
    return response


@admin_required
def gerar_relatorio_consolidado_cobranca_pdf(request):
    """Exibe relatório consolidado de cobranças no layout padrão de impressão."""
    # Defesa em profundidade: cliente não deve acessar este relatório.
    if getattr(request.user, 'tipo_usuario', None) == 'cliente':
        messages.error(request, 'Acesso negado. Relatório consolidado indisponível para usuário cliente.')
        return redirect('notas:dashboard')

    cliente_id = request.GET.get('cliente')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    base_qs = CobrancaCarregamento.objects.all().select_related('cliente').prefetch_related('romaneios')
    data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
    data_fim_obj = parse_date_iso(data_fim) if data_fim else None

    # Se data foi informada mas inválida, não retorna tudo por engano.
    if data_inicio and not data_inicio_obj:
        messages.error(request, 'Data inicial inválida. Use o formato YYYY-MM-DD.')
        base_qs = base_qs.none()
    if data_fim and not data_fim_obj:
        messages.error(request, 'Data final inválida. Use o formato YYYY-MM-DD.')
        base_qs = base_qs.none()

    tem_filtro = bool(cliente_id or status or data_inicio or data_fim)
    if not tem_filtro:
        # Consolidado sem filtro não deve exibir todos os registros.
        cobrancas = base_qs.none()
    else:
        cobrancas = base_qs
        if cliente_id:
            cobrancas = cobrancas.filter(cliente_id=cliente_id)
        if status:
            cobrancas = cobrancas.filter(status=status)
        if data_inicio_obj:
            cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio_obj)
        if data_fim_obj:
            cobrancas = cobrancas.filter(criado_em__date__lte=data_fim_obj)
    
    cliente_selecionado = None
    if cliente_id:
        try:
            cliente_selecionado = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            pass

    itens = list(cobrancas.order_by('-criado_em'))
    total_carregamento = Decimal('0.00')
    total_distribuicao = Decimal('0.00')
    total_margem_estelar = Decimal('0.00')
    total_cte_manifesto = Decimal('0.00')
    total_cte_terceiro = Decimal('0.00')
    total_lucro_cte = Decimal('0.00')
    total_geral = Decimal('0.00')

    for c in itens:
        total_carregamento += c.valor_carregamento or Decimal('0.00')
        total_distribuicao += c.valor_distribuicao_trabalhadores or Decimal('0.00')
        total_margem_estelar += c.margem_carregamento or Decimal('0.00')
        total_cte_manifesto += c.valor_cte_manifesto or Decimal('0.00')
        total_cte_terceiro += c.valor_cte_terceiro or Decimal('0.00')
        total_lucro_cte += c.lucro_cte or Decimal('0.00')
        total_geral += c.valor_total or Decimal('0.00')

    data_inicio_fmt = data_inicio_obj.strftime('%d/%m/%Y') if data_inicio_obj else '-'
    data_fim_fmt = data_fim_obj.strftime('%d/%m/%Y') if data_fim_obj else '-'

    context = {
        'titulo_relatorio': 'RELATÓRIO CONSOLIDADO DE COBRANÇAS',
        'itens': itens,
        'mostrar_colunas_restritas': getattr(request.user, 'tipo_usuario', None) == 'cliente',
        'data_inicio': data_inicio_fmt,
        'data_fim': data_fim_fmt,
        'data_geracao': datetime.now().strftime('%d/%m/%Y às %H:%M'),
        'cliente_selecionado': cliente_selecionado,
        'total_carregamento': total_carregamento,
        'total_distribuicao': total_distribuicao,
        'total_margem_estelar': total_margem_estelar,
        'total_cte_manifesto': total_cte_manifesto,
        'total_cte_terceiro': total_cte_terceiro,
        'total_lucro_cte': total_lucro_cte,
        'total_geral': total_geral,
    }
    response = render(request, 'notas/relatorio_consolidado_cobranca_pdf.html', context)
    response['Content-Disposition'] = 'inline'
    return response
