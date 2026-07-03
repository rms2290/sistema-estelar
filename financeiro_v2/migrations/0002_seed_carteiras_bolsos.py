"""
Data migration: cria os registros iniciais de Carteira e Bolso.

Carteiras: Dinheiro (caixa físico) e Banco (conta corrente / PIX).
Bolsos: Operacional, Estelar, Documentação, Fundo Gás (eh_terceiro=True).

Saldo inicial das carteiras fica em zero. O usuário pode ajustar depois
em Admin → Financeiro V2 → Carteiras.
"""
from decimal import Decimal

from django.db import migrations


CARTEIRAS_INICIAIS = [
    {'codigo': 'DINHEIRO', 'nome': 'Dinheiro (caixa físico)'},
    {'codigo': 'BANCO', 'nome': 'Banco (conta corrente / PIX)'},
]

BOLSOS_INICIAIS = [
    {'codigo': 'OPERACIONAL', 'nome': 'Operacional', 'eh_terceiro': False, 'ordem': 1},
    {'codigo': 'ESTELAR', 'nome': 'Estelar', 'eh_terceiro': False, 'ordem': 2},
    {'codigo': 'DOCUMENTACAO', 'nome': 'Documentação', 'eh_terceiro': False, 'ordem': 3},
    {'codigo': 'FUNDO_GAS', 'nome': 'Fundo Gás (Chapas)', 'eh_terceiro': True, 'ordem': 10},
]


def criar_seeds(apps, schema_editor):
    Carteira = apps.get_model('financeiro_v2', 'Carteira')
    Bolso = apps.get_model('financeiro_v2', 'Bolso')

    for c in CARTEIRAS_INICIAIS:
        Carteira.objects.get_or_create(
            codigo=c['codigo'],
            defaults={'nome': c['nome'], 'saldo_inicial': Decimal('0.00'), 'ativa': True},
        )

    for b in BOLSOS_INICIAIS:
        Bolso.objects.get_or_create(
            codigo=b['codigo'],
            defaults={
                'nome': b['nome'],
                'eh_terceiro': b['eh_terceiro'],
                'ordem': b['ordem'],
                'ativo': True,
            },
        )


def remover_seeds(apps, schema_editor):
    Carteira = apps.get_model('financeiro_v2', 'Carteira')
    Bolso = apps.get_model('financeiro_v2', 'Bolso')
    Carteira.objects.filter(codigo__in=[c['codigo'] for c in CARTEIRAS_INICIAIS]).delete()
    Bolso.objects.filter(codigo__in=[b['codigo'] for b in BOLSOS_INICIAIS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro_v2', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_seeds, reverse_code=remover_seeds),
    ]
