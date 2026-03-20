from django.urls import path, include
from django.shortcuts import redirect
from .views import (
    auth_views,
    dashboard_views,
    cliente_views,
    nota_fiscal_views,
    motorista_views,
    veiculo_views,
    romaneio_views,
    admin_views,
    relatorio_views,
    api_views,
    api_fechamento_views,
)
from financeiro import views as financeiro_views

app_name = 'notas'

urlpatterns = [
# URLs para Dashboard
    path('', dashboard_views.dashboard, name='dashboard'),
    path('dashboard-cliente/', dashboard_views.dashboard_cliente, name='dashboard_cliente'),
# URLs para Notas Fiscais
    path('notas/', nota_fiscal_views.listar_notas_fiscais, name='listar_notas_fiscais'),
    path('adicionar/', nota_fiscal_views.adicionar_nota_fiscal, name='adicionar_nota_fiscal'),
    path('editar/<int:pk>/', nota_fiscal_views.editar_nota_fiscal, name='editar_nota_fiscal'),
    path('excluir/<int:pk>/', nota_fiscal_views.excluir_nota_fiscal, name='excluir_nota_fiscal'),
    path('notas/<int:pk>/detalhes/', nota_fiscal_views.detalhes_nota_fiscal, name='detalhes_nota_fiscal'),
    path('buscar-mercadorias/', nota_fiscal_views.buscar_mercadorias_deposito, name='buscar_mercadorias_deposito'),

# Novas URLs para Clientes
    path('clientes/', cliente_views.listar_clientes, name='listar_clientes'),
    path('clientes/adicionar/', cliente_views.adicionar_cliente, name='adicionar_cliente'),
    path('clientes/editar/<int:pk>/', cliente_views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:pk>/', cliente_views.excluir_cliente, name='excluir_cliente'),
    path('clientes/<int:pk>/detalhes/', cliente_views.detalhes_cliente, name='detalhes_cliente'),
    path('clientes/<int:pk>/toggle-status/', cliente_views.toggle_status_cliente, name='toggle_status_cliente'),
    path('clientes/<int:pk>/imprimir/', cliente_views.imprimir_detalhes_cliente, name='imprimir_detalhes_cliente'),
    path('clientes/imprimir/', cliente_views.imprimir_relatorio_clientes, name='imprimir_relatorio_clientes'),

# Novas URLs para Motoristas
    path('motoristas/', motorista_views.listar_motoristas, name='listar_motoristas'),
    path('motoristas/adicionar/', motorista_views.adicionar_motorista, name='adicionar_motorista'),
    path('motoristas/editar/<int:pk>/', motorista_views.editar_motorista, name='editar_motorista'),
    path('motoristas/excluir/<int:pk>/', motorista_views.excluir_motorista, name='excluir_motorista'),
    path('motoristas/<int:pk>/adicionar-consulta/', motorista_views.adicionar_historico_consulta, name='adicionar_historico_consulta'),
    path('motoristas/<int:pk>/registrar-consulta/', motorista_views.registrar_consulta_motorista, name='registrar_consulta_motorista'),
    path('motoristas/<int:pk>/detalhes/', motorista_views.detalhes_motorista, name='detalhes_motorista'),

# Novas URLs para Veículo
    path('veiculos/', veiculo_views.listar_veiculos, name='listar_veiculos'),
    path('veiculos/adicionar/', veiculo_views.adicionar_veiculo, name='adicionar_veiculo'),
    path('veiculos/editar/<int:pk>/', veiculo_views.editar_veiculo, name='editar_veiculo'),
    path('veiculos/excluir/<int:pk>/', veiculo_views.excluir_veiculo, name='excluir_veiculo'),
    path('veiculos/<int:pk>/detalhes/', veiculo_views.detalhes_veiculo, name='detalhes_veiculo'),

# Novas URLs para Romaneio
    path('romaneios/', romaneio_views.listar_romaneios, name='listar_romaneios'),
    path('romaneios/adicionar/', romaneio_views.adicionar_romaneio, name='adicionar_romaneio'),
    path('romaneios/generico/adicionar/', romaneio_views.adicionar_romaneio_generico, name='adicionar_romaneio_generico'),
    path('romaneios/editar/<int:pk>/', romaneio_views.editar_romaneio, name='editar_romaneio'),
    path('romaneios/excluir/<int:pk>/', romaneio_views.excluir_romaneio, name='excluir_romaneio'),
    path('romaneios/<int:pk>/detalhes/', romaneio_views.detalhes_romaneio, name='detalhes_romaneio'),
    path('romaneios/<int:pk>/imprimir-novo/', romaneio_views.imprimir_romaneio_novo, name='imprimir_romaneio_novo'),
    path('romaneios/<int:pk>/gerar-pdf/', romaneio_views.gerar_romaneio_pdf, name='gerar_romaneio_pdf'),

# URL para carregar notas fiscais via AJAX
    path('ajax/load-notas/', api_views.load_notas_fiscais, name='ajax_load_notas'),
    path('ajax/load-notas-edicao/', api_views.load_notas_fiscais_edicao, name='ajax_load_notas_edicao'),

# URL para filtrar veículos por composição via AJAX
    path('ajax/filtrar-veiculos/', api_views.filtrar_veiculos_por_composicao, name='ajax_filtrar_veiculos'),
    
    # URL para obter tipo de veículo via AJAX
    path('api/veiculo/<int:veiculo_id>/tipo/', api_views.obter_tipo_veiculo, name='obter_tipo_veiculo'),

# URL para validar credenciais de administrador via AJAX
    path('ajax/validar-credenciais-admin/', api_views.validar_credenciais_admin_ajax, name='ajax_validar_credenciais_admin'),

# Nova URL para pesquisar mercadorias no depósito
    path('mercadorias-deposito/', nota_fiscal_views.pesquisar_mercadorias_deposito, name='pesquisar_mercadorias_deposito'),
    path('mercadorias-deposito/imprimir/', nota_fiscal_views.imprimir_relatorio_mercadorias_deposito, name='imprimir_relatorio_mercadorias_deposito'),

# Nova URL para procurar mercadorias no depósito (tela vazia)
    path('procurar-mercadorias-deposito/', nota_fiscal_views.procurar_mercadorias_deposito, name='procurar_mercadorias_deposito'),

# Simular Carregamento (Depósito)
    path('simular-carregamento/', nota_fiscal_views.simular_carregamento, name='simular_carregamento'),

    # URLs de Autenticação
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('perfil/', auth_views.perfil_usuario, name='perfil'),
    path('alterar-senha/', auth_views.alterar_senha, name='alterar_senha'),
    path('minhas-notas/', nota_fiscal_views.minhas_notas_fiscais, name='minhas_notas_fiscais'),
    path('minhas-notas/<int:pk>/imprimir/', nota_fiscal_views.imprimir_nota_fiscal, name='imprimir_nota_fiscal'),
    path('minhas-notas/imprimir-relatorio-deposito/', nota_fiscal_views.imprimir_relatorio_deposito, name='imprimir_relatorio_deposito'),
    path('meus-romaneios/', romaneio_views.meus_romaneios, name='meus_romaneios'),
    path('minhas-cobrancas-carregamento/', nota_fiscal_views.minhas_cobrancas_carregamento, name='minhas_cobrancas_carregamento'),
    path('minhas-cobrancas-carregamento/<int:cobranca_id>/pdf/', nota_fiscal_views.gerar_relatorio_cobranca_carregamento_pdf_cliente, name='gerar_relatorio_cobranca_carregamento_pdf_cliente'),
    
    # URLs para Gerenciamento de Usuários (apenas administradores)
    path('usuarios/', admin_views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/cadastrar/', admin_views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/editar/<int:pk>/', admin_views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/toggle-status/', admin_views.toggle_status_usuario, name='toggle_status_usuario'),
    path('usuarios/excluir/<int:pk>/', admin_views.excluir_usuario, name='excluir_usuario'),
    
    # URLs para Tabela de Seguros
    path('tabela-seguros/', admin_views.listar_tabela_seguros, name='listar_tabela_seguros'),
    path('tabela-seguros/editar/<int:pk>/', admin_views.editar_tabela_seguro, name='editar_tabela_seguro'),
    path('tabela-seguros/atualizar/<int:pk>/ajax/', admin_views.atualizar_tabela_seguro_ajax, name='atualizar_tabela_seguro_ajax'),
    path('tabela-seguros/atualizar-em-lote/ajax/', admin_views.atualizar_tabela_seguros_em_lote_ajax, name='atualizar_tabela_seguros_em_lote_ajax'),
    
    # URL para Totalizador por Estado
    path('totalizador-por-estado/', relatorio_views.totalizador_por_estado, name='totalizador_por_estado'),
    path('totalizador-por-estado/pdf/', relatorio_views.totalizador_por_estado_pdf, name='totalizador_por_estado_pdf'),
    path('totalizador-por-estado/excel/', relatorio_views.totalizador_por_estado_excel, name='totalizador_por_estado_excel'),
    
    # URLs para novos relatórios
    path('relatorios/totalizador-por-cliente/', relatorio_views.totalizador_por_cliente, name='totalizador_por_cliente'),
    path('relatorios/totalizador-por-cliente/pdf/', relatorio_views.totalizador_por_cliente_pdf, name='totalizador_por_cliente_pdf'),
    path('relatorios/totalizador-por-cliente/excel/', relatorio_views.totalizador_por_cliente_excel, name='totalizador_por_cliente_excel'),
    path('relatorios/fechamento-frete/', relatorio_views.fechamento_frete, name='fechamento_frete'),
    path('relatorios/fechamento-frete/criar/', relatorio_views.criar_fechamento_frete, name='criar_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/editar/', relatorio_views.editar_fechamento_frete, name='editar_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/imprimir/', relatorio_views.imprimir_fechamento_frete, name='imprimir_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/', relatorio_views.detalhes_fechamento_frete, name='detalhes_fechamento_frete'),
    path('ajax/carregar-dados-romaneios/', api_fechamento_views.carregar_dados_romaneios, name='carregar_dados_romaneios'),
    path('ajax/carregar-mais-romaneios/', api_fechamento_views.carregar_mais_romaneios, name='carregar_mais_romaneios'),
    path('ajax/buscar-clientes-ativos/', api_fechamento_views.buscar_clientes_ativos, name='buscar_clientes_ativos'),
    path('ajax/buscar-romaneios-filtrados/', api_fechamento_views.buscar_romaneios_filtrados, name='buscar_romaneios_filtrados'),
    path('relatorios/cobranca-mensal/', relatorio_views.cobranca_mensal, name='cobranca_mensal'),
    path('relatorios/cobranca-carregamento/', relatorio_views.cobranca_carregamento, name='cobranca_carregamento'),
    path('relatorios/dados-bancarios-setores/', admin_views.listar_setores_bancarios, name='listar_setores_bancarios'),
    path('relatorios/dados-bancarios-setores/<int:pk>/editar/', admin_views.editar_setor_bancario, name='editar_setor_bancario'),
    
    # URLs para nova estrutura de cobrança de carregamento
    path('cobranca-carregamento/criar/', admin_views.criar_cobranca_carregamento, name='criar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/visualizar/', admin_views.visualizar_cobranca_carregamento, name='visualizar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/editar/', admin_views.editar_cobranca_carregamento, name='editar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/baixar/', admin_views.baixar_cobranca_carregamento, name='baixar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/excluir/', admin_views.excluir_cobranca_carregamento, name='excluir_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/gerar-pdf/', admin_views.gerar_relatorio_cobranca_carregamento_pdf, name='gerar_relatorio_cobranca_carregamento_pdf'),
    path('cobranca-carregamento/relatorio-consolidado/', admin_views.gerar_relatorio_consolidado_cobranca_pdf, name='gerar_relatorio_consolidado_cobranca'),
    path('api/romaneios-cliente/<int:cliente_id>/', api_views.carregar_romaneios_cliente, name='carregar_romaneios_cliente'),
    path('api/notas/<int:nota_id>/ocorrencia/', api_views.salvar_ocorrencia_nota_fiscal, name='salvar_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/editar/', api_views.editar_ocorrencia_nota_fiscal, name='editar_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/excluir/', api_views.excluir_ocorrencia_nota_fiscal, name='excluir_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/obter/', api_views.obter_ocorrencia_nota_fiscal, name='obter_ocorrencia_nota_fiscal'),
    
    # API fluxo-caixa: duplicação intencional para compatibilidade com chamadas antigas
    # que usam /notas/api/fluxo-caixa/...; as mesmas views estão em financeiro/urls sob
    # /notas/fluxo-caixa/api/periodo/...
    path('api/fluxo-caixa/periodo/<int:pk>/fechar/', financeiro_views.fechar_periodo_movimento_caixa_ajax, name='fechar_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/editar/', financeiro_views.editar_periodo_movimento_caixa_ajax, name='editar_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/obter/', financeiro_views.obter_periodo_movimento_caixa_ajax, name='obter_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/excluir/', financeiro_views.excluir_periodo_movimento_caixa_ajax, name='excluir_periodo_movimento_caixa_ajax'),

    # URLs para gerenciamento de despesas de carregamento (comentadas - views não implementadas)
    # path('romaneios/<int:romaneio_id>/despesas/', views.gerenciar_despesas_romaneio, name='gerenciar_despesas_romaneio'),
    # path('despesas/<int:despesa_id>/baixar/', views.baixar_despesa, name='baixar_despesa'),
    # path('despesas/<int:despesa_id>/editar/', views.editar_despesa, name='editar_despesa'),
    # path('despesas/<int:despesa_id>/excluir/', views.excluir_despesa, name='excluir_despesa'),
    
    # URLs para Logs de Auditoria (apenas administradores)
    path('auditoria/logs/', admin_views.listar_logs_auditoria, name='listar_logs_auditoria'),
    path('auditoria/logs/<int:pk>/', admin_views.detalhes_log_auditoria, name='detalhes_log_auditoria'),
    path('auditoria/registros-excluidos/', admin_views.listar_registros_excluidos, name='listar_registros_excluidos'),
    path('auditoria/restaurar/<str:modelo>/<int:pk>/', admin_views.restaurar_registro, name='restaurar_registro'),
    
    path('api/notas-fiscais/<int:cliente_id>/', api_views.load_notas_fiscais_para_romaneio, name='api_notas_fiscais_para_romaneio'),
]
