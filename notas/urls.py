from django.urls import path
from . import views

app_name = 'notas'

urlpatterns = [
# URLs para Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard-cliente/', views.dashboard_cliente, name='dashboard_cliente'),
# URLs para Notas Fiscais
    path('notas/', views.listar_notas_fiscais, name='listar_notas_fiscais'),
    path('adicionar/', views.adicionar_nota_fiscal, name='adicionar_nota_fiscal'),
    path('editar/<int:pk>/', views.editar_nota_fiscal, name='editar_nota_fiscal'),
    path('excluir/<int:pk>/', views.excluir_nota_fiscal, name='excluir_nota_fiscal'),
    path('notas/<int:pk>/detalhes/', views.detalhes_nota_fiscal, name='detalhes_nota_fiscal'),
    path('buscar-mercadorias/', views.buscar_mercadorias_deposito, name='buscar_mercadorias_deposito'),

# Novas URLs para Clientes
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/adicionar/', views.adicionar_cliente, name='adicionar_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:pk>/', views.excluir_cliente, name='excluir_cliente'),
    path('clientes/<int:pk>/detalhes/', views.detalhes_cliente, name='detalhes_cliente'),
    path('clientes/<int:pk>/toggle-status/', views.toggle_status_cliente, name='toggle_status_cliente'),
    path('clientes/<int:pk>/imprimir/', views.imprimir_detalhes_cliente, name='imprimir_detalhes_cliente'),
    path('clientes/imprimir/', views.imprimir_relatorio_clientes, name='imprimir_relatorio_clientes'),

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
    path('romaneios/<int:pk>/imprimir-novo/', views.imprimir_romaneio_novo, name='imprimir_romaneio_novo'),
    path('romaneios/<int:pk>/gerar-pdf/', views.gerar_romaneio_pdf, name='gerar_romaneio_pdf'),

# URL para carregar notas fiscais via AJAX
    path('ajax/load-notas/', views.load_notas_fiscais, name='ajax_load_notas'),
    path('ajax/load-notas-edicao/', views.load_notas_fiscais_edicao, name='ajax_load_notas_edicao'),

# URL para filtrar veículos por composição via AJAX
    path('ajax/filtrar-veiculos/', views.filtrar_veiculos_por_composicao, name='ajax_filtrar_veiculos'),
    
    # URL para obter tipo de veículo via AJAX
    path('api/veiculo/<int:veiculo_id>/tipo/', views.obter_tipo_veiculo, name='obter_tipo_veiculo'),

# URL para validar credenciais de administrador via AJAX
    path('ajax/validar-credenciais-admin/', views.validar_credenciais_admin_ajax, name='ajax_validar_credenciais_admin'),

# Nova URL para pesquisar mercadorias no depósito
    path('mercadorias-deposito/', views.pesquisar_mercadorias_deposito, name='pesquisar_mercadorias_deposito'),
    path('mercadorias-deposito/imprimir/', views.imprimir_relatorio_mercadorias_deposito, name='imprimir_relatorio_mercadorias_deposito'),

# Nova URL para procurar mercadorias no depósito (tela vazia)
    path('procurar-mercadorias-deposito/', views.procurar_mercadorias_deposito, name='procurar_mercadorias_deposito'),

    # URLs de Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
    path('minhas-notas/', views.minhas_notas_fiscais, name='minhas_notas_fiscais'),
    path('minhas-notas/<int:pk>/imprimir/', views.imprimir_nota_fiscal, name='imprimir_nota_fiscal'),
    path('minhas-notas/imprimir-relatorio-deposito/', views.imprimir_relatorio_deposito, name='imprimir_relatorio_deposito'),
    path('meus-romaneios/', views.meus_romaneios, name='meus_romaneios'),
    path('minhas-cobrancas-carregamento/', views.minhas_cobrancas_carregamento, name='minhas_cobrancas_carregamento'),
    path('minhas-cobrancas-carregamento/<int:cobranca_id>/pdf/', views.gerar_relatorio_cobranca_carregamento_pdf_cliente, name='gerar_relatorio_cobranca_carregamento_pdf_cliente'),
    
    # URLs para Gerenciamento de Usuários (apenas administradores)
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/toggle-status/', views.toggle_status_usuario, name='toggle_status_usuario'),
    path('usuarios/excluir/<int:pk>/', views.excluir_usuario, name='excluir_usuario'),
    
    # URLs para Tabela de Seguros
    path('tabela-seguros/', views.listar_tabela_seguros, name='listar_tabela_seguros'),
    path('tabela-seguros/editar/<int:pk>/', views.editar_tabela_seguro, name='editar_tabela_seguro'),
    path('tabela-seguros/atualizar/<int:pk>/ajax/', views.atualizar_tabela_seguro_ajax, name='atualizar_tabela_seguro_ajax'),
    
    # URL para Totalizador por Estado
    path('totalizador-por-estado/', views.totalizador_por_estado, name='totalizador_por_estado'),
    path('totalizador-por-estado/pdf/', views.totalizador_por_estado_pdf, name='totalizador_por_estado_pdf'),
    path('totalizador-por-estado/excel/', views.totalizador_por_estado_excel, name='totalizador_por_estado_excel'),
    
    # URLs para novos relatórios
    path('relatorios/totalizador-por-cliente/', views.totalizador_por_cliente, name='totalizador_por_cliente'),
    path('relatorios/totalizador-por-cliente/pdf/', views.totalizador_por_cliente_pdf, name='totalizador_por_cliente_pdf'),
    path('relatorios/totalizador-por-cliente/excel/', views.totalizador_por_cliente_excel, name='totalizador_por_cliente_excel'),
    path('relatorios/fechamento-frete/', views.fechamento_frete, name='fechamento_frete'),
    path('relatorios/fechamento-frete/criar/', views.criar_fechamento_frete, name='criar_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/editar/', views.editar_fechamento_frete, name='editar_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/imprimir/', views.imprimir_fechamento_frete, name='imprimir_fechamento_frete'),
    path('relatorios/fechamento-frete/<int:pk>/', views.detalhes_fechamento_frete, name='detalhes_fechamento_frete'),
    path('ajax/carregar-dados-romaneios/', views.carregar_dados_romaneios, name='carregar_dados_romaneios'),
    path('ajax/carregar-mais-romaneios/', views.carregar_mais_romaneios, name='carregar_mais_romaneios'),
    path('ajax/buscar-clientes-ativos/', views.buscar_clientes_ativos, name='buscar_clientes_ativos'),
    path('ajax/buscar-romaneios-filtrados/', views.buscar_romaneios_filtrados, name='buscar_romaneios_filtrados'),
    path('relatorios/cobranca-mensal/', views.cobranca_mensal, name='cobranca_mensal'),
    path('relatorios/cobranca-carregamento/', views.cobranca_carregamento, name='cobranca_carregamento'),
    
    # URLs para nova estrutura de cobrança de carregamento
    path('cobranca-carregamento/criar/', views.criar_cobranca_carregamento, name='criar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/editar/', views.editar_cobranca_carregamento, name='editar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/baixar/', views.baixar_cobranca_carregamento, name='baixar_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/excluir/', views.excluir_cobranca_carregamento, name='excluir_cobranca_carregamento'),
    path('cobranca-carregamento/<int:cobranca_id>/gerar-pdf/', views.gerar_relatorio_cobranca_carregamento_pdf, name='gerar_relatorio_cobranca_carregamento_pdf'),
    path('cobranca-carregamento/relatorio-consolidado/', views.gerar_relatorio_consolidado_cobranca_pdf, name='gerar_relatorio_consolidado_cobranca'),
    path('api/romaneios-cliente/<int:cliente_id>/', views.carregar_romaneios_cliente, name='carregar_romaneios_cliente'),
    path('api/notas/<int:nota_id>/ocorrencia/', views.salvar_ocorrencia_nota_fiscal, name='salvar_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/editar/', views.editar_ocorrencia_nota_fiscal, name='editar_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/excluir/', views.excluir_ocorrencia_nota_fiscal, name='excluir_ocorrencia_nota_fiscal'),
    path('api/ocorrencia/<int:ocorrencia_id>/obter/', views.obter_ocorrencia_nota_fiscal, name='obter_ocorrencia_nota_fiscal'),
    
    # URLs para Fluxo de Caixa
    path('fluxo-caixa/', views.dashboard_fluxo_caixa, name='dashboard_fluxo_caixa'),
    path('fluxo-caixa/receitas/criar/', views.criar_receita_empresa, name='criar_receita_empresa'),
    path('fluxo-caixa/receitas/<int:pk>/editar/', views.editar_receita_empresa, name='editar_receita_empresa'),
    path('fluxo-caixa/receitas/<int:pk>/excluir/', views.excluir_receita_empresa, name='excluir_receita_empresa'),
    path('fluxo-caixa/caixa-funcionario/criar/', views.criar_caixa_funcionario, name='criar_caixa_funcionario'),
    path('fluxo-caixa/caixa-funcionario/<int:pk>/acertar/', views.acertar_caixa_funcionario, name='acertar_caixa_funcionario'),
    path('fluxo-caixa/movimento-bancario/criar/', views.criar_movimento_bancario, name='criar_movimento_bancario'),
    path('fluxo-caixa/movimento-bancario/<int:pk>/editar/', views.editar_movimento_bancario, name='editar_movimento_bancario'),
    path('fluxo-caixa/movimento-bancario/<int:pk>/excluir/', views.excluir_movimento_bancario, name='excluir_movimento_bancario'),
    path('fluxo-caixa/controle-saldo/<int:pk>/atualizar/', views.atualizar_controle_saldo, name='atualizar_controle_saldo'),
    path('fluxo-caixa/funcionario/criar-ajax/', views.criar_funcionario_ajax, name='criar_funcionario_ajax'),
    path('fluxo-caixa/movimento-caixa/', views.movimento_caixa, name='movimento_caixa'),
    # URLs para Acerto Diário de Carregamento
    path('fluxo-caixa/acerto-diario/', views.acerto_diario_carregamento, name='acerto_diario_carregamento'),
    path('fluxo-caixa/acerto-diario/listar/', views.listar_acertos_diarios, name='listar_acertos_diarios'),
    path('fluxo-caixa/acerto-diario/salvar/', views.salvar_acerto_diario, name='salvar_acerto_diario'),
    path('fluxo-caixa/acerto-diario/carregamento/adicionar/', views.adicionar_carregamento_cliente_ajax, name='adicionar_carregamento_cliente_ajax'),
    path('fluxo-caixa/acerto-diario/carregamento/<int:pk>/remover/', views.remover_carregamento_cliente_ajax, name='remover_carregamento_cliente_ajax'),
    path('fluxo-caixa/acerto-diario/distribuicao/adicionar/', views.adicionar_distribuicao_funcionario_ajax, name='adicionar_distribuicao_funcionario_ajax'),
    path('fluxo-caixa/acerto-diario/distribuicao/<int:pk>/remover/', views.remover_distribuicao_funcionario_ajax, name='remover_distribuicao_funcionario_ajax'),
    path('fluxo-caixa/acerto-diario/valor-estelar/salvar/', views.salvar_valor_estelar_ajax, name='salvar_valor_estelar_ajax'),
    # URLs para Gerenciamento de Movimento de Caixa
    path('fluxo-caixa/gerenciar-movimento-caixa/', views.gerenciar_movimento_caixa, name='gerenciar_movimento_caixa'),
    path('fluxo-caixa/iniciar-periodo/', views.iniciar_periodo_movimento_caixa, name='iniciar_periodo_movimento_caixa'),
    path('fluxo-caixa/pesquisar-periodo/', views.pesquisar_periodo_movimento_caixa, name='pesquisar_periodo_movimento_caixa'),
    path('fluxo-caixa/periodo/<int:pk>/visualizar/', views.visualizar_periodo_movimento_caixa, name='visualizar_periodo_movimento_caixa'),
    path('api/fluxo-caixa/periodo/<int:pk>/fechar/', views.fechar_periodo_movimento_caixa_ajax, name='fechar_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/editar/', views.editar_periodo_movimento_caixa_ajax, name='editar_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/obter/', views.obter_periodo_movimento_caixa_ajax, name='obter_periodo_movimento_caixa_ajax'),
    path('api/fluxo-caixa/periodo/<int:pk>/excluir/', views.excluir_periodo_movimento_caixa_ajax, name='excluir_periodo_movimento_caixa_ajax'),
    path('fluxo-caixa/movimento-caixa/criar/', views.criar_movimento_caixa_ajax, name='criar_movimento_caixa_ajax'),
    path('fluxo-caixa/movimento-caixa/<int:pk>/editar/', views.editar_movimento_caixa_ajax, name='editar_movimento_caixa_ajax'),
    path('fluxo-caixa/movimento-caixa/<int:pk>/excluir/', views.excluir_movimento_caixa_ajax, name='excluir_movimento_caixa_ajax'),
    path('fluxo-caixa/movimento-caixa/<int:pk>/obter/', views.obter_movimento_caixa_ajax, name='obter_movimento_caixa_ajax'),
    path('fluxo-caixa/funcionario/<int:funcionario_id>/acumulado/', views.obter_acumulado_funcionario_ajax, name='obter_acumulado_funcionario_ajax'),
    
    # URLs para gerenciamento de despesas de carregamento (comentadas - views não implementadas)
    # path('romaneios/<int:romaneio_id>/despesas/', views.gerenciar_despesas_romaneio, name='gerenciar_despesas_romaneio'),
    # path('despesas/<int:despesa_id>/baixar/', views.baixar_despesa, name='baixar_despesa'),
    # path('despesas/<int:despesa_id>/editar/', views.editar_despesa, name='editar_despesa'),
    # path('despesas/<int:despesa_id>/excluir/', views.excluir_despesa, name='excluir_despesa'),
    
    # URLs para Agenda de Entregas
    path('agenda-entregas/', views.listar_agenda_entregas, name='listar_agenda_entregas'),
    path('agenda-entregas/adicionar/', views.adicionar_agenda_entrega, name='adicionar_agenda_entrega'),
    path('agenda-entregas/editar/<int:pk>/', views.editar_agenda_entrega, name='editar_agenda_entrega'),
    path('agenda-entregas/excluir/<int:pk>/', views.excluir_agenda_entrega, name='excluir_agenda_entrega'),
    path('agenda-entregas/<int:pk>/detalhes/', views.detalhes_agenda_entrega, name='detalhes_agenda_entrega'),
    path('agenda-entregas/<int:pk>/alterar-status/', views.alterar_status_agenda, name='alterar_status_agenda'),
    path('agenda-entregas/<int:pk>/em-andamento/', views.marcar_em_andamento, name='marcar_em_andamento'),
    path('agenda-entregas/<int:pk>/concluida/', views.marcar_concluida, name='marcar_concluida'),
    path('agenda-entregas/<int:pk>/entregue/', views.marcar_entregue, name='marcar_entregue'),
    path('agenda-entregas/<int:pk>/cancelada/', views.marcar_cancelada, name='marcar_cancelada'),
    path('widget-agenda-entregas/', views.widget_agenda_entregas, name='widget_agenda_entregas'),
    path('test-widget-agenda/', views.test_widget_agenda, name='test_widget_agenda'),
    
    # URLs para Logs de Auditoria (apenas administradores)
    path('auditoria/logs/', views.listar_logs_auditoria, name='listar_logs_auditoria'),
    path('auditoria/logs/<int:pk>/', views.detalhes_log_auditoria, name='detalhes_log_auditoria'),
    path('auditoria/registros-excluidos/', views.listar_registros_excluidos, name='listar_registros_excluidos'),
    path('auditoria/restaurar/<str:modelo>/<int:pk>/', views.restaurar_registro, name='restaurar_registro'),
    
    path('api/notas-fiscais/<int:cliente_id>/', views.load_notas_fiscais_para_romaneio, name='api_notas_fiscais_para_romaneio'),
]
