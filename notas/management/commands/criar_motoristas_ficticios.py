"""
Comando Django para criar 4 motoristas fictícios com dados variados e realistas.
Uso: python manage.py criar_motoristas_ficticios
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from notas.models import Motorista

# 4 motoristas com dados completos e variados (CPFs válidos para formato)
MOTORISTAS = [
    {
        'nome': 'CARLOS EDUARDO OLIVEIRA SANTOS',
        'cpf': '11144477735',
        'rg': '12.345.678-9',
        'cnh': '87654321098',
        'codigo_seguranca': 'A1B2C3',
        'vencimento_cnh': date(2027, 3, 15),
        'uf_emissao_cnh': 'PR',
        'telefone': '(41) 99876-5432',
        'endereco': 'RUA DAS PALMEIRAS',
        'numero': '445',
        'complemento': 'CASA',
        'bairro': 'JARDIM SOCIAL',
        'cidade': 'CURITIBA',
        'estado': 'PR',
        'cep': '82520100',
        'data_nascimento': date(1985, 8, 22),
        'tipo_composicao_motorista': 'Carreta',
        'observacoes': 'Experiência em rotas Sul e Sudeste.',
    },
    {
        'nome': 'JOAO PAULO FERREIRA COSTA',
        'cpf': '52998224725',
        'rg': '98.765.432-1',
        'cnh': '11223344556',
        'codigo_seguranca': 'X9Y8Z7',
        'vencimento_cnh': date(2026, 11, 20),
        'uf_emissao_cnh': 'RS',
        'telefone': '(51) 98765-4321',
        'endereco': 'AVENIDA ASSIS BRASIL',
        'numero': '2100',
        'complemento': 'APTO 302',
        'bairro': 'PASSO DAREIA',
        'cidade': 'PORTO ALEGRE',
        'estado': 'RS',
        'cep': '91010000',
        'data_nascimento': date(1979, 2, 14),
        'tipo_composicao_motorista': 'Bitrem',
        'observacoes': 'Habilitação para transporte de grãos e cargas secas.',
    },
    {
        'nome': 'MARCOS ANTONIO RIBEIRO LIMA',
        'cpf': '98765432100',
        'rg': '15.789.456-3',
        'cnh': '55443322110',
        'codigo_seguranca': 'K5L6M7',
        'vencimento_cnh': date(2028, 1, 10),
        'uf_emissao_cnh': 'SC',
        'telefone': '(48) 99123-4567',
        'endereco': 'RUA FELIPE SCHMIDT',
        'numero': '780',
        'complemento': None,
        'bairro': 'CENTRO',
        'cidade': 'FLORIANOPOLIS',
        'estado': 'SC',
        'cep': '88015200',
        'data_nascimento': date(1991, 11, 5),
        'tipo_composicao_motorista': 'Caminhão',
        'observacoes': 'Rotas regionais Santa Catarina e Paraná.',
    },
    {
        'nome': 'ANDRE LUIZ PEREIRA SILVA',
        'cpf': '74823596120',
        'rg': '32.654.987-0',
        'cnh': '99887766554',
        'codigo_seguranca': 'P2Q3R4',
        'vencimento_cnh': date(2026, 7, 8),
        'uf_emissao_cnh': 'SP',
        'telefone': '(11) 97654-3210',
        'endereco': 'RUA VOLUNTARIOS DA PATRIA',
        'numero': '1850',
        'complemento': 'SALA 12',
        'bairro': 'SANTANA',
        'cidade': 'SAO PAULO',
        'estado': 'SP',
        'cep': '02011100',
        'data_nascimento': date(1988, 4, 30),
        'tipo_composicao_motorista': 'Carreta',
        'observacoes': 'Atua em longas distâncias. Categoria E.',
    },
]


class Command(BaseCommand):
    help = 'Cria 4 motoristas fictícios com dados variados e realistas'

    def handle(self, *args, **options):
        criados = 0
        for dados in MOTORISTAS:
            if Motorista.objects.filter(cpf=dados['cpf']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Motorista com CPF {dados["cpf"]} já existe. Pulando.')
                )
                continue
            kwargs = {k: v for k, v in dados.items() if v is not None}
            motorista = Motorista.objects.create(**kwargs)
            criados += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'{motorista.nome} | CPF {motorista.cpf} | {motorista.cidade}/{motorista.estado} | '
                    f'{motorista.get_tipo_composicao_motorista_display()}'
                )
            )
        self.stdout.write(self.style.SUCCESS(f'\nTotal: {criados} motorista(s) criado(s).'))
