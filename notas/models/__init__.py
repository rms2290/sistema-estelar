"""
Pacote de modelos do Sistema Estelar.

Mantém compatibilidade com imports existentes:
    from notas.models import Cliente, NotaFiscal, Usuario, ...
"""
from .mixins import UpperCaseMixin, UsuarioManager
from .cliente import Cliente
from .usuario import Usuario
from .nota_fiscal import NotaFiscal, OcorrenciaNotaFiscal, FotoOcorrencia
from .veiculo import TipoVeiculo, PlacaVeiculo, Veiculo
from .motorista import Motorista
from .tabela_seguro import TabelaSeguro
from .romaneio import RomaneioViagem
from .auxiliares import (
    HistoricoConsulta,
    AuditoriaLog,
    CobrancaCarregamento,
    CobrancaCTEAvulsa,
    FechamentoFrete,
    ItemFechamentoFrete,
    DetalheItemFechamento,
)

__all__ = [
    'UpperCaseMixin',
    'UsuarioManager',
    'Cliente',
    'Usuario',
    'NotaFiscal',
    'OcorrenciaNotaFiscal',
    'FotoOcorrencia',
    'TipoVeiculo',
    'PlacaVeiculo',
    'Veiculo',
    'Motorista',
    'TabelaSeguro',
    'RomaneioViagem',
    'HistoricoConsulta',
    'AuditoriaLog',
    'CobrancaCarregamento',
    'CobrancaCTEAvulsa',
    'FechamentoFrete',
    'ItemFechamentoFrete',
    'DetalheItemFechamento',
]
