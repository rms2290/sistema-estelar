from django.urls import path
from . import views

app_name = 'notas'

urlpatterns = [
# URLs para Dashboard
    path('', views.dashboard, name='dashboard'),
# URLs para Notas Fiscais
    path('notas/', views.listar_notas_fiscais, name='listar_notas_fiscais'),
    path('adicionar/', views.adicionar_nota_fiscal, name='adicionar_nota_fiscal'),
    path('editar/<int:pk>/', views.editar_nota_fiscal, name='editar_nota_fiscal'),
    path('excluir/<int:pk>/', views.excluir_nota_fiscal, name='excluir_nota_fiscal'),
    path('notas/<int:pk>/detalhes/', views.detalhes_nota_fiscal, name='detalhes_nota_fiscal'),

# Novas URLs para Clientes
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/adicionar/', views.adicionar_cliente, name='adicionar_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:pk>/', views.excluir_cliente, name='excluir_cliente'),
    path('clientes/<int:pk>/detalhes/', views.detalhes_cliente, name='detalhes_cliente'),

# Novas URLs para Motoristas
    path('motoristas/', views.listar_motoristas, name='listar_motoristas'),
    path('motoristas/adicionar/', views.adicionar_motorista, name='adicionar_motorista'),
    path('motoristas/editar/<int:pk>/', views.editar_motorista, name='editar_motorista'),
    path('motoristas/excluir/<int:pk>/', views.excluir_motorista, name='excluir_motorista'),
    path('motoristas/<int:pk>/adicionar-consulta/', views.adicionar_historico_consulta, name='adicionar_historico_consulta'),
    path('motoristas/<int:pk>/registrar-consulta/', views.registrar_consulta_motorista, name='registrar_consulta_motorista'),
    path('motoristas/<int:pk>/detalhes/', views.detalhes_motorista, name='detalhes_motorista'),

# Novas URLs para Veículo
    path('veiculos/', views.listar_veiculos, name='listar_veiculos'),
    path('veiculos/adicionar/', views.adicionar_veiculo, name='adicionar_veiculo'),
    path('veiculos/editar/<int:pk>/', views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/excluir/<int:pk>/', views.excluir_veiculo, name='excluir_veiculo'),
    path('veiculos/<int:pk>/detalhes/', views.detalhes_veiculo, name='detalhes_veiculo'),

# Novas URLs para Romaneio
    path('romaneios/', views.listar_romaneios, name='listar_romaneios'),
    path('romaneios/adicionar/', views.adicionar_romaneio, name='adicionar_romaneio'),
    path('romaneios/generico/adicionar/', views.adicionar_romaneio_generico, name='adicionar_romaneio_generico'),
    path('romaneios/editar/<int:pk>/', views.editar_romaneio, name='editar_romaneio'),
    path('romaneios/excluir/<int:pk>/', views.excluir_romaneio, name='excluir_romaneio'),
    path('romaneios/<int:pk>/detalhes/', views.detalhes_romaneio, name='detalhes_romaneio'),
    path('romaneios/<int:pk>/visualizar-impressao/', views.visualizar_romaneio_para_impressao, name='visualizar_romaneio_para_impressao'),
    path('romaneios/<int:pk>/visualizar-paisagem/', views.visualizar_romaneio_paisagem, name='visualizar_romaneio_paisagem'),

# URL para carregar notas fiscais via AJAX
    path('ajax/load-notas/', views.load_notas_fiscais, name='ajax_load_notas'),
    path('ajax/load-notas-edicao/', views.load_notas_fiscais_edicao, name='ajax_load_notas_edicao'),

# Nova URL para pesquisar mercadorias no depósito
    path('mercadorias-deposito/', views.pesquisar_mercadorias_deposito, name='pesquisar_mercadorias_deposito'),

    # URLs de Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
    path('minhas-notas/', views.minhas_notas_fiscais, name='minhas_notas_fiscais'),
    path('minhas-notas/<int:pk>/imprimir/', views.imprimir_nota_fiscal, name='imprimir_nota_fiscal'),
    path('meus-romaneios/', views.meus_romaneios, name='meus_romaneios'),
    
    # URLs para Gerenciamento de Usuários (apenas administradores)
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir/<int:pk>/', views.excluir_usuario, name='excluir_usuario'),
    
    # URLs para Tabela de Seguros
    path('tabela-seguros/', views.listar_tabela_seguros, name='listar_tabela_seguros'),
    path('tabela-seguros/editar/<int:pk>/', views.editar_tabela_seguro, name='editar_tabela_seguro'),
    path('tabela-seguros/atualizar/<int:pk>/ajax/', views.atualizar_tabela_seguro_ajax, name='atualizar_tabela_seguro_ajax'),
    
    # URL para Totalizador por Estado
    path('totalizador-por-estado/', views.totalizador_por_estado, name='totalizador_por_estado'),
    
    # URLs para novos relatórios
    path('relatorios/totalizador-por-cliente/', views.totalizador_por_cliente, name='totalizador_por_cliente'),
    path('relatorios/fechamento-frete/', views.fechamento_frete, name='fechamento_frete'),
    path('relatorios/cobranca-mensal/', views.cobranca_mensal, name='cobranca_mensal'),
    path('relatorios/cobranca-carregamento/', views.cobranca_carregamento, name='cobranca_carregamento'),
    
    path('api/notas-fiscais/<int:cliente_id>/', views.load_notas_fiscais_para_romaneio, name='api_notas_fiscais_para_romaneio'),
]
