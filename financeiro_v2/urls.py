"""URLs do Financeiro V2."""
from django.urls import path

from . import views
from notas.views.cobranca_carregamento_views import (
    criar_cobranca_carregamento as cc_criar,
    visualizar_cobranca_carregamento as cc_visualizar,
    editar_cobranca_carregamento as cc_editar,
    baixar_cobranca_carregamento as cc_baixar,
    excluir_cobranca_carregamento as cc_excluir,
    gerar_relatorio_cobranca_carregamento_pdf as cc_pdf,
    gerar_relatorio_consolidado_cobranca_pdf as cc_pdf_consolidado,
    relatorio_cobranca_cliente as cc_relatorio_cliente,
)
from notas.views.cobranca_relatorio_views import (
    cobranca_carregamento as cc_lista,
)

app_name = 'financeiro_v2'

urlpatterns = [
    # Onda 1
    path('', views.painel, name='painel'),
    # Onda 2
    path('caixa/', views.caixa_do_dia, name='caixa_do_dia'),
    path('lancamento/novo/', views.criar_lancamento, name='criar_lancamento'),
    path('despesa/nova/', views.criar_despesa, name='criar_despesa'),
    path('xerox/novo/', views.criar_xerox, name='criar_xerox'),
    # Onda 3
    path('a-receber/', views.a_receber_lista, name='a_receber_lista'),
    path(
        'a-receber/<str:tipo>/<int:pk>/baixar/',
        views.a_receber_baixar,
        name='a_receber_baixar',
    ),
    # Onda 4
    path('a-pagar/', views.a_pagar_lista, name='a_pagar_lista'),
    path('a-pagar/chapa/<int:pk>/', views.a_pagar_chapa, name='a_pagar_chapa'),
    path(
        'a-pagar/chapa/lote/<int:funcionario_pk>/',
        views.a_pagar_chapa_lote,
        name='a_pagar_chapa_lote',
    ),
    path(
        'a-pagar/terceiro/<str:tipo>/<int:pk>/',
        views.a_pagar_terceiro,
        name='a_pagar_terceiro',
    ),
    # Onda 5
    path('doc-avulsa/nova/', views.criar_cte_avulsa, name='criar_cte_avulsa'),
    path('descarga-avulsa/nova/', views.criar_descarga_avulsa, name='criar_descarga_avulsa'),
    path('lancamento/<int:pk>/editar/', views.editar_lancamento, name='editar_lancamento'),
    path('lancamento/<int:pk>/excluir/', views.excluir_lancamento, name='excluir_lancamento'),
    # Onda 6
    path('cliente/<int:pk>/extrato/', views.cliente_extrato, name='cliente_extrato'),
    path('distribuir-gerentes/', views.distribuir_gerentes, name='distribuir_gerentes'),
    path('fundo-gas/', views.fundo_gas, name='fundo_gas'),
    # Onda 7
    path('historico/', views.historico_lancamentos, name='historico_lancamentos'),
    path('dre/', views.dre_periodo, name='dre_periodo'),
    path('inadimplencia/', views.inadimplencia_lista, name='inadimplencia_lista'),
    # Onda 8 - Acerto Diário V2
    path('acerto-diario/', views.acerto_diario_v2_lista, name='acerto_diario_v2_lista'),
    path('acerto-diario/abrir/', views.acerto_diario_v2_abrir, name='acerto_diario_v2_abrir'),
    path(
        'acerto-diario/<int:pk>/',
        views.acerto_diario_v2_detalhe,
        name='acerto_diario_v2_detalhe',
    ),
    path(
        'acerto-diario/<int:pk>/salvar/',
        views.acerto_diario_v2_salvar,
        name='acerto_diario_v2_salvar',
    ),
    path(
        'acerto-diario/<int:pk>/excluir/',
        views.acerto_diario_v2_excluir,
        name='acerto_diario_v2_excluir',
    ),
    path(
        'acerto-diario/<int:pk>/add-carregamento/',
        views.acerto_v2_add_carregamento_cliente,
        name='acerto_v2_add_carregamento',
    ),
    path(
        'acerto-diario/<int:pk>/add-descarga/',
        views.acerto_v2_add_descarga,
        name='acerto_v2_add_descarga',
    ),
    path(
        'acerto-diario/<int:pk>/remove-carregamento/<int:carreg_pk>/',
        views.acerto_v2_remove_carregamento,
        name='acerto_v2_remove_carregamento',
    ),
    path(
        'acerto-diario/<int:pk>/add-distribuicao/',
        views.acerto_v2_add_distribuicao,
        name='acerto_v2_add_distribuicao',
    ),
    path(
        'acerto-diario/<int:pk>/remove-distribuicao/<int:distrib_pk>/',
        views.acerto_v2_remove_distribuicao,
        name='acerto_v2_remove_distribuicao',
    ),
    # Cutover - Cobrança de Carregamento
    # Reusa as views do app `notas` (modelo continua em notas), apenas aproxima o
    # entry-point ao Financeiro V2. As URLs antigas em /notas/... seguem como
    # redirects (ver notas/urls.py) para preservar bookmarks.
    path('cobranca-carregamento/', cc_lista, name='cobranca_carregamento_lista'),
    path('cobranca-carregamento/criar/', cc_criar, name='criar_cobranca_carregamento'),
    path(
        'cobranca-carregamento/relatorio-cliente/',
        cc_relatorio_cliente,
        name='relatorio_cobranca_cliente',
    ),
    path(
        'cobranca-carregamento/relatorio-consolidado/',
        cc_pdf_consolidado,
        name='gerar_relatorio_consolidado_cobranca',
    ),
    path(
        'cobranca-carregamento/<int:cobranca_id>/visualizar/',
        cc_visualizar,
        name='visualizar_cobranca_carregamento',
    ),
    path(
        'cobranca-carregamento/<int:cobranca_id>/editar/',
        cc_editar,
        name='editar_cobranca_carregamento',
    ),
    path(
        'cobranca-carregamento/<int:cobranca_id>/baixar/',
        cc_baixar,
        name='baixar_cobranca_carregamento',
    ),
    path(
        'cobranca-carregamento/<int:cobranca_id>/excluir/',
        cc_excluir,
        name='excluir_cobranca_carregamento',
    ),
    path(
        'cobranca-carregamento/<int:cobranca_id>/gerar-pdf/',
        cc_pdf,
        name='gerar_relatorio_cobranca_carregamento_pdf',
    ),
]
