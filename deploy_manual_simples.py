#!/usr/bin/env python3
"""
Script de Deploy Manual Simples para Locaweb
Sistema Estelar - Deploy das alterações de ordenação
"""

import subprocess
import os
import sys

def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"\n🔄 {description}")
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Sucesso: {description}")
        if result.stdout:
            print(f"Saída: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro: {description}")
        print(f"Código de erro: {e.returncode}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False

def main():
    """Função principal"""
    print("🚀 Deploy Manual Simples - Sistema Estelar")
    print("=" * 50)
    
    # Verificar se está no diretório correto
    if not os.path.exists("manage.py"):
        print("❌ Execute este script no diretório raiz do projeto Django")
        sys.exit(1)
    
    # 1. Coletar arquivos estáticos
    if not run_command("python manage.py collectstatic --noinput", "Coletando arquivos estáticos"):
        print("❌ Falha ao coletar arquivos estáticos")
        return False
    
    # 2. Aplicar migrações
    if not run_command("python manage.py migrate", "Aplicando migrações"):
        print("❌ Falha ao aplicar migrações")
        return False
    
    # 3. Verificar configuração
    if not run_command("python manage.py check", "Verificando configuração"):
        print("❌ Falha na verificação de configuração")
        return False
    
    print("\n🎉 Deploy manual concluído com sucesso!")
    print("=" * 50)
    print("📋 Próximos passos para o servidor:")
    print("1. Faça upload dos arquivos para o servidor")
    print("2. Execute os mesmos comandos no servidor")
    print("3. Reinicie o servidor web (nginx/apache)")
    print("4. Reinicie o servidor de aplicação (gunicorn/uwsgi)")

if __name__ == "__main__":
    main()

