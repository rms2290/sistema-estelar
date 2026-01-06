"""
Formulários modulares do sistema Estelar
Este arquivo centraliza todos os imports dos formulários divididos em módulos
"""

# Importar campos e constantes comuns
from .base import UpperCaseCharField, ESTADOS_CHOICES

# Importar formulários de clientes
from .cliente_forms import ClienteForm, ClienteSearchForm

# Importar formulários de notas fiscais
from .nota_fiscal_forms import NotaFiscalForm, NotaFiscalSearchForm, MercadoriaDepositoSearchForm

# Importar formulários de autenticação
from .auth_forms import LoginForm, CadastroUsuarioForm, AlterarSenhaForm

# Importar formulários de motoristas
from .motorista_forms import MotoristaForm, MotoristaSearchForm, HistoricoConsultaForm

# Importar formulários de veículos
from .veiculo_forms import VeiculoForm, VeiculoSearchForm

# Importar formulários de romaneios
from .romaneio_forms import RomaneioViagemForm, RomaneioSearchForm

# Importar formulários administrativos
from .admin_forms import TabelaSeguroForm, AgendaEntregaForm, CobrancaCarregamentoForm

# Importar formulários de fechamento de frete
from .fechamento_frete_forms import FechamentoFreteForm, ItemFechamentoFreteForm

__all__ = [
    # Campos e constantes
    'UpperCaseCharField',
    'ESTADOS_CHOICES',
    # Clientes
    'ClienteForm',
    'ClienteSearchForm',
    # Notas Fiscais
    'NotaFiscalForm',
    'NotaFiscalSearchForm',
    'MercadoriaDepositoSearchForm',
    # Autenticação
    'LoginForm',
    'CadastroUsuarioForm',
    'AlterarSenhaForm',
    # Motoristas
    'MotoristaForm',
    'MotoristaSearchForm',
    'HistoricoConsultaForm',
    # Veículos
    'VeiculoForm',
    'VeiculoSearchForm',
    # Romaneios
    'RomaneioViagemForm',
    'RomaneioSearchForm',
    # Admin
    'TabelaSeguroForm',
    'AgendaEntregaForm',
    'CobrancaCarregamentoForm',
    # Fechamento de Frete
    'FechamentoFreteForm',
    'ItemFechamentoFreteForm',
]

