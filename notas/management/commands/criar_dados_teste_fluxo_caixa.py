"""
Comando para criar dados de teste para o fluxo de caixa.
Limpa os dados existentes e cria um novo período com acertos diários para 5 dias.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from notas.models import Usuario
from financeiro.models import (
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
    AcertoDiarioCarregamento,
    DistribuicaoFuncionario,
    CarregamentoCliente,
    FuncionarioFluxoCaixa,
)


class Command(BaseCommand):
    help = 'Limpa dados de fluxo de caixa e cria dados de teste (período de 5 dias com acertos diários)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-inicio',
            type=str,
            help='Data de início do período (formato: YYYY-MM-DD). Se não informado, usa hoje.',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== LIMPANDO DADOS EXISTENTES ==='))
        
        # 1. Excluir todos os movimentos de caixa
        movimentos_count = MovimentoCaixa.objects.count()
        MovimentoCaixa.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[OK] Excluidos {movimentos_count} movimentos de caixa'))
        
        # 2. Excluir todos os períodos
        periodos_count = PeriodoMovimentoCaixa.objects.count()
        PeriodoMovimentoCaixa.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[OK] Excluidos {periodos_count} periodos'))
        
        # 3. Excluir todas as distribuições de funcionários
        distribuicoes_count = DistribuicaoFuncionario.objects.count()
        DistribuicaoFuncionario.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[OK] Excluidas {distribuicoes_count} distribuicoes de funcionarios'))
        
        # 4. Excluir todos os carregamentos de clientes
        carregamentos_count = CarregamentoCliente.objects.count()
        CarregamentoCliente.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[OK] Excluidos {carregamentos_count} carregamentos de clientes'))
        
        # 5. Excluir todos os acertos diários
        acertos_count = AcertoDiarioCarregamento.objects.count()
        AcertoDiarioCarregamento.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'[OK] Excluidos {acertos_count} acertos diarios'))
        
        self.stdout.write(self.style.SUCCESS('\n=== DADOS LIMPOS ===\n'))
        
        # 6. Verificar se existem funcionários cadastrados
        funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True)
        if funcionarios.count() < 3:
            self.stdout.write(self.style.ERROR('[ERRO] E necessario ter pelo menos 3 funcionarios cadastrados!'))
            self.stdout.write(self.style.ERROR(f'   Funcionarios encontrados: {funcionarios.count()}'))
            return
        
        funcionarios_list = list(funcionarios[:3])
        self.stdout.write(self.style.SUCCESS(f'[OK] Usando {len(funcionarios_list)} funcionarios:'))
        for func in funcionarios_list:
            self.stdout.write(f'   - {func.nome}')
        
        # 7. Obter um usuário admin para criar os registros
        try:
            usuario_admin = Usuario.objects.filter(tipo_usuario='admin', is_active=True).first()
            if not usuario_admin:
                usuario_admin = Usuario.objects.filter(is_staff=True, is_active=True).first()
            if not usuario_admin:
                self.stdout.write(self.style.ERROR('[ERRO] E necessario ter pelo menos um usuario admin ativo!'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERRO] Erro ao buscar usuario admin: {str(e)}'))
            return
        
        # 8. Definir data de início
        if options['data_inicio']:
            try:
                data_inicio = date.fromisoformat(options['data_inicio'])
            except ValueError:
                self.stdout.write(self.style.ERROR(f'[ERRO] Data invalida: {options["data_inicio"]}. Use o formato YYYY-MM-DD'))
                return
        else:
            data_inicio = timezone.now().date()
        
        data_fim = data_inicio + timedelta(days=4)  # 5 dias (incluindo o primeiro)
        
        self.stdout.write(self.style.SUCCESS(f'\n=== CRIANDO PERÍODO DE {data_inicio.strftime("%d/%m/%Y")} A {data_fim.strftime("%d/%m/%Y")} ==='))
        
        # 9. Criar novo período
        periodo = PeriodoMovimentoCaixa.objects.create(
            data_inicio=data_inicio,
            data_fim=None,  # Período aberto
            valor_inicial_caixa=Decimal('1000.00'),
            status='Aberto',
            usuario_criacao=usuario_admin
        )
        self.stdout.write(self.style.SUCCESS(f'[OK] Periodo criado: {periodo}'))
        
        # 10. Criar acertos diários para 5 dias
        valores_por_dia = [
            {'estelar': Decimal('200.00'), 'func1': Decimal('100.00'), 'func2': Decimal('150.00'), 'func3': Decimal('50.00')},
            {'estelar': Decimal('300.00'), 'func1': Decimal('120.00'), 'func2': Decimal('180.00'), 'func3': Decimal('100.00')},
            {'estelar': Decimal('250.00'), 'func1': Decimal('140.00'), 'func2': Decimal('160.00'), 'func3': Decimal('80.00')},
            {'estelar': Decimal('350.00'), 'func1': Decimal('160.00'), 'func2': Decimal('200.00'), 'func3': Decimal('120.00')},
            {'estelar': Decimal('400.00'), 'func1': Decimal('180.00'), 'func2': Decimal('220.00'), 'func3': Decimal('150.00')},
        ]
        
        for i in range(5):
            data_acerto = data_inicio + timedelta(days=i)
            valores = valores_por_dia[i]
            
            # Criar acerto diário
            acerto = AcertoDiarioCarregamento.objects.create(
                data=data_acerto,
                valor_estelar=valores['estelar'],
                usuario_criacao=usuario_admin
            )
            
            # Criar distribuições para os 3 funcionários
            DistribuicaoFuncionario.objects.create(
                acerto_diario=acerto,
                funcionario=funcionarios_list[0],
                valor=valores['func1']
            )
            DistribuicaoFuncionario.objects.create(
                acerto_diario=acerto,
                funcionario=funcionarios_list[1],
                valor=valores['func2']
            )
            DistribuicaoFuncionario.objects.create(
                acerto_diario=acerto,
                funcionario=funcionarios_list[2],
                valor=valores['func3']
            )
            
            # Criar movimentos de caixa para as distribuições
            # Valor Estelar (entrada)
            MovimentoCaixa.objects.create(
                periodo=periodo,
                data=data_acerto,
                tipo='Entrada',
                valor=valores['estelar'],
                descricao=f'Estelar',
                categoria='RecebimentoCliente',
                acerto_diario=acerto,
                usuario_criacao=usuario_admin
            )
            
            # Distribuições para funcionários (entradas - valores acumulados)
            for j, func in enumerate(funcionarios_list):
                valor_func = valores[f'func{j+1}']
                MovimentoCaixa.objects.create(
                    periodo=periodo,
                    data=data_acerto,
                    tipo='AcertoFuncionario',
                    valor=valor_func,
                    descricao=func.nome,
                    funcionario=func,
                    acerto_diario=acerto,
                    usuario_criacao=usuario_admin
                )
            
            self.stdout.write(self.style.SUCCESS(
                f'[OK] Dia {data_acerto.strftime("%d/%m/%Y")}: '
                f'Estelar R$ {valores["estelar"]}, '
                f'Func1 R$ {valores["func1"]}, '
                f'Func2 R$ {valores["func2"]}, '
                f'Func3 R$ {valores["func3"]}'
            ))
        
        # 11. Resumo
        self.stdout.write(self.style.SUCCESS('\n=== RESUMO ==='))
        self.stdout.write(f'Período: {periodo.data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Valor inicial: R$ {periodo.valor_inicial_caixa}')
        self.stdout.write(f'Total de acertos diários: {AcertoDiarioCarregamento.objects.count()}')
        self.stdout.write(f'Total de distribuições: {DistribuicaoFuncionario.objects.count()}')
        self.stdout.write(f'Total de movimentos: {MovimentoCaixa.objects.count()}')
        
        # Calcular totais
        total_estelar = sum(valores['estelar'] for valores in valores_por_dia)
        total_func1 = sum(valores['func1'] for valores in valores_por_dia)
        total_func2 = sum(valores['func2'] for valores in valores_por_dia)
        total_func3 = sum(valores['func3'] for valores in valores_por_dia)
        
        self.stdout.write(self.style.SUCCESS('\n=== TOTAIS ESPERADOS ==='))
        self.stdout.write(f'Total Estelar: R$ {total_estelar}')
        self.stdout.write(f'Total {funcionarios_list[0].nome}: R$ {total_func1}')
        self.stdout.write(f'Total {funcionarios_list[1].nome}: R$ {total_func2}')
        self.stdout.write(f'Total {funcionarios_list[2].nome}: R$ {total_func3}')
        self.stdout.write(f'Total Geral Funcionários: R$ {total_func1 + total_func2 + total_func3}')
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Dados de teste criados com sucesso!'))
        self.stdout.write(self.style.SUCCESS('Acesse a página "Fechamento de Caixa" para verificar os valores acumulados.'))

