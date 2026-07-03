"""
Montagem de contexto para impressão de romaneios.
"""
from typing import Any, Dict, List

from ..models import RomaneioViagem
from ..services.romaneio_service import RomaneioService
from ..utils.nota_ordering import ordenar_instancias_notas_fiscais

LINHAS_PRIMEIRA_PAGINA = 17
LINHAS_DEMAIS_PAGINAS = 24


def paginar_notas_romaneio(notas_romaneadas) -> List[list]:
    """Divide as notas do romaneio em páginas para o layout de impressão."""
    notas_list = list(notas_romaneadas)
    if not notas_list:
        return [[]]

    primeira = notas_list[:LINHAS_PRIMEIRA_PAGINA]
    restante = notas_list[LINHAS_PRIMEIRA_PAGINA:]
    demais = [
        restante[i:i + LINHAS_DEMAIS_PAGINAS]
        for i in range(0, len(restante), LINHAS_DEMAIS_PAGINAS)
    ]
    paginas_notas = [primeira] + demais

    while len(paginas_notas[0]) < LINHAS_PRIMEIRA_PAGINA:
        paginas_notas[0].append(None)
    for pagina in paginas_notas[1:]:
        while len(pagina) < LINHAS_DEMAIS_PAGINAS:
            pagina.append(None)

    return paginas_notas


def montar_item_impressao_romaneio(romaneio: RomaneioViagem) -> Dict[str, Any]:
    """Monta o contexto de impressão de um romaneio."""
    notas_romaneadas = ordenar_instancias_notas_fiscais(romaneio.notas_fiscais.all())
    totais = RomaneioService.calcular_totais_romaneio(romaneio)
    paginas_notas = paginar_notas_romaneio(notas_romaneadas)

    return {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'paginas_notas': paginas_notas,
        'total_paginas': len(paginas_notas),
        'total_peso': totais['total_peso'],
        'total_valor': totais['total_valor'],
    }
