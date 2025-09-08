from django.core.management.base import BaseCommand
from notas.models import Veiculo

class Command(BaseCommand):
    help = 'Testar exclusão de veículos'

    def handle(self, *args, **options):
        self.stdout.write("=== TESTE DE EXCLUSÃO DE VEÍCULOS ===")
        
        # Listar veículos
        veiculos = Veiculo.objects.all()
        self.stdout.write(f"Total de veículos: {veiculos.count()}")
        
        for veiculo in veiculos:
            self.stdout.write(f"\nVeículo ID {veiculo.id}: {veiculo.placa}")
            
            # Verificar uso em romaneios
            romaneios_principal = veiculo.romaneios_veiculo_principal.count()
            romaneios_reboque1 = veiculo.romaneios_reboque_1.count()
            romaneios_reboque2 = veiculo.romaneios_reboque_2.count()
            
            total = romaneios_principal + romaneios_reboque1 + romaneios_reboque2
            
            self.stdout.write(f"  - Romaneios como veículo principal: {romaneios_principal}")
            self.stdout.write(f"  - Romaneios como reboque 1: {romaneios_reboque1}")
            self.stdout.write(f"  - Romaneios como reboque 2: {romaneios_reboque2}")
            self.stdout.write(f"  - Total de romaneios vinculados: {total}")
            
            if total == 0:
                self.stdout.write(f"  ✅ Veículo {veiculo.placa} pode ser excluído")
                
                # Tentar excluir
                try:
                    veiculo.delete()
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Veículo {veiculo.placa} excluído com sucesso!"))
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ Erro ao excluir veículo {veiculo.placa}: {str(e)}"))
            else:
                self.stdout.write(f"  ⚠️  Veículo {veiculo.placa} está em uso em {total} romaneio(s)")
        
        self.stdout.write("\n=== FIM DO TESTE ===")
