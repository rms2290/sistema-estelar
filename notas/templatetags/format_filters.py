from django import template
from django.template.defaultfilters import floatformat
import locale

register = template.Library()

@register.filter
def format_brazilian_currency(value):
    """
    Formata um valor decimal como moeda brasileira (R$ 1.250,00)
    """
    if value is None:
        return ''
    
    try:
        # Configurar locale para português brasileiro
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        # Fallback se o locale não estiver disponível
        pass
    
    try:
        # Converter para float e formatar
        float_value = float(value)
        if float_value == 0:
            return 'R$ 0,00'
        
        # Formatar com separador de milhares e vírgula decimal
        formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return str(value)

@register.filter
def format_brazilian_number(value, decimal_places=0):
    """
    Formata um valor decimal como número brasileiro (1.250,00)
    """
    if value is None:
        return ''
    
    try:
        # Configurar locale para português brasileiro
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        # Fallback se o locale não estiver disponível
        pass
    
    try:
        # Converter para float e formatar
        float_value = float(value)
        if float_value == 0:
            return '0'
        
        # Formatar com separador de milhares e vírgula decimal
        if decimal_places == 0:
            formatted = f"{float_value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            formatted = f"{float_value:,.{decimal_places}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted
    except (ValueError, TypeError):
        return str(value)

@register.filter
def format_brazilian_weight(value):
    """
    Formata um valor de peso como número brasileiro com unidade kg (1.250,00 kg)
    """
    if value is None:
        return ''
    
    formatted_number = format_brazilian_number(value, 0)
    return f"{formatted_number} kg"

@register.filter
def format_brazilian_quantity(value):
    """
    Formata um valor de quantidade como número brasileiro
    """
    return format_brazilian_number(value, 0) 