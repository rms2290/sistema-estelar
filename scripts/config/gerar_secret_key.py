#!/usr/bin/env python
"""
Script para gerar SECRET_KEY do Django
Uso: python scripts/config/gerar_secret_key.py
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')

try:
    from django.core.management.utils import get_random_secret_key
    
    print("=" * 60)
    print("GERADOR DE SECRET_KEY - Sistema Estelar")
    print("=" * 60)
    print()
    
    secret_key = get_random_secret_key()
    
    print("SECRET_KEY gerada:")
    print("-" * 60)
    print(secret_key)
    print("-" * 60)
    print()
    print("Adicione esta linha ao seu arquivo .env:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("OU copie e cole diretamente:")
    print()
    print(f"echo SECRET_KEY={secret_key} >> .env")
    print()
    print("=" * 60)
    
except ImportError:
    print("ERRO: Django não está instalado ou não pode ser importado.")
    print("Ative o ambiente virtual primeiro.")
    sys.exit(1)


