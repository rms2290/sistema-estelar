#!/usr/bin/env python
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Veiculo, Usuario

def testar_exclusao():
    print("=== TESTE FINAL DE EXCLUSÃO ===")
    
    # Verificar usuários administradores
    admins = Usuario.objects.filter(tipo_usuario='admin')
    print(f"Administradores encontrados: {admins.count()}")
    for admin in admins:
        print(f"  - {admin.username} ({admin.tipo_usuario})")
    
    # Listar veículos
    veiculos = Veiculo.objects.all()
    print(f"\nTotal de veículos: {veiculos.count()}")
    
    for veiculo in veiculos:
        print(f"\nVeículo ID {veiculo.id}: {veiculo.placa}")
        
        # Verificar uso em romaneios
        romaneios_principal = veiculo.romaneios_veiculo_principal.count()
        romaneios_reboque1 = veiculo.romaneios_reboque_1.count()
        romaneios_reboque2 = veiculo.romaneios_reboque_2.count()
        
        total = romaneios_principal + romaneios_reboque1 + romaneios_reboque2
        
        print(f"  - Romaneios como veículo principal: {romaneios_principal}")
        print(f"  - Romaneios como reboque 1: {romaneios_reboque1}")
        print(f"  - Romaneios como reboque 2: {romaneios_reboque2}")
        print(f"  - Total de romaneios vinculados: {total}")
        
        if total == 0:
            print(f"  ✅ Veículo {veiculo.placa} pode ser excluído")
            
            # Tentar excluir
            try:
                veiculo.delete()
                print(f"  ✅ Veículo {veiculo.placa} excluído com sucesso!")
                break
            except Exception as e:
                print(f"  ❌ Erro ao excluir veículo {veiculo.placa}: {str(e)}")
        else:
            print(f"  ⚠️  Veículo {veiculo.placa} está em uso em {total} romaneio(s)")

if __name__ == "__main__":
    testar_exclusao()
