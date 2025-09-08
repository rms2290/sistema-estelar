from django.core.management.base import BaseCommand
from notas.models import Veiculo, PlacaVeiculo


class Command(BaseCommand):
    help = 'Migra as placas existentes dos veículos para a nova tabela PlacaVeiculo'

    def handle(self, *args, **options):
        # Buscar todos os veículos existentes
        veiculos = Veiculo.objects.all()
        
        self.stdout.write(f'Encontrados {veiculos.count()} veículos para migrar...')
        
        for veiculo in veiculos:
            # Criar registros na nova tabela PlacaVeiculo
            if veiculo.placa:
                placa_obj, created = PlacaVeiculo.objects.get_or_create(
                    placa=veiculo.placa,
                    defaults={
                        'estado': veiculo.estado,
                        'cidade': veiculo.cidade,
                        'pais': veiculo.pais or 'Brasil',
                        'ativa': True,
                        'observacoes': f'Migrado do veículo ID {veiculo.id}'
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Criada placa: {veiculo.placa}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Placa já existe: {veiculo.placa}')
                    )

        self.stdout.write(
            self.style.SUCCESS('Migração de placas concluída!')
        ) 