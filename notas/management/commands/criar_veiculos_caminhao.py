"""
Comando Django para criar 2 veículos do tipo Caminhão com dados fictícios realistas.
Uso: python manage.py criar_veiculos_caminhao
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from notas.models import Veiculo

CAMINHOES = [
    {
        'tipo_unidade': 'Caminhão',
        'placa': 'ABC4E56',
        'pais': 'Brasil',
        'estado': 'PR',
        'cidade': 'CURITIBA',
        'chassi': '9BM9570XXMB123456',
        'renavam': '11223344556',
        'rntrc': '123456789012',
        'ano_fabricacao': 2021,
        'marca': 'MERCEDES-BENZ',
        'modelo': 'ACTROS 2651',
        'largura': Decimal('2.60'),
        'altura': Decimal('2.90'),
        'comprimento': Decimal('14.00'),
        'cubagem': Decimal('105.56'),
        'capacidade_maxima_kg': Decimal('23000.00'),
        'proprietario_nome_razao_social': 'TRANSPORTES RODOVIA SUL LTDA',
        'proprietario_cpf_cnpj': '12345678000199',
        'proprietario_rg_ie': '9012345678',
        'proprietario_telefone': '(41) 3333-2200',
        'proprietario_endereco': 'RODOVIA BR 116 KM 98',
        'proprietario_numero': 'S/N',
        'proprietario_bairro': 'DISTRITO INDUSTRIAL',
        'proprietario_cidade': 'CAMPO LARGO',
        'proprietario_estado': 'PR',
        'proprietario_cep': '83606300',
    },
    {
        'tipo_unidade': 'Caminhão',
        'placa': 'FGH7I89',
        'pais': 'Brasil',
        'estado': 'RS',
        'cidade': 'NOVO HAMBURGO',
        'chassi': '9BV9530YYNC789012',
        'renavam': '99887766554',
        'rntrc': '987654321098',
        'ano_fabricacao': 2022,
        'marca': 'VOLVO',
        'modelo': 'FH 540',
        'largura': Decimal('2.55'),
        'altura': Decimal('2.85'),
        'comprimento': Decimal('13.60'),
        'cubagem': Decimal('98.78'),
        'capacidade_maxima_kg': Decimal('25000.00'),
        'proprietario_nome_razao_social': 'LOGISTICA CAMPESTRE EIRELI',
        'proprietario_cpf_cnpj': '98765432000111',
        'proprietario_rg_ie': '1122334455',
        'proprietario_telefone': '(51) 3598-7700',
        'proprietario_endereco': 'AV BRASIL LESTE',
        'proprietario_numero': '5500',
        'proprietario_bairro': 'INDUSTRIAL',
        'proprietario_cidade': 'NOVO HAMBURGO',
        'proprietario_estado': 'RS',
        'proprietario_cep': '93534000',
    },
]


class Command(BaseCommand):
    help = 'Cria 2 veículos do tipo Caminhão com dados fictícios realistas'

    def handle(self, *args, **options):
        criados = 0
        for dados in CAMINHOES:
            if Veiculo.objects.filter(placa=dados['placa']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Veículo com placa {dados["placa"]} já existe. Pulando.')
                )
                continue
            Veiculo.objects.create(**dados)
            criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'{dados["placa"]} | {dados["marca"]} {dados["modelo"]} | '
                    f'{dados["ano_fabricacao"]} | {dados["cidade"]}/{dados["estado"]}'
                )
            )
        self.stdout.write(self.style.SUCCESS(f'\nTotal: {criados} veículo(s) criado(s).'))
