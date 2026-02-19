"""
Comando para limpar descrições de movimentos de caixa, removendo
a parte "- ACERTO DIÁRIO {data}" das descrições.
"""
from django.core.management.base import BaseCommand
from financeiro.models import MovimentoCaixa
import re


class Command(BaseCommand):
    help = 'Remove "- ACERTO DIÁRIO {data}" das descrições dos movimentos de caixa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra o que seria alterado, sem salvar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Padrões para remover
        patterns = [
            r'\s*-\s*ACERTO\s+DIÁRIO\s+\d{2}/\d{2}/\d{4}',
            r'\s*-\s*ACERTO\s+DIARIO\s+\d{2}/\d{2}/\d{4}',
            r'\s*-\s*ACERTO\s+DIÁRIO\s+\d{2}/\d{2}/\d{4}',
        ]
        
        # Buscar movimentos com essas descrições
        movimentos = MovimentoCaixa.objects.filter(
            descricao__iregex=r'ACERTO\s+DI[ÁA]RIO'
        )
        
        total = movimentos.count()
        atualizados = 0
        
        self.stdout.write(f'Encontrados {total} movimentos para atualizar.')
        
        for movimento in movimentos:
            descricao_original = movimento.descricao
            descricao_nova = descricao_original
            
            # Aplicar cada padrão
            for pattern in patterns:
                descricao_nova = re.sub(pattern, '', descricao_nova, flags=re.IGNORECASE)
            
            # Limpar espaços extras no final
            descricao_nova = descricao_nova.strip()
            
            if descricao_original != descricao_nova:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Movimento {movimento.pk}: '
                        f'"{descricao_original}" -> "{descricao_nova}"'
                    )
                else:
                    movimento.descricao = descricao_nova
                    movimento.save(update_fields=['descricao'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Movimento {movimento.pk} atualizado: "{descricao_nova}"'
                        )
                    )
                atualizados += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] {atualizados} movimentos seriam atualizados.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n{atualizados} movimentos atualizados com sucesso!'
                )
            )

