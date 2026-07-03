"""
Utilitários para telas de pesquisa com filtros.
"""
from typing import Any, Iterable


def tem_filtro_preenchido(cleaned_data: dict, campos: Iterable[str]) -> bool:
    """Retorna True se pelo menos um campo de filtro tiver valor."""
    for campo in campos:
        valor = cleaned_data.get(campo)
        if valor not in (None, ''):
            return True
    return False
