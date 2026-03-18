"""
Comando Django para criar dois clientes pessoa jurídica com todos os campos preenchidos.
Uso: python manage.py criar_clientes_pj
"""
from django.core.management.base import BaseCommand
from notas.models import Cliente


class Command(BaseCommand):
    help = 'Cria dois clientes pessoa jurídica com dados completos para testes'

    def handle(self, *args, **options):
        clientes_data = [
            {
                'razao_social': 'TRANSPORTES E LOGISTICA SUL LTDA',
                'cnpj': '11222333000181',
                'nome_fantasia': 'SUL LOG',
                'inscricao_estadual': '123456789012',
                'endereco': 'RUA DAS INDUSTRIAS',
                'numero': '1500',
                'complemento': 'SALA 302',
                'bairro': 'DISTRITO INDUSTRIAL',
                'cidade': 'CURITIBA',
                'estado': 'PR',
                'cep': '81200100',
                'telefone': '(41) 3333-4444',
                'email': 'contato@sullog.com.br',
                'status': 'Ativo',
            },
            {
                'razao_social': 'COMERCIO DE GRAOS NORDESTE S/A',
                'cnpj': '07282557000100',
                'nome_fantasia': 'GRAOS NE',
                'inscricao_estadual': '987654321098',
                'endereco': 'AVENIDA BRASILIA',
                'numero': '5000',
                'complemento': 'GALPAO 2',
                'bairro': 'ZONA FRANCA',
                'cidade': 'RECIFE',
                'estado': 'PE',
                'cep': '51020001',
                'telefone': '(81) 3456-7890',
                'email': 'fiscal@graosne.com.br',
                'status': 'Ativo',
            },
        ]

        for data in clientes_data:
            if Cliente.objects.filter(razao_social=data['razao_social']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Cliente "{data["razao_social"]}" já existe. Pulando.')
                )
                continue
            cliente = Cliente.objects.create(**data)
            self.stdout.write(
                self.style.SUCCESS(f'Cliente criado: {cliente.razao_social} (CNPJ {cliente.cnpj})')
            )

        self.stdout.write(self.style.SUCCESS('\nConcluído.'))
