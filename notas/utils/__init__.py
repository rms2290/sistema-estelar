"""
Utilitários do sistema Estelar
Este módulo centraliza todas as funções utilitárias organizadas por funcionalidade
"""

# Formatação
from .formatters import (
    formatar_valor_brasileiro,
    formatar_peso_brasileiro,
    formatar_data_brasileira,
    formatar_cnpj,
    formatar_cpf,
    formatar_telefone,
    formatar_cep,
)

# Validação
from .validators import (
    validar_cnpj,
    validar_cpf,
    validar_placa,
    validar_telefone,
    validar_cep,
    validar_email,
)

# Constantes
from .constants import (
    ESTADOS_BRASIL,
    TIPO_COMPOSICAO_MOTORISTA_CHOICES,
    TIPO_UNIDADE_CHOICES,
    STATUS_CLIENTE_CHOICES,
    STATUS_NF_CHOICES,
    STATUS_ROMANEIO_CHOICES,
    STATUS_CONSULTA_CHOICES,
    TIPO_USUARIO_CHOICES,
    MARCAS_VEICULOS,
    PAISES_MERCOSUL,
    ITENS_POR_PAGINA,
    TAMANHO_MAX_UPLOAD,
    TIPOS_PERMITIDOS_UPLOAD,
    MENSAGENS_ERRO,
    FORMATOS_DATA,
    FORMATOS_MOEDA,
)

# Auditoria
from .auditoria import (
    registrar_criacao,
    registrar_edicao,
    registrar_exclusao,
    restaurar_registro,
)

# Validação de exclusão
from .validacao_exclusao import (
    validar_exclusao_com_senha_admin,
)

# Relatórios
from .relatorios import (
    gerar_relatorio_pdf_cobranca_carregamento,
    gerar_resposta_pdf,
)
# Importar função de relatório consolidado de cobranças
try:
    from .relatorios import gerar_relatorio_pdf_consolidado_cobranca
    # Alias para compatibilidade
    gerar_relatorio_consolidado_pdf_cobrancas = gerar_relatorio_pdf_consolidado_cobranca
except ImportError:
    gerar_relatorio_pdf_consolidado_cobranca = None
    gerar_relatorio_consolidado_pdf_cobrancas = None

__all__ = [
    # Formatação
    'formatar_valor_brasileiro',
    'formatar_peso_brasileiro',
    'formatar_data_brasileira',
    'formatar_cnpj',
    'formatar_cpf',
    'formatar_telefone',
    'formatar_cep',
    # Validação
    'validar_cnpj',
    'validar_cpf',
    'validar_placa',
    'validar_telefone',
    'validar_cep',
    'validar_email',
    # Constantes
    'ESTADOS_BRASIL',
    'TIPO_COMPOSICAO_MOTORISTA_CHOICES',
    'TIPO_UNIDADE_CHOICES',
    'STATUS_CLIENTE_CHOICES',
    'STATUS_NF_CHOICES',
    'STATUS_ROMANEIO_CHOICES',
    'STATUS_CONSULTA_CHOICES',
    'TIPO_USUARIO_CHOICES',
    'MARCAS_VEICULOS',
    'PAISES_MERCOSUL',
    'ITENS_POR_PAGINA',
    'TAMANHO_MAX_UPLOAD',
    'TIPOS_PERMITIDOS_UPLOAD',
    'MENSAGENS_ERRO',
    'FORMATOS_DATA',
    'FORMATOS_MOEDA',
    # Auditoria
    'registrar_criacao',
    'registrar_edicao',
    'registrar_exclusao',
    'restaurar_registro',
    # Validação de exclusão
    'validar_exclusao_com_senha_admin',
    # Relatórios
    'gerar_relatorio_pdf_cobranca_carregamento',
    'gerar_resposta_pdf',
]

# Adicionar função consolidada se existir
try:
    if 'gerar_relatorio_pdf_consolidado_cobranca' in globals() and gerar_relatorio_pdf_consolidado_cobranca:
        __all__.append('gerar_relatorio_pdf_consolidado_cobranca')
    if 'gerar_relatorio_consolidado_pdf_cobrancas' in globals() and gerar_relatorio_consolidado_pdf_cobrancas:
        __all__.append('gerar_relatorio_consolidado_pdf_cobrancas')
except NameError:
    pass 