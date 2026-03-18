"""
Comando Django para criar 4 veículos do tipo Reboque com dados fictícios realistas.
Cubagem variando entre 80 e 90 m³.
Uso: python manage.py criar_veiculos_reboque
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from notas.models import Veiculo

# Largura x Altura x Comprimento = cubagem (entre 80 e 90 m³)
REBOQUES = [
    {
        'tipo_unidade': 'Reboque',
        'placa': 'RST6U78',
        'pais': 'Brasil',
        'estado': 'PR',
        'cidade': 'PONTA GROSSA',
        'chassi': '9BR9520AAMF111222',
        'renavam': '22334455661',
        'rntrc': '111222333444',
        'ano_fabricacao': 2019,
        'marca': 'RANDON',
        'modelo': 'CARRETA BAU 3 EIXOS',
        'largura': Decimal('2.60'),
        'altura': Decimal('2.90'),
        'comprimento': Decimal('10.65'),
        'cubagem': Decimal('80.42'),
        'capacidade_maxima_kg': Decimal('25000.00'),
        'proprietario_nome_razao_social': 'TRANSPORTES CAMPOS GERAIS LTDA',
        'proprietario_cpf_cnpj': '44556677000133',
        'proprietario_rg_ie': '1122334455',
        'proprietario_telefone': '(42) 3225-1188',
        'proprietario_endereco': 'RODOVIA BR 376 KM 512',
        'proprietario_numero': 'S/N',
        'proprietario_bairro': 'INDUSTRIAL',
        'proprietario_cidade': 'PONTA GROSSA',
        'proprietario_estado': 'PR',
        'proprietario_cep': '84070180',
    },
    {
        'tipo_unidade': 'Reboque',
        'placa': 'VWX9Y01',
        'pais': 'Brasil',
        'estado': 'RS',
        'cidade': 'CANOAS',
        'chassi': '9BR9520BBMG333444',
        'renavam': '66778899002',
        'rntrc': '555666777888',
        'ano_fabricacao': 2021,
        'marca': 'ROCHA',
        'modelo': 'BAU FRIGORIFICO 3 EIXOS',
        'largura': Decimal('2.55'),
        'altura': Decimal('2.85'),
        'comprimento': Decimal('11.40'),
        'cubagem': Decimal('82.85'),
        'capacidade_maxima_kg': Decimal('23000.00'),
        'proprietario_nome_razao_social': 'FRIGORIFICOS SUL CAMINHOES LTDA',
        'proprietario_cpf_cnpj': '88990011000244',
        'proprietario_rg_ie': '5544332211',
        'proprietario_telefone': '(51) 3476-9922',
        'proprietario_endereco': 'ESTRADA RS 240',
        'proprietario_numero': '8500',
        'proprietario_bairro': 'NOVA SANTA RITA',
        'proprietario_cidade': 'CANOAS',
        'proprietario_estado': 'RS',
        'proprietario_cep': '92025600',
    },
    {
        'tipo_unidade': 'Reboque',
        'placa': 'YZA2B34',
        'pais': 'Brasil',
        'estado': 'SC',
        'cidade': 'BLUMENAU',
        'chassi': '9BR9520CCNH555666',
        'renavam': '99887766550',
        'rntrc': '999888777666',
        'ano_fabricacao': 2022,
        'marca': 'MASCARELLO',
        'modelo': 'BAU SECO MEGA 3 EIXOS',
        'largura': Decimal('2.60'),
        'altura': Decimal('2.95'),
        'comprimento': Decimal('11.30'),
        'cubagem': Decimal('86.52'),
        'capacidade_maxima_kg': Decimal('27000.00'),
        'proprietario_nome_razao_social': 'LOGISTICA VALE DO ITAJAI LTDA',
        'proprietario_cpf_cnpj': '11223344000355',
        'proprietario_rg_ie': '7788990011',
        'proprietario_telefone': '(47) 3334-5566',
        'proprietario_endereco': 'RUA HANS DIETER SCHMIDT',
        'proprietario_numero': '2100',
        'proprietario_bairro': 'VORSTADT',
        'proprietario_cidade': 'BLUMENAU',
        'proprietario_estado': 'SC',
        'proprietario_cep': '89037002',
    },
    {
        'tipo_unidade': 'Reboque',
        'placa': 'CDE5F67',
        'pais': 'Brasil',
        'estado': 'SP',
        'cidade': 'SOROCABA',
        'chassi': '9BR9520DDNI777888',
        'renavam': '33445566778',
        'rntrc': '123456789011',
        'ano_fabricacao': 2023,
        'marca': 'TROLLER',
        'modelo': 'CARRETA BAU GRANEL 3 EIXOS',
        'largura': Decimal('2.58'),
        'altura': Decimal('2.92'),
        'comprimento': Decimal('11.95'),
        'cubagem': Decimal('89.78'),
        'capacidade_maxima_kg': Decimal('28000.00'),
        'proprietario_nome_razao_social': 'TRANSPORTES INTERIOR PAULISTA LTDA',
        'proprietario_cpf_cnpj': '55667788000466',
        'proprietario_rg_ie': '9988776655',
        'proprietario_telefone': '(15) 3232-7788',
        'proprietario_endereco': 'AVENIDA ROBERTO SIMONSEN',
        'proprietario_numero': '1500',
        'proprietario_bairro': 'JARDIM GONCALVES',
        'proprietario_cidade': 'SOROCABA',
        'proprietario_estado': 'SP',
        'proprietario_cep': '18095100',
    },
]


class Command(BaseCommand):
    help = 'Cria 4 veículos do tipo Reboque com dados fictícios e cubagem entre 80 e 90 m³'

    def handle(self, *args, **options):
        criados = 0
        for dados in REBOQUES:
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
                    f'{dados["cubagem"]} m³ | {dados["cidade"]}/{dados["estado"]}'
                )
            )
        self.stdout.write(self.style.SUCCESS(f'\nTotal: {criados} veículo(s) criado(s).'))
