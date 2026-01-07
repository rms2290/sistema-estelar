#!/usr/bin/env python3
"""
Script completo para aplicar funcionalidades de auditoria do commit cd1da75
"""

import os
import sys
import subprocess
import re

def run_git_show(commit_hash, file_path):
    """Executa git show e retorna o conteúdo"""
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit_hash}:{file_path}'],
            capture_output=True,
            text=True,
            check=True,
            cwd='/var/www/sistema-estelar'
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao obter {file_path}: {e}")
        return None

def extract_class_from_content(content, class_name):
    """Extrai uma classe completa do conteúdo"""
    pattern = rf'^class {class_name}\([^)]+\):.*?(?=^class |^# -{20,}|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(0).rstrip() + '\n'
    return None

def extract_function_from_content(content, func_name):
    """Extrai uma função completa do conteúdo"""
    pattern = rf'^def {func_name}\([^)]+\):.*?(?=^def |^class |\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(0).rstrip() + '\n'
    return None

def extract_admin_register(content, model_name):
    """Extrai o registro completo do admin"""
    pattern = rf'@admin\.register\({model_name}\)\s*\nclass \w+Admin.*?(?=@admin\.register|^class |\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(0).rstrip() + '\n'
    return None

def main():
    print("=" * 60)
    print("  APLICANDO FUNCIONALIDADES DE AUDITORIA")
    print("=" * 60)
    print()
    
    os.chdir('/var/www/sistema-estelar')
    
    # 1. Criar arquivo de utilitários
    print("1. Criando arquivo de utilitários de auditoria...")
    os.makedirs('notas/utils', exist_ok=True)
    utils_content = run_git_show('cd1da75', 'notas/utils/auditoria.py')
    if utils_content:
        with open('notas/utils/auditoria.py', 'w', encoding='utf-8') as f:
            f.write(utils_content)
        print("   ✓ notas/utils/auditoria.py criado")
    else:
        print("   ❌ Falha ao criar arquivo de utilitários")
        return False
    
    # 2. Adicionar modelo AuditoriaLog
    print()
    print("2. Adicionando modelo AuditoriaLog...")
    models_file = 'notas/models.py'
    
    with open(models_file, 'r', encoding='utf-8') as f:
        models_content = f.read()
    
    if 'class AuditoriaLog' in models_content:
        print("   ✓ Modelo AuditoriaLog já existe")
    else:
        models_commit = run_git_show('cd1da75', 'notas/models.py')
        if models_commit:
            auditoria_model = extract_class_from_content(models_commit, 'AuditoriaLog')
            if auditoria_model:
                with open(models_file, 'a', encoding='utf-8') as f:
                    f.write('\n\n# --------------------------------------------------------------------------------------\n')
                    f.write('# Auditoria\n')
                    f.write('# --------------------------------------------------------------------------------------\n')
                    f.write(auditoria_model)
                print("   ✓ Modelo AuditoriaLog adicionado")
            else:
                print("   ❌ Não foi possível extrair o modelo")
                return False
        else:
            print("   ❌ Falha ao obter models.py do commit")
            return False
    
    # 3. Adicionar views de auditoria
    print()
    print("3. Adicionando views de auditoria...")
    views_file = 'notas/views.py'
    
    with open(views_file, 'r', encoding='utf-8') as f:
        views_content = f.read()
    
    views_commit = run_git_show('cd1da75', 'notas/views.py')
    if not views_commit:
        print("   ❌ Falha ao obter views.py do commit")
        return False
    
    views_to_add = [
        'listar_logs_auditoria',
        'detalhes_log_auditoria',
        'listar_registros_excluidos',
        'restaurar_registro'
    ]
    
    for view_name in views_to_add:
        if f'def {view_name}(' in views_content:
            print(f"   ✓ View {view_name} já existe")
        else:
            view_func = extract_function_from_content(views_commit, view_name)
            if view_func:
                with open(views_file, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + view_func)
                print(f"   ✓ View {view_name} adicionada")
            else:
                print(f"   ⚠ Não foi possível extrair a view {view_name}")
    
    # 4. Adicionar import e registro no admin.py
    print()
    print("4. Adicionando import e registro no admin.py...")
    admin_file = 'notas/admin.py'
    
    with open(admin_file, 'r', encoding='utf-8') as f:
        admin_content = f.read()
    
    # Adicionar import
    if 'AuditoriaLog' not in admin_content:
        import_pattern = r'from \.models import ([^\n]+)'
        match = re.search(import_pattern, admin_content)
        if match:
            imports = match.group(1)
            if 'AuditoriaLog' not in imports:
                new_imports = imports.rstrip() + ', AuditoriaLog'
                admin_content = admin_content.replace(
                    match.group(0),
                    f'from .models import {new_imports}'
                )
                print("   ✓ Import de AuditoriaLog adicionado")
    
    # Adicionar registro do admin
    if '@admin.register(AuditoriaLog)' not in admin_content:
        admin_commit = run_git_show('cd1da75', 'notas/admin.py')
        if admin_commit:
            admin_register = extract_admin_register(admin_commit, 'AuditoriaLog')
            if admin_register:
                with open(admin_file, 'a', encoding='utf-8') as f:
                    f.write('\n\n' + admin_register)
                print("   ✓ Registro do AuditoriaLogAdmin adicionado")
    
    # Salvar admin.py se foi modificado
    if '@admin.register(AuditoriaLog)' not in admin_content:
        with open(admin_file, 'w', encoding='utf-8') as f:
            f.write(admin_content)
    
    print()
    print("=" * 60)
    print("  APLICAÇÃO CONCLUÍDA!")
    print("=" * 60)
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Descomentar URLs de auditoria em notas/urls.py")
    print("2. python manage.py makemigrations")
    print("3. python manage.py migrate")
    print("4. python manage.py check")
    print("5. Reiniciar Gunicorn")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
