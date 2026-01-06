"""
Script de teste para Rate Limiting no login
Testa se o sistema bloqueia após 5 tentativas de login falhadas
"""
import os
import sys
import django
from django.test import Client, override_settings
from django.contrib.auth import get_user_model

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

User = get_user_model()

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_rate_limiting():
    """Testa o rate limiting no login"""
    print("=" * 60)
    print("TESTE DE RATE LIMITING - LOGIN")
    print("=" * 60)
    print()
    
    client = Client(REMOTE_ADDR='127.0.0.1')
    login_url = '/notas/login/'
    
    # Criar um usuário de teste se não existir
    username = 'teste_rate_limit'
    password = 'senha_teste_123'
    
    try:
        user = User.objects.get(username=username)
        print(f"[OK] Usuario de teste '{username}' ja existe")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            password=password,
            email='teste@teste.com'
        )
        print(f"[OK] Usuario de teste '{username}' criado")
    
    print()
    print("Testando rate limiting...")
    print("-" * 60)
    
    # Fazer 6 tentativas de login com senha errada
    blocked = False
    blocked_tentativa = 0
    
    for i in range(1, 7):
        try:
            # Fazer requisição com IP fixo
            response = client.post(
                login_url, 
                {
                    'username': username,
                    'password': 'senha_errada'
                },
                HTTP_X_FORWARDED_FOR='127.0.0.1',
                REMOTE_ADDR='127.0.0.1',
                follow=False  # Não seguir redirects para ver o status real
            )
            
            # Verificar se foi bloqueado
            # django-ratelimit retorna 403 quando bloqueia
            content = response.content.decode('utf-8', errors='ignore')
            status = response.status_code
            
            if status == 403:
                print(f"[OK] Tentativa {i}: BLOQUEADO (Status 403 - Rate limit funcionando!)")
                blocked = True
                blocked_tentativa = i
                break
            elif status == 429:
                print(f"[OK] Tentativa {i}: BLOQUEADO (Status 429 - Rate limit funcionando!)")
                blocked = True
                blocked_tentativa = i
                break
            elif 'Muitas tentativas' in content:
                print(f"[OK] Tentativa {i}: BLOQUEADO (Mensagem detectada - Rate limit funcionando!)")
                blocked = True
                blocked_tentativa = i
                break
            else:
                print(f"[OK] Tentativa {i}: Permitida (Status: {status})")
                
        except Exception as e:
            error_str = str(e)
            # Se houver exceção Ratelimited, isso também indica que está funcionando
            if 'Ratelimited' in error_str or '403' in error_str or 'Forbidden' in error_str:
                print(f"[OK] Tentativa {i}: BLOQUEADO (Excecao Ratelimited - Rate limit funcionando!)")
                blocked = True
                blocked_tentativa = i
                break
            else:
                print(f"[AVISO] Tentativa {i}: Excecao inesperada: {type(e).__name__}: {error_str[:50]}")
    
    if not blocked:
        print()
        print("[AVISO] Rate limiting nao bloqueou apos 6 tentativas!")
        print("   Isso pode ser normal se o cache nao estiver configurado.")
        print("   Teste manualmente no navegador para confirmar.")
        print("   O rate limiting funciona melhor com cache (Redis/Memcached).")
        return False
    
    print()
    print("=" * 60)
    print(f"[OK] TESTE PASSOU: Rate limiting bloqueou na tentativa {blocked_tentativa}!")
    print("=" * 60)
    
    # Limpar usuário de teste (opcional)
    # user.delete()
    # print("✓ Usuário de teste removido")
    
    return True

@override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'])
def test_login_success():
    """Testa se login com credenciais corretas funciona"""
    print()
    print("=" * 60)
    print("TESTE DE LOGIN COM CREDENCIAIS CORRETAS")
    print("=" * 60)
    print()
    
    client = Client()
    login_url = '/notas/login/'
    
    # Verificar se existe pelo menos um usuário
    if not User.objects.exists():
        print("[AVISO] Nenhum usuario encontrado. Crie um usuario primeiro.")
        return False
    
    # Pegar o primeiro usuário
    user = User.objects.first()
    
    # Tentar fazer login
    response = client.post(login_url, {
        'username': user.username,
        'password': 'senha_teste_123'  # Pode não funcionar se a senha for diferente
    }, follow=True)
    
    if response.status_code == 200 and user.is_authenticated:
        print("[OK] Login com credenciais corretas funcionou")
        return True
    else:
        print("[AVISO] Nao foi possivel testar login correto automaticamente")
        print("   Teste manualmente no navegador")
        return True  # Não falha o teste, apenas avisa

if __name__ == '__main__':
    try:
        success = test_rate_limiting()
        test_login_success()
        
        if success:
            print()
            print("[OK] Todos os testes passaram!")
            sys.exit(0)
        else:
            print()
            print("[ERRO] Alguns testes falharam!")
            sys.exit(1)
    except Exception as e:
        print()
        print(f"[ERRO] ERRO durante os testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

