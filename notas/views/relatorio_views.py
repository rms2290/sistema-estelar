"""
Views de relatórios (apenas administradores).
Reexporta views dos submódulos para compatibilidade com urls e __init__.
"""
from .totalizador_views import (
    totalizador_por_estado,
    totalizador_por_estado_pdf,
    totalizador_por_estado_excel,
    totalizador_por_cliente,
    totalizador_por_cliente_pdf,
    totalizador_por_cliente_excel,
)
from .fechamento_frete_views import (
    fechamento_frete,
    criar_fechamento_frete,
    editar_fechamento_frete,
    imprimir_fechamento_frete,
    detalhes_fechamento_frete,
)
from .cobranca_relatorio_views import (
    cobranca_mensal,
    cobranca_carregamento,
)

__all__ = [
    'totalizador_por_estado',
    'totalizador_por_estado_pdf',
    'totalizador_por_estado_excel',
    'totalizador_por_cliente',
    'totalizador_por_cliente_pdf',
    'totalizador_por_cliente_excel',
    'fechamento_frete',
    'criar_fechamento_frete',
    'editar_fechamento_frete',
    'imprimir_fechamento_frete',
    'detalhes_fechamento_frete',
    'cobranca_mensal',
    'cobranca_carregamento',
]
