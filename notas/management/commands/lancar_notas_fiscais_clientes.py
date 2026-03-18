"""
Comando Django para lançar 10 notas fiscais por cliente (SUL LOG e GRAOS NE) com dados fictícios variados.
Uso: python manage.py lancar_notas_fiscais_clientes
"""
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from notas.models import Cliente, NotaFiscal

# Fornecedores fictícios variados (não genéricos)
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

# Mercadorias variadas
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

# Valores e pesos variados e quebrados (valor até 50.000, peso até 800 kg)
# Cada linha: (valor, peso_kg, quantidade)
DADOS_NUMERICOS = [
    (Decimal("12457.83"), Decimal("342.50"), Decimal("1250.00")),
    (Decimal("28933.17"), Decimal("156.25"), Decimal("580.50")),
    (Decimal("41206.44"), Decimal("723.80"), Decimal("890.25")),
    (Decimal("5678.92"), Decimal("89.30"), Decimal("320.00")),
    (Decimal("35621.05"), Decimal("654.00"), Decimal("1420.75")),
    (Decimal("18744.33"), Decimal("278.60"), Decimal("756.40")),
    (Decimal("43987.61"), Decimal("798.20"), Decimal("1680.00")),
    (Decimal("9234.78"), Decimal("112.45"), Decimal("410.30")),
    (Decimal("27155.19"), Decimal("445.90"), Decimal("935.60")),
    (Decimal("49812.36"), Decimal("791.15"), Decimal("1920.25")),
]


def gerar_datas_ultimos_meses(qtd, dias_atras_max=120):
    """Gera qtd datas variadas nos últimos meses."""
    from random import randint
    hoje = date.today()
    return [hoje - timedelta(days=randint(1, dias_atras_max)) for _ in range(qtd)]


class Command(BaseCommand):
    help = 'Lança 10 notas fiscais para cada um dos clientes SUL LOG e GRAOS NE com dados fictícios variados'

    def handle(self, *args, **options):
        clientes = list(
            Cliente.objects.filter(
                razao_social__in=[
                    'TRANSPORTES E LOGISTICA SUL LTDA',
                    'COMERCIO DE GRAOS NORDESTE S/A',
                ]
            ).order_by('razao_social')
        )
        if len(clientes) != 2:
            self.stdout.write(
                self.style.WARNING('É necessário ter os dois clientes (SUL LOG e GRAOS NE). Execute criar_clientes_pj antes.')
            )
            return

        datas = gerar_datas_ultimos_meses(20)  # 20 datas para as 20 notas

        criadas = 0
        for idx_cliente, cliente in enumerate(clientes):
            prefixo_nota = 5000 + (idx_cliente + 1) * 1000  # 5001-5010 e 6001-6010
            for i in range(10):
                numero_nota = str(prefixo_nota + i + 1)
                valor, peso, quantidade = DADOS_NUMERICOS[i]
                data_emissao = datas[idx_cliente * 10 + i]
                # Evitar duplicata pela constraint: (nota, cliente, mercadoria, quantidade, peso)
                if NotaFiscal.objects.filter(
                    cliente=cliente,
                    nota=numero_nota,
                    mercadoria=MERCADORIAS[i],
                    quantidade=quantidade,
                    peso=peso,
                ).exists():
                    self.stdout.write(
                        self.style.WARNING(f'Nota {numero_nota} já existe para {cliente.nome_fantasia or cliente.razao_social}. Pulando.')
                    )
                    continue
                NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=numero_nota,
                    data=data_emissao,
                    fornecedor=FORNECEDORES[i],
                    mercadoria=MERCADORIAS[i],
                    quantidade=quantidade,
                    peso=peso,
                    valor=valor,
                    status='Depósito',  # só fica Enviada quando vinculada a um romaneio
                    local=str((i % 5) + 1),
                )
                criadas += 1
                self.stdout.write(
                    f'  Nota {numero_nota} | {cliente.nome_fantasia or cliente.razao_social} | '
                    f'{FORNECEDORES[i][:30]}... | R$ {valor} | {peso} kg'
                )

        self.stdout.write(self.style.SUCCESS(f'\nTotal: {criadas} nota(s) fiscal(is) lançada(s).'))
