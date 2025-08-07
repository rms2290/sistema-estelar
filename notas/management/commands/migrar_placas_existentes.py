from django.core.management.base import BaseCommand
from notas.models import Veiculo, PlacaVeiculo


class Command(BaseCommand):
    help = 'Migra as placas existentes dos veículos para a nova tabela PlacaVeiculo'

    def handle(self, *args, **options):
        # Obter todas as placas únicas dos veículos existentes
        placas_existentes = set()
        for veiculo in Veiculo.objects.all():
            if veiculo.placa:
                placas_existentes.add(veiculo.placa)
        
        self.stdout.write(f'Encontradas {len(placas_existentes)} placas únicas para migrar.')
        
        # Criar registros na nova tabela PlacaVeiculo
        placas_criadas = 0
        for placa in placas_existentes:
            placa_obj, created = PlacaVeiculo.objects.get_or_create(
                placa=placa,
                defaults={
                    'estado': None,
                    'cidade': None,
                    'pais': 'Brasil',
                    'ativa': True,
                }
            )
            
            if created:
                placas_criadas += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Criada placa: {placa}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Placa já existe: {placa}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Migração concluída! {placas_criadas} placas criadas.')
        ) 