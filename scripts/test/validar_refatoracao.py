"""
Script para validar a refatoração da Fase 2
Verifica imports, estrutura de arquivos e funcionalidades básicas
"""
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')

import django
django.setup()

def test_imports():
    """Testa se todos os imports estão funcionando"""
    print("\n=== TESTE 1: IMPORTS ===")
    erros = []
    
    try:
        from notas.views import dashboard, login_view, listar_clientes
        print("[OK] Imports de views básicas")
    except Exception as e:
        print(f"[ERRO] Imports de views: {e}")
        erros.append(f"Views: {e}")
    
    try:
        from notas.services import RomaneioService, NotaFiscalService
        print("[OK] Imports de services")
    except Exception as e:
        print(f"[ERRO] Imports de services: {e}")
        erros.append(f"Services: {e}")
    
    try:
        from notas.forms import ClienteForm, NotaFiscalForm, LoginForm
        print("[OK] Imports de forms")
    except Exception as e:
        print(f"[ERRO] Imports de forms: {e}")
        erros.append(f"Forms: {e}")
    
    try:
        from notas.utils import formatar_valor_brasileiro, validar_cnpj
        print("[OK] Imports de utils")
    except Exception as e:
        print(f"[ERRO] Imports de utils: {e}")
        erros.append(f"Utils: {e}")
    
    try:
        from notas.decorators import admin_required, funcionario_required
        print("[OK] Imports de decorators")
    except Exception as e:
        print(f"[ERRO] Imports de decorators: {e}")
        erros.append(f"Decorators: {e}")
    
    return erros


def test_structure():
    """Testa se a estrutura de arquivos está correta"""
    print("\n=== TESTE 2: ESTRUTURA DE ARQUIVOS ===")
    erros = []
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    notas_path = os.path.join(base_path, 'notas')
    
    # Verificar diretórios
    dirs_esperados = ['views', 'services', 'forms', 'utils', 'tests']
    for dir_name in dirs_esperados:
        dir_path = os.path.join(notas_path, dir_name)
        if os.path.exists(dir_path):
            print(f"[OK] Diretorio {dir_name}/ existe")
        else:
            print(f"[ERRO] Diretorio {dir_name}/ nao encontrado")
            erros.append(f"Diretorio {dir_name}/ nao encontrado")
    
    # Verificar arquivos importantes
    arquivos_esperados = [
        'views/__init__.py',
        'services/__init__.py',
        'forms/__init__.py',
        'decorators.py',
    ]
    
    for arquivo in arquivos_esperados:
        arquivo_path = os.path.join(notas_path, arquivo)
        if os.path.exists(arquivo_path):
            print(f"[OK] Arquivo {arquivo} existe")
        else:
            print(f"[ERRO] Arquivo {arquivo} nao encontrado")
            erros.append(f"Arquivo {arquivo} nao encontrado")
    
    return erros


def test_services():
    """Testa se os serviços têm os métodos esperados"""
    print("\n=== TESTE 3: SERVIÇOS ===")
    erros = []
    
    from notas.services import RomaneioService, NotaFiscalService, CalculoService, ValidacaoService
    
    # Testar RomaneioService
    metodos_esperados = [
        'criar_romaneio',
        'editar_romaneio',
        'excluir_romaneio',
        'calcular_totais_romaneio',
        'obter_notas_disponiveis_para_cliente',
    ]
    
    for metodo in metodos_esperados:
        if hasattr(RomaneioService, metodo):
            print(f"[OK] RomaneioService.{metodo} existe")
        else:
            print(f"[ERRO] RomaneioService.{metodo} nao encontrado")
            erros.append(f"RomaneioService.{metodo}")
    
    # Testar outros serviços
    if hasattr(NotaFiscalService, 'criar_nota_fiscal'):
        print("[OK] NotaFiscalService tem metodos esperados")
    else:
        erros.append("NotaFiscalService")
    
    if hasattr(CalculoService, 'calcular_seguro_por_estado'):
        print("[OK] CalculoService tem metodos esperados")
    else:
        erros.append("CalculoService")
    
    if hasattr(ValidacaoService, 'validar_cnpj'):
        print("[OK] ValidacaoService tem metodos esperados")
    else:
        erros.append("ValidacaoService")
    
    return erros


def test_urls():
    """Testa se as URLs estão configuradas"""
    print("\n=== TESTE 4: URLS ===")
    erros = []
    
    try:
        from notas import urls
        total_urls = len(urls.urlpatterns)
        print(f"[OK] {total_urls} URLs configuradas")
        
        if total_urls < 50:
            print(f"[AVISO] Esperado mais URLs (encontrado {total_urls})")
    except Exception as e:
        print(f"[ERRO] Erro ao verificar URLs: {e}")
        erros.append(f"URLs: {e}")
    
    return erros


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("VALIDACAO DA REFATORACAO - FASE 2")
    print("=" * 60)
    
    todos_erros = []
    
    # Executar testes
    erros = test_imports()
    todos_erros.extend(erros)
    
    erros = test_structure()
    todos_erros.extend(erros)
    
    erros = test_services()
    todos_erros.extend(erros)
    
    erros = test_urls()
    todos_erros.extend(erros)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    if todos_erros:
        print(f"[ERRO] {len(todos_erros)} problema(s) encontrado(s):")
        for erro in todos_erros:
            print(f"  - {erro}")
        return 1
    else:
        print("[OK] Todos os testes passaram!")
        print("\nEstrutura de refatoracao validada com sucesso!")
        return 0


if __name__ == '__main__':
    sys.exit(main())


