"""
Comando: python manage.py adicionar_notas_clientes_rondonia

Adiciona 10 notas fiscais fictícias para cada cliente de Rondônia (RO).
Valor até R$ 60.000,00 e peso até 500 kg por nota.
"""
import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from notas.models import Cliente, NotaFiscal


FORNECEDORES = [
    "COOPERATIVA AGRÍCOLA DO NORTE",
    "CEREALISTA SUL LTDA",
    "GRÃOS E SEMENTES CENTRO-OESTE",
    "ALIMENTOS BRASIL S/A",
    "AGROINDÚSTRIA RONDONIA",
    "DEPÓSITO DE GRÃOS PORTO VELHO",
    "SUMINISTROS AGRÍCOLAS LTDA",
    "FAZENDA SANTA MARIA",
    "COMERCIAL DE INSUMOS RO",
    "ABASTECEDORA NORTE",
]

MERCADORIAS = [
    "SOJA EM GRAOS",
    "MILHO",
    "ARROZ EM CASCA",
    "FEIJÃO CARIOCA",
    "TRIGO",
    "FARINHA DE TRIGO",
    "FARELO DE SOJA",
    "RAÇÃO BOVINA",
    "SEMENTES DE SOJA",
    "ADUBO NPK",
]


def gerar_nota_unica(existentes):
    """Gera número de nota único (evita conflito com constraint)."""
    while True:
        n = random.randint(100000, 999999)
        cod = f"NF-RO-{n}"
        if cod not in existentes:
            existentes.add(cod)
            return cod


class Command(BaseCommand):
    help = "Adiciona 10 notas fiscais fictícias para cada cliente de Rondônia (valor até 60000, peso até 500 kg)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-inicio",
            type=str,
            default="2026-03-01",
            help="Data inicial para as notas (YYYY-MM-DD). Padrão: 2026-03-01",
        )
        parser.add_argument(
            "--data-fim",
            type=str,
            default="2026-03-05",
            help="Data final para as notas (YYYY-MM-DD). Padrão: 2026-03-05",
        )

    def handle(self, *args, **options):
        try:
            data_inicio = date.fromisoformat(options["data_inicio"])
            data_fim = date.fromisoformat(options["data_fim"])
        except ValueError:
            self.stdout.write(self.style.ERROR("Datas inválidas. Use YYYY-MM-DD."))
            return

        clientes_ro = Cliente.objects.filter(estado="RO").order_by("razao_social")
        if not clientes_ro.exists():
            self.stdout.write(self.style.WARNING("Nenhum cliente de Rondônia encontrado. Execute antes: python manage.py adicionar_clientes_rondonia"))
            return

        notas_criadas = 0
        existentes = set(NotaFiscal.objects.values_list("nota", flat=True))

        for cliente in clientes_ro:
            for i in range(10):
                nota_num = gerar_nota_unica(existentes)
                delta_days = random.randint(0, (data_fim - data_inicio).days) if data_fim != data_inicio else 0
                data_emissao = data_inicio + timedelta(days=delta_days)
                valor = Decimal(str(round(random.uniform(1000, 60000), 2)))
                peso = Decimal(str(round(random.uniform(50, 500), 2)))
                quantidade = Decimal(str(round(random.uniform(10, 200), 2)))

                mercadoria = random.choice(MERCADORIAS)
                fornecedor = random.choice(FORNECEDORES)

                try:
                    NotaFiscal.objects.create(
                        cliente=cliente,
                        nota=nota_num,
                        data=data_emissao,
                        fornecedor=fornecedor,
                        mercadoria=mercadoria,
                        quantidade=quantidade,
                        peso=peso,
                        valor=valor,
                        status="Depósito",
                        local=random.choice(["1", "2", "3", "4", "5"]),
                    )
                    notas_criadas += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Nota {nota_num} (cliente {cliente.razao_social}): {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nTotal: {notas_criadas} nota(s) fiscal(is) criada(s) para clientes de Rondônia."))
