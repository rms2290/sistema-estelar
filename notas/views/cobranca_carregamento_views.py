"""
Views de cobrança de carregamento (apenas administradores).
"""
import logging
from datetime import datetime
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
                    romaneios = RomaneioViagem.objects.filter(cliente=cliente_obj).order_by('-data_emissao')
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
                romaneios = RomaneioViagem.objects.filter(cliente=cliente_obj).order_by('-data_emissao')
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
@rate_limit_critical
def editar_cobranca_carregamento(request, cobranca_id):
    """View para editar uma cobrança de carregamento"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
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
    
    context = {
        'form': form,
        'cobranca': cobranca,
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
    """View para gerar PDF de uma cobrança de carregamento"""
    from ..utils.relatorios import gerar_relatorio_pdf_cobranca_carregamento, gerar_resposta_pdf
    
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    try:
        pdf_content = gerar_relatorio_pdf_cobranca_carregamento(cobranca)
        nome_cliente = cobranca.cliente.razao_social.replace(' ', '_').replace('/', '_').replace('\\', '_')
        nome_cliente = ''.join(c for c in nome_cliente if c.isalnum() or c in ('_', '-'))
        nome_arquivo = f"cobranca_carregamento_{cobranca.id}_{nome_cliente}.pdf"
        return gerar_resposta_pdf(pdf_content, nome_arquivo, inline=True)
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('notas:cobranca_carregamento')


@admin_required
def gerar_relatorio_consolidado_cobranca_pdf(request):
    """View para gerar PDF consolidado de cobranças"""
    from ..utils.relatorios import gerar_relatorio_pdf_consolidado_cobranca, gerar_resposta_pdf
    
    cliente_id = request.GET.get('cliente')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    cobrancas = CobrancaCarregamento.objects.all().select_related('cliente').prefetch_related('romaneios')
    
    if cliente_id:
        cobrancas = cobrancas.filter(cliente_id=cliente_id)
    if status:
        cobrancas = cobrancas.filter(status=status)
    data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
    if data_inicio_obj:
        cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio_obj)
    data_fim_obj = parse_date_iso(data_fim) if data_fim else None
    if data_fim_obj:
        cobrancas = cobrancas.filter(criado_em__date__lte=data_fim_obj)
    
    cliente_selecionado = None
    if cliente_id:
        try:
            cliente_selecionado = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            pass
    
    try:
        pdf_content = gerar_relatorio_pdf_consolidado_cobranca(cobrancas, cliente_selecionado=cliente_selecionado)
        nome_arquivo = f"relatorio_consolidado_cobrancas_{datetime.now().strftime('%Y%m%d')}.pdf"
        return gerar_resposta_pdf(pdf_content, nome_arquivo, inline=True)
    except Exception as e:
        logger.error(
            'Erro ao gerar relatorio consolidado de cobrancas',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'cliente_id': cliente_id,
                'error': str(e)
            },
            exc_info=True
        )
        messages.error(request, f'Erro ao gerar PDF consolidado: {str(e)}')
        return redirect('notas:cobranca_carregamento')
