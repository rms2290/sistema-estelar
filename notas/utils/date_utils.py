"""
Utilitários de data (parsing ISO e helpers).
"""
from datetime import date, datetime


def parse_date_iso(value):
    """
    Converte string no formato '%Y-%m-%d' em date.
    Retorna None se o valor for vazio, inválido ou não for string.
    """
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
