"""
Utilitários para validação de dados
"""
import re
from validate_docbr import CPF, CNPJ

def validar_cpf(cpf):
    """
    Valida CPF usando a biblioteca validate_docbr
    
    Args:
        cpf: CPF a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    
    if len(cpf_limpo) != 11:
        return False
    
    return CPF().validate(cpf_limpo)

def validar_cnpj(cnpj):
    """
    Valida CNPJ usando a biblioteca validate_docbr
    
    Args:
        cnpj: CNPJ a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cnpj:
        return False
    
    # Remove caracteres não numéricos
    cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
    
    if len(cnpj_limpo) != 14:
        return False
    
    return CNPJ().validate(cnpj_limpo)

def validar_placa(placa):
    """
    Valida placa de veículo brasileira (Mercosul ou antiga)
    
    Args:
        placa: Placa a ser validada
    
    Returns:
        bool: True se válida, False caso contrário
    """
    if not placa:
        return False
    
    # Remove espaços e converte para maiúsculo
    placa_limpa = placa.replace(' ', '').upper()
    
    # Padrão Mercosul: ABC1D23
    padrao_mercosul = r'^[A-Z]{3}[0-9][A-Z][0-9]{2}$'
    
    # Padrão antigo: ABC1234
    padrao_antigo = r'^[A-Z]{3}[0-9]{4}$'
    
    return bool(re.match(padrao_mercosul, placa_limpa) or re.match(padrao_antigo, placa_limpa))

def validar_telefone(telefone):
    """
    Valida telefone brasileiro
    
    Args:
        telefone: Telefone a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not telefone:
        return False
    
    # Remove caracteres não numéricos
    telefone_limpo = ''.join(filter(str.isdigit, str(telefone)))
    
    # Telefone deve ter 10 ou 11 dígitos
    return len(telefone_limpo) in [10, 11]

def validar_cep(cep):
    """
    Valida CEP brasileiro
    
    Args:
        cep: CEP a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not cep:
        return False
    
    # Remove caracteres não numéricos
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    
    # CEP deve ter 8 dígitos
    return len(cep_limpo) == 8

def validar_chassi(chassi):
    """
    Valida chassi de veículo
    
    Args:
        chassi: Chassi a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not chassi:
        return False
    
    # Remove espaços e converte para maiúsculo
    chassi_limpo = chassi.replace(' ', '').upper()
    
    # Chassi deve ter 17 caracteres alfanuméricos
    if len(chassi_limpo) != 17:
        return False
    
    # Verifica se contém apenas caracteres válidos
    return bool(re.match(r'^[A-Z0-9]{17}$', chassi_limpo))

def validar_renavam(renavam):
    """
    Valida RENAVAM
    
    Args:
        renavam: RENAVAM a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not renavam:
        return False
    
    # Remove caracteres não numéricos
    renavam_limpo = ''.join(filter(str.isdigit, str(renavam)))
    
    # RENAVAM deve ter 11 dígitos
    return len(renavam_limpo) == 11

def validar_email(email):
    """
    Valida formato de email
    
    Args:
        email: Email a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    if not email:
        return False
    
    # Padrão básico de email
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(padrao, email))

def limpar_documento(documento):
    """
    Remove caracteres não numéricos de um documento
    
    Args:
        documento: Documento a ser limpo
    
    Returns:
        str: Documento apenas com números
    """
    if not documento:
        return ''
    
    return ''.join(filter(str.isdigit, str(documento))) 