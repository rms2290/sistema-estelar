"""
Comando Django para limpar todos os dados do sistema, mantendo apenas usuários.
Uso: python manage.py limpar_dados_sistema --confirmar
"""
from django.core.management.base import BaseCommand
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
    # Tabelas auxiliares
    TabelaSeguro,
)
from financeiro.models import (
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
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
    SetorBancario,
)


class Command(BaseCommand):
    help = 'Limpa todos os dados do sistema, mantendo apenas usuários do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a limpeza (obrigatório para executar)',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.ERROR(
                    '\nATENÇÃO: Esta operação irá REMOVER TODOS os dados do sistema!\n'
                    'Serão mantidos apenas os usuários do sistema.\n\n'
                    'Para confirmar, execute: python manage.py limpar_dados_sistema --confirmar\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('LIMPEZA DE DADOS DO SISTEMA'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('\nIniciando limpeza...\n')

        try:
            with transaction.atomic():
                # Contadores
                contadores = {}
                
                # 1. Limpar Fluxo de Caixa (dependências primeiro)
                self.stdout.write('Limpando Fluxo de Caixa...')
                contadores['MovimentoCaixa'] = MovimentoCaixa.objects.all().delete()[0]
                contadores['PeriodoMovimentoCaixa'] = PeriodoMovimentoCaixa.objects.all().delete()[0]
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
                contadores['SetorBancario'] = SetorBancario.objects.all().delete()[0]
                
                # 2. Limpar Ocorrências
                self.stdout.write('Limpando Ocorrências...')
                contadores['FotoOcorrencia'] = FotoOcorrencia.objects.all().delete()[0]
                contadores['OcorrenciaNotaFiscal'] = OcorrenciaNotaFiscal.objects.all().delete()[0]
                
                # 3. Limpar Fechamentos de Frete
                self.stdout.write('Limpando Fechamentos de Frete...')
                contadores['DetalheItemFechamento'] = DetalheItemFechamento.objects.all().delete()[0]
                contadores['ItemFechamentoFrete'] = ItemFechamentoFrete.objects.all().delete()[0]
                contadores['FechamentoFrete'] = FechamentoFrete.objects.all().delete()[0]
                
                # 4. Limpar Cobranças
                self.stdout.write('Limpando Cobranças...')
                contadores['CobrancaCarregamento'] = CobrancaCarregamento.objects.all().delete()[0]
                
                # 5. Limpar Romaneios
                self.stdout.write('Limpando Romaneios...')
                contadores['RomaneioViagem'] = RomaneioViagem.objects.all().delete()[0]
                
                # 6. Limpar Notas Fiscais
                self.stdout.write('Limpando Notas Fiscais...')
                contadores['NotaFiscal'] = NotaFiscal.objects.all().delete()[0]
                
                # 7. Limpar Histórico e Auditoria
                self.stdout.write('Limpando Histórico e Auditoria...')
                contadores['HistoricoConsulta'] = HistoricoConsulta.objects.all().delete()[0]
                contadores['AuditoriaLog'] = AuditoriaLog.objects.all().delete()[0]
                
                # 8. Limpar Clientes
                self.stdout.write('Limpando Clientes...')
                contadores['Cliente'] = Cliente.objects.all().delete()[0]
                
                # 9. Limpar Veículos e Placas
                self.stdout.write('Limpando Veículos...')
                contadores['PlacaVeiculo'] = PlacaVeiculo.objects.all().delete()[0]
                contadores['Veiculo'] = Veiculo.objects.all().delete()[0]
                contadores['TipoVeiculo'] = TipoVeiculo.objects.all().delete()[0]
                
                # 10. Limpar Motoristas
                self.stdout.write('Limpando Motoristas...')
                contadores['Motorista'] = Motorista.objects.all().delete()[0]
                
                # 11. Limpar Tabela de Seguro
                self.stdout.write('Limpando Tabela de Seguro...')
                contadores['TabelaSeguro'] = TabelaSeguro.objects.all().delete()[0]
                
                self.stdout.write('\n' + '=' * 60)
                self.stdout.write(self.style.SUCCESS('LIMPEZA CONCLUÍDA!'))
                self.stdout.write('=' * 60)
                self.stdout.write('\nResumo de registros removidos:\n')
                
                total = 0
                for modelo, quantidade in sorted(contadores.items()):
                    if quantidade > 0:
                        self.stdout.write(f'  {modelo}: {quantidade} registro(s)')
                        total += quantidade
                
                self.stdout.write(f'\nTotal: {total} registro(s) removido(s)')
                self.stdout.write('\nUsuários do sistema foram mantidos.')
                self.stdout.write('=' * 60 + '\n')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nERRO durante a limpeza: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR('A transação foi revertida. Nenhum dado foi alterado.')
            )
            raise

