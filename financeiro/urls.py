"""
URLs do app Financeiro (fluxo de caixa).
Incluídas em notas/urls.py sob o prefixo 'fluxo-caixa/', mantendo as mesmas URLs.
"""
from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('', views.dashboard_fluxo_caixa, name='dashboard_fluxo_caixa'),
    path('receitas/criar/', views.criar_receita_empresa, name='criar_receita_empresa'),
    path('receitas/<int:pk>/editar/', views.editar_receita_empresa, name='editar_receita_empresa'),
    path('receitas/<int:pk>/excluir/', views.excluir_receita_empresa, name='excluir_receita_empresa'),
    path('caixa-funcionario/criar/', views.criar_caixa_funcionario, name='criar_caixa_funcionario'),
    path('caixa-funcionario/<int:pk>/acertar/', views.acertar_caixa_funcionario, name='acertar_caixa_funcionario'),
    path('movimento-bancario/criar/', views.criar_movimento_bancario, name='criar_movimento_bancario'),
    path('movimento-bancario/<int:pk>/editar/', views.editar_movimento_bancario, name='editar_movimento_bancario'),
    path('movimento-bancario/<int:pk>/excluir/', views.excluir_movimento_bancario, name='excluir_movimento_bancario'),
    path('controle-saldo/<int:pk>/atualizar/', views.atualizar_controle_saldo, name='atualizar_controle_saldo'),
    path('funcionario/criar-ajax/', views.criar_funcionario_ajax, name='criar_funcionario_ajax'),
    path('movimento-caixa/', lambda request: redirect('financeiro:gerenciar_movimento_caixa'), name='movimento_caixa'),
    path('acerto-diario/', views.acerto_diario_carregamento, name='acerto_diario_carregamento'),
    path('acerto-diario/listar/', views.listar_acertos_diarios, name='listar_acertos_diarios'),
    path('acerto-diario/salvar/', views.salvar_acerto_diario, name='salvar_acerto_diario'),
    path('acerto-diario/carregamento/adicionar/', views.adicionar_carregamento_cliente_ajax, name='adicionar_carregamento_cliente_ajax'),
    path('acerto-diario/carregamento/<int:pk>/remover/', views.remover_carregamento_cliente_ajax, name='remover_carregamento_cliente_ajax'),
    path('acerto-diario/distribuicao/adicionar/', views.adicionar_distribuicao_funcionario_ajax, name='adicionar_distribuicao_funcionario_ajax'),
    path('acerto-diario/distribuicao/<int:pk>/remover/', views.remover_distribuicao_funcionario_ajax, name='remover_distribuicao_funcionario_ajax'),
    path('acerto-diario/valor-estelar/salvar/', views.salvar_valor_estelar_ajax, name='salvar_valor_estelar_ajax'),
    path('gerenciar-movimento-caixa/', views.gerenciar_movimento_caixa, name='gerenciar_movimento_caixa'),
    path('iniciar-periodo/', views.iniciar_periodo_movimento_caixa, name='iniciar_periodo_movimento_caixa'),
    path('pesquisar-periodo/', views.pesquisar_periodo_movimento_caixa, name='pesquisar_periodo_movimento_caixa'),
    path('periodo/<int:pk>/visualizar/', views.visualizar_periodo_movimento_caixa, name='visualizar_periodo_movimento_caixa'),
    path('periodo/<int:pk>/imprimir/', views.imprimir_periodo_movimento_caixa, name='imprimir_periodo_movimento_caixa'),
    path('movimento-caixa/criar/', views.criar_movimento_caixa_ajax, name='criar_movimento_caixa_ajax'),
    path('movimento-caixa/<int:pk>/editar/', views.editar_movimento_caixa_ajax, name='editar_movimento_caixa_ajax'),
    path('movimento-caixa/<int:pk>/excluir/', views.excluir_movimento_caixa_ajax, name='excluir_movimento_caixa_ajax'),
    path('movimento-caixa/<int:pk>/obter/', views.obter_movimento_caixa_ajax, name='obter_movimento_caixa_ajax'),
    path('funcionario/<int:funcionario_id>/acumulado/', views.obter_acumulado_funcionario_ajax, name='obter_acumulado_funcionario_ajax'),
    path('fechamento-caixa/', views.fechamento_caixa, name='fechamento_caixa'),
    # API (chamadas sob fluxo-caixa/ quando incluído em notas/urls)
    path('api/periodo/<int:pk>/fechar/', views.fechar_periodo_movimento_caixa_ajax, name='fechar_periodo_movimento_caixa_ajax'),
    path('api/periodo/<int:pk>/editar/', views.editar_periodo_movimento_caixa_ajax, name='editar_periodo_movimento_caixa_ajax'),
    path('api/periodo/<int:pk>/obter/', views.obter_periodo_movimento_caixa_ajax, name='obter_periodo_movimento_caixa_ajax'),
    path('api/periodo/<int:pk>/excluir/', views.excluir_periodo_movimento_caixa_ajax, name='excluir_periodo_movimento_caixa_ajax'),
]
