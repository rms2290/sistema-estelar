"""
Utilitários para formatação de dados
"""
import locale
from decimal import Decimal

def formatar_valor_brasileiro(valor, tipo='numero'):
    """
    Formata um valor decimal como número brasileiro (1.250,00)
    
    Args:
        valor: Valor a ser formatado
        tipo: 'numero' ou 'moeda'
    
    Returns:
        str: Valor formatado
    """
    if valor is None:
        return ''
    
    try:
        # Configurar locale para português brasileiro
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        # Fallback se o locale não estiver disponível
        pass
    
    try:
        # Converter para float e formatar
        float_value = float(valor)
        if float_value == 0:
            return '0' if tipo == 'numero' else 'R$ 0,00'
        
        # Formatar com separador de milhares e vírgula decimal
        if tipo == 'numero':
            formatted = f"{float_value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:  # moeda
            formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            formatted = f"R$ {formatted}"
        
        return formatted
    except (ValueError, TypeError):
        return str(valor)

def formatar_peso_brasileiro(valor):
    """
    Formata um valor de peso como número brasileiro com unidade kg
    
    Args:
        valor: Valor do peso
    
    Returns:
        str: Peso formatado com unidade
    """
    if valor is None:
        return ''
    
    peso_formatado = formatar_valor_brasileiro(valor, 'numero')
    return f"{peso_formatado} kg"

def formatar_cpf(cpf):
    """
    Formata CPF no padrão brasileiro (000.000.000-00)
    
    Args:
        cpf: CPF sem formatação
    
    Returns:
        str: CPF formatado
    """
    if not cpf:
        return ''
    
    # Remove caracteres não numéricos
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    
    if len(cpf_limpo) != 11:
        return cpf
    
    return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"

def formatar_cnpj(cnpj):
    """
    Formata CNPJ no padrão brasileiro (00.000.000/0000-00)
    
    Args:
        cnpj: CNPJ sem formatação
    
    Returns:
        str: CNPJ formatado
    """
    if not cnpj:
        return ''
    
    # Remove caracteres não numéricos
    cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
    
    if len(cnpj_limpo) != 14:
        return cnpj
    
    return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"

def formatar_telefone(telefone):
    """
    Formata telefone no padrão brasileiro
    
    Args:
        telefone: Telefone sem formatação
    
    Returns:
        str: Telefone formatado
    """
    if not telefone:
        return ''
    
    # Remove caracteres não numéricos
    telefone_limpo = ''.join(filter(str.isdigit, str(telefone)))
    
    if len(telefone_limpo) == 11:
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
    elif len(telefone_limpo) == 10:
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
    else:
        return telefone 