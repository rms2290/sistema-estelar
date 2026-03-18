"""
Cria 30 notas fiscais para o cliente COMERCIO DE GRAOS NORDESTE S/A com dados fictícios:
valor até 10.000,00, peso até 800 kg, numeração não sequencial.
Uso: python manage.py criar_notas_graos_nordeste
"""
import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from notas.models import Cliente, NotaFiscal

RAZAO_CLIENTE = 'COMERCIO DE GRAOS NORDESTE S/A'

FORNECEDORES = [
    "COOPERATIVA AGRICOLA VALE DO IGUACU S/C",
    "MOINHO SANTA RITA INDUSTRIA E COMERCIO LTDA",
    "CEREALISTA NORDESTE SUL MERCADOS LTDA",
    "ARMACAO E COMERCIO GRANJEIRO DO PARANA",
    "ALIMENTOS BOM GRANEL DISTRIBUIDORA SA",
    "AGROINDUSTRIA PAMPEANA CEREAIS LTDA",
    "COMERCIO DE GRAOS CAMPESTRE EIRELI",
    "ARMAZEM GERAL SERRA GAUCHA LTDA",
    "EXPEDIDORA RURAL CENTRO-OESTE LTDA",
    "SUMINISTROS AGRICOLAS VALE DO TAQUARI LTDA",
]

MERCADORIAS = [
    "SOJA EM GRAOS TIPO 1",
    "MILHO EM GRAOS SECO",
    "TRIGO EM GRAOS CLASSE 2",
    "FARELO DE SOJA 46%",
    "SORGO EM GRAOS",
    "CEVADA EM GRAOS",
    "RESIDUO DE MILHO (DDG)",
    "FARINHA DE TRIGO ESPECIAL",
    "GRAOS DE GIRASSOL",
    "AVEIA EM GRAOS DESCASCADA",
]

LOCAIS = ['1', '2', '3', '4', '5']


class Command(BaseCommand):
    help = (
        'Cria 30 notas fiscais para COMERCIO DE GRAOS NORDESTE S/A com dados fictícios '
        '(valor até 10.000, peso até 800 kg, numeração não sequencial).'
    )

    def handle(self, *args, **options):
        cliente = Cliente.objects.filter(razao_social=RAZAO_CLIENTE).first()
        if not cliente:
            self.stdout.write(
                self.style.ERROR(f'Cliente "{RAZAO_CLIENTE}" não encontrado.')
            )
            return

        # Numeração não sequencial: 30 números distintos em um intervalo (ex: 8200 a 8499)
        base = random.randint(8000, 8500)
        numeros = random.sample(range(base, base + 150), 30)

        hoje = date.today()
        criadas = 0
        for i, numero_nota in enumerate(numeros):
            nota_str = str(numero_nota)
            valor = Decimal(random.randint(100, 10_000_00) / 100)  # até 10.000,00
            peso = Decimal(random.randint(10, 800_00) / 100)        # até 800 kg
            quantidade = Decimal(random.randint(50, 3000_00) / 100)
            data_emissao = hoje - timedelta(days=random.randint(1, 90))
            fornecedor = random.choice(FORNECEDORES)
            mercadoria = random.choice(MERCADORIAS)
            local = random.choice(LOCAIS)

            if NotaFiscal.objects.filter(
                cliente=cliente,
                nota=nota_str,
                mercadoria=mercadoria,
                quantidade=quantidade,
                peso=peso,
            ).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Nota {nota_str} já existe (mesma chave). Pulando.'
                    )
                )
                continue

            NotaFiscal.objects.create(
                cliente=cliente,
                nota=nota_str,
                data=data_emissao,
                fornecedor=fornecedor,
                mercadoria=mercadoria,
                quantidade=quantidade,
                peso=peso,
                valor=valor,
                status='Depósito',
                local=local,
            )
            criadas += 1
            self.stdout.write(
                f'  Nota {nota_str} | {fornecedor[:28]}... | '
                f'R$ {valor:.2f} | {peso:.2f} kg'
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nTotal: {criadas} nota(s) fiscal(is) criada(s).')
        )
