"""
=============================================================================
VIEWS DE CLIENTES
=============================================================================

Este módulo contém todas as views relacionadas ao gerenciamento de clientes.

Funcionalidades:
----------------
1. CRUD Completo (Create, Read, Update, Delete)
2. Listagem com filtros de busca
3. Toggle de status (Ativo/Inativo)
4. Exclusão com validação de senha de administrador
5. Detalhes do cliente

Autor: Sistema Estelar
Data: 2025
Versão: 2.0
=============================================================================
"""
import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from sistema_estelar.api_utils import json_success, json_error
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Cliente
from ..forms import ClienteForm, ClienteSearchForm
from ..decorators import rate_limit_critical

# Configurar logger
logger = logging.getLogger(__name__)


# ============================================================================
# VIEWS DE CRUD
# ============================================================================

@login_required
@rate_limit_critical
def adicionar_cliente(request):
    """
    View para adicionar um novo cliente ao sistema.
    
    Métodos Suportados:
        - GET: Exibe formulário vazio para criação
        - POST: Processa formulário e cria cliente
    
    Fluxo:
        1. Se POST e formulário válido → Cria cliente e redireciona
        2. Se POST e formulário inválido → Exibe erros
        3. Se GET → Exibe formulário vazio
    
    Redirecionamento:
        - Sucesso: /notas/clientes/ (listar clientes)
        - Erro: Permanece na página com mensagens de erro
    
    Template:
        notas/adicionar_cliente.html
    
    Exemplo de Uso:
        POST /notas/clientes/adicionar/
        {
            'razao_social': 'Empresa XYZ LTDA',
            'cnpj': '12345678000190',
            'status': 'Ativo'
        }
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                cliente = form.save()
                logger.info(
                    f'Cliente {cliente.razao_social} criado com sucesso',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'cliente_id': cliente.pk,
                        'cliente_cnpj': cliente.cnpj
                    }
                )
                messages.success(request, 'Cliente adicionado com sucesso!')
                return redirect('notas:listar_clientes')
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro ao criar cliente',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao adicionar cliente: {str(e)}')
        else:
            logger.warning(
                f'Formulário de cliente inválido',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'errors': form.errors
                }
            )
            messages.error(request, 'Houve um erro ao adicionar o cliente. Verifique os campos.')
    else:
        form = ClienteForm()
    return render(request, 'notas/adicionar_cliente.html', {'form': form})


@login_required
@rate_limit_critical
def editar_cliente(request, pk):
    """
    View para editar um cliente existente.
    
    Args:
        pk (int): Primary key do cliente a ser editado
    
    Métodos Suportados:
        - GET: Exibe formulário preenchido com dados do cliente
        - POST: Processa formulário e atualiza cliente
    
    Fluxo:
        1. Busca cliente por pk (404 se não existir)
        2. Se POST e formulário válido → Atualiza e redireciona
        3. Se POST e formulário inválido → Exibe erros
        4. Se GET → Exibe formulário preenchido
    
    Redirecionamento:
        - Sucesso: /notas/clientes/ (listar clientes)
        - Erro: Permanece na página com mensagens de erro
    
    Template:
        notas/editar_cliente.html
    
    Context:
        - form: Instância do ClienteForm
        - cliente: Instância do Cliente sendo editado
    
    Exemplo de Uso:
        GET /notas/clientes/editar/1/
        POST /notas/clientes/editar/1/ com dados atualizados
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            try:
                form.save()
                logger.info(
                    f'Cliente {cliente.razao_social} atualizado com sucesso',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'cliente_id': cliente.pk
                    }
                )
                messages.success(request, 'Cliente atualizado com sucesso!')
                return redirect('notas:listar_clientes')
            except (IntegrityError, ValidationError) as e:
                logger.error(
                    f'Erro ao atualizar cliente {cliente.pk}',
                    extra={
                        'user': request.user.username if request.user.is_authenticated else 'anonymous',
                        'cliente_id': cliente.pk,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'Erro ao atualizar cliente: {str(e)}')
        else:
            logger.warning(
                f'Formulário de edição de cliente inválido',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'cliente_id': cliente.pk,
                    'errors': form.errors
                }
            )
            messages.error(request, 'Houve um erro ao atualizar o cliente. Verifique os campos.')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'notas/editar_cliente.html', {'form': form, 'cliente': cliente})


@login_required
@login_required
@rate_limit_critical
def excluir_cliente(request, pk):
    """
    View para excluir um cliente (requer validação de senha de administrador).
    
    Args:
        pk (int): Primary key do cliente a ser excluído
    
    Segurança:
        - Requer autenticação (@login_required)
        - Requer validação de senha de administrador
        - Registra exclusão na auditoria
    
    Métodos Suportados:
        - GET: Exibe página de confirmação
        - POST: Processa exclusão após validação
    
    Fluxo:
        1. Busca cliente por pk (404 se não existir)
        2. Se POST:
           a. Valida credenciais de administrador
           b. Se válido → Registra auditoria e exclui
           c. Se inválido → Exibe erro
        3. Se GET → Exibe página de confirmação
    
    Suporte AJAX:
        - Aceita requisições AJAX (X-Requested-With: XMLHttpRequest)
        - Retorna JSON com resultado da operação
    
    Redirecionamento:
        - Sucesso: /notas/clientes/ (listar clientes)
        - Erro: Permanece na página com mensagem de erro
    
    Template:
        notas/excluir_cliente.html
    
    Context:
        - cliente: Instância do Cliente a ser excluído
        - erro_senha: Boolean indicando se houve erro de validação
    
    Exemplo de Uso:
        GET /notas/clientes/excluir/1/
        POST /notas/clientes/excluir/1/ com username_admin e senha_admin
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Verificar se é requisição AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            import json
            try:
                data = json.loads(request.body)
                username_admin = data.get('username_admin', '')
                senha_admin = data.get('senha_admin', '')
            except json.JSONDecodeError:
                return json_error('Erro ao processar requisição', status=400)
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
            return render(request, 'notas/excluir_cliente.html', {
                'cliente': cliente,
                'erro_senha': True
            })
        
        try:
            # Registrar na auditoria
            from ..utils.auditoria import registrar_exclusao
            observacao = f"Exclusão solicitada por {request.user.username}"
            if admin_autorizador and admin_autorizador != request.user:
                observacao += f", autorizada por {admin_autorizador.username}"
            
            try:
                registrar_exclusao(
                    usuario=request.user,
                    instancia=cliente,
                    request=request,
                    descricao=observacao
                )
            except Exception as audit_error:
                logger.error(
                    f'Erro ao registrar exclusão na auditoria',
                    extra={
                        'user': request.user.username,
                        'cliente_id': cliente.pk,
                        'error': str(audit_error)
                    },
                    exc_info=True
                )
            
            cliente.delete()
            
            logger.info(
                f'Cliente {cliente.razao_social} excluído com sucesso',
                extra={
                    'user': request.user.username,
                    'cliente_id': cliente.pk,
                    'admin_autorizador': admin_autorizador.username if admin_autorizador else None
                }
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_success(
                    message='Cliente excluído com sucesso!',
                    redirect_url='/notas/clientes/',
                )
            
            messages.success(request, 'Cliente excluído com sucesso!')
        except (IntegrityError, ValidationError) as e:
            error_msg = str(e)
            logger.error(
                f'Erro de integridade/validação ao excluir cliente {cliente.pk}',
                extra={
                    'user': request.user.username if request.user.is_authenticated else 'anonymous',
                    'cliente_id': cliente.pk,
                    'error': error_msg,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_error(f'Não foi possível excluir o cliente: {error_msg}', status=400)
            messages.error(request, f'Não foi possível excluir o cliente: {error_msg}')
        
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect('notas:listar_clientes')
    
    return render(request, 'notas/excluir_cliente.html', {
        'cliente': cliente,
        'erro_senha': False
    })


@login_required
def detalhes_cliente(request, pk):
    """
    View para exibir detalhes completos de um cliente.
    
    Args:
        pk (int): Primary key do cliente
    
    Métodos Suportados:
        - GET: Exibe página de detalhes
    
    Fluxo:
        1. Busca cliente por pk (404 se não existir)
        2. Valida permissão de acesso (clientes só veem seus próprios dados)
        3. Renderiza template com dados do cliente
    
    Template:
        notas/detalhes_cliente.html
    
    Context:
        - cliente: Instância do Cliente com todos os dados
    
    Exemplo de Uso:
        GET /notas/clientes/1/detalhes/
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Validar acesso: clientes só podem ver seus próprios dados
    if request.user.is_cliente and request.user.cliente != cliente:
        messages.error(request, 'Acesso negado. Você só pode visualizar seus próprios dados.')
        return redirect('notas:dashboard')
    context = {
        'cliente': cliente,
    }
    return render(request, 'notas/detalhes_cliente.html', context)


@login_required
def imprimir_detalhes_cliente(request, pk):
    """
    View para imprimir detalhes de um cliente em nova janela.
    
    Args:
        pk (int): Primary key do cliente
    
    Métodos Suportados:
        - GET: Exibe página de impressão
    
    Fluxo:
        1. Busca cliente por pk (404 se não existir)
        2. Valida permissão de acesso (clientes só veem seus próprios dados)
        3. Renderiza template de impressão
    
    Template:
        notas/relatorios/imprimir_detalhes_cliente.html
    
    Context:
        - cliente: Instância do Cliente com todos os dados
        - data_emissao: Data e hora da emissão do relatório
    
    Exemplo de Uso:
        GET /notas/clientes/1/imprimir/
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Validar acesso: clientes só podem ver seus próprios dados
    if request.user.is_cliente and request.user.cliente != cliente:
        messages.error(request, 'Acesso negado. Você só pode visualizar seus próprios dados.')
        return redirect('notas:dashboard')
    
    context = {
        'cliente': cliente,
        'data_emissao': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }
    return render(request, 'notas/relatorios/imprimir_detalhes_cliente.html', context)


@login_required
def toggle_status_cliente(request, pk):
    """
    Alterna o status de um cliente entre 'Ativo' e 'Inativo'.
    
    Args:
        pk (int): Primary key do cliente
    
    Métodos Suportados:
        - POST: Alterna status e salva
    
    Fluxo:
        1. Busca cliente por pk (404 se não existir)
        2. Se status atual é 'Ativo' → Muda para 'Inativo'
        3. Se status atual é 'Inativo' → Muda para 'Ativo'
        4. Salva alteração e redireciona para detalhes
    
    Redirecionamento:
        - Sempre: /notas/clientes/{pk}/detalhes/
    
    Mensagens:
        - Sucesso: Mensagem informando novo status
    
    Exemplo de Uso:
        POST /notas/clientes/1/toggle-status/
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Alternar o status
        if cliente.status == 'Ativo':
            cliente.status = 'Inativo'
            messages.success(request, f'Cliente {cliente.razao_social} foi desativado com sucesso!')
        else:
            cliente.status = 'Ativo'
            messages.success(request, f'Cliente {cliente.razao_social} foi ativado com sucesso!')
        
        cliente.save()
        return redirect('notas:detalhes_cliente', pk=cliente.pk)
    
    return redirect('notas:detalhes_cliente', pk=cliente.pk)


@login_required
def listar_clientes(request):
    """
    Lista todos os clientes com sistema de busca e filtros.
    
    Segurança:
        - Requer autenticação (@login_required)
    
    Métodos Suportados:
        - GET: Exibe lista de clientes (com ou sem filtros)
    
    Filtros Disponíveis:
        - razao_social: Busca parcial (case-insensitive)
        - cnpj: Busca parcial no CNPJ
        - status: Filtro exato (Ativo/Inativo)
    
    Fluxo:
        1. Cria formulário de busca com dados GET
        2. Se formulário válido e há parâmetros → Aplica filtros
        3. Se não há parâmetros → Lista vazia (não mostra todos)
        4. Ordena resultados por razão social
    
    Template:
        notas/listar_clientes.html
    
    Context:
        - clientes: QuerySet de clientes filtrados
        - search_form: Instância do ClienteSearchForm
        - search_performed: Boolean indicando se busca foi realizada
    
    Exemplo de Uso:
        GET /notas/clientes/
        GET /notas/clientes/?razao_social=XYZ&status=Ativo
    """
    search_form = ClienteSearchForm(request.GET)
    clientes = Cliente.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        # Query já otimizada (Cliente não tem ForeignKeys principais)
        queryset = Cliente.objects.all()
        razao_social = search_form.cleaned_data.get('razao_social')
        cnpj = search_form.cleaned_data.get('cnpj')
        status = search_form.cleaned_data.get('status')

        if razao_social:
            queryset = queryset.filter(razao_social__icontains=razao_social)
        if cnpj:
            queryset = queryset.filter(cnpj__icontains=cnpj)
        if status:
            queryset = queryset.filter(status=status)
        
        clientes = queryset.order_by('razao_social')
    
    context = {
        'clientes': clientes,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_clientes.html', context)


@login_required
def imprimir_relatorio_clientes(request):
    """
    View para imprimir relatório de clientes filtrados em nova janela.
    
    Recebe os mesmos parâmetros de filtro da view listar_clientes e
    renderiza um template de impressão com as informações dos clientes.
    """
    search_form = ClienteSearchForm(request.GET)
    clientes = Cliente.objects.none()
    search_performed = bool(request.GET)
    
    razao_social = None
    cnpj = None
    status = None

    if search_performed and search_form.is_valid():
        queryset = Cliente.objects.all()
        razao_social = search_form.cleaned_data.get('razao_social')
        cnpj = search_form.cleaned_data.get('cnpj')
        status = search_form.cleaned_data.get('status')

        if razao_social:
            queryset = queryset.filter(razao_social__icontains=razao_social)
        if cnpj:
            queryset = queryset.filter(cnpj__icontains=cnpj)
        if status:
            queryset = queryset.filter(status=status)
        
        clientes = queryset.order_by('razao_social')
    
    # Informações dos filtros aplicados para exibir no relatório
    filtros_aplicados = []
    if razao_social:
        filtros_aplicados.append(f"Razão Social: {razao_social}")
    if cnpj:
        filtros_aplicados.append(f"CNPJ: {cnpj}")
    if status:
        filtros_aplicados.append(f"Status: {status}")
    
    context = {
        'clientes': clientes,
        'filtros_aplicados': filtros_aplicados,
        'total_clientes': clientes.count(),
        'data_emissao': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }
    return render(request, 'notas/relatorios/imprimir_clientes.html', context)
