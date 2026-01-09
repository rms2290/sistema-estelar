"""
Views relacionadas a Romaneios
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.db.models import Q
from django.core.exceptions import ValidationError

from ..models import RomaneioViagem, Cliente, NotaFiscal
from ..forms import RomaneioViagemForm, RomaneioSearchForm
from ..decorators import rate_limit_critical
from .base import get_next_romaneio_codigo, get_next_romaneio_generico_codigo, is_cliente
from ..services import RomaneioService, NotaFiscalService

# Configurar logger
logger = logging.getLogger(__name__)


@login_required
@rate_limit_critical
def adicionar_romaneio(request):
    """View para adicionar um novo romaneio"""
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        # Configurar o queryset das notas fiscais baseado no cliente selecionado
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            try:
                form.fields['notas_fiscais'].queryset = RomaneioService.obter_notas_disponiveis_para_cliente(cliente_id)
            except Cliente.DoesNotExist:
                logger.warning(
                    f'Tentativa de criar romaneio com cliente inexistente: {cliente_id}',
                    extra={'user': request.user.username if request.user.is_authenticated else 'anonymous'}
                )
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
                messages.error(request, 'Cliente selecionado não encontrado.')
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        
        if form.is_valid():
            # Usar serviço para criar romaneio
            emitir = 'emitir' in request.POST
            try:
                romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
                    form_data=form,
                    emitir=emitir,
                    tipo='normal'
                )
                
                if sucesso:
                    logger.info(
                        f'Romaneio {romaneio.codigo} criado com sucesso',
                        extra={
                            'user': request.user.username if request.user.is_authenticated else 'anonymous',
                            'romaneio_id': romaneio.pk,
                            'romaneio_codigo': romaneio.codigo,
                            'status': romaneio.status
                        }
                    )
                    messages.success(request, mensagem)
                    return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
                else:
                    logger.error(
                        f'Erro ao criar romaneio: {mensagem}',
                        extra={
                            'user': request.user.username if request.user.is_authenticated else 'anonymous',
                            'error': mensagem
                        }
                    )
                    messages.error(request, mensagem)
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro de integridade/validação ao criar romaneio',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao criar romaneio: {str(e)}')
        else:
            # Reconfigurar queryset em caso de erro de validação
            if cliente_id:
                form.fields['notas_fiscais'].queryset = RomaneioService.obter_notas_disponiveis_para_cliente(cliente_id)
            else:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
            
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio. Verifique os campos.')
            provisional_codigo = get_next_romaneio_codigo()
    else:
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_codigo()

    context = {
        'form': form,
        'provisional_codigo': provisional_codigo,
    }
    return render(request, 'notas/adicionar_romaneio.html', context)


@login_required
@rate_limit_critical
def adicionar_romaneio_generico(request):
    """View para adicionar um romaneio genérico"""
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            form.fields['notas_fiscais'].queryset = RomaneioService.obter_notas_disponiveis_para_cliente(cliente_id)
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            # Usar serviço para criar romaneio genérico
            emitir = 'emitir' in request.POST
            romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
                form_data=form,
                emitir=emitir,
                tipo='generico'
            )
            
            if sucesso:
                messages.success(request, mensagem)
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
            else:
                messages.error(request, mensagem)
        else:
            # Reconfigurar queryset em caso de erro de validação
            if cliente_id:
                form.fields['notas_fiscais'].queryset = RomaneioService.obter_notas_disponiveis_para_cliente(cliente_id)
            else:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
            
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio genérico. Verifique os campos.')
            provisional_codigo = get_next_romaneio_generico_codigo()
    else:
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_generico_codigo()

    context = {
        'form': form,
        'provisional_codigo': provisional_codigo,
    }
    return render(request, 'notas/adicionar_romaneio_generico.html', context)


@login_required
@rate_limit_critical
def editar_romaneio(request, pk):
    """View para editar um romaneio existente"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Validar acesso: clientes só podem editar romaneios com suas notas
    if request.user.is_cliente and request.user.cliente:
        if not romaneio.notas_fiscais.filter(cliente=request.user.cliente).exists():
            messages.error(request, 'Acesso negado. Você só pode editar romaneios com suas notas fiscais.')
            return redirect('notas:meus_romaneios')
    
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST, instance=romaneio)
        
        cliente_id = request.POST.get('cliente')
        if not cliente_id:
            cliente_id = romaneio.cliente.pk if romaneio.cliente else None
        
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj
                ).filter(
                    Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
                ).order_by('nota')
            except Cliente.DoesNotExist:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            # Usar serviço para editar romaneio
            emitir = 'emitir' in request.POST
            salvar = 'salvar' in request.POST
            
            romaneio, sucesso, mensagem = RomaneioService.editar_romaneio(
                romaneio=romaneio,
                form_data=form,
                emitir=emitir,
                salvar=salvar
            )
            
            if sucesso:
                messages.success(request, mensagem)
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
            else:
                messages.error(request, mensagem)
        else:
            # Reconfigurar queryset em caso de erro de validação
            if cliente_id:
                try:
                    cliente_obj = Cliente.objects.get(pk=cliente_id)
                    form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                        cliente=cliente_obj
                    ).filter(
                        Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
                    ).order_by('nota')
                except Cliente.DoesNotExist:
                    form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
            else:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
            
            messages.error(request, 'Houve um erro ao atualizar o romaneio. Verifique os campos.')
    else:
        form = RomaneioViagemForm(instance=romaneio)

    context = {
        'form': form,
        'romaneio': romaneio,
        'provisional_codigo': romaneio.codigo,
    }
    return render(request, 'notas/editar_romaneio.html', context)


@login_required
@rate_limit_critical
def excluir_romaneio(request, pk):
    """View para excluir um romaneio (com validação de senha admin)"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Validar acesso: clientes só podem excluir romaneios com suas notas
    if request.user.is_cliente and request.user.cliente:
        if not romaneio.notas_fiscais.filter(cliente=request.user.cliente).exists():
            messages.error(request, 'Acesso negado. Você só pode excluir romaneios com suas notas fiscais.')
            return redirect('notas:meus_romaneios')
    
    if request.method == 'POST':
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
            return render(request, 'notas/confirmar_exclusao_romaneio.html', {
                'romaneio': romaneio,
                'erro_senha': True
            })
        
        # Usar serviço para excluir romaneio
        sucesso, mensagem = RomaneioService.excluir_romaneio(romaneio)
        
        if sucesso:
            # Registrar na auditoria
            from ..utils.auditoria import registrar_exclusao
            observacao = f"Exclusão solicitada por {request.user.username}"
            if admin_autorizador and admin_autorizador != request.user:
                observacao += f", autorizada por {admin_autorizador.username}"
            
            registrar_exclusao(
                usuario=request.user,
                instancia=romaneio,
                request=request,
                descricao=observacao
            )
            
            messages.success(request, mensagem)
        else:
            messages.error(request, mensagem)
        
        return redirect('notas:listar_romaneios')
    
    return render(request, 'notas/confirmar_exclusao_romaneio.html', {
        'romaneio': romaneio,
        'erro_senha': False
    })


def detalhes_romaneio(request, pk):
    """View para exibir detalhes de um romaneio"""
    # Otimizar query com select_related e prefetch_related
    romaneio = get_object_or_404(
        RomaneioViagem.objects.select_related(
            'cliente', 'motorista', 'veiculo_principal',
            'reboque_1', 'reboque_2', 'usuario_criacao', 'usuario_ultima_edicao'
        ).prefetch_related('notas_fiscais__cliente'),
        pk=pk
    )
    
    # Verificar se o usuário tem permissão para ver este romaneio
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        if not romaneio.notas_fiscais.filter(cliente=request.user.cliente).exists():
            messages.error(request, 'Você não tem permissão para acessar este romaneio.')
            return redirect('notas:meus_romaneios')
    
    # Notas já foram carregadas via prefetch_related
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota')
    
    # Garantir que os totais estejam calculados
    if notas_romaneadas.exists():
        romaneio.calcular_totais()

    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
    }
    return render(request, 'notas/detalhes_romaneio.html', context)


@login_required
def listar_romaneios(request):
    """Lista todos os romaneios com filtros de busca"""
    search_form = RomaneioSearchForm(request.GET)
    romaneios = RomaneioViagem.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        # Otimizar query com select_related para evitar N+1
        # Filtrar por cliente se usuário for cliente
        if request.user.is_cliente and request.user.cliente:
            queryset = RomaneioViagem.objects.filter(
                notas_fiscais__cliente=request.user.cliente
            ).select_related(
                'cliente', 'motorista', 'veiculo_principal'
            ).prefetch_related('notas_fiscais').distinct()
        else:
            queryset = RomaneioViagem.objects.select_related(
                'cliente', 'motorista', 'veiculo_principal'
            ).prefetch_related('notas_fiscais')
        codigo = search_form.cleaned_data.get('codigo')
        tipo_romaneio = search_form.cleaned_data.get('tipo_romaneio')
        cliente = search_form.cleaned_data.get('cliente')
        motorista = search_form.cleaned_data.get('motorista')
        veiculo_principal = search_form.cleaned_data.get('veiculo_principal')
        status = search_form.cleaned_data.get('status')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if codigo:
            queryset = queryset.filter(codigo__icontains=codigo)
        if tipo_romaneio:
            if tipo_romaneio == 'normal':
                queryset = queryset.filter(codigo__startswith='ROM-').exclude(codigo__startswith='ROM-100-')
            elif tipo_romaneio == 'generico':
                queryset = queryset.filter(codigo__startswith='ROM-100-')
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if motorista:
            queryset = queryset.filter(motorista=motorista)
        if veiculo_principal:
            queryset = queryset.filter(veiculo_principal=veiculo_principal)
        if status:
            queryset = queryset.filter(status=status)
        if data_inicio:
            queryset = queryset.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_emissao__date__lte=data_fim)
        
        romaneios = queryset.order_by('-data_emissao', '-codigo')
    
    context = {
        'romaneios': romaneios,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_romaneios.html', context)


@login_required
def imprimir_romaneio_novo(request, pk):
    """View para imprimir romaneio usando o novo template"""
    import time
    # Otimizar query com select_related e prefetch_related
    romaneio = get_object_or_404(
        RomaneioViagem.objects.select_related(
            'cliente', 'motorista', 'veiculo_principal', 'reboque_1', 'reboque_2'
        ).prefetch_related('notas_fiscais'),
        pk=pk
    )
    
    try:
        notas_romaneadas = romaneio.notas_fiscais.all().order_by('data')
        
        # Usar serviço para calcular totais
        totais = RomaneioService.calcular_totais_romaneio(romaneio)
        total_peso = totais['total_peso']
        total_valor = totais['total_valor']
        
        # Tentar caber tudo em uma página (aumentar limite se necessário)
        notas_list = list(notas_romaneadas)
        notas_paginas = []
        # Aumentar para 30 notas por página para tentar caber tudo
        for i in range(0, len(notas_list), 30):
            pagina = notas_list[i:i + 30]
            notas_paginas.append(pagina)
        
        version = int(time.time())
        
        context = {
            'romaneio': romaneio,
            'notas_romaneadas': notas_romaneadas,
            'notas_paginas': notas_paginas,
            'total_peso': total_peso,
            'total_valor': total_valor,
            'version': version
        }
        
        return render(request, 'notas/visualizar_romaneio_para_impressao.html', context)
    except (RomaneioViagem.DoesNotExist, AttributeError) as e:
        # Tratamento específico para erros conhecidos
        logger.error(
            f'Erro ao gerar impressão do romaneio {pk}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'romaneio_id': pk,
                'error': str(e),
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        messages.error(request, f'Erro ao gerar impressão do romaneio: {str(e)}')
        return render(request, 'notas/visualizar_romaneio_para_impressao.html', {
            'romaneio': romaneio,
            'notas_romaneadas': [],
            'notas_paginas': [],
            'total_peso': 0,
            'total_valor': 0,
            'version': int(time.time()),
            'erro': str(e)
        })


@login_required
def gerar_romaneio_pdf(request, pk):
    """View para gerar PDF do romaneio"""
    from django.template.loader import get_template
    
    # Otimizar query com select_related e prefetch_related
    romaneio = get_object_or_404(
        RomaneioViagem.objects.select_related(
            'cliente', 'motorista', 'veiculo_principal', 'reboque_1', 'reboque_2'
        ).prefetch_related('notas_fiscais'),
        pk=pk
    )
    
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('data')
    
    # Usar serviço para calcular totais
    from ..services.romaneio_service import RomaneioService
    totais = RomaneioService.calcular_totais_romaneio(romaneio)
    total_peso = totais['total_peso']
    total_valor = totais['total_valor']
    
    # Dividir notas em páginas (30 por página)
    notas_list = list(notas_romaneadas)
    notas_paginas = []
    for i in range(0, len(notas_list), 30):
        pagina = notas_list[i:i + 30]
        notas_paginas.append(pagina)
    
    import time
    version = int(time.time())
    
    template = get_template('notas/visualizar_romaneio_para_impressao.html')
    html = template.render({
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'notas_paginas': notas_paginas,
        'total_peso': total_peso,
        'total_valor': total_valor,
        'version': version
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="romaneio_{romaneio.codigo}.pdf"'
    
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        font_config = FontConfiguration()
        css = CSS(string='''
            @page {
                size: A4;
                margin: 0.8cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 11px;
                line-height: 1.2;
                margin: 0;
                padding: 0;
            }
            .header {
                text-align: center;
                margin-bottom: 8px;
                padding-bottom: 5px;
                border-bottom: 2px solid #000;
            }
            .header h1 {
                font-size: 17px;
                margin: 0;
            }
            .info-container {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                gap: 8px;
            }
            .romaneio-info, .motorista-info, .cliente-info {
                flex: 1;
                padding: 5px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }
            .report-title {
                text-align: center;
                margin: 8px 0 5px 0;
                font-size: 13px;
                font-weight: bold;
                border-bottom: 1px solid #000;
                padding-bottom: 3px;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
                margin: 5px 0 8px 0;
            }
            .table th, .table td {
                border: 1px solid #ddd;
                padding: 3px 4px;
                font-size: 9px;
            }
            .table th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            .table tbody tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .no-print {
                display: none !important;
            }
            .print-button {
                display: none !important;
            }
        ''', font_config=font_config)
        
        HTML(string=html).write_pdf(response, stylesheets=[css], font_config=font_config)
        
    except ImportError:
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="romaneio_{romaneio.codigo}.html"'
        messages.warning(request, 'Biblioteca WeasyPrint não encontrada. Instale com: pip install weasyprint')
    
    return response


@login_required
@user_passes_test(is_cliente)
def meus_romaneios(request):
    """View para clientes verem apenas seus romaneios"""
    if request.user.tipo_usuario.upper() == 'CLIENTE' and request.user.cliente:
        romaneios = RomaneioViagem.objects.filter(
            notas_fiscais__cliente=request.user.cliente
        ).select_related(
            'cliente', 'motorista', 'veiculo_principal'
        ).prefetch_related('notas_fiscais').distinct().order_by('-data_emissao')
    else:
        romaneios = RomaneioViagem.objects.all().select_related(
            'cliente', 'motorista', 'veiculo_principal'
        ).prefetch_related('notas_fiscais').order_by('-data_emissao')
    
    return render(request, 'notas/auth/meus_romaneios.html', {
        'romaneios': romaneios
    })

