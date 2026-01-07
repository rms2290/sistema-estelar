"""
Script para limpar todos os dados do sistema, mantendo apenas usuários do sistema.
ATENÇÃO: Esta operação é IRREVERSÍVEL!
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from django.db import transaction
from notas.models import (
    # Dados principais
    Cliente,
    NotaFiscal,
    Motorista,
    Veiculo,
    RomaneioViagem,
    PlacaVeiculo,
    TipoVeiculo,
    
    # Relatórios e fechamentos
    FechamentoFrete,
    ItemFechamentoFrete,
    DetalheItemFechamento,
    
    # Cobranças
    CobrancaCarregamento,
    
    # Ocorrências
    OcorrenciaNotaFiscal,
    FotoOcorrencia,
    
    # Histórico e auditoria
    HistoricoConsulta,
    AuditoriaLog,
    
    # Fluxo de Caixa
    ReceitaEmpresa,
    FuncionarioFluxoCaixa,
    CaixaFuncionario,
    MovimentoCaixaFuncionario,
    MovimentoBancario,
    ControleSaldoSemanal,
    AcertoDiarioCarregamento,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    AcumuladoFuncionario,
    
    # Tabelas auxiliares
    TabelaSeguro,
)

def limpar_dados_sistema():
    """Limpa todos os dados do sistema, mantendo apenas usuários"""
    
    print("=" * 60)
    print("LIMPEZA DE DADOS DO SISTEMA")
    print("=" * 60)
    print("\nATENÇÃO: Esta operação irá REMOVER TODOS os dados do sistema!")
    print("Serão mantidos apenas os usuários do sistema.\n")
    
    resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if resposta != 'SIM':
        print("\nOperação cancelada.")
        return
    
    print("\nIniciando limpeza...\n")
    
    try:
        with transaction.atomic():
            # Contadores
            contadores = {}
            
            # 1. Limpar Fluxo de Caixa (dependências primeiro)
            print("Limpando Fluxo de Caixa...")
            contadores['AcumuladoFuncionario'] = AcumuladoFuncionario.objects.all().delete()[0]
            contadores['DistribuicaoFuncionario'] = DistribuicaoFuncionario.objects.all().delete()[0]
            contadores['CarregamentoCliente'] = CarregamentoCliente.objects.all().delete()[0]
            contadores['AcertoDiarioCarregamento'] = AcertoDiarioCarregamento.objects.all().delete()[0]
            contadores['MovimentoCaixaFuncionario'] = MovimentoCaixaFuncionario.objects.all().delete()[0]
            contadores['CaixaFuncionario'] = CaixaFuncionario.objects.all().delete()[0]
            contadores['MovimentoBancario'] = MovimentoBancario.objects.all().delete()[0]
            contadores['ControleSaldoSemanal'] = ControleSaldoSemanal.objects.all().delete()[0]
            contadores['ReceitaEmpresa'] = ReceitaEmpresa.objects.all().delete()[0]
            contadores['FuncionarioFluxoCaixa'] = FuncionarioFluxoCaixa.objects.all().delete()[0]
            
            # 2. Limpar Ocorrências
            print("Limpando Ocorrências...")
            contadores['FotoOcorrencia'] = FotoOcorrencia.objects.all().delete()[0]
            contadores['OcorrenciaNotaFiscal'] = OcorrenciaNotaFiscal.objects.all().delete()[0]
            
            # 3. Limpar Fechamentos de Frete
            print("Limpando Fechamentos de Frete...")
            contadores['DetalheItemFechamento'] = DetalheItemFechamento.objects.all().delete()[0]
            contadores['ItemFechamentoFrete'] = ItemFechamentoFrete.objects.all().delete()[0]
            contadores['FechamentoFrete'] = FechamentoFrete.objects.all().delete()[0]
            
            # 4. Limpar Cobranças
            print("Limpando Cobranças...")
            contadores['CobrancaCarregamento'] = CobrancaCarregamento.objects.all().delete()[0]
            
            # 5. Limpar Romaneios
            print("Limpando Romaneios...")
            contadores['RomaneioViagem'] = RomaneioViagem.objects.all().delete()[0]
            
            # 6. Limpar Notas Fiscais
            print("Limpando Notas Fiscais...")
            contadores['NotaFiscal'] = NotaFiscal.objects.all().delete()[0]
            
            # 7. Limpar Histórico e Auditoria
            print("Limpando Histórico e Auditoria...")
            contadores['HistoricoConsulta'] = HistoricoConsulta.objects.all().delete()[0]
            contadores['AuditoriaLog'] = AuditoriaLog.objects.all().delete()[0]
            
            # 8. Limpar Clientes
            print("Limpando Clientes...")
            contadores['Cliente'] = Cliente.objects.all().delete()[0]
            
            # 9. Limpar Veículos e Placas
            print("Limpando Veículos...")
            contadores['PlacaVeiculo'] = PlacaVeiculo.objects.all().delete()[0]
            contadores['Veiculo'] = Veiculo.objects.all().delete()[0]
            contadores['TipoVeiculo'] = TipoVeiculo.objects.all().delete()[0]
            
            # 10. Limpar Motoristas
            print("Limpando Motoristas...")
            contadores['Motorista'] = Motorista.objects.all().delete()[0]
            
            # 11. Limpar Tabela de Seguro
            print("Limpando Tabela de Seguro...")
            contadores['TabelaSeguro'] = TabelaSeguro.objects.all().delete()[0]
            
            print("\n" + "=" * 60)
            print("LIMPEZA CONCLUÍDA!")
            print("=" * 60)
            print("\nResumo de registros removidos:\n")
            
            total = 0
            for modelo, quantidade in sorted(contadores.items()):
                if quantidade > 0:
                    print(f"  {modelo}: {quantidade} registro(s)")
                    total += quantidade
            
            print(f"\nTotal: {total} registro(s) removido(s)")
            print("\nUsuários do sistema foram mantidos.")
            print("=" * 60)
            
    except Exception as e:
        print(f"\nERRO durante a limpeza: {str(e)}")
        print("A transação foi revertida. Nenhum dado foi alterado.")
        raise

if __name__ == '__main__':
    limpar_dados_sistema()

