"""
Views administrativas (apenas para administradores)
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import datetime, date, timedelta

from ..models import Usuario, TabelaSeguro, AgendaEntrega, AuditoriaLog, CobrancaCarregamento, Cliente, RomaneioViagem, SetorBancario
from ..forms import CadastroUsuarioForm, TabelaSeguroForm, AgendaEntregaForm, CobrancaCarregamentoForm, SetorBancarioForm
from ..decorators import admin_required, rate_limit_critical
from .base import is_admin

# Configurar logger
logger = logging.getLogger(__name__)


@admin_required
@rate_limit_critical
def cadastrar_usuario(request):
    """View para cadastrar um novo usuário"""
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário {user.username} cadastrado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao cadastrar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'notas/auth/cadastrar_usuario.html', {'form': form})


@admin_required
def listar_usuarios(request):
    """Lista todos os usuários"""
    # Otimizar query com select_related se houver relacionamentos
    usuarios = Usuario.objects.select_related('cliente').order_by('username')
    return render(request, 'notas/auth/listar_usuarios.html', {'usuarios': usuarios})


@admin_required
@rate_limit_critical
def editar_usuario(request, pk):
    """View para editar um usuário existente"""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            if form.cleaned_data.get('password1'):
                usuario.set_password(form.cleaned_data['password1'])
            form.save()
            messages.success(request, f'Usuário {usuario.username} atualizado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm(instance=usuario)
    
    return render(request, 'notas/auth/editar_usuario.html', {'form': form, 'usuario': usuario})


@admin_required
@rate_limit_critical
def toggle_status_usuario(request, pk):
    """Alterna o status (ativo/inativo) de um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        # Alternar o status
        if usuario.is_active:
            usuario.is_active = False
            messages.success(request, f'Usuário {usuario.username} foi desativado com sucesso!')
        else:
            usuario.is_active = True
            messages.success(request, f'Usuário {usuario.username} foi ativado com sucesso!')
        
        usuario.save()
        return redirect('notas:listar_usuarios')
    
    return redirect('notas:listar_usuarios')


@admin_required
@rate_limit_critical
def excluir_usuario(request, pk):
    """View para excluir um usuário"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if usuario == request.user:
        messages.error(request, 'Você não pode excluir seu próprio usuário.')
        return redirect('notas:listar_usuarios')
    
    if request.method == 'POST':
        try:
            username = usuario.username
            usuario.delete()
            messages.success(request, f'Usuário {username} excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o usuário: {e}')
        return redirect('notas:listar_usuarios')
    
    return render(request, 'notas/auth/confirmar_exclusao_usuario.html', {'usuario': usuario})


@login_required
@user_passes_test(is_admin)
def listar_tabela_seguros(request):
    """Lista todos os registros da tabela de seguros"""
    tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    if not tabela_seguros.exists():
        for estado_uf, estado_nome in TabelaSeguro.ESTADOS_BRASIL:
            TabelaSeguro.objects.create(
                estado=estado_uf,
                percentual_seguro=0.00
            )
        tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    context = {
        'tabela_seguros': tabela_seguros,
    }
    return render(request, 'notas/listar_tabela_seguros.html', context)


@login_required
@user_passes_test(is_admin)
def editar_tabela_seguro(request, pk):
    """Edita um registro específico da tabela de seguros"""
    tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
    
    if request.method == 'POST':
        form = TabelaSeguroForm(request.POST, instance=tabela_seguro)
        if form.is_valid():
            form.save()
            messages.success(request, f'Percentual de seguro para {tabela_seguro.get_estado_display()} atualizado com sucesso!')
            return redirect('notas:listar_tabela_seguros')
        else:
            messages.error(request, 'Houve um erro ao atualizar o percentual. Verifique os campos.')
    else:
        form = TabelaSeguroForm(instance=tabela_seguro)
    
    context = {
        'form': form,
        'tabela_seguro': tabela_seguro,
    }
    return render(request, 'notas/editar_tabela_seguro.html', context)


@login_required
@user_passes_test(is_admin)
def atualizar_tabela_seguro_ajax(request, pk):
    """Atualiza um registro da tabela de seguros via AJAX"""
    if request.method == 'POST':
        tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
        percentual = request.POST.get('percentual_seguro')
        
        try:
            percentual_float = float(percentual)
            if 0 <= percentual_float <= 100:
                tabela_seguro.percentual_seguro = percentual_float
                tabela_seguro.save()
                
                messages.success(request, f'Percentual de seguro para {tabela_seguro.get_estado_display()} atualizado para {percentual_float}%')
                
                return JsonResponse({
                    'success': True,
                    'message': f'Percentual atualizado para {percentual_float}%',
                    'percentual': percentual_float
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Percentual deve estar entre 0% e 100%'
                })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Valor inválido para percentual'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})


# Views de Agenda de Entregas
@login_required
@user_passes_test(is_admin)
def listar_agenda_entregas(request):
    """Lista todas as entregas agendadas"""
    # Filtros
    status_filter = request.GET.get('status', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Query base
    entregas = AgendaEntrega.objects.select_related('cliente', 'usuario_criacao').all()
    
    # Aplicar filtros
    if status_filter:
        entregas = entregas.filter(status=status_filter)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            entregas = entregas.filter(data_entrega__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            entregas = entregas.filter(data_entrega__lte=data_fim_obj)
        except ValueError:
            pass
    
    # Ordenar por data de entrega
    entregas = entregas.order_by('data_entrega', 'cliente__razao_social')
    
    # Estatísticas
    total_entregas = entregas.count()
    entregas_agendadas = entregas.filter(status='Agendada').count()
    entregas_entregues = entregas.filter(status='Entregue').count()
    entregas_canceladas = entregas.filter(status='Cancelada').count()
    
    # Próximas entregas (próximos 7 dias)
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    proximas_entregas = entregas.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).order_by('data_entrega')[:10]
    
    context = {
        'title': 'Agenda de Entregas',
        'entregas': entregas,
        'proximas_entregas': proximas_entregas,
        'total_entregas': total_entregas,
        'entregas_agendadas': entregas_agendadas,
        'entregas_entregues': entregas_entregues,
        'entregas_canceladas': entregas_canceladas,
        'status_filter': status_filter,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_choices': AgendaEntrega.STATUS_ENTREGA_CHOICES,
    }
    
    return render(request, 'notas/agenda/listar_agenda_entregas.html', context)


@login_required
@user_passes_test(is_admin)
@rate_limit_critical
def adicionar_agenda_entrega(request):
    """Adiciona uma nova entrega à agenda"""
    if request.method == 'POST':
        form = AgendaEntregaForm(request.POST)
        if form.is_valid():
            agenda_entrega = form.save(commit=False)
            agenda_entrega.usuario_criacao = request.user
            agenda_entrega.save()
            messages.success(request, 'Entrega agendada com sucesso!')
            return redirect('notas:listar_agenda_entregas')
    else:
        form = AgendaEntregaForm()
    
    context = {
        'title': 'Agendar Nova Entrega',
        'form': form,
    }
    
    return render(request, 'notas/agenda/adicionar_agenda_entrega.html', context)


@login_required
@user_passes_test(is_admin)
@rate_limit_critical
def editar_agenda_entrega(request, pk):
    """Edita uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        form = AgendaEntregaForm(request.POST, instance=agenda_entrega)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrega atualizada com sucesso!')
            return redirect('notas:listar_agenda_entregas')
    else:
        form = AgendaEntregaForm(instance=agenda_entrega)
    
    context = {
        'title': f'Editar Entrega - {agenda_entrega.cliente.razao_social}',
        'form': form,
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/editar_agenda_entrega.html', context)


@login_required
@user_passes_test(is_admin)
@rate_limit_critical
def excluir_agenda_entrega(request, pk):
    """Exclui uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        try:
            cliente_nome = agenda_entrega.cliente.razao_social
            data_entrega = agenda_entrega.data_entrega.strftime('%d/%m/%Y')
            agenda_entrega.delete()
            messages.success(request, f'Entrega para {cliente_nome} em {data_entrega} excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir a entrega: {e}')
        return redirect('notas:listar_agenda_entregas')
    
    context = {
        'title': 'Confirmar Exclusão',
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/confirmar_exclusao_agenda_entrega.html', context)


@login_required
@user_passes_test(is_admin)
def detalhes_agenda_entrega(request, pk):
    """Mostra os detalhes de uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    context = {
        'title': f'Detalhes da Entrega - {agenda_entrega.cliente.razao_social}',
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/detalhes_agenda_entrega.html', context)


@login_required
@user_passes_test(is_admin)
def alterar_status_agenda(request, pk):
    """Altera o status de uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in [choice[0] for choice in AgendaEntrega.STATUS_ENTREGA_CHOICES]:
            agenda_entrega.status = novo_status
            agenda_entrega.save()
            messages.success(request, f'Status alterado para {agenda_entrega.get_status_display()}!')
            return redirect('notas:listar_agenda_entregas')
        else:
            messages.error(request, 'Status inválido!')
    
    context = {
        'title': f'Alterar Status - {agenda_entrega.cliente.razao_social}',
        'agenda_entrega': agenda_entrega,
        'status_choices': AgendaEntrega.STATUS_ENTREGA_CHOICES,
    }
    
    return render(request, 'notas/agenda/alterar_status_agenda.html', context)


@login_required
@user_passes_test(is_admin)
def marcar_em_andamento(request, pk):
    """Marca uma entrega como em andamento"""
    entrega = get_object_or_404(AgendaEntrega, pk=pk)
    entrega.status = 'Em Andamento'
    entrega.save()
    messages.success(request, 'Entrega marcada como em andamento!')
    return redirect('notas:listar_agenda_entregas')


@login_required
@user_passes_test(is_admin)
def marcar_concluida(request, pk):
    """Marca uma entrega como concluída"""
    entrega = get_object_or_404(AgendaEntrega, pk=pk)
    entrega.status = 'Concluída'
    entrega.save()
    messages.success(request, 'Entrega marcada como concluída!')
    return redirect('notas:listar_agenda_entregas')


@login_required
@user_passes_test(is_admin)
def marcar_entregue(request, pk):
    """Marca uma entrega como entregue"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    agenda_entrega.status = 'Entregue'
    agenda_entrega.save()
    
    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': 'Entrega marcada como Entregue!'
        })
    
    # Se for uma requisição normal, redirecionar
    messages.success(request, 'Entrega marcada como Entregue!')
    return redirect('notas:listar_agenda_entregas')


@login_required
@user_passes_test(is_admin)
def marcar_cancelada(request, pk):
    """Marca uma entrega como cancelada"""
    entrega = get_object_or_404(AgendaEntrega, pk=pk)
    entrega.status = 'Cancelada'
    entrega.save()
    messages.success(request, 'Entrega marcada como cancelada!')
    return redirect('notas:listar_agenda_entregas')


@login_required
@user_passes_test(is_admin)
def widget_agenda_entregas(request):
    """Widget de agenda de entregas para o dashboard"""
    # Próximas entregas (próximos 7 dias)
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    
    proximas_entregas = AgendaEntrega.objects.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('data_entrega')[:5]
    
    # Entregas de hoje
    entregas_hoje = AgendaEntrega.objects.filter(
        data_entrega=hoje,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('cliente__razao_social')
    
    # Estatísticas rápidas
    total_agendadas = AgendaEntrega.objects.filter(status='Agendada').count()
    total_em_andamento = AgendaEntrega.objects.filter(status='Em Andamento').count()
    
    context = {
        'proximas_entregas': proximas_entregas,
        'entregas_hoje': entregas_hoje,
        'total_agendadas': total_agendadas,
        'total_em_andamento': total_em_andamento,
        'hoje': hoje,
    }
    
    return render(request, 'notas/widget_agenda_entregas.html', context)


@login_required
@user_passes_test(is_admin)
def test_widget_agenda(request):
    """Teste do widget de agenda"""
    return render(request, 'notas/test_widget_agenda.html')


# Views de Cobrança de Carregamento
@login_required
@user_passes_test(is_admin)
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
            # Exibir erros específicos do formulário
            error_messages = []
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    error_messages.append(f"{field_name}: {error}")
            if error_messages:
                messages.error(request, 'Erro ao criar cobrança: ' + ' | '.join(error_messages))
            else:
                messages.error(request, 'Erro ao criar cobrança. Verifique os campos.')
            
            # Se houver cliente selecionado, manter os romaneios disponíveis
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


@login_required
@user_passes_test(is_admin)
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


@login_required
@user_passes_test(is_admin)
@rate_limit_critical
def excluir_cobranca_carregamento(request, cobranca_id):
    """View para excluir uma cobrança de carregamento"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        # Verificar credenciais de administrador
        from ..utils.validacao_exclusao import validar_exclusao_com_senha_admin
        
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
        
        # Registrar na auditoria
        from ..utils.auditoria import registrar_exclusao
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


@login_required
@user_passes_test(is_admin)
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


@login_required
@user_passes_test(is_admin)
def gerar_relatorio_cobranca_carregamento_pdf(request, cobranca_id):
    """View para gerar PDF de uma cobrança de carregamento"""
    from ..utils.relatorios import gerar_relatorio_pdf_cobranca_carregamento, gerar_resposta_pdf
    
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    try:
        pdf_content = gerar_relatorio_pdf_cobranca_carregamento(cobranca)
        # Limpar nome do arquivo removendo caracteres inválidos
        nome_cliente = cobranca.cliente.razao_social.replace(' ', '_').replace('/', '_').replace('\\', '_')
        nome_cliente = ''.join(c for c in nome_cliente if c.isalnum() or c in ('_', '-'))
        nome_arquivo = f"cobranca_carregamento_{cobranca.id}_{nome_cliente}.pdf"
        return gerar_resposta_pdf(pdf_content, nome_arquivo, inline=True)
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('notas:cobranca_carregamento')


@login_required
@user_passes_test(is_admin)
def gerar_relatorio_consolidado_cobranca_pdf(request):
    """View para gerar PDF consolidado de cobranças"""
    from ..utils.relatorios import gerar_relatorio_pdf_consolidado_cobranca, gerar_resposta_pdf
    
    # Filtros
    cliente_id = request.GET.get('cliente')
    status = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    cobrancas = CobrancaCarregamento.objects.all().select_related('cliente').prefetch_related('romaneios')
    
    if cliente_id:
        cobrancas = cobrancas.filter(cliente_id=cliente_id)
    if status:
        cobrancas = cobrancas.filter(status=status)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio_obj)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            cobrancas = cobrancas.filter(criado_em__date__lte=data_fim_obj)
        except ValueError:
            pass
    
    # Obter cliente selecionado se houver
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


# Views de Auditoria
@admin_required
def listar_logs_auditoria(request):
    """Lista todos os logs de auditoria"""
    from django.core.paginator import Paginator
    
    logs = AuditoriaLog.objects.all().select_related('usuario')
    
    # Filtros
    modelo_filtro = request.GET.get('modelo', '')
    acao_filtro = request.GET.get('acao', '')
    usuario_filtro = request.GET.get('usuario', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    if modelo_filtro:
        logs = logs.filter(modelo__icontains=modelo_filtro)
    if acao_filtro:
        logs = logs.filter(acao=acao_filtro)
    if usuario_filtro:
        logs = logs.filter(usuario__username__icontains=usuario_filtro)
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            logs = logs.filter(data_hora__date__gte=data_inicio_obj)
        except ValueError:
            pass
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            logs = logs.filter(data_hora__date__lte=data_fim_obj)
        except ValueError:
            pass
    
    # Paginação
    paginator = Paginator(logs, 50)  # 50 logs por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    total_logs = AuditoriaLog.objects.count()
    acoes_count = AuditoriaLog.objects.values_list('acao', flat=True).distinct()
    modelos_count = AuditoriaLog.objects.values_list('modelo', flat=True).distinct()
    
    # Lista de usuários para o filtro
    usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'modelo_filtro': modelo_filtro,
        'acao_filtro': acao_filtro,
        'usuario_filtro': usuario_filtro,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'acoes': AuditoriaLog.ACAO_CHOICES,
        'ACTION_CHOICES': AuditoriaLog.ACAO_CHOICES,  # Para compatibilidade com template
        'total_logs': total_logs,
        'acoes_count': acoes_count,
        'modelos_count': modelos_count,
        'usuarios': usuarios,
        'acao_atual': acao_filtro,
        'modelo_atual': modelo_filtro,
        'usuario_atual': usuario_filtro,
        'data_inicio_atual': data_inicio,
        'data_fim_atual': data_fim,
    }
    
    return render(request, 'notas/auditoria/listar_logs.html', context)


@admin_required
def detalhes_log_auditoria(request, pk):
    """Exibe os detalhes de um log de auditoria específico"""
    log = get_object_or_404(AuditoriaLog, pk=pk)
    
    context = {
        'log': log,
    }
    
    return render(request, 'notas/auditoria/detalhes_log.html', context)


@admin_required
def listar_registros_excluidos(request):
    """Lista todos os registros que foram excluídos (soft delete)"""
    from django.contrib.contenttypes.models import ContentType
    
    # Buscar logs de exclusão
    logs_exclusao = AuditoriaLog.objects.filter(acao='DELETE').select_related('usuario')
    
    # Agrupar por modelo
    modelos_excluidos = {}
    for log in logs_exclusao:
        if log.modelo not in modelos_excluidos:
            modelos_excluidos[log.modelo] = []
        modelos_excluidos[log.modelo].append(log)
    
    context = {
        'modelos_excluidos': modelos_excluidos,
    }
    
    return render(request, 'notas/auditoria/registros_excluidos.html', context)


@login_required
@user_passes_test(is_admin)
def listar_setores_bancarios(request):
    """Lista todos os setores bancários cadastrados"""
    setores = SetorBancario.objects.all().order_by('setor')
    
    # Criar setores padrão se não existirem
    if not setores.exists():
        SetorBancario.objects.create(
            setor='Carregamento',
            nome_responsavel='',
            banco='',
            agencia='',
            conta_corrente='',
            chave_pix='',
            tipo_chave_pix='Telefone',
            ativo=True
        )
        SetorBancario.objects.create(
            setor='Armazenagem',
            nome_responsavel='',
            banco='',
            agencia='',
            conta_corrente='',
            chave_pix='',
            tipo_chave_pix='CNPJ',
            ativo=True
        )
        setores = SetorBancario.objects.all().order_by('setor')
    
    context = {
        'setores': setores,
    }
    return render(request, 'notas/listar_setores_bancarios.html', context)


@login_required
@user_passes_test(is_admin)
def editar_setor_bancario(request, pk):
    """Edita um setor bancário específico"""
    setor = get_object_or_404(SetorBancario, pk=pk)
    
    if request.method == 'POST':
        form = SetorBancarioForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dados bancários do setor {setor.get_setor_display()} atualizados com sucesso!')
            return redirect('notas:listar_setores_bancarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar os dados. Verifique os campos.')
    else:
        form = SetorBancarioForm(instance=setor)
    
    context = {
        'form': form,
        'setor': setor,
    }
    return render(request, 'notas/editar_setor_bancario.html', context)


@admin_required
def restaurar_registro(request, modelo, pk):
    """Restaura um registro excluído usando os dados do log de auditoria"""
    from ..utils.auditoria import restaurar_registro as restaurar
    
    try:
        objeto_restaurado = restaurar(modelo, pk, usuario=request.user, request=request)
        
        if objeto_restaurado:
            messages.success(request, f'{modelo} #{objeto_restaurado.pk} restaurado com sucesso!')
        else:
            messages.error(request, f'Não foi possível restaurar {modelo} #{pk}. Log de exclusão não encontrado ou dados inválidos.')
    except Exception as e:
        messages.error(request, f'Erro ao restaurar registro: {str(e)}')
    
    return redirect('notas:listar_registros_excluidos')

