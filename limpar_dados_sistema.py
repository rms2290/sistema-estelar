#!/usr/bin/env python
"""
Script para limpar todos os dados do sistema, mantendo apenas o usuário admin
Execute: python limpar_dados_sistema.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import (
    NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, 
    HistoricoConsulta, TabelaSeguro, AgendaEntrega, 
    DespesaCarregamento, CobrancaCarregamento, Usuario, TipoVeiculo, PlacaVeiculo
)

def limpar_dados():
    """Limpa todos os dados do sistema, mantendo apenas o usuário admin"""
    
    print("=" * 60)
    print("  LIMPEZA DE DADOS DO SISTEMA ESTELAR")
    print("=" * 60)
    print()
    
    # Confirmar ação
    print("⚠️  ATENÇÃO: Esta operação irá:")
    print("   - Excluir TODOS os dados do sistema")
    print("   - Manter APENAS o usuário admin")
    print("   - Manter a estrutura do banco de dados")
    print()
    
    resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if resposta != 'SIM':
        print("Operação cancelada.")
        return
    
    print()
    print("Iniciando limpeza...")
    print()
    
    # Contadores
    contadores = {}
    
    try:
        # 1. Excluir Cobranças de Carregamento
        print("1. Excluindo cobranças de carregamento...")
        count = CobrancaCarregamento.objects.all().count()
        CobrancaCarregamento.objects.all().delete()
        contadores['Cobranças de Carregamento'] = count
        print(f"   ✓ {count} cobrança(s) excluída(s)")
        
        # 2. Excluir Despesas de Carregamento
        print("2. Excluindo despesas de carregamento...")
        count = DespesaCarregamento.objects.all().count()
        DespesaCarregamento.objects.all().delete()
        contadores['Despesas de Carregamento'] = count
        print(f"   ✓ {count} despesa(s) excluída(s)")
        
        # 3. Excluir Romaneios
        print("3. Excluindo romaneios...")
        count = RomaneioViagem.objects.all().count()
        RomaneioViagem.objects.all().delete()
        contadores['Romaneios'] = count
        print(f"   ✓ {count} romaneio(s) excluído(s)")
        
        # 4. Excluir Notas Fiscais
        print("4. Excluindo notas fiscais...")
        count = NotaFiscal.objects.all().count()
        NotaFiscal.objects.all().delete()
        contadores['Notas Fiscais'] = count
        print(f"   ✓ {count} nota(s) fiscal(is) excluída(s)")
        
        # 5. Excluir Histórico de Consultas
        print("5. Excluindo histórico de consultas...")
        count = HistoricoConsulta.objects.all().count()
        HistoricoConsulta.objects.all().delete()
        contadores['Histórico de Consultas'] = count
        print(f"   ✓ {count} consulta(s) excluída(s)")
        
        # 6. Excluir Agenda de Entrega
        print("6. Excluindo agenda de entrega...")
        count = AgendaEntrega.objects.all().count()
        AgendaEntrega.objects.all().delete()
        contadores['Agenda de Entrega'] = count
        print(f"   ✓ {count} registro(s) excluído(s)")
        
        # 7. Excluir Clientes (exceto se houver usuários vinculados)
        print("7. Excluindo clientes...")
        # Verificar se há usuários vinculados a clientes
        usuarios_com_cliente = Usuario.objects.exclude(cliente__isnull=True).exclude(username='admin')
        if usuarios_com_cliente.exists():
            print("   ⚠️  Existem usuários vinculados a clientes. Excluindo usuários primeiro...")
            count_usuarios = usuarios_com_cliente.count()
            usuarios_com_cliente.delete()
            print(f"   ✓ {count_usuarios} usuário(s) excluído(s)")
        
        count = Cliente.objects.all().count()
        Cliente.objects.all().delete()
        contadores['Clientes'] = count
        print(f"   ✓ {count} cliente(s) excluído(s)")
        
        # 8. Excluir Motoristas
        print("8. Excluindo motoristas...")
        count = Motorista.objects.all().count()
        Motorista.objects.all().delete()
        contadores['Motoristas'] = count
        print(f"   ✓ {count} motorista(s) excluído(s)")
        
        # 9. Excluir Veículos e Placas
        print("9. Excluindo veículos e placas...")
        count_placas = PlacaVeiculo.objects.all().count()
        PlacaVeiculo.objects.all().delete()
        print(f"   ✓ {count_placas} placa(s) excluída(s)")
        
        count = Veiculo.objects.all().count()
        Veiculo.objects.all().delete()
        contadores['Veículos'] = count
        print(f"   ✓ {count} veículo(s) excluído(s)")
        
        # 10. Excluir todos os usuários exceto admin
        print("10. Excluindo usuários (exceto admin)...")
        usuarios_para_excluir = Usuario.objects.exclude(username='admin')
        count = usuarios_para_excluir.count()
        usuarios_para_excluir.delete()
        contadores['Usuários'] = count
        print(f"   ✓ {count} usuário(s) excluído(s)")
        
        # 11. Verificar se admin existe, se não, criar
        print("11. Verificando usuário admin...")
        if not Usuario.objects.filter(username='admin').exists():
            print("   ⚠️  Usuário admin não encontrado. Criando...")
            admin = Usuario.objects.create(
                username='admin',
                email='admin@estelar.com',
                first_name='Administrador',
                last_name='Sistema',
                tipo_usuario='admin',
                is_active=True,
                is_staff=True
            )
            admin.set_password('123456')
            admin.save()
            print("   ✓ Usuário admin criado (senha: 123456)")
        else:
            admin = Usuario.objects.get(username='admin')
            print(f"   ✓ Usuário admin mantido: {admin.username}")
            print(f"   - Email: {admin.email}")
            print(f"   - Tipo: {admin.tipo_usuario}")
        
        # 12. Manter TabelaSeguro e TipoVeiculo (dados de referência)
        print("12. Mantendo dados de referência...")
        count_seguro = TabelaSeguro.objects.all().count()
        count_tipo = TipoVeiculo.objects.all().count()
        print(f"   ✓ Tabela de Seguro: {count_seguro} registro(s) mantido(s)")
        print(f"   ✓ Tipos de Veículo: {count_tipo} registro(s) mantido(s)")
        
        print()
        print("=" * 60)
        print("  LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print()
        print("Resumo dos dados excluídos:")
        for item, quantidade in contadores.items():
            print(f"   - {item}: {quantidade}")
        print()
        print("Dados mantidos:")
        print("   - Usuário admin")
        print("   - Tabela de Seguro")
        print("   - Tipos de Veículo")
        print("   - Estrutura do banco de dados")
        print()
        print("⚠️  IMPORTANTE: Altere a senha do admin após o primeiro login!")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("  ERRO DURANTE A LIMPEZA")
        print("=" * 60)
        print(f"Erro: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    limpar_dados()

