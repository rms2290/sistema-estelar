#!/usr/bin/env python
"""
Script para verificar qual banco de dados está sendo usado
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from django.conf import settings
from django.db import connection

print("=" * 70)
print("VERIFICAÇÃO DO BANCO DE DADOS")
print("=" * 70)
print()

# Verificar configuração
db_config = settings.DATABASES['default']
print(f"ENGINE: {db_config['ENGINE']}")
print(f"NAME: {db_config['NAME']}")

if 'HOST' in db_config:
    print(f"HOST: {db_config.get('HOST', 'N/A')}")
    print(f"USER: {db_config.get('USER', 'N/A')}")
    print(f"PORT: {db_config.get('PORT', 'N/A')}")

print()

# Verificar conexão
try:
    connection.ensure_connection()
    print("✅ Conexão estabelecida com sucesso!")
    print(f"Banco de dados ativo: {connection.settings_dict['ENGINE']}")
    
    # Verificar se é SQLite
    if 'sqlite3' in db_config['ENGINE']:
        print()
        print("📊 SQLite está em uso")
        db_path = db_config['NAME']
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"   Arquivo: {db_path}")
            print(f"   Tamanho: {size:,} bytes ({size/1024:.2f} KB)")
            
            # Verificar tabelas
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            print(f"   Tabelas: {len(tables)}")
            if tables:
                print("   Primeiras tabelas:")
                for table in tables[:5]:
                    print(f"     - {table[0]}")
        else:
            print(f"   ⚠️ Arquivo não encontrado: {db_path}")
    
    # Verificar se é PostgreSQL
    elif 'postgresql' in db_config['ENGINE']:
        print()
        print("🐘 PostgreSQL está em uso")
        print(f"   Database: {db_config.get('NAME', 'N/A')}")
        print(f"   Host: {db_config.get('HOST', 'N/A')}")
        print(f"   Port: {db_config.get('PORT', 'N/A')}")
        print(f"   User: {db_config.get('USER', 'N/A')}")
        
        # Verificar tabelas
        cursor = connection.cursor()
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename LIMIT 5")
        tables = cursor.fetchall()
        print(f"   Tabelas: {len(tables)} (mostrando primeiras 5)")
        if tables:
            for table in tables:
                print(f"     - {table[0]}")
    
    print()
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    print()
    print("=" * 70)

