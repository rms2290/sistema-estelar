#!/usr/bin/env python
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Veiculo

def testar_exclusao():
    print("=== TESTE SIMPLES DE EXCLUSÃO ===")
    
    # Listar veículos
    veiculos = Veiculo.objects.all()
    print(f"Total de veículos: {veiculos.count()}")
    
    for veiculo in veiculos:
        print(f"ID: {veiculo.id}, Placa: {veiculo.placa}")
        
        # Verificar uso em romaneios
        romaneios_principal = veiculo.romaneios_veiculo_principal.count()
        romaneios_reboque1 = veiculo.romaneios_reboque_1.count()
        romaneios_reboque2 = veiculo.romaneios_reboque_2.count()
        
        total = romaneios_principal + romaneios_reboque1 + romaneios_reboque2
        
        if total == 0:
            print(f"  ✅ Pode ser excluído")
            try:
                veiculo.delete()
                print(f"  ✅ Excluído com sucesso!")
                break
            except Exception as e:
                print(f"  ❌ Erro: {e}")
        else:
            print(f"  ⚠️  Em uso em {total} romaneio(s)")

if __name__ == "__main__":
    testar_exclusao()
