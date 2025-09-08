#!/usr/bin/env python
"""
Script para backup do banco de dados
"""
import os
import subprocess
import datetime
import shutil

def create_backup():
    """Cria backup do banco de dados"""
    # Configurações do banco
    db_name = os.environ.get('DB_NAME', 'sistema_estelar')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    
    # Nome do arquivo de backup
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{db_name}_{timestamp}.sql'
    backup_path = os.path.join('backups', backup_filename)
    
    # Criar diretório de backups se não existir
    os.makedirs('backups', exist_ok=True)
    
    # Comando pg_dump
    cmd = [
        'pg_dump',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '-f', backup_path,
        '--verbose'
    ]
    
    try:
        print(f"🔄 Criando backup: {backup_filename}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Backup criado com sucesso: {backup_path}")
        
        # Comprimir backup
        compressed_path = f"{backup_path}.gz"
        shutil.make_archive(backup_path, 'gztar', 'backups', backup_filename)
        print(f"✅ Backup comprimido: {compressed_path}")
        
        # Remover arquivo não comprimido
        os.remove(backup_path)
        
        return compressed_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar backup: {e.stderr}")
        return None

def restore_backup(backup_file):
    """Restaura backup do banco de dados"""
    # Configurações do banco
    db_name = os.environ.get('DB_NAME', 'sistema_estelar')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    
    # Comando psql
    cmd = [
        'psql',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-d', db_name,
        '-f', backup_file
    ]
    
    try:
        print(f"🔄 Restaurando backup: {backup_file}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Backup restaurado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao restaurar backup: {e.stderr}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("❌ Especifique o arquivo de backup para restaurar")
    else:
        create_backup()
