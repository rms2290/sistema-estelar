#!/usr/bin/env python
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Veiculo, RomaneioViagem
from django.contrib.auth.models import User

def testar_exclusao_veiculos():
    print("=== TESTE DE EXCLUSÃO DE VEÍCULOS ===")
    
    # Listar veículos existentes
    veiculos = Veiculo.objects.all()
    print(f"\nTotal de veículos: {veiculos.count()}")
    
    for veiculo in veiculos:
        print(f"\nVeículo ID {veiculo.id}: {veiculo.placa}")
        
        # Verificar se está sendo usado em romaneios
        romaneios_principal = veiculo.romaneios_veiculo_principal.all()
        romaneios_reboque1 = veiculo.romaneios_reboque_1.all()
        romaneios_reboque2 = veiculo.romaneios_reboque_2.all()
        
        total_romaneios = romaneios_principal.count() + romaneios_reboque1.count() + romaneios_reboque2.count()
        
        print(f"  - Romaneios como veículo principal: {romaneios_principal.count()}")
        print(f"  - Romaneios como reboque 1: {romaneios_reboque1.count()}")
        print(f"  - Romaneios como reboque 2: {romaneios_reboque2.count()}")
        print(f"  - Total de romaneios vinculados: {total_romaneios}")
        
        if total_romaneios == 0:
            print(f"  ✅ Veículo {veiculo.placa} pode ser excluído (não está em uso)")
        else:
            print(f"  ⚠️  Veículo {veiculo.placa} está em uso em {total_romaneios} romaneio(s)")
    
    # Tentar excluir um veículo que não está em uso
    veiculos_livres = [v for v in veiculos if not any([
        v.romaneios_veiculo_principal.exists(),
        v.romaneios_reboque_1.exists(),
        v.romaneios_reboque_2.exists()
    ])]
    
    if veiculos_livres:
        veiculo_teste = veiculos_livres[0]
        print(f"\n\n=== TESTANDO EXCLUSÃO DO VEÍCULO {veiculo_teste.placa} ===")
        
        try:
            # Simular o processo de exclusão da view
            romaneios_vinculados = veiculo_teste.romaneios_veiculo.all()
            if romaneios_vinculados.exists():
                for romaneio in romaneios_vinculados:
                    romaneio.veiculo = None
                    romaneio.save()
                print(f"Veículo desvinculado de {romaneios_vinculados.count()} romaneio(s)")
            
            veiculo_teste.delete()
            print(f"✅ Veículo {veiculo_teste.placa} excluído com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao excluir veículo {veiculo_teste.placa}: {str(e)}")
    else:
        print("\n❌ Nenhum veículo disponível para exclusão (todos estão em uso)")

if __name__ == "__main__":
    testar_exclusao_veiculos()
