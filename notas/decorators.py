"""
=============================================================================
DECORATORS DE CONTROLE DE ACESSO E RATE LIMITING
=============================================================================

Este módulo contém decorators customizados para controle de acesso e
permissões no sistema. Implementa controle granular baseado em tipos
de usuário (admin, funcionário, cliente) e rate limiting para proteção
contra abuso.

Decorators Disponíveis:
-----------------------
1. @admin_required: Acesso restrito a administradores
2. @funcionario_required: Acesso para funcionários e administradores
3. @cliente_required: Acesso para todos os tipos de usuário autenticados
4. @can_access_cliente_data: Verifica acesso a dados de cliente específico
5. @rate_limit_critical: Rate limiting para endpoints críticos

Uso:
    from notas.decorators import admin_required, funcionario_required, rate_limit_critical
    
    @admin_required
    @rate_limit_critical
    def minha_view_admin(request):
        # Apenas admins podem acessar, com rate limiting
        pass
    
    @funcionario_required
    def minha_view_funcionario(request):
        # Funcionários e admins podem acessar
        pass

Autor: Sistema Estelar
Data: 2025
Versão: 2.1
=============================================================================
"""
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

# Importação de rate limiting
try:
    from django_ratelimit.decorators import ratelimit
except ImportError:
    # Se django_ratelimit não estiver instalado, criar um decorator dummy
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# ============================================================================
# DECORATORS DE PERMISSÃO
# ============================================================================

def admin_required(view_func):
    """
    Decorator que restringe acesso apenas a administradores.
    
    Comportamento:
        - Se usuário não autenticado → Redireciona para login
        - Se usuário não é admin → Redireciona para dashboard com mensagem
        - Se usuário é admin → Permite acesso à view
    
    Uso:
        @admin_required
        def excluir_cliente(request, pk):
            # Apenas admins podem excluir
            pass
    
    Exemplo:
        @admin_required
        def cadastrar_usuario(request):
            # View acessível apenas por administradores
            return render(request, 'cadastrar_usuario.html')
    
    Nota:
        Este decorator já inclui @login_required, não é necessário
        adicionar ambos.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('notas:login')
        
        # Verificar se é admin usando o método do modelo
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return view_func(request, *args, **kwargs)
        elif hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso negado. Esta área é restrita a administradores.')
            return redirect('notas:dashboard')
    
    return wrapper


def funcionario_required(view_func):
    """
    Decorator que restringe acesso a funcionários e administradores.
    
    Comportamento:
        - Se usuário não autenticado → Redireciona para login
        - Se usuário é admin ou funcionário → Permite acesso
        - Se usuário é cliente → Redireciona para dashboard com mensagem
    
    Uso:
        @funcionario_required
        def listar_romaneios(request):
            # Funcionários e admins podem listar
            pass
    
    Exemplo:
        @funcionario_required
        def criar_romaneio(request):
            # View acessível por funcionários e administradores
            return render(request, 'criar_romaneio.html')
    
    Nota:
        Este decorator já inclui @login_required.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('notas:login')
        
        # Admin e funcionários têm acesso
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return view_func(request, *args, **kwargs)
        elif hasattr(request.user, 'tipo_usuario'):
            if request.user.tipo_usuario in ['admin', 'funcionario']:
                return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Acesso negado. Esta área é restrita a funcionários e administradores.')
        return redirect('notas:dashboard')
    
    return wrapper


def cliente_required(view_func):
    """
    Decorator que requer autenticação (todos os tipos de usuário).
    
    Comportamento:
        - Se usuário não autenticado → Redireciona para login
        - Se usuário autenticado (qualquer tipo) → Permite acesso
    
    Uso:
        @cliente_required
        def minhas_notas(request):
            # Qualquer usuário autenticado pode acessar
            pass
    
    Exemplo:
        @cliente_required
        def dashboard(request):
            # View acessível por todos os usuários autenticados
            return render(request, 'dashboard.html')
    
    Nota:
        Este decorator já inclui @login_required.
        Use quando a view deve ser acessível por qualquer usuário autenticado.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('notas:login')
        
        # Todos os tipos de usuário têm acesso
        if hasattr(request.user, 'tipo_usuario'):
            if request.user.tipo_usuario in ['admin', 'funcionario', 'cliente']:
                return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Acesso negado. Faça login para continuar.')
        return redirect('notas:login')
    
    return wrapper


def can_access_cliente_data(view_func):
    """
    Decorator que verifica acesso a dados de cliente específico.
    
    Regras de Acesso:
        - Administradores: Acesso total (todos os clientes)
        - Funcionários: Acesso total (todos os clientes)
        - Clientes: Apenas seus próprios dados
    
    Comportamento:
        - Verifica autenticação
        - Admin/Funcionário → Permite acesso
        - Cliente → Permite acesso (validação específica deve ser feita na view)
    
    Uso:
        @can_access_cliente_data
        def detalhes_cliente(request, pk):
            cliente = get_object_or_404(Cliente, pk=pk)
            # Verificar se cliente pode acessar (se for tipo cliente)
            if request.user.is_cliente and request.user.cliente != cliente:
                return redirect('notas:dashboard')
            return render(request, 'detalhes_cliente.html', {'cliente': cliente})
    
    Nota:
        Este decorator faz verificação básica. A validação específica
        de acesso a dados do cliente deve ser implementada dentro da view.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('notas:login')
        
        # Admin e funcionários têm acesso total
        if hasattr(request.user, 'is_admin') and request.user.is_admin:
            return view_func(request, *args, **kwargs)
        elif hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario in ['admin', 'funcionario']:
            return view_func(request, *args, **kwargs)
        
        # Clientes só podem acessar seus próprios dados
        # Esta verificação deve ser feita dentro da view também
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# DECORATORS DE RATE LIMITING
# ============================================================================

def rate_limit_critical(view_func):
    """
    Decorator que aplica rate limiting em endpoints críticos.
    
    Configuração:
        - Máximo 10 requisições por minuto por IP
        - Aplica apenas em métodos POST, PUT, DELETE
        - Bloqueia requisições que excedem o limite
    
    Uso:
        @rate_limit_critical
        @login_required
        def criar_romaneio(request):
            # Protegido contra abuso
            pass
    
    Exemplo:
        @rate_limit_critical
        @admin_required
        def excluir_cliente(request, pk):
            # Endpoint crítico protegido
            return redirect('notas:listar_clientes')
    
    Nota:
        Este decorator deve ser usado em endpoints que modificam dados
        (criação, edição, exclusão) para prevenir abuso e ataques.
    """
    @wraps(view_func)
    @ratelimit(key='ip', rate='10/m', method=['POST', 'PUT', 'DELETE'], block=True)
    def wrapper(request, *args, **kwargs):
        # Verificar se foi bloqueado por rate limit
        if getattr(request, 'limited', False):
            messages.error(
                request,
                'Muitas requisições. Aguarde 1 minuto antes de tentar novamente.'
            )
            # Redirecionar para a página anterior ou dashboard
            return redirect(request.META.get('HTTP_REFERER', 'notas:dashboard'))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit_moderate(view_func):
    """
    Decorator que aplica rate limiting moderado em endpoints.
    
    Configuração:
        - Máximo 30 requisições por minuto por IP
        - Aplica apenas em métodos POST
        - Bloqueia requisições que excedem o limite
    
    Uso:
        @rate_limit_moderate
        @login_required
        def buscar_notas(request):
            # Protegido contra abuso moderado
            pass
    
    Nota:
        Use este decorator em endpoints de busca e consulta que podem
        ser abusados mas não são tão críticos quanto criação/edição.
    """
    @wraps(view_func)
    @ratelimit(key='ip', rate='30/m', method='POST', block=True)
    def wrapper(request, *args, **kwargs):
        # Verificar se foi bloqueado por rate limit
        if getattr(request, 'limited', False):
            messages.warning(
                request,
                'Muitas requisições. Aguarde alguns segundos antes de tentar novamente.'
            )
            return redirect(request.META.get('HTTP_REFERER', 'notas:dashboard'))
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

