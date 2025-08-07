from django.core.management.base import BaseCommand
from notas.models import TipoVeiculo


class Command(BaseCommand):
    help = 'Popula os tipos de veículos padrão no sistema'

    def handle(self, *args, **options):
        tipos_veiculos = [
            {
                'nome': 'Carro',
                'descricao': 'Veículo de passeio para transporte de pequenas cargas',
                'ativo': True
            },
            {
                'nome': 'Van',
                'descricao': 'Veículo utilitário para transporte de cargas médias',
                'ativo': True
            },
            {
                'nome': 'Caminhão',
                'descricao': 'Veículo de carga para transporte de grandes volumes',
                'ativo': True
            },
            {
                'nome': 'Cavalo',
                'descricao': 'Caminhão trator para acoplar reboques e semi-reboques',
                'ativo': True
            },
            {
                'nome': 'Reboque',
                'descricao': 'Unidade de carga acoplada ao caminhão trator',
                'ativo': True
            },
            {
                'nome': 'Semi-reboque',
                'descricao': 'Unidade de carga semi-acoplada ao caminhão trator',
                'ativo': True
            }
        ]

        for tipo in tipos_veiculos:
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
            self.style.SUCCESS('Tipos de veículos populados com sucesso!')
        ) 