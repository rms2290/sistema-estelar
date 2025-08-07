from django.core.management.base import BaseCommand
from notas.models import TipoVeiculo


class Command(BaseCommand):
    help = 'Popula a tabela TipoVeiculo com os tipos padrão'

    def handle(self, *args, **options):
        tipos_padrao = [
            {
                'nome': 'Carro',
                'descricao': 'Veículo de passeio com até 8 lugares',
                'ativo': True
            },
            {
                'nome': 'Van',
                'descricao': 'Veículo utilitário para transporte de passageiros',
                'ativo': True
            },
            {
                'nome': 'Caminhão',
                'descricao': 'Veículo de carga com capacidade superior a 3.500 kg',
                'ativo': True
            },
            {
                'nome': 'Cavalo',
                'descricao': 'Caminhão trator para reboques',
                'ativo': True
            },
            {
                'nome': 'Reboque',
                'descricao': 'Carreta para transporte de cargas',
                'ativo': True
            },
            {
                'nome': 'Semi-reboque',
                'descricao': 'Carreta semi-reboque para transporte de cargas',
                'ativo': True
            },
        ]

        for tipo in tipos_padrao:
            tipo_obj, created = TipoVeiculo.objects.get_or_create(
                nome=tipo['nome'],
                defaults={
                    'descricao': tipo['descricao'],
                    'ativo': tipo['ativo']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Criado tipo de veículo: {tipo["nome"]}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tipo de veículo já existe: {tipo["nome"]}')
                )

        self.stdout.write(
            self.style.SUCCESS('População de tipos de veículos concluída!')
        ) 