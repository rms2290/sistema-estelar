# Migração de dados: cria 3 clientes fictícios (SP, RS e MG) se não existirem

from django.db import migrations


def criar_clientes_ficticios(apps, schema_editor):
    Cliente = apps.get_model('notas', 'Cliente')
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
    for dados in clientes:
        Cliente.objects.get_or_create(
            razao_social=dados['razao_social'],
            defaults=dados,
        )


def reverter_clientes_ficticios(apps, schema_editor):
    Cliente = apps.get_model('notas', 'Cliente')
    Cliente.objects.filter(
        razao_social__in=[
            'TRANSPORTES E LOGÍSTICA PAULISTA LTDA',
            'CARGA SUL TRANSPORTES LTDA',
            'MINAS CARGA E LOGÍSTICA LTDA',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0063_veiculo_capacidade_maxima_kg'),
    ]

    operations = [
        migrations.RunPython(criar_clientes_ficticios, reverter_clientes_ficticios),
    ]
