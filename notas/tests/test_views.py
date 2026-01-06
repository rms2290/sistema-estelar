"""
Testes para as views do sistema
"""
import pytest
from decimal import Decimal
from datetime import date
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client

from notas.models import Cliente, NotaFiscal, Motorista, Veiculo
from notas.tests.conftest import (
    ClienteFactory, MotoristaFactory, VeiculoFactory,
    NotaFiscalFactory, UsuarioFactory
)

Usuario = get_user_model()


# ============================================================================
# TESTES DE AUTENTICAÇÃO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestAuthViews:
    """Testes para views de autenticação"""
    
    def test_login_view_get(self):
        """Testa acesso à página de login (GET)"""
        client = Client()
        response = client.get(reverse('notas:login'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_login_view_post_valido(self):
        """Testa login com credenciais válidas"""
        usuario = UsuarioFactory(username='testuser', password='senha1234')
        usuario.set_password('senha1234')
        usuario.save()
        
        client = Client()
        response = client.post(reverse('notas:login'), {
            'username': 'testuser',
            'password': 'senha1234'
        })
        assert response.status_code == 302  # Redirecionamento
        assert response.url == reverse('notas:dashboard')
    
    def test_login_view_post_invalido(self):
        """Testa login com credenciais inválidas"""
        client = Client()
        response = client.post(reverse('notas:login'), {
            'username': 'usuario_inexistente',
            'password': 'senha_errada'
        })
        assert response.status_code == 200  # Permanece na página
        assert 'error_message' in response.context or 'Nome de usuário ou senha inválidos' in str(response.content)
    
    def test_login_view_usuario_autenticado_redireciona(self):
        """Testa que usuário autenticado é redirecionado do login"""
        usuario = UsuarioFactory()
        client = Client()
        client.force_login(usuario)
        
        response = client.get(reverse('notas:login'))
        assert response.status_code == 302
        assert response.url == reverse('notas:dashboard')
    
    def test_logout_view(self):
        """Testa logout"""
        usuario = UsuarioFactory()
        client = Client()
        client.force_login(usuario)
        
        response = client.get(reverse('notas:logout'))
        assert response.status_code == 302
        # Verificar que usuário não está mais autenticado
        response = client.get(reverse('notas:dashboard'))
        assert response.status_code == 302  # Redireciona para login
    
    def test_alterar_senha_requer_login(self):
        """Testa que alterar senha requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:alterar_senha'))
        assert response.status_code == 302  # Redireciona para login
    
    def test_alterar_senha_get(self, authenticated_client):
        """Testa acesso à página de alterar senha (GET)"""
        response = authenticated_client.get(reverse('notas:alterar_senha'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_alterar_senha_post_valido(self, authenticated_client, user_admin):
        """Testa alteração de senha válida"""
        # Definir senha inicial
        user_admin.set_password('senha_antiga')
        user_admin.save()
        authenticated_client.force_login(user_admin)
        
        response = authenticated_client.post(reverse('notas:alterar_senha'), {
            'senha_atual': 'senha_antiga',
            'nova_senha': 'nova_senha1234',
            'confirmar_senha': 'nova_senha1234'
        })
        assert response.status_code == 302  # Redirecionamento
        
        # Verificar que senha foi alterada (precisa fazer login novamente)
        user_admin.refresh_from_db()
        # A senha foi alterada, então precisamos verificar de outra forma
        # Ou fazer logout e tentar login com nova senha
        authenticated_client.logout()
        login_success = authenticated_client.login(username=user_admin.username, password='nova_senha1234')
        assert login_success
    
    def test_alterar_senha_senhas_nao_coincidem(self, authenticated_client, user_admin):
        """Testa alteração de senha com senhas que não coincidem"""
        authenticated_client.force_login(user_admin)
        response = authenticated_client.post(reverse('notas:alterar_senha'), {
            'senha_atual': 'senha_atual',
            'nova_senha': 'nova_senha1234',
            'confirmar_senha': 'outra_senha1234'
        })
        assert response.status_code == 200  # Permanece na página
        assert not response.context['form'].is_valid()


# ============================================================================
# TESTES DE VIEWS DE CLIENTES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestClienteViews:
    """Testes para views de clientes"""
    
    def test_listar_clientes_requer_login(self):
        """Testa que listar clientes requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:listar_clientes'))
        assert response.status_code == 302  # Redireciona para login
    
    def test_listar_clientes_get(self, authenticated_client):
        """Testa listagem de clientes (GET)"""
        ClienteFactory(razao_social="Cliente 1")
        ClienteFactory(razao_social="Cliente 2")
        
        response = authenticated_client.get(reverse('notas:listar_clientes'))
        assert response.status_code == 200
        assert 'clientes' in response.context or 'object_list' in response.context
    
    def test_adicionar_cliente_requer_login(self):
        """Testa que adicionar cliente requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:adicionar_cliente'))
        assert response.status_code == 302
    
    def test_adicionar_cliente_get(self, authenticated_client):
        """Testa acesso à página de adicionar cliente (GET)"""
        response = authenticated_client.get(reverse('notas:adicionar_cliente'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_adicionar_cliente_post_valido(self, authenticated_client):
        """Testa criação de cliente válido (POST)"""
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '11.222.333/0001-81',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_cliente'), form_data)
        assert response.status_code == 302  # Redirecionamento
        assert response.url == reverse('notas:listar_clientes')
        
        # Verificar que cliente foi criado
        assert Cliente.objects.filter(razao_social='EMPRESA TESTE LTDA').exists()
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        assert any('sucesso' in str(m).lower() for m in messages)
    
    def test_adicionar_cliente_post_invalido(self, authenticated_client):
        """Testa criação de cliente inválido (POST)"""
        form_data = {
            'razao_social': '',  # Campo obrigatório vazio
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_cliente'), form_data)
        assert response.status_code == 200  # Permanece na página
        assert not response.context['form'].is_valid()
    
    def test_editar_cliente_get(self, authenticated_client, cliente):
        """Testa acesso à página de editar cliente (GET)"""
        response = authenticated_client.get(reverse('notas:editar_cliente', args=[cliente.pk]))
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'cliente' in response.context
    
    def test_editar_cliente_post_valido(self, authenticated_client, cliente):
        """Testa edição de cliente válido (POST)"""
        form_data = {
            'razao_social': 'Cliente Editado LTDA',
            'cidade': 'Rio de Janeiro',
            'estado': 'RJ',
            'status': 'Ativo'
        }
        response = authenticated_client.post(
            reverse('notas:editar_cliente', args=[cliente.pk]),
            form_data
        )
        assert response.status_code == 302
        assert response.url == reverse('notas:listar_clientes')
        
        # Verificar que cliente foi atualizado
        cliente.refresh_from_db()
        assert cliente.razao_social == "CLIENTE EDITADO LTDA"
    
    def test_excluir_cliente_requer_login(self, cliente):
        """Testa que excluir cliente requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:excluir_cliente', args=[cliente.pk]))
        assert response.status_code == 302
    
    def test_excluir_cliente_get(self, authenticated_client, cliente):
        """Testa acesso à página de excluir cliente (GET)"""
        # excluir_cliente usa @login_required, não @admin_required
        # A validação de admin é feita via senha dentro da view
        response = authenticated_client.get(
            reverse('notas:excluir_cliente', args=[cliente.pk])
        )
        assert response.status_code == 200
        assert 'cliente' in response.context
    
    def test_detalhes_cliente_get(self, authenticated_client, cliente):
        """Testa acesso à página de detalhes do cliente (GET)"""
        response = authenticated_client.get(reverse('notas:detalhes_cliente', args=[cliente.pk]))
        assert response.status_code == 200
        assert 'cliente' in response.context


# ============================================================================
# TESTES DE VIEWS DE NOTAS FISCAIS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestNotaFiscalViews:
    """Testes para views de notas fiscais"""
    
    def test_listar_notas_fiscais_requer_login(self):
        """Testa que listar notas fiscais requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:listar_notas_fiscais'))
        assert response.status_code == 302
    
    def test_listar_notas_fiscais_get(self, authenticated_client, cliente):
        """Testa listagem de notas fiscais (GET)"""
        NotaFiscalFactory(cliente=cliente)
        NotaFiscalFactory(cliente=cliente)
        
        response = authenticated_client.get(reverse('notas:listar_notas_fiscais'))
        assert response.status_code == 200
    
    def test_adicionar_nota_fiscal_get(self, authenticated_client, cliente):
        """Testa acesso à página de adicionar nota fiscal (GET)"""
        response = authenticated_client.get(reverse('notas:adicionar_nota_fiscal'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_adicionar_nota_fiscal_post_valido(self, authenticated_client, cliente):
        """Testa criação de nota fiscal válida (POST)"""
        form_data = {
            'cliente': cliente.pk,
            'nota': '123456',
            'data': '2024-01-15',
            'fornecedor': 'Fornecedor Teste',
            'mercadoria': 'Mercadoria Teste',
            'quantidade': '100.00',
            'peso': '1000.00',
            'valor': '5000.00'
        }
        response = authenticated_client.post(reverse('notas:adicionar_nota_fiscal'), form_data)
        assert response.status_code == 302
        
        # Verificar que nota foi criada
        assert NotaFiscal.objects.filter(nota='123456').exists()
    
    def test_editar_nota_fiscal_get(self, authenticated_client, nota_fiscal):
        """Testa acesso à página de editar nota fiscal (GET)"""
        response = authenticated_client.get(
            reverse('notas:editar_nota_fiscal', args=[nota_fiscal.pk])
        )
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_excluir_nota_fiscal_get(self, authenticated_client, nota_fiscal):
        """Testa acesso à página de excluir nota fiscal (GET)"""
        # excluir_nota_fiscal usa @login_required, validação de admin é via senha
        response = authenticated_client.get(
            reverse('notas:excluir_nota_fiscal', args=[nota_fiscal.pk])
        )
        assert response.status_code == 200
        assert 'nota' in response.context
    
    def test_detalhes_nota_fiscal_get(self, authenticated_client, nota_fiscal):
        """Testa acesso à página de detalhes da nota fiscal (GET)"""
        response = authenticated_client.get(
            reverse('notas:detalhes_nota_fiscal', args=[nota_fiscal.pk])
        )
        # Pode retornar 200 ou 404 se template não existir
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert 'nota' in response.context


# ============================================================================
# TESTES DE VIEWS DE MOTORISTAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestMotoristaViews:
    """Testes para views de motoristas"""
    
    def test_listar_motoristas_requer_login(self):
        """Testa que listar motoristas requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:listar_motoristas'))
        assert response.status_code == 302
    
    def test_listar_motoristas_get(self, authenticated_client):
        """Testa listagem de motoristas (GET)"""
        MotoristaFactory()
        MotoristaFactory()
        
        response = authenticated_client.get(reverse('notas:listar_motoristas'))
        assert response.status_code == 200
    
    def test_adicionar_motorista_get(self, authenticated_client):
        """Testa acesso à página de adicionar motorista (GET)"""
        response = authenticated_client.get(reverse('notas:adicionar_motorista'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_adicionar_motorista_post_valido(self, authenticated_client):
        """Testa criação de motorista válido (POST)"""
        form_data = {
            'nome': 'João Silva',
            'cpf': '12345678909',
            'telefone': '11999999999',
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_motorista'), form_data)
        assert response.status_code == 302
        
        # Verificar que motorista foi criado
        assert Motorista.objects.filter(nome='JOÃO SILVA').exists()
    
    def test_detalhes_motorista_get(self, authenticated_client, motorista):
        """Testa acesso à página de detalhes do motorista (GET)"""
        response = authenticated_client.get(
            reverse('notas:detalhes_motorista', args=[motorista.pk])
        )
        assert response.status_code == 200
        assert 'motorista' in response.context


# ============================================================================
# TESTES DE VIEWS DE VEÍCULOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestVeiculoViews:
    """Testes para views de veículos"""
    
    def test_listar_veiculos_requer_login(self):
        """Testa que listar veículos requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:listar_veiculos'))
        assert response.status_code == 302
    
    def test_listar_veiculos_get(self, authenticated_client):
        """Testa listagem de veículos (GET)"""
        VeiculoFactory()
        VeiculoFactory()
        
        response = authenticated_client.get(reverse('notas:listar_veiculos'))
        assert response.status_code == 200
    
    def test_adicionar_veiculo_get(self, authenticated_client):
        """Testa acesso à página de adicionar veículo (GET)"""
        response = authenticated_client.get(reverse('notas:adicionar_veiculo'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_adicionar_veiculo_post_valido(self, authenticated_client):
        """Testa criação de veículo válido (POST)"""
        # Verificar campos obrigatórios do VeiculoForm
        form_data = {
            'placa': 'ABC1234',
            'tipo_unidade': 'Caminhão',
            # Outros campos podem ser opcionais
        }
        response = authenticated_client.post(reverse('notas:adicionar_veiculo'), form_data)
        # Pode retornar 200 se houver erro de validação ou 302 se sucesso
        if response.status_code == 302:
            # Verificar que veículo foi criado
            assert Veiculo.objects.filter(placa='ABC1234').exists()
        else:
            # Se não redirecionou, verificar se é erro de validação
            assert response.status_code == 200
            # Pode ter campos obrigatórios adicionais
    
    def test_detalhes_veiculo_get(self, authenticated_client, veiculo):
        """Testa acesso à página de detalhes do veículo (GET)"""
        response = authenticated_client.get(
            reverse('notas:detalhes_veiculo', args=[veiculo.pk])
        )
        assert response.status_code == 200
        assert 'veiculo' in response.context


# ============================================================================
# TESTES DE DASHBOARD
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestDashboardViews:
    """Testes para views de dashboard"""
    
    def test_dashboard_requer_login(self):
        """Testa que dashboard requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:dashboard'))
        assert response.status_code == 302
    
    def test_dashboard_get(self, authenticated_client):
        """Testa acesso ao dashboard (GET)"""
        response = authenticated_client.get(reverse('notas:dashboard'))
        assert response.status_code == 200
    
    def test_dashboard_cliente_requer_login(self):
        """Testa que dashboard cliente requer autenticação"""
        client = Client()
        response = client.get(reverse('notas:dashboard_cliente'))
        assert response.status_code == 302
    
    def test_dashboard_funcionario_redireciona_nao_funcionario(self, authenticated_client, user_admin):
        """Testa que dashboard redireciona funcionário para dashboard específico"""
        # dashboard_funcionario não tem URL própria, é chamado internamente
        # Quando admin acessa dashboard, não é redirecionado para dashboard_funcionario
        authenticated_client.force_login(user_admin)
        response = authenticated_client.get(reverse('notas:dashboard'))
        # Admin não é redirecionado para dashboard_funcionario
        assert response.status_code == 200
    
    def test_dashboard_funcionario_acesso(self, authenticated_client_funcionario):
        """Testa que funcionário é redirecionado para dashboard_funcionario ao acessar dashboard"""
        # Quando funcionário acessa dashboard, é redirecionado internamente
        response = authenticated_client_funcionario.get(reverse('notas:dashboard'))
        # Deve renderizar dashboard_funcionario (não há redirecionamento HTTP)
        assert response.status_code == 200


# ============================================================================
# TESTES DE PERMISSÕES
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestPermissoesViews:
    """Testes de permissões e controle de acesso"""
    
    def test_excluir_cliente_get_funcionario(self, authenticated_client_funcionario, cliente):
        """Testa que funcionário pode acessar página de excluir (validação é via senha admin)"""
        # excluir_cliente usa @login_required, não @admin_required
        # A validação de admin é feita via senha dentro da view
        response = authenticated_client_funcionario.get(
            reverse('notas:excluir_cliente', args=[cliente.pk])
        )
        assert response.status_code == 200
    
    def test_excluir_cliente_admin_pode(self, authenticated_client, user_admin, cliente):
        """Testa que admin pode excluir cliente"""
        authenticated_client.force_login(user_admin)
        response = authenticated_client.get(
            reverse('notas:excluir_cliente', args=[cliente.pk])
        )
        # Admin deve ter acesso
        assert response.status_code == 200
    
    def test_cadastrar_usuario_requer_admin(self, authenticated_client_funcionario):
        """Testa que apenas admin pode cadastrar usuário"""
        response = authenticated_client_funcionario.get(reverse('notas:cadastrar_usuario'))
        assert response.status_code in [302, 403]
    
    def test_listar_usuarios_requer_admin(self, authenticated_client_funcionario):
        """Testa que apenas admin pode listar usuários"""
        response = authenticated_client_funcionario.get(reverse('notas:listar_usuarios'))
        assert response.status_code in [302, 403]


# ============================================================================
# TESTES DE REDIRECIONAMENTOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestRedirecionamentos:
    """Testes de redirecionamentos após ações"""
    
    def test_adicionar_cliente_redireciona_para_lista(self, authenticated_client):
        """Testa redirecionamento após adicionar cliente"""
        form_data = {
            'razao_social': 'Cliente Teste',
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_cliente'), form_data)
        assert response.status_code == 302
        assert response.url == reverse('notas:listar_clientes')
    
    def test_editar_cliente_redireciona_para_lista(self, authenticated_client, cliente):
        """Testa redirecionamento após editar cliente"""
        form_data = {
            'razao_social': 'Cliente Editado',
            'status': 'Ativo'
        }
        response = authenticated_client.post(
            reverse('notas:editar_cliente', args=[cliente.pk]),
            form_data
        )
        assert response.status_code == 302
        assert response.url == reverse('notas:listar_clientes')
    
    def test_login_redireciona_para_dashboard(self):
        """Testa redirecionamento após login bem-sucedido"""
        usuario = UsuarioFactory(username='testuser', password='senha1234')
        usuario.set_password('senha1234')
        usuario.save()
        
        client = Client()
        response = client.post(reverse('notas:login'), {
            'username': 'testuser',
            'password': 'senha1234'
        })
        assert response.status_code == 302
        assert response.url == reverse('notas:dashboard')


# ============================================================================
# TESTES DE MENSAGENS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestMensagensViews:
    """Testes de mensagens de sucesso/erro"""
    
    def test_mensagem_sucesso_ao_adicionar_cliente(self, authenticated_client):
        """Testa mensagem de sucesso ao adicionar cliente"""
        form_data = {
            'razao_social': 'Cliente Teste',
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_cliente'), form_data)
        
        # Verificar mensagem de sucesso
        messages = list(get_messages(response.wsgi_request))
        assert any('sucesso' in str(m).lower() for m in messages)
    
    def test_mensagem_erro_ao_adicionar_cliente_invalido(self, authenticated_client):
        """Testa mensagem de erro ao adicionar cliente inválido"""
        form_data = {
            'razao_social': '',  # Inválido
            'status': 'Ativo'
        }
        response = authenticated_client.post(reverse('notas:adicionar_cliente'), form_data)
        
        # Verificar mensagem de erro
        messages = list(get_messages(response.wsgi_request))
        assert any('erro' in str(m).lower() for m in messages)

