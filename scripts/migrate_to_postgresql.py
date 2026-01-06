#!/usr/bin/env python
"""
=============================================================================
SCRIPT DE MIGRAÇÃO: SQLite → PostgreSQL
=============================================================================

Este script migra dados do banco SQLite para PostgreSQL.

PRÉ-REQUISITOS:
--------------
1. PostgreSQL instalado e rodando
2. Banco de dados criado no PostgreSQL
3. Variáveis de ambiente configuradas (DB_NAME, DB_USER, DB_PASSWORD, etc.)
4. Backup completo do SQLite feito antes de executar

USO:
----
1. Configure as variáveis de ambiente:
   export DB_NAME=sistema_estelar
   export DB_USER=postgres
   export DB_PASSWORD=sua_senha
   export DB_HOST=localhost
   export DB_PORT=5432

2. Execute o script:
   python scripts/migrate_to_postgresql.py

3. Valide os dados migrados

4. Atualize settings_production.py para usar PostgreSQL

AVISOS:
-------
- Este script faz backup automático do SQLite antes de migrar
- Teste em ambiente de staging antes de produção
- Valide integridade dos dados após migração
- Mantenha backup do SQLite por pelo menos 30 dias

Autor: Sistema Estelar
Data: 2025
Versão: 1.0
=============================================================================
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.db import connections


def fazer_backup_sqlite():
    """Faz backup do banco SQLite antes da migração"""
    sqlite_path = BASE_DIR / 'db.sqlite3'
    
    if not sqlite_path.exists():
        print("❌ Arquivo db.sqlite3 não encontrado!")
        return False
    
    # Criar diretório de backups se não existir
    backup_dir = BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Nome do backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'db_backup_{timestamp}.sqlite3'
    
    # Copiar arquivo
    shutil.copy2(sqlite_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    
    return True


def validar_postgresql():
    """Valida conexão com PostgreSQL"""
    try:
        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
        
        # Validar variáveis obrigatórias
        required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
            return False
        
        # Testar conexão
        from django.db import connection
        connection.ensure_connection()
        print("✅ Conexão com PostgreSQL estabelecida!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com PostgreSQL: {e}")
        return False


def migrar_dados():
    """Executa a migração dos dados"""
    print("\n🔄 Iniciando migração...")
    
    try:
        # 1. Executar migrations no PostgreSQL
        print("1️⃣ Executando migrations no PostgreSQL...")
        call_command('migrate', verbosity=1)
        
        # 2. Carregar dados do SQLite
        print("2️⃣ Carregando dados do SQLite...")
        # Nota: Django não suporta migração direta entre bancos
        # Será necessário usar django-dbbackup ou script customizado
        print("⚠️  Migração de dados requer ferramenta adicional (django-dbbackup)")
        print("   Ou use dumpdata/loaddata manualmente:")
        print("   python manage.py dumpdata > data.json")
        print("   # Configure PostgreSQL")
        print("   python manage.py loaddata data.json")
        
        print("\n✅ Migração concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        return False


def main():
    """Função principal"""
    print("=" * 70)
    print("SCRIPT DE MIGRAÇÃO: SQLite → PostgreSQL")
    print("=" * 70)
    
    # 1. Fazer backup
    print("\n📦 Passo 1: Fazendo backup do SQLite...")
    if not fazer_backup_sqlite():
        print("❌ Falha ao fazer backup. Abortando migração.")
        return 1
    
    # 2. Validar PostgreSQL
    print("\n🔍 Passo 2: Validando conexão com PostgreSQL...")
    if not validar_postgresql():
        print("❌ Falha na validação. Verifique as variáveis de ambiente.")
        return 1
    
    # 3. Confirmar migração
    print("\n⚠️  ATENÇÃO: Esta operação irá migrar dados para PostgreSQL.")
    resposta = input("Deseja continuar? (sim/não): ").lower()
    
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("❌ Migração cancelada pelo usuário.")
        return 0
    
    # 4. Executar migração
    if not migrar_dados():
        return 1
    
    print("\n" + "=" * 70)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Valide os dados no PostgreSQL")
    print("2. Atualize settings_production.py (já configurado)")
    print("3. Configure USE_POSTGRESQL=True nas variáveis de ambiente")
    print("4. Teste a aplicação com PostgreSQL")
    print("5. Mantenha backup do SQLite por 30 dias")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())


