"""
Views relacionadas a Notas Fiscais
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from sistema_estelar.api_utils import json_success, json_error
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count, IntegerField
from django.db.models.functions import Cast
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import datetime

from ..models import NotaFiscal, CobrancaCarregamento, OcorrenciaNotaFiscal, Cliente
from ..forms import NotaFiscalForm, NotaFiscalSearchForm, MercadoriaDepositoSearchForm
from ..decorators import rate_limit_critical
from ..utils.date_utils import parse_date_iso
from .base import is_cliente

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
@rate_limit_critical
def adicionar_nota_fiscal(request):
    """View para adicionar uma nova nota fiscal"""
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            try:
                nota_fiscal = form.save(commit=False)
                nota_fiscal.status = 'Depósito' 
                nota_fiscal.save()
                
                logger.info(
                    f'Nota fiscal {nota_fiscal.nota} criada com sucesso',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'nota_id': nota_fiscal.pk,
                        'nota_numero': nota_fiscal.nota,
                        'cliente_id': nota_fiscal.cliente.pk if nota_fiscal.cliente else None
                    }
                )
                
                messages.success(request, f'Nota Fiscal {nota_fiscal.nota} adicionada com sucesso!')

                if 'salvar_e_adicionar' in request.POST:
                    # Retorna para a mesma página com formulário limpo
                    form = NotaFiscalForm()
                    return render(request, 'notas/adicionar_nota.html', {
                        'form': form,
                        'focus_nota': True  # Flag para focar no campo nota
                    })
                else:
                    return redirect('notas:detalhes_nota_fiscal', pk=nota_fiscal.pk)
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro ao criar nota fiscal',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao adicionar nota fiscal: {str(e)}')
        else:
            logger.warning(
                f'Formulário de nota fiscal inválido',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'errors': form.errors
                }
            )
            messages.error(request, 'Houve um erro ao adicionar a nota fiscal. Verifique os campos.')
    else:
        form = NotaFiscalForm()
    return render(request, 'notas/adicionar_nota.html', {'form': form})


@login_required
@rate_limit_critical
def editar_nota_fiscal(request, pk):
    """View para editar uma nota fiscal existente"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    # Validar acesso: clientes só podem editar suas próprias notas
    if request.user.is_cliente and request.user.cliente != nota.cliente:
        messages.error(request, 'Acesso negado. Você só pode editar suas próprias notas fiscais.')
        return redirect('notas:minhas_notas_fiscais')
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota fiscal atualizada com sucesso!')
            return redirect('notas:detalhes_nota_fiscal', pk=nota.pk)
        else:
            messages.error(request, 'Houve um erro ao atualizar a nota fiscal. Verifique os campos.')
    else:
        form = NotaFiscalForm(instance=nota)
    return render(request, 'notas/editar_nota.html', {'form': form, 'nota': nota})


@login_required
@rate_limit_critical
def excluir_nota_fiscal(request, pk):
    """View para excluir uma nota fiscal (com validação de senha admin)"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    # Validar acesso: clientes só podem excluir suas próprias notas
    if request.user.is_cliente and request.user.cliente != nota.cliente:
        messages.error(request, 'Acesso negado. Você só pode excluir suas próprias notas fiscais.')
        return redirect('notas:minhas_notas_fiscais')
    
    if request.method == 'POST':
        # Verificar se é requisição AJAX e se é JSON ou FormData
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                import json
                try:
                    body = request.body
                    if isinstance(body, bytes):
                        body = body.decode('utf-8')
                    data = json.loads(body)
                    username_admin = data.get('username_admin', '')
                    senha_admin = data.get('senha_admin', '')
                except (json.JSONDecodeError, ValueError):
                    return json_error('Erro ao processar requisição JSON', status=400)
            else:
                username_admin = request.POST.get('username_admin', '')
                senha_admin = request.POST.get('senha_admin', '')
        else:
            username_admin = request.POST.get('username_admin', '')
            senha_admin = request.POST.get('senha_admin', '')
        
        # Verificar credenciais de administrador
        from ..utils.validacao_exclusao import validar_exclusao_com_senha_admin
        
        valido, admin_autorizador, mensagem_erro = validar_exclusao_com_senha_admin(
            username_admin=username_admin,
            senha_admin=senha_admin,
            usuario_solicitante=request.user
        )
        
        if not valido:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error(mensagem_erro, status=400)
            messages.error(request, mensagem_erro)
            return render(request, 'notas/excluir_nota.html', {
                'nota': nota,
                'erro_senha': True
            })
        
        # Registrar na auditoria ANTES de excluir
        from ..utils.auditoria import registrar_exclusao
        if request.user.is_authenticated:
            observacao = f"Exclusão solicitada por {request.user.username}"
            if admin_autorizador and admin_autorizador != request.user:
                observacao += f", autorizada por {admin_autorizador.username}"
            
            registrar_exclusao(
                usuario=request.user,
                instancia=nota,
                request=request,
                descricao=observacao
            )
        
        try:
            # Remover nota dos romaneios vinculados
            for romaneio in nota.romaneios_vinculados.all():
                romaneio.notas_fiscais.remove(nota)
            
            # Excluir a nota
            nota.delete()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_success(
                    message='Nota fiscal excluída com sucesso!',
                    redirect_url='/notas/notas/',
                )
            
            messages.success(request, 'Nota fiscal excluída com sucesso!')
            return redirect('notas:listar_notas_fiscais')
        except IntegrityError as e:
            logger.error(
                'Erro de integridade ao excluir nota fiscal',
                extra={
                    'user': request.user.username,
                    'nota_id': pk,
                    'error': str(e)
                },
                exc_info=True
            )
            error_msg = 'Não foi possível excluir a nota fiscal. Ela pode estar vinculada a outros registros.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error(error_msg, status=400)
            messages.error(request, error_msg)
        except Exception as e:
            logger.error(
                'Erro inesperado ao excluir nota fiscal',
                extra={
                    'user': request.user.username,
                    'nota_id': pk,
                    'error_type': type(e).__name__,
                    'error': str(e)
                },
                exc_info=True
            )
            error_msg = 'Erro inesperado ao excluir nota fiscal. Tente novamente ou entre em contato com o suporte.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error(error_msg, status=500)
            messages.error(request, error_msg)
            return render(request, 'notas/excluir_nota.html', {
                'nota': nota,
                'erro_senha': False
            })
    
    return render(request, 'notas/excluir_nota.html', {
        'nota': nota,
        'erro_senha': False
    })


@login_required
def detalhes_nota_fiscal(request, pk):
    """View para exibir detalhes de uma nota fiscal"""
    # Otimizar query com select_related
    nota = get_object_or_404(
        NotaFiscal.objects.select_related('cliente'),
        pk=pk
    )
    
    # Validar acesso: clientes só podem ver suas próprias notas
    if request.user.is_cliente and request.user.cliente != nota.cliente:
        messages.error(request, 'Acesso negado. Você só pode visualizar suas próprias notas fiscais.')
        return redirect('notas:minhas_notas_fiscais')
    
    # Otimizar query de romaneios vinculados
    romaneios_vinculados = nota.romaneios_vinculados.select_related(
        'cliente', 'motorista', 'veiculo_principal'
    ).order_by('-data_emissao')
    
    # Buscar ocorrências da nota fiscal com fotos otimizadas
    ocorrencias = nota.ocorrencias.select_related('usuario_criacao').prefetch_related('fotos').order_by('-data_criacao')
    
    context = {
        'nota': nota,
        'romaneios_vinculados': romaneios_vinculados,
        'ocorrencias': ocorrencias,
    }
    return render(request, 'notas/detalhes_nota_fiscal.html', context)


@login_required
def listar_notas_fiscais(request):
    """Lista todas as notas fiscais com filtros de busca"""
    search_form = NotaFiscalSearchForm(request.GET)
    notas_fiscais = NotaFiscal.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        # Otimizar query com select_related para evitar N+1
        # Filtrar por cliente se usuário for cliente
        if request.user.is_cliente and request.user.cliente:
            queryset = NotaFiscal.objects.filter(cliente=request.user.cliente).select_related('cliente')
        else:
            queryset = NotaFiscal.objects.select_related('cliente')
        nota = search_form.cleaned_data.get('nota')
        cliente = search_form.cleaned_data.get('cliente')
        data = search_form.cleaned_data.get('data')
        local = search_form.cleaned_data.get('local')
        status = search_form.cleaned_data.get('status')
        
        if nota:
            queryset = queryset.filter(nota__icontains=nota)
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if data:
            queryset = queryset.filter(data=data)
        if local:
            queryset = queryset.filter(local=local)
        if status:
            queryset = queryset.filter(status=status)
        
        notas_fiscais = queryset.order_by('nota')
    
    context = {
        'notas_fiscais': notas_fiscais,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_notas.html', context)


@login_required
def buscar_mercadorias_deposito(request):
    """Busca mercadorias no depósito com foco na localização"""
    search_form = MercadoriaDepositoSearchForm(request.GET)
    mercadorias = NotaFiscal.objects.none()
    search_performed = bool(request.GET)
    
    # Contagem por galpão
    contagem_galpoes = {}
    galpoes_com_mercadorias = set()
    galpoes_info = []
    
    for choice in NotaFiscal.LOCAL_CHOICES:
        codigo = choice[0]
        nome = choice[1]
        contagem = NotaFiscal.objects.filter(local=codigo, status='Depósito').count()
        contagem_galpoes[nome] = contagem
        galpoes_info.append({
            'codigo': codigo,
            'nome': nome,
            'quantidade': contagem
        })

    if search_performed and search_form.is_valid():
        # Na tela de busca por localização, sempre filtrar apenas status "Depósito"
        # Otimizar query com select_related para evitar N+1
        queryset = NotaFiscal.objects.filter(status='Depósito').select_related('cliente')
        cliente = search_form.cleaned_data.get('cliente')
        mercadoria = search_form.cleaned_data.get('mercadoria')
        nota = search_form.cleaned_data.get('nota')
        local = search_form.cleaned_data.get('local')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if mercadoria:
            queryset = queryset.filter(mercadoria__icontains=mercadoria)
        if nota:
            queryset = queryset.filter(nota__icontains=nota)
        if data_inicio:
            queryset = queryset.filter(data__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data__lte=data_fim)
        
        # Se foi filtrado por galpão específico, agrupar por cliente
        if local:
            queryset = queryset.filter(local=local)
            mercadorias = queryset.values('cliente__razao_social', 'cliente__id').annotate(
                valor_total=Sum('valor'),
                peso_total=Sum('peso'),
                quantidade_total=Sum('quantidade'),
                total_notas=Count('id')
            ).order_by('cliente__razao_social')
        # Se foi filtrado por cliente (sem galpão específico), agrupar por galpão
        elif cliente:
            mercadorias = queryset.values('local', 'cliente__razao_social', 'cliente__id').annotate(
                valor_total=Sum('valor'),
                peso_total=Sum('peso'),
                quantidade_total=Sum('quantidade'),
                total_notas=Count('id')
            ).order_by('local', 'cliente__razao_social')
        else:
            # Busca geral, mostrar lista normal
            # select_related já aplicado no queryset acima
            mercadorias = queryset.select_related('cliente').order_by('local', 'cliente__razao_social', 'mercadoria')
        
        # Identificar galpões com mercadorias do cliente pesquisado
        if cliente:
            galpoes_com_mercadorias = set()
            # Otimizar query com select_related
            cliente_mercadorias = NotaFiscal.objects.filter(
                cliente=cliente, status='Depósito'
            ).select_related('cliente')
            for mercadoria in cliente_mercadorias:
                if mercadoria.local:
                    galpoes_com_mercadorias.add(mercadoria.local)
        elif local:
            # Quando apenas galpão é selecionado, marcar esse galpão como tendo mercadorias se houver resultados
            galpoes_com_mercadorias = {local} if list(mercadorias) else set()
        else:
            # Busca geral - identificar galpões com mercadorias
            galpoes_com_mercadorias = set()
            for mercadoria in mercadorias:
                if hasattr(mercadoria, 'local') and mercadoria.local:
                    galpoes_com_mercadorias.add(mercadoria.local)
    
    # Preparar dados do formulário para o template
    form_data = {}
    if search_form.is_valid():
        form_data = search_form.cleaned_data
    
    context = {
        'mercadorias': mercadorias,
        'search_form': search_form,
        'search_performed': search_performed,
        'form_data': form_data,  # Passar dados limpos para o template
        'contagem_galpoes': contagem_galpoes,
        'galpoes_com_mercadorias': list(galpoes_com_mercadorias),
        'galpoes_info': galpoes_info,
    }
    return render(request, 'notas/buscar_mercadorias_deposito.html', context)


@login_required
def pesquisar_mercadorias_deposito(request):
    """Pesquisa mercadorias no depósito"""
    from django.db.models import Sum, Count
    from decimal import Decimal
    
    search_form = MercadoriaDepositoSearchForm(request.GET)
    mercadorias = NotaFiscal.objects.none()
    search_performed = bool(request.GET)
    total_quantidade = Decimal('0.00')
    total_peso = Decimal('0.00')
    total_valor = Decimal('0.00')
    
    if search_performed and search_form.is_valid():
        # Filtrar apenas notas com status "Depósito"
        queryset = NotaFiscal.objects.filter(status='Depósito').select_related('cliente')
        
        cliente = search_form.cleaned_data.get('cliente')
        mercadoria = search_form.cleaned_data.get('mercadoria')
        fornecedor = search_form.cleaned_data.get('fornecedor')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if mercadoria:
            queryset = queryset.filter(mercadoria__icontains=mercadoria)
        if fornecedor:
            queryset = queryset.filter(fornecedor__icontains=fornecedor)
        if data_inicio:
            queryset = queryset.filter(data__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data__lte=data_fim)
        
        # Ordenar numericamente pela NF em ordem crescente (campo nota é CharField)
        mercadorias = queryset.annotate(
            nota_numero=Cast('nota', IntegerField())
        ).order_by('nota_numero', 'nota')
        
        # Calcular totais
        if mercadorias.exists():
            totais = mercadorias.aggregate(
                total_quantidade=Sum('quantidade'),
                total_peso=Sum('peso'),
                total_valor=Sum('valor')
            )
            total_quantidade = totais['total_quantidade'] or Decimal('0.00')
            total_peso = totais['total_peso'] or Decimal('0.00')
            total_valor = totais['total_valor'] or Decimal('0.00')
    
    context = {
        'search_form': search_form,
        'mercadorias': mercadorias,
        'search_performed': search_performed,
        'total_quantidade': total_quantidade,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/pesquisar_mercadorias_deposito.html', context)


@login_required
def procurar_mercadorias_deposito(request):
    """Procurar mercadorias no depósito (tela vazia)"""
    return render(request, 'notas/procurar_mercadorias_deposito.html')


@login_required
def simular_carregamento(request):
    """Tela para simular carregamento de mercadorias do depósito (clientes e totais)."""
    # Clientes com mercadorias no depósito: totais de peso e valor por cliente
    agregado = NotaFiscal.objects.filter(status='Depósito').values('cliente').annotate(
        total_peso=Sum('peso'),
        total_valor=Sum('valor'),
    ).order_by('cliente')
    clientes_deposito = []
    for item in agregado:
        try:
            cliente = Cliente.objects.get(pk=item['cliente'])
            clientes_deposito.append({
                'cliente': cliente,
                'total_peso': item['total_peso'] or Decimal('0'),
                'total_valor': item['total_valor'] or Decimal('0'),
            })
        except Cliente.DoesNotExist:
            continue
    clientes_deposito.sort(key=lambda x: (x['cliente'].razao_social or '').upper())
    # JSON para o front: listar clientes disponíveis e adicionar um por vez à tabela
    clientes_deposito_json = json.dumps([
        {
            'id': item['cliente'].pk,
            'razao_social': item['cliente'].razao_social or '',
            'total_peso': str(item['total_peso']),
            'total_valor': str(item['total_valor']),
        }
        for item in clientes_deposito
    ], ensure_ascii=False)
    return render(request, 'notas/simular_carregamento.html', {
        'clientes_deposito': clientes_deposito,
        'clientes_deposito_json': clientes_deposito_json,
    })


@login_required
def imprimir_relatorio_mercadorias_deposito(request):
    """Imprime relatório de mercadorias no depósito"""
    search_form = MercadoriaDepositoSearchForm(request.GET)
    # Otimizar query com select_related para evitar N+1
    mercadorias = NotaFiscal.objects.filter(status='Depósito').select_related('cliente')
    
    if request.GET:
        if search_form.is_valid():
            cliente = search_form.cleaned_data.get('cliente')
            mercadoria = search_form.cleaned_data.get('mercadoria')
            nota = search_form.cleaned_data.get('nota')
            local = search_form.cleaned_data.get('local')
            data_inicio = search_form.cleaned_data.get('data_inicio')
            data_fim = search_form.cleaned_data.get('data_fim')
            
            if cliente:
                mercadorias = mercadorias.filter(cliente=cliente)
            if mercadoria:
                mercadorias = mercadorias.filter(mercadoria__icontains=mercadoria)
            if nota:
                mercadorias = mercadorias.filter(nota__icontains=nota)
            if local:
                mercadorias = mercadorias.filter(local=local)
            if data_inicio:
                mercadorias = mercadorias.filter(data__gte=data_inicio)
            if data_fim:
                mercadorias = mercadorias.filter(data__lte=data_fim)
    
    mercadorias = mercadorias.annotate(
        nota_numero=Cast('nota', IntegerField())
    ).order_by('nota_numero', 'nota')
    
    # Calcular totais
    total_peso = sum(m.peso for m in mercadorias if m.peso)
    total_valor = sum(m.valor for m in mercadorias if m.valor)
    
    return render(request, 'notas/imprimir_relatorio_mercadorias_deposito.html', {
        'mercadorias': mercadorias,
        'total_peso': total_peso,
        'total_valor': total_valor,
    })


@login_required
@user_passes_test(is_cliente)
def minhas_notas_fiscais(request):
    """View para clientes verem apenas suas notas fiscais"""
    status_filter = request.GET.get('status', 'deposito')
    
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        notas_fiscais = NotaFiscal.objects.filter(cliente=request.user.cliente)
    else:
        notas_fiscais = NotaFiscal.objects.all()
    
    # Aplicar filtro por status
    if status_filter == 'deposito':
        notas_fiscais = notas_fiscais.filter(status='Depósito')
    elif status_filter == 'enviada':
        notas_fiscais = notas_fiscais.filter(status='Enviada')
    
    # Otimizar query com select_related para evitar N+1 e ordenar por numero da nota
    notas_fiscais = notas_fiscais.select_related('cliente').order_by('nota')
    
    # Calcular totais
    total_quantidade = sum(nota.quantidade for nota in notas_fiscais if nota.quantidade)
    total_peso = sum(nota.peso for nota in notas_fiscais if nota.peso)
    total_valor = sum(nota.valor for nota in notas_fiscais if nota.valor)
    
    return render(request, 'notas/auth/minhas_notas.html', {
        'notas_fiscais': notas_fiscais,
        'status_filter': status_filter,
        'total_quantidade': total_quantidade,
        'total_peso': total_peso,
        'total_valor': total_valor
    })


@login_required
@user_passes_test(is_cliente)
def imprimir_nota_fiscal(request, pk):
    """Imprime uma nota fiscal específica"""
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    # Verificar se o usuário tem permissão para ver esta nota
    if request.user.tipo_usuario == 'cliente' and request.user.cliente != nota.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta nota fiscal.')
        return redirect('notas:minhas_notas_fiscais')
    
    return render(request, 'notas/auth/imprimir_nota_fiscal.html', {
        'nota': nota
    })


@login_required
def imprimir_relatorio_deposito(request):
    """Imprime relatório de notas em depósito (ou filtradas quando informado via querystring)."""
    nota = request.GET.get('nota')
    cliente_id = request.GET.get('cliente')
    data = request.GET.get('data')
    local = request.GET.get('local')
    status = request.GET.get('status')

    filtros_informados = any([nota, cliente_id, data, local, status])

    if filtros_informados:
        # Mesmo comportamento da tela "Pesquisar Notas Fiscais", com restrição por cliente quando aplicável.
        if request.user.is_cliente and request.user.cliente:
            notas_fiscais = NotaFiscal.objects.filter(cliente=request.user.cliente).select_related('cliente')
        else:
            notas_fiscais = NotaFiscal.objects.select_related('cliente')

        if nota:
            notas_fiscais = notas_fiscais.filter(nota__icontains=nota)
        if cliente_id:
            notas_fiscais = notas_fiscais.filter(cliente_id=cliente_id)
        if data:
            data_obj = parse_date_iso(data)
            if data_obj:
                notas_fiscais = notas_fiscais.filter(data=data_obj)
        if local:
            notas_fiscais = notas_fiscais.filter(local=local)
        if status:
            notas_fiscais = notas_fiscais.filter(status=status)

        notas_fiscais = notas_fiscais.order_by('nota')
    else:
        # Comportamento original do relatório de depósito quando aberto sem filtros.
        if request.user.tipo_usuario == 'cliente' and request.user.cliente:
            notas_fiscais = NotaFiscal.objects.filter(
                cliente=request.user.cliente,
                status='Depósito'
            ).select_related('cliente').order_by('data')
        else:
            notas_fiscais = NotaFiscal.objects.filter(
                status='Depósito'
            ).select_related('cliente').order_by('data')

    total_quantidade = sum(nota.quantidade for nota in notas_fiscais if nota.quantidade)
    total_peso = sum(nota.peso for nota in notas_fiscais)
    total_valor = sum(nota.valor for nota in notas_fiscais)

    return render(request, 'notas/auth/imprimir_relatorio_deposito.html', {
        'notas_fiscais': notas_fiscais,
        'total_quantidade': total_quantidade,
        'total_peso': total_peso,
        'total_valor': total_valor,
        'cliente': request.user.cliente if request.user.cliente else None
    })


@login_required
@user_passes_test(is_cliente)
def minhas_cobrancas_carregamento(request):
    """View para clientes verem apenas suas cobranças de carregamento"""
    # Verificar se o usuário é cliente e tem cliente vinculado
    if not hasattr(request.user, 'cliente') or not request.user.cliente:
        messages.error(request, 'Você não possui um cliente vinculado. Entre em contato com o administrador.')
        return redirect('notas:dashboard_cliente')
    
    # Buscar cobranças do cliente
    cobrancas = CobrancaCarregamento.objects.filter(
        cliente=request.user.cliente
    ).select_related('cliente').prefetch_related('romaneios').order_by('-criado_em')
    
    # Aplicar filtros
    status_filter = request.GET.get('status', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    if status_filter:
        cobrancas = cobrancas.filter(status=status_filter)
    
    data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
    if data_inicio_obj:
        cobrancas = cobrancas.filter(criado_em__gte=data_inicio_obj)
    data_fim_obj = parse_date_iso(data_fim) if data_fim else None
    if data_fim_obj:
        cobrancas = cobrancas.filter(criado_em__lte=data_fim_obj)
    
    return render(request, 'notas/auth/minhas_cobrancas_carregamento.html', {
        'cobrancas': cobrancas
    })


@login_required
@user_passes_test(is_cliente)
def gerar_relatorio_cobranca_carregamento_pdf_cliente(request, cobranca_id):
    """View para clientes visualizarem o relatório de suas cobranças de carregamento."""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)

    # Verificar se o usuário tem cliente vinculado
    if not hasattr(request.user, 'cliente') or not request.user.cliente:
        messages.error(request, 'Você não possui um cliente vinculado.')
        return redirect('notas:dashboard_cliente')

    # Verificar se a cobrança pertence ao cliente do usuário
    if request.user.cliente != cobranca.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta cobrança.')
        return redirect('notas:minhas_cobrancas_carregamento')

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

