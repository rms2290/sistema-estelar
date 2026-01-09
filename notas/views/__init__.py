"""
Views modulares do sistema Estelar
Este arquivo centraliza todos os imports das views divididas em módulos
"""

# Imports comuns que serão usados em todas as views
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test

# Importação opcional de django_ratelimit
try:
    from django_ratelimit.decorators import ratelimit
    from django_ratelimit.exceptions import Ratelimited
except ImportError:
    # Se django_ratelimit não estiver instalado, criar um decorator dummy
    def ratelimit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    Ratelimited = Exception

# Importar decorators customizados
from ..decorators import admin_required, funcionario_required, cliente_required

# Importar modelos
from ..models import (
    NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem,
    HistoricoConsulta, TabelaSeguro, AgendaEntrega, AuditoriaLog,
    CobrancaCarregamento, Usuario
)

# Importar formulários
from ..forms import (
    NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm,
    RomaneioViagemForm, NotaFiscalSearchForm, ClienteSearchForm,
    MotoristaSearchForm, HistoricoConsultaForm, VeiculoSearchForm,
    RomaneioSearchForm, MercadoriaDepositoSearchForm, TabelaSeguroForm,
    AgendaEntregaForm, CobrancaCarregamentoForm, CadastroUsuarioForm,
    LoginForm, AlterarSenhaForm
)

# Importar utilitários comuns
from .base import (
    formatar_valor_brasileiro,
    formatar_peso_brasileiro,
    get_next_romaneio_codigo,
    get_next_romaneio_generico_codigo,
    is_admin,
    is_funcionario,
    is_cliente,
)

# Importar todas as views dos módulos
from .auth_views import (
    login_view,
    logout_view,
    alterar_senha,
    perfil_usuario,
)

from .cliente_views import (
    listar_clientes,
    adicionar_cliente,
    editar_cliente,
    excluir_cliente,
    detalhes_cliente,
    toggle_status_cliente,
    imprimir_relatorio_clientes,
    imprimir_detalhes_cliente,
)

from .motorista_views import (
    listar_motoristas,
    adicionar_motorista,
    editar_motorista,
    excluir_motorista,
    detalhes_motorista,
    adicionar_historico_consulta,
    registrar_consulta_motorista,
)

from .veiculo_views import (
    listar_veiculos,
    adicionar_veiculo,
    editar_veiculo,
    excluir_veiculo,
    detalhes_veiculo,
)

from .nota_fiscal_views import (
    listar_notas_fiscais,
    adicionar_nota_fiscal,
    editar_nota_fiscal,
    excluir_nota_fiscal,
    detalhes_nota_fiscal,
    buscar_mercadorias_deposito,
    pesquisar_mercadorias_deposito,
    procurar_mercadorias_deposito,
    imprimir_relatorio_mercadorias_deposito,
    minhas_notas_fiscais,
    imprimir_nota_fiscal,
    imprimir_relatorio_deposito,
    minhas_cobrancas_carregamento,
    gerar_relatorio_cobranca_carregamento_pdf_cliente,
)

from .romaneio_views import (
    listar_romaneios,
    adicionar_romaneio,
    adicionar_romaneio_generico,
    editar_romaneio,
    excluir_romaneio,
    detalhes_romaneio,
    imprimir_romaneio_novo,
    gerar_romaneio_pdf,
    meus_romaneios,
)

from .dashboard_views import (
    dashboard,
    dashboard_cliente,
    dashboard_funcionario,
)

from .admin_views import (
    cadastrar_usuario,
    listar_usuarios,
    editar_usuario,
    toggle_status_usuario,
    excluir_usuario,
    listar_tabela_seguros,
    editar_tabela_seguro,
    atualizar_tabela_seguro_ajax,
    listar_agenda_entregas,
    adicionar_agenda_entrega,
    editar_agenda_entrega,
    excluir_agenda_entrega,
    detalhes_agenda_entrega,
    alterar_status_agenda,
    marcar_em_andamento,
    marcar_concluida,
    marcar_entregue,
    marcar_cancelada,
    widget_agenda_entregas,
    test_widget_agenda,
    criar_cobranca_carregamento,
    editar_cobranca_carregamento,
    excluir_cobranca_carregamento,
    baixar_cobranca_carregamento,
    gerar_relatorio_cobranca_carregamento_pdf,
    gerar_relatorio_consolidado_cobranca_pdf,
    listar_logs_auditoria,
    detalhes_log_auditoria,
    listar_registros_excluidos,
    restaurar_registro,
    listar_setores_bancarios,
    editar_setor_bancario,
)

from .relatorio_views import (
    totalizador_por_estado,
    totalizador_por_estado_pdf,
    totalizador_por_estado_excel,
    totalizador_por_cliente,
    totalizador_por_cliente_pdf,
    totalizador_por_cliente_excel,
    fechamento_frete,
    criar_fechamento_frete,
    editar_fechamento_frete,
    imprimir_fechamento_frete,
    detalhes_fechamento_frete,
    cobranca_mensal,
    cobranca_carregamento,
)

from .api_views import (
    load_notas_fiscais,
    load_notas_fiscais_edicao,
    load_notas_fiscais_para_romaneio,
    validar_credenciais_admin_ajax,
    filtrar_veiculos_por_composicao,
    carregar_romaneios_cliente,
    salvar_ocorrencia_nota_fiscal,
    editar_ocorrencia_nota_fiscal,
    excluir_ocorrencia_nota_fiscal,
    obter_ocorrencia_nota_fiscal,
    obter_tipo_veiculo,
)

from .api_fechamento_views import (
    carregar_dados_romaneios,
    carregar_mais_romaneios,
    buscar_clientes_ativos,
    buscar_romaneios_filtrados,
)

from .fluxo_caixa_views import (
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
    acerto_diario_carregamento,
    listar_acertos_diarios,
    salvar_acerto_diario,
    adicionar_carregamento_cliente_ajax,
    remover_carregamento_cliente_ajax,
    adicionar_distribuicao_funcionario_ajax,
    remover_distribuicao_funcionario_ajax,
    salvar_valor_estelar_ajax,
    gerenciar_movimento_caixa,
    criar_movimento_caixa_ajax,
    editar_movimento_caixa_ajax,
    excluir_movimento_caixa_ajax,
    obter_movimento_caixa_ajax,
    obter_acumulado_funcionario_ajax,
    iniciar_periodo_movimento_caixa,
    pesquisar_periodo_movimento_caixa,
    fechar_periodo_movimento_caixa_ajax,
    editar_periodo_movimento_caixa_ajax,
    obter_periodo_movimento_caixa_ajax,
    excluir_periodo_movimento_caixa_ajax,
    pesquisar_periodo_movimento_caixa,
    visualizar_periodo_movimento_caixa,
    imprimir_periodo_movimento_caixa,
    fechamento_caixa,
)

# Manter compatibilidade com código antigo
__all__ = [
    # Auth
    'login_view', 'logout_view', 'alterar_senha', 'perfil_usuario',
    # Cliente
    'listar_clientes', 'adicionar_cliente', 'editar_cliente',
    'excluir_cliente', 'detalhes_cliente', 'toggle_status_cliente',
    'imprimir_relatorio_clientes', 'imprimir_detalhes_cliente',
    # Motorista
    'listar_motoristas', 'adicionar_motorista', 'editar_motorista',
    'excluir_motorista', 'detalhes_motorista', 'adicionar_historico_consulta',
    'registrar_consulta_motorista',
    # Veículo
    'listar_veiculos', 'adicionar_veiculo', 'editar_veiculo',
    'excluir_veiculo', 'detalhes_veiculo',
    # Nota Fiscal
    'listar_notas_fiscais', 'adicionar_nota_fiscal', 'editar_nota_fiscal',
    'excluir_nota_fiscal', 'detalhes_nota_fiscal', 'buscar_mercadorias_deposito',
    'pesquisar_mercadorias_deposito', 'procurar_mercadorias_deposito',
    'imprimir_relatorio_mercadorias_deposito', 'minhas_notas_fiscais',
    'imprimir_nota_fiscal', 'imprimir_relatorio_deposito', 'minhas_cobrancas_carregamento',
    'gerar_relatorio_cobranca_carregamento_pdf_cliente',
    # Romaneio
    'listar_romaneios', 'adicionar_romaneio', 'adicionar_romaneio_generico',
    'editar_romaneio', 'excluir_romaneio', 'detalhes_romaneio',
    'imprimir_romaneio_novo', 'gerar_romaneio_pdf', 'meus_romaneios',
    # Dashboard
    'dashboard', 'dashboard_cliente', 'dashboard_funcionario',
    # Admin
    'cadastrar_usuario', 'listar_usuarios', 'editar_usuario', 'toggle_status_usuario', 'excluir_usuario',
    'listar_tabela_seguros', 'editar_tabela_seguro', 'atualizar_tabela_seguro_ajax',
    'listar_agenda_entregas', 'adicionar_agenda_entrega', 'editar_agenda_entrega',
    'excluir_agenda_entrega', 'detalhes_agenda_entrega', 'alterar_status_agenda',
    'marcar_em_andamento', 'marcar_concluida', 'marcar_entregue', 'marcar_cancelada',
    'widget_agenda_entregas', 'test_widget_agenda',
    'criar_cobranca_carregamento', 'editar_cobranca_carregamento',
    'excluir_cobranca_carregamento', 'baixar_cobranca_carregamento',
    'gerar_relatorio_cobranca_carregamento_pdf', 'gerar_relatorio_consolidado_cobranca_pdf',
    'listar_logs_auditoria', 'detalhes_log_auditoria',
    'listar_registros_excluidos', 'restaurar_registro',
    # Relatórios
    'totalizador_por_estado', 'totalizador_por_estado_pdf', 'totalizador_por_estado_excel',
    'totalizador_por_cliente', 'totalizador_por_cliente_pdf', 'totalizador_por_cliente_excel',
    'fechamento_frete', 'criar_fechamento_frete', 'editar_fechamento_frete', 'imprimir_fechamento_frete', 'detalhes_fechamento_frete',
    'cobranca_mensal', 'cobranca_carregamento',
    'carregar_dados_romaneios', 'carregar_mais_romaneios',
    'buscar_clientes_ativos', 'buscar_romaneios_filtrados',
    # API/AJAX
    'load_notas_fiscais', 'load_notas_fiscais_edicao', 'load_notas_fiscais_para_romaneio',
    'validar_credenciais_admin_ajax', 'filtrar_veiculos_por_composicao',
    'carregar_romaneios_cliente', 'salvar_ocorrencia_nota_fiscal', 'editar_ocorrencia_nota_fiscal', 'excluir_ocorrencia_nota_fiscal', 'obter_ocorrencia_nota_fiscal', 'obter_tipo_veiculo',
    # Fluxo de Caixa
    'dashboard_fluxo_caixa', 'criar_receita_empresa', 'editar_receita_empresa',
    'excluir_receita_empresa', 'criar_caixa_funcionario', 'acertar_caixa_funcionario',
    'criar_movimento_bancario', 'editar_movimento_bancario', 'excluir_movimento_bancario',
    'atualizar_controle_saldo', 'criar_funcionario_ajax',
    'acerto_diario_carregamento', 'listar_acertos_diarios', 'salvar_acerto_diario',
    'adicionar_carregamento_cliente_ajax', 'remover_carregamento_cliente_ajax',
    'adicionar_distribuicao_funcionario_ajax', 'remover_distribuicao_funcionario_ajax',
    'salvar_valor_estelar_ajax',
    'gerenciar_movimento_caixa', 'criar_movimento_caixa_ajax',
    'editar_movimento_caixa_ajax', 'excluir_movimento_caixa_ajax',
    'obter_movimento_caixa_ajax', 'obter_acumulado_funcionario_ajax',
    'iniciar_periodo_movimento_caixa', 'pesquisar_periodo_movimento_caixa',
    'fechar_periodo_movimento_caixa_ajax', 'editar_periodo_movimento_caixa_ajax',
    'obter_periodo_movimento_caixa_ajax', 'excluir_periodo_movimento_caixa_ajax',
    'visualizar_periodo_movimento_caixa', 'imprimir_periodo_movimento_caixa',
    'fechamento_caixa',
    # Utilitários
    'formatar_valor_brasileiro', 'formatar_peso_brasileiro',
    'get_next_romaneio_codigo', 'get_next_romaneio_generico_codigo',
    'is_admin', 'is_funcionario', 'is_cliente',
]

