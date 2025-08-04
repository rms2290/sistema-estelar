from django.urls import path
from . import views

app_name = 'notas'

urlpatterns = [
    # URLs para Notas Fiscais
    path('', views.listar_notas_fiscais, name='listar_notas_fiscais'),
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
    path('romaneios/editar/<int:pk>/', views.editar_romaneio, name='editar_romaneio'),
    path('romaneios/excluir/<int:pk>/', views.excluir_romaneio, name='excluir_romaneio'),
    path('romaneios/<int:pk>/detalhes/', views.detalhes_romaneio, name='detalhes_romaneio'),
    path('romaneios/<int:pk>/visualizar-impressao/', views.visualizar_romaneio_para_impressao, name='visualizar_romaneio_para_impressao'),

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
    path('meus-romaneios/', views.meus_romaneios, name='meus_romaneios'),
]
