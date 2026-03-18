"""
Comando Django para criar 3 clientes fictícios com dados realistas de diferentes estados.
Uso: python manage.py criar_clientes_ficticios
"""
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Cria 3 clientes fictícios com dados realistas (SP, RS e MG).'

    def handle(self, *args, **options):
        try:
            from notas.models import Cliente
        except ImportError:
            self.stderr.write(self.style.ERROR('Não foi possível importar o modelo Cliente (notas.models).'))
            return

        clientes = [
            {
                'razao_social': 'TRANSPORTES E LOGÍSTICA PAULISTA LTDA',
                'nome_fantasia': 'Logística Paulista',
                'cnpj': '12.345.678/0001-90',
                'inscricao_estadual': '123.456.789.012',
                'endereco': 'Av. das Nações Unidas',
                'numero': '18001',
                'complemento': 'Sala 2301',
                'bairro': 'Brooklin Paulista',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'cep': '04578-000',
                'telefone': '(11) 3456-7890',
                'email': 'contato@logisticapaulista.com.br',
                'status': 'Ativo',
            },
            {
                'razao_social': 'CARGA SUL TRANSPORTES LTDA',
                'nome_fantasia': 'Carga Sul',
                'cnpj': '98.765.432/0001-10',
                'inscricao_estadual': '987.654.321.098',
                'endereco': 'Av. dos Estados',
                'numero': '1560',
                'complemento': '',
                'bairro': 'Centro',
                'cidade': 'Porto Alegre',
                'estado': 'RS',
                'cep': '90020-001',
                'telefone': '(51) 3228-4500',
                'email': 'contato@cargasul.com.br',
                'status': 'Ativo',
            },
            {
                'razao_social': 'MINAS CARGA E LOGÍSTICA LTDA',
                'nome_fantasia': 'Minas Carga',
                'cnpj': '17.234.567/0001-33',
                'inscricao_estadual': '001.234.567.890',
                'endereco': 'Av. Amazonas',
                'numero': '3050',
                'complemento': 'Bloco A',
                'bairro': 'Centro',
                'cidade': 'Belo Horizonte',
                'estado': 'MG',
                'cep': '30120-000',
                'telefone': '(31) 3245-6789',
                'email': 'contato@minascarga.com.br',
                'status': 'Ativo',
            },
        ]

        criados = 0
        for dados in clientes:
            try:
                obj, created = Cliente.objects.get_or_create(
                    razao_social=dados['razao_social'],
                    defaults=dados,
                )
                if created:
                    criados += 1
                    self.stdout.write(
                        self.style.SUCCESS('Cliente criado: %s (%s)' % (obj.razao_social, obj.estado))
                    )
                else:
                    self.stdout.write('Cliente já existe: %s' % obj.razao_social)
            except IntegrityError as e:
                self.stderr.write(self.style.WARNING('Erro ao criar %s: %s' % (dados['razao_social'], e)))

        if criados:
            self.stdout.write(self.style.SUCCESS('Total: %d cliente(s) criado(s).' % criados))
        else:
            self.stdout.write('Nenhum cliente novo criado (todos já existiam).')
