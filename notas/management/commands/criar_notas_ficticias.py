"""
Comando Django para criar 20 notas fiscais por cliente para os 3 clientes fictícios.
Números não sequenciais, dados realistas, valor até R$ 50.000,00 e peso até 600 kg.
Uso: python manage.py criar_notas_ficticias
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone


# Razões sociais dos 3 clientes fictícios
RAZOES_CLIENTES_FICTICIOS = [
    'TRANSPORTES E LOGÍSTICA PAULISTA LTDA',
    'CARGA SUL TRANSPORTES LTDA',
    'MINAS CARGA E LOGÍSTICA LTDA',
]

# Fornecedores realistas (agrícolas/grãos)
FORNECEDORES = [
    'COOPERATIVA AGRÍCOLA ALTO URUGUAI LTDA',
    'CEREALISTA SUL BRASIL S/A',
    'AGRÍCOLA SANTA FÉ LTDA',
    'COOP AGRÍCOLA NOROESTE RS',
    'ARMazénS GERAIS DO ESTADO DE SÃO PAULO',
    'SOJA E MILHO CAMPO GRANDE LTDA',
    'COOPERATIVA TRITÍCOLA DE MINAS GERAIS',
    'GRANJÃO COMÉRCIO DE GRÃOS LTDA',
    'ALIMENTOS BRASIL S/A',
    'CARGILL AGRÍCOLA S/A',
]

# Mercadorias realistas
MERCADORIAS = [
    'SOJA EM GRAOS',
    'MILHO EM GRAOS',
    'TRIGO',
    'FARINHA DE TRIGO',
    'FARELO DE SOJA',
    'ÓLEO DE SOJA',
    'ARROZ EM CASCA',
    'FEIJÃO PRETO',
    'FEIJÃO CARIOCA',
    'SORGO',
    'CEVADA',
    'GIRASSOL',
    'RESÍDUO DE SOJA',
    'MILHO MOÍDO',
    'RAÇÃO SOJA 45%',
]


def gerar_numeros_nao_sequenciais(quantidade, min_val=50000, max_val=999999):
    """Gera quantidade de números únicos não sequenciais no intervalo."""
    pool = set()
    while len(pool) < quantidade:
        pool.add(random.randint(min_val, max_val))
    return list(pool)


class Command(BaseCommand):
    help = 'Cria 20 notas fiscais para cada um dos 3 clientes fictícios (dados realistas, valor até 50.000, peso até 600 kg).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas simula, não grava no banco.',
        )

    def handle(self, *args, **options):
        try:
            from notas.models import Cliente, NotaFiscal
        except ImportError as e:
            self.stderr.write(self.style.ERROR('Não foi possível importar modelos: %s' % e))
            return

        dry_run = options.get('dry_run', False)
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo dry-run: nenhuma nota será gravada.'))

        clientes = list(
            Cliente.objects.filter(razao_social__in=RAZOES_CLIENTES_FICTICIOS).order_by('razao_social')
        )
        if len(clientes) < 3:
            self.stderr.write(
                self.style.ERROR(
                    'Encontrados %d dos 3 clientes fictícios. Execute antes: python manage.py criar_clientes_ficticios'
                    % len(clientes)
                )
            )
            return

        random.seed(42)
        hoje = timezone.now().date()
        total_criadas = 0

        for cliente in clientes:
            numeros_nota = gerar_numeros_nao_sequenciais(20)
            criadas_cliente = 0
            for i in range(20):
                nota_num = str(numeros_nota[i])
                # Datas variadas nos últimos 90 dias
                data = hoje - timedelta(days=random.randint(0, 90))
                fornecedor = random.choice(FORNECEDORES)
                mercadoria = random.choice(MERCADORIAS)
                quantidade = Decimal(str(round(random.uniform(1, 500), 2)))
                peso = Decimal(str(random.randint(1, 600)))
                # Valor até 50.000,00
                valor = Decimal(str(round(random.uniform(100, 50000), 2)))
                local = random.choice([None, '1', '2', '3', '4', '5'])

                if dry_run:
                    self.stdout.write(
                        '  [dry-run] %s | %s | %s | %s kg | R$ %s' % (nota_num, fornecedor[:30], mercadoria, peso, valor)
                    )
                    criadas_cliente += 1
                    continue

                _, created = NotaFiscal.objects.get_or_create(
                    nota=nota_num,
                    cliente=cliente,
                    mercadoria=mercadoria,
                    quantidade=quantidade,
                    peso=peso,
                    defaults={
                        'data': data,
                        'fornecedor': fornecedor,
                        'valor': valor,
                        'status': 'Depósito',
                        'local': local,
                    },
                )
                if created:
                    criadas_cliente += 1

            total_criadas += criadas_cliente
            self.stdout.write(
                self.style.SUCCESS('%s: %d nota(s) criada(s).' % (cliente.razao_social, criadas_cliente))
            )

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: total simulado %d notas.' % total_criadas))
        else:
            self.stdout.write(self.style.SUCCESS('Total: %d nota(s) fiscal(is) criada(s).' % total_criadas))
