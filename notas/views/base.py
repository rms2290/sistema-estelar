"""
Funções utilitárias e helpers comuns para todas as views
"""
from decimal import Decimal
from django.db.models import Max
from ..models import TabelaSeguro

# Importar funções de formatação de utils para evitar duplicação
from ..utils.formatters import formatar_valor_brasileiro, formatar_peso_brasileiro

# Funções de geração de código provisório para preview em formulários
# Nota: A geração real do código é feita pelo método gerar_codigo_automatico() do modelo RomaneioViagem
# Estas funções são usadas apenas para mostrar um código provisório no formulário antes de salvar

def get_next_romaneio_codigo():
    """
    Gera código provisório para preview no formulário (formato antigo: ROM-NNN).
    
    Nota: O código real é gerado automaticamente pelo modelo no formato ROM-YYYY-MM-NNNN
    Esta função é usada apenas para preview no formulário.
    """
    from ..models import RomaneioViagem
    prefix = "ROM-"
    last_romaneio = RomaneioViagem.objects.filter(
        codigo__startswith=prefix
    ).exclude(
        codigo__startswith="ROM-100-"
    ).order_by('-codigo').first()

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 2 and parts[0] == 'ROM':
                next_sequence = int(parts[1]) + 1
        except (ValueError, IndexError):
            pass

    return f"ROM-{next_sequence:03d}"


def get_next_romaneio_generico_codigo():
    """
    Gera código provisório para preview no formulário (formato: ROM-100-NNN).
    
    Nota: O código real é gerado automaticamente pelo modelo no formato ROM-YYYY-MM-NNNN
    Esta função é usada apenas para preview no formulário.
    """
    from ..models import RomaneioViagem
    prefix = "ROM-100-"
    last_romaneio = RomaneioViagem.objects.filter(
        codigo__startswith=prefix
    ).order_by('-codigo').first()

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 3 and parts[0] == 'ROM' and parts[1] == '100':
                next_sequence = int(parts[2]) + 1
        except (ValueError, IndexError):
            pass

    return f"ROM-100-{next_sequence:03d}"


def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_authenticated and user.is_admin


def is_funcionario(user):
    """Verifica se o usuário é funcionário (admin ou funcionário)"""
    return user.is_authenticated and (user.is_admin or user.is_funcionario)


def is_cliente(user):
    """Verifica se o usuário é cliente"""
    return user.is_authenticated and user.is_cliente

