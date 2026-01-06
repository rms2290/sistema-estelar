from django.core.management.base import BaseCommand
from notas.models import Motorista


class Command(BaseCommand):
    help = 'Apaga todos os motoristas cadastrados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão de todos os motoristas',
        )

    def handle(self, *args, **options):
        total = Motorista.objects.count()
        
        if total == 0:
            self.stdout.write(
                self.style.WARNING('Não há motoristas cadastrados.')
            )
            return
        
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    f'ATENÇÃO: Esta operação irá apagar {total} motorista(s)!'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Para confirmar, execute: python manage.py apagar_motoristas --confirmar'
                )
            )
            return
        
        # Apagar todos os motoristas
        Motorista.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'{total} motorista(s) apagado(s) com sucesso!')
        )


