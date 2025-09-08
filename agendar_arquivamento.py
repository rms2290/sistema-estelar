#!/usr/bin/env python
"""
Script de agendamento para arquivamento automático
Executa arquivamento mensal de dados antigos
"""

import os
import sys
import django
import schedule
import time
from datetime import datetime
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

def executar_arquivamento_mensal():
    """Executa arquivamento mensal de dados antigos"""
    print(f"\n🕐 [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando arquivamento mensal...")
    
    try:
        # Executar comando de arquivamento com backup
        os.system('python manage.py arquivar_dados_antigos --backup --anos 5')
        print("✅ Arquivamento mensal concluído com sucesso!")
        
        # Criar relatório de execução
        criar_relatorio_execucao()
        
    except Exception as e:
        print(f"❌ Erro no arquivamento mensal: {e}")

def executar_limpeza_trimestral():
    """Executa limpeza trimestral mais agressiva"""
    print(f"\n🕐 [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando limpeza trimestral...")
    
    try:
        # Executar comando de arquivamento com backup (dados de 3+ anos)
        os.system('python manage.py arquivar_dados_antigos --backup --anos 3')
        print("✅ Limpeza trimestral concluída com sucesso!")
        
        # Criar relatório de execução
        criar_relatorio_execucao()
        
    except Exception as e:
        print(f"❌ Erro na limpeza trimestral: {e}")

def executar_backup_diario():
    """Executa backup diário dos dados ativos"""
    print(f"\n🕐 [{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando backup diário...")
    
    try:
        # Executar apenas backup (sem arquivamento)
        os.system('python manage.py arquivar_dados_antigos --backup --dry-run')
        print("✅ Backup diário concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no backup diário: {e}")

def criar_relatorio_execucao():
    """Cria relatório de execução do arquivamento"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    relatorio_file = f'dados_arquivados/relatorios/relatorio_{timestamp}.txt'
    
    # Criar diretório se não existir
    Path('dados_arquivados/relatorios').mkdir(parents=True, exist_ok=True)
    
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write(f"RELATÓRIO DE ARQUIVAMENTO - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Data/Hora: {datetime.now()}\n")
        f.write(f"Tipo: Arquivamento Automático\n")
        f.write(f"Status: Concluído\n")
        f.write("=" * 50 + "\n")
    
    print(f"📄 Relatório criado: {relatorio_file}")

def configurar_agendamento():
    """Configura o agendamento das tarefas"""
    print("📅 CONFIGURANDO AGENDAMENTO AUTOMÁTICO...")
    
    # Arquivamento mensal (primeiro dia do mês às 02:00)
    schedule.every().month.at("02:00").do(executar_arquivamento_mensal)
    print("   ✅ Arquivamento mensal: 1º dia do mês às 02:00")
    
    # Limpeza trimestral (primeiro dia de cada trimestre às 03:00)
    schedule.every(3).months.at("03:00").do(executar_limpeza_trimestral)
    print("   ✅ Limpeza trimestral: 1º dia do trimestre às 03:00")
    
    # Backup diário (todos os dias às 01:00)
    schedule.every().day.at("01:00").do(executar_backup_diario)
    print("   ✅ Backup diário: Todos os dias às 01:00")
    
    print("\n🔄 Monitorando agendamento...")
    print("   Pressione Ctrl+C para parar")

def executar_agendamento():
    """Executa o loop de agendamento"""
    configurar_agendamento()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
            
    except KeyboardInterrupt:
        print("\n⏹️  Agendamento interrompido pelo usuário")

def executar_teste():
    """Executa teste do sistema de arquivamento"""
    print("🧪 EXECUTANDO TESTE DO SISTEMA DE ARQUIVAMENTO...")
    
    # Teste 1: Simular arquivamento
    print("\n1️⃣ Testando simulação de arquivamento...")
    os.system('python manage.py arquivar_dados_antigos --dry-run --anos 5')
    
    # Teste 2: Listar arquivos disponíveis
    print("\n2️⃣ Testando listagem de arquivos...")
    os.system('python manage.py consultar_arquivo --listar')
    
    # Teste 3: Consultar dados arquivados
    print("\n3️⃣ Testando consulta de dados...")
    os.system('python manage.py consultar_arquivo --tipo romaneios')
    
    print("\n✅ Testes concluídos!")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == 'iniciar':
            executar_agendamento()
        elif comando == 'teste':
            executar_teste()
        elif comando == 'mensal':
            executar_arquivamento_mensal()
        elif comando == 'trimestral':
            executar_limpeza_trimestral()
        elif comando == 'backup':
            executar_backup_diario()
        else:
            print("Uso: python agendar_arquivamento.py [iniciar|teste|mensal|trimestral|backup]")
    else:
        print("SISTEMA DE ARQUIVAMENTO AUTOMÁTICO")
        print("=" * 40)
        print("Comandos disponíveis:")
        print("  iniciar    - Inicia o agendamento automático")
        print("  teste      - Executa testes do sistema")
        print("  mensal     - Executa arquivamento mensal")
        print("  trimestral - Executa limpeza trimestral")
        print("  backup     - Executa backup diário")
        print("\nExemplo: python agendar_arquivamento.py iniciar") 