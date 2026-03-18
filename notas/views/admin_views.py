"""
Views administrativas (apenas para administradores).
Reexporta views dos submódulos para compatibilidade com urls e __init__.
"""
from .usuario_views import (
    cadastrar_usuario,
    listar_usuarios,
    editar_usuario,
    toggle_status_usuario,
    excluir_usuario,
)
from .tabela_seguro_views import (
    listar_tabela_seguros,
    editar_tabela_seguro,
    atualizar_tabela_seguro_ajax,
)
from .cobranca_carregamento_views import (
    criar_cobranca_carregamento,
    visualizar_cobranca_carregamento,
    editar_cobranca_carregamento,
    excluir_cobranca_carregamento,
    baixar_cobranca_carregamento,
    gerar_relatorio_cobranca_carregamento_pdf,
    gerar_relatorio_consolidado_cobranca_pdf,
)
from .auditoria_views import (
    listar_logs_auditoria,
    detalhes_log_auditoria,
    listar_registros_excluidos,
    restaurar_registro,
)
from .setor_bancario_views import (
    listar_setores_bancarios,
    editar_setor_bancario,
)

__all__ = [
    'cadastrar_usuario',
    'listar_usuarios',
    'editar_usuario',
    'toggle_status_usuario',
    'excluir_usuario',
    'listar_tabela_seguros',
    'editar_tabela_seguro',
    'atualizar_tabela_seguro_ajax',
    'criar_cobranca_carregamento',
    'visualizar_cobranca_carregamento',
    'editar_cobranca_carregamento',
    'excluir_cobranca_carregamento',
    'baixar_cobranca_carregamento',
    'gerar_relatorio_cobranca_carregamento_pdf',
    'gerar_relatorio_consolidado_cobranca_pdf',
    'listar_logs_auditoria',
    'detalhes_log_auditoria',
    'listar_registros_excluidos',
    'restaurar_registro',
    'listar_setores_bancarios',
    'editar_setor_bancario',
]
