"""
Utilitários para validação de exclusão com senha de administrador
"""
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from ..models import Usuario


def verificar_credenciais_admin(username, senha):
    """
    Verifica se o username e senha fornecidos pertencem a um usuário administrador
    
    Args:
        username: Nome de usuário do administrador
        senha: Senha a ser verificada
        
    Returns:
        Usuario: Objeto do usuário admin se as credenciais forem válidas, None caso contrário
    """
    if not username or not senha:
        return None
    
    try:
        # Buscar o usuário pelo username
        admin = Usuario.objects.get(
            username=username,
            tipo_usuario='admin',
            is_active=True
        )
        
        # Verificar se a senha corresponde
        if admin.check_password(senha):
            return admin
    except Usuario.DoesNotExist:
        pass
    
    return None


def validar_exclusao_com_senha_admin(username_admin, senha_admin, usuario_solicitante):
    """
    Valida se a exclusão pode ser realizada verificando as credenciais de administrador
    
    Args:
        username_admin: Nome de usuário do administrador
        senha_admin: Senha do administrador fornecida
        usuario_solicitante: Usuário que está solicitando a exclusão
        
    Returns:
        tuple: (bool, Usuario ou None, str)
            - bool: True se a validação passou, False caso contrário
            - Usuario: Objeto do admin que autorizou (ou None)
            - str: Mensagem de erro (ou None)
    """
    # Se o próprio usuário já é admin, não precisa de credenciais
    if usuario_solicitante.is_admin:
        return True, usuario_solicitante, None
    
    # Verificar se as credenciais foram fornecidas
    if not username_admin:
        return False, None, "Nome de usuário do administrador é obrigatório para excluir registros."
    
    if not senha_admin:
        return False, None, "Senha de administrador é obrigatória para excluir registros."
    
    # Verificar se as credenciais pertencem a um admin
    admin_autorizador = verificar_credenciais_admin(username_admin, senha_admin)
    
    if not admin_autorizador:
        return False, None, "Credenciais de administrador inválidas. Verifique o nome de usuário e senha."
    
    return True, admin_autorizador, None


