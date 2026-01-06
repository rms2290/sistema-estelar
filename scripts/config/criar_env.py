#!/usr/bin/env python
"""
Script para criar arquivo .env a partir do exemplo
Uso: python scripts/config/criar_env.py
"""
import os
import sys
from pathlib import Path
from shutil import copyfile

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_EXAMPLE = BASE_DIR / 'config' / 'examples' / 'env_example.txt'
ENV_FILE = BASE_DIR / '.env'

print("=" * 60)
print("CRIADOR DE ARQUIVO .env - Sistema Estelar")
print("=" * 60)
print()

if ENV_FILE.exists():
    resposta = input(f"Arquivo .env já existe em {ENV_FILE}. Sobrescrever? (s/N): ")
    if resposta.lower() != 's':
        print("Operação cancelada.")
        sys.exit(0)

# Copiar exemplo
try:
    copyfile(ENV_EXAMPLE, ENV_FILE)
    print(f"[OK] Arquivo .env criado em: {ENV_FILE}")
    print()
    print("⚠️  IMPORTANTE:")
    print("1. Edite o arquivo .env e configure:")
    print("   - SECRET_KEY (use: python scripts/config/gerar_secret_key.py)")
    print("   - DEBUG=True (para desenvolvimento)")
    print("   - ALLOWED_HOSTS (para desenvolvimento: localhost,127.0.0.1)")
    print()
    print("2. NUNCA commite o arquivo .env no Git!")
    print()
    print("=" * 60)
except Exception as e:
    print(f"[ERRO] Falha ao criar .env: {e}")
    sys.exit(1)


