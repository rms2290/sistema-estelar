"""
Comando Django para criar 2 veículos do tipo Cavalo (trator) com dados fictícios realistas.
Cavalo não possui baú – apenas o trator; medidas/cubagem/capacidade ficam em branco.
Uso: python manage.py criar_veiculos_cavalo
"""
from django.core.management.base import BaseCommand
from notas.models import Veiculo

CAVALOS = [
    {
        'tipo_unidade': 'Cavalo',
        'placa': 'JKL0M12',
        'pais': 'Brasil',
        'estado': 'SP',
        'cidade': 'JUNDIAI',
        'chassi': '9BM9570XXMC456789',
        'renavam': '55667788990',
        'rntrc': '456789012345',
        'ano_fabricacao': 2020,
        'marca': 'MERCEDES-BENZ',
        'modelo': 'ACTROS 2651 LS',
        'largura': None,
        'altura': None,
        'comprimento': None,
        'cubagem': None,
        'capacidade_maxima_kg': None,
        'proprietario_nome_razao_social': 'TRANSPORTES CARVALHO E FILHOS LTDA',
        'proprietario_cpf_cnpj': '33445566000177',
        'proprietario_rg_ie': '5678901234',
        'proprietario_telefone': '(11) 4587-3300',
        'proprietario_endereco': 'RODOVIA ANHANGUERA KM 58',
        'proprietario_numero': 'S/N',
        'proprietario_bairro': 'DISTRITO INDUSTRIAL',
        'proprietario_cidade': 'JUNDIAI',
        'proprietario_estado': 'SP',
        'proprietario_cep': '13215000',
    },
    {
        'tipo_unidade': 'Cavalo',
        'placa': 'NOP3Q45',
        'pais': 'Brasil',
        'estado': 'MG',
        'cidade': 'CONTAGEM',
        'chassi': '9BS9540ZZND321098',
        'renavam': '11223344557',
        'rntrc': '654321098765',
        'ano_fabricacao': 2023,
        'marca': 'SCANIA',
        'modelo': 'R 450',
        'largura': None,
        'altura': None,
        'comprimento': None,
        'cubagem': None,
        'capacidade_maxima_kg': None,
        'proprietario_nome_razao_social': 'FRETES MINAS SUL TRANSPORTES LTDA',
        'proprietario_cpf_cnpj': '77889911000288',
        'proprietario_rg_ie': '9876543210',
        'proprietario_telefone': '(31) 3398-4455',
        'proprietario_endereco': 'AVENIDA JOAO CESAR DE OLIVEIRA',
        'proprietario_numero': '3200',
        'proprietario_bairro': 'NOVA CONTAGEM',
        'proprietario_cidade': 'CONTAGEM',
        'proprietario_estado': 'MG',
        'proprietario_cep': '32140320',
    },
]


class Command(BaseCommand):
    help = 'Cria 2 veículos do tipo Cavalo (trator) com dados fictícios realistas'

    def handle(self, *args, **options):
        criados = 0
        for dados in CAVALOS:
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
