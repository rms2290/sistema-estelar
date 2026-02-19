"""
Pacote de views do app Financeiro (fluxo de caixa).

Reexporta todas as views para manter compatibilidade com:
    from financeiro import views  # ou from . import views em urls
"""
from .dashboard_receitas import (
    dashboard_fluxo_caixa,
    criar_receita_empresa,
    editar_receita_empresa,
    excluir_receita_empresa,
    criar_caixa_funcionario,
    acertar_caixa_funcionario,
    criar_movimento_bancario,
    editar_movimento_bancario,
    excluir_movimento_bancario,
    atualizar_controle_saldo,
    criar_funcionario_ajax,
)
from .acerto_diario import (
    listar_acertos_diarios,
    acerto_diario_carregamento,
    salvar_acerto_diario,
    adicionar_carregamento_cliente_ajax,
    remover_carregamento_cliente_ajax,
    adicionar_distribuicao_funcionario_ajax,
    remover_distribuicao_funcionario_ajax,
    salvar_valor_estelar_ajax,
)
from .movimento_caixa import (
    movimento_caixa,
    gerenciar_movimento_caixa,
    criar_movimento_caixa_ajax,
    editar_movimento_caixa_ajax,
    excluir_movimento_caixa_ajax,
    obter_movimento_caixa_ajax,
    obter_acumulado_funcionario_ajax,
)
from .periodo_caixa import (
    iniciar_periodo_movimento_caixa,
    pesquisar_periodo_movimento_caixa,
    visualizar_periodo_movimento_caixa,
    imprimir_periodo_movimento_caixa,
    fechar_periodo_movimento_caixa_ajax,
    editar_periodo_movimento_caixa_ajax,
    obter_periodo_movimento_caixa_ajax,
    excluir_periodo_movimento_caixa_ajax,
)
from .fechamento_caixa import fechamento_caixa

__all__ = [
    'dashboard_fluxo_caixa',
    'criar_receita_empresa',
    'editar_receita_empresa',
    'excluir_receita_empresa',
    'criar_caixa_funcionario',
    'acertar_caixa_funcionario',
    'criar_movimento_bancario',
    'editar_movimento_bancario',
    'excluir_movimento_bancario',
    'atualizar_controle_saldo',
    'criar_funcionario_ajax',
    'listar_acertos_diarios',
    'acerto_diario_carregamento',
    'salvar_acerto_diario',
    'adicionar_carregamento_cliente_ajax',
    'remover_carregamento_cliente_ajax',
    'adicionar_distribuicao_funcionario_ajax',
    'remover_distribuicao_funcionario_ajax',
    'salvar_valor_estelar_ajax',
    'movimento_caixa',
    'gerenciar_movimento_caixa',
    'criar_movimento_caixa_ajax',
    'editar_movimento_caixa_ajax',
    'excluir_movimento_caixa_ajax',
    'obter_movimento_caixa_ajax',
    'obter_acumulado_funcionario_ajax',
    'iniciar_periodo_movimento_caixa',
    'pesquisar_periodo_movimento_caixa',
    'visualizar_periodo_movimento_caixa',
    'imprimir_periodo_movimento_caixa',
    'fechar_periodo_movimento_caixa_ajax',
    'editar_periodo_movimento_caixa_ajax',
    'obter_periodo_movimento_caixa_ajax',
    'excluir_periodo_movimento_caixa_ajax',
    'fechamento_caixa',
]
