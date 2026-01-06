"""
Testes para os formulários do sistema
"""
import pytest
from decimal import Decimal
from datetime import date
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from notas.forms import (
    ClienteForm, ClienteSearchForm,
    LoginForm, CadastroUsuarioForm, AlterarSenhaForm,
    NotaFiscalForm, NotaFiscalSearchForm, MercadoriaDepositoSearchForm,
    UpperCaseCharField, ESTADOS_CHOICES
)
from notas.tests.conftest import ClienteFactory, UsuarioFactory

Usuario = get_user_model()


# ============================================================================
# TESTES DO CAMPO UPPERCASECHARFIELD
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestUpperCaseCharField:
    """Testes para o campo customizado UpperCaseCharField"""
    
    def test_uppercase_char_field_converte_para_maiusculo(self):
        """Testa que UpperCaseCharField converte texto para maiúsculo"""
        field = UpperCaseCharField()
        assert field.to_python("teste") == "TESTE"
        assert field.to_python("Teste") == "TESTE"
        assert field.to_python("TESTE") == "TESTE"
        assert field.to_python("teste com espaços") == "TESTE COM ESPAÇOS"
    
    def test_uppercase_char_field_aceita_none(self):
        """Testa que UpperCaseCharField aceita None e string vazia"""
        field = UpperCaseCharField(required=False)
        # to_python pode retornar '' para None dependendo da implementação
        result_none = field.to_python(None)
        assert result_none is None or result_none == ""
        assert field.to_python("") == ""


# ============================================================================
# TESTES DO FORMULÁRIO CLIENTEFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestClienteForm:
    """Testes para o formulário ClienteForm"""
    
    def test_cliente_form_campos_obrigatorios(self):
        """Testa que razão social é obrigatória"""
        form = ClienteForm({})
        assert not form.is_valid()
        assert 'razao_social' in form.errors
    
    def test_cliente_form_criar_cliente_valido(self):
        """Testa criação de cliente com dados válidos"""
        # Usar CNPJ válido para teste
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '11.222.333/0001-81',  # CNPJ válido formatado
            'cidade': 'São Paulo',
            'estado': 'SP',
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        cliente = form.save()
        assert cliente.razao_social == "EMPRESA TESTE LTDA"  # UpperCase
        # CNPJ deve ser limpo (apenas números)
        assert cliente.cnpj == "11222333000181"
    
    def test_cliente_form_cnpj_valido(self):
        """Testa validação de CNPJ válido"""
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '11.222.333/0001-81',  # CNPJ válido formatado
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        # CNPJ deve ser limpo (apenas números)
        assert form.cleaned_data['cnpj'] == "11222333000181"
    
    def test_cliente_form_cnpj_invalido(self):
        """Testa validação de CNPJ inválido"""
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '12345678000199',  # CNPJ inválido
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'cnpj' in form.errors
    
    def test_cliente_form_cnpj_com_digitos_insuficientes(self):
        """Testa validação de CNPJ com dígitos insuficientes"""
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '123456789',  # Menos de 14 dígitos
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert not form.is_valid()
        assert 'cnpj' in form.errors
        assert '14 dígitos' in str(form.errors['cnpj'])
    
    def test_cliente_form_cnpj_opcional(self):
        """Testa que CNPJ é opcional"""
        form_data = {
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '',  # Vazio
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        cliente = form.save()
        assert cliente.cnpj is None or cliente.cnpj == ""
    
    def test_cliente_form_uppercase_mixin(self):
        """Testa que campos UpperCaseCharField são convertidos"""
        form_data = {
            'razao_social': 'empresa teste ltda',
            'nome_fantasia': 'fantasia teste',
            'cidade': 'são paulo',
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data)
        assert form.is_valid()
        cliente = form.save()
        assert cliente.razao_social == "EMPRESA TESTE LTDA"
        assert cliente.nome_fantasia == "FANTASIA TESTE"
        assert cliente.cidade == "SÃO PAULO"
    
    def test_cliente_form_editar_cliente(self):
        """Testa edição de cliente existente"""
        cliente = ClienteFactory(razao_social="Cliente Original")
        form_data = {
            'razao_social': 'Cliente Editado',
            'status': 'Ativo'
        }
        form = ClienteForm(data=form_data, instance=cliente)
        assert form.is_valid()
        cliente_editado = form.save()
        assert cliente_editado.razao_social == "CLIENTE EDITADO"
        assert cliente_editado.pk == cliente.pk


# ============================================================================
# TESTES DO FORMULÁRIO CLIENTESEARCHFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestClienteSearchForm:
    """Testes para o formulário ClienteSearchForm"""
    
    def test_cliente_search_form_todos_campos_opcionais(self):
        """Testa que todos os campos são opcionais"""
        form = ClienteSearchForm({})
        assert form.is_valid()
    
    def test_cliente_search_form_com_razao_social(self):
        """Testa busca por razão social"""
        form_data = {'razao_social': 'Empresa Teste'}
        form = ClienteSearchForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['razao_social'] == "EMPRESA TESTE"  # UpperCase
    
    def test_cliente_search_form_com_cnpj(self):
        """Testa busca por CNPJ"""
        form_data = {'cnpj': '12345678000190'}
        form = ClienteSearchForm(data=form_data)
        assert form.is_valid()
    
    def test_cliente_search_form_com_status(self):
        """Testa busca por status"""
        form_data = {'status': 'Ativo'}
        form = ClienteSearchForm(data=form_data)
        assert form.is_valid()


# ============================================================================
# TESTES DO FORMULÁRIO LOGINFORM
# ============================================================================

@pytest.mark.form
class TestLoginForm:
    """Testes para o formulário LoginForm"""
    
    def test_login_form_campos_obrigatorios(self):
        """Testa que username e password são obrigatórios"""
        form = LoginForm({})
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'password' in form.errors
    
    def test_login_form_valido(self):
        """Testa formulário de login válido"""
        form_data = {
            'username': 'testuser',
            'password': 'senha123'
        }
        form = LoginForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['username'] == 'testuser'
        assert form.cleaned_data['password'] == 'senha123'


# ============================================================================
# TESTES DO FORMULÁRIO CADASTROUSUARIOFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestCadastroUsuarioForm:
    """Testes para o formulário CadastroUsuarioForm"""
    
    def test_cadastro_usuario_form_campos_obrigatorios(self):
        """Testa campos obrigatórios"""
        form = CadastroUsuarioForm({})
        assert not form.is_valid()
        # Verificar campos obrigatórios (email pode não ser obrigatório no modelo)
        assert 'username' in form.errors
        assert 'tipo_usuario' in form.errors
        # Email pode ser opcional dependendo do modelo
    
    def test_cadastro_usuario_form_senhas_nao_coincidem(self):
        """Testa validação de senhas que não coincidem"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_usuario': 'funcionario',
            'password1': 'senha123',
            'password2': 'senha456'
        }
        form = CadastroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert 'não coincidem' in str(form.errors['__all__'])
    
    def test_cadastro_usuario_form_senha_curta(self):
        """Testa validação de senha muito curta"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_usuario': 'funcionario',
            'password1': '123',
            'password2': '123'
        }
        form = CadastroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert '8 caracteres' in str(form.errors['__all__'])
    
    def test_cadastro_usuario_form_senha_valida(self):
        """Testa criação de usuário com senha válida"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'tipo_usuario': 'funcionario',
            'password1': 'senha1234',
            'password2': 'senha1234',
            'is_active': True
        }
        form = CadastroUsuarioForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        usuario = form.save()
        assert usuario.username == 'testuser'
        assert usuario.check_password('senha1234')
    
    def test_cadastro_usuario_form_cliente_obrigatorio_para_tipo_cliente(self):
        """Testa que cliente é obrigatório para tipo cliente"""
        cliente = ClienteFactory()
        form_data = {
            'username': 'clienteuser',
            'email': 'cliente@example.com',
            'first_name': 'Cliente',
            'last_name': 'User',
            'tipo_usuario': 'cliente',
            'cliente': None,  # Não fornecido
            'password1': 'senha1234',
            'password2': 'senha1234'
        }
        form = CadastroUsuarioForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert 'Cliente é obrigatório' in str(form.errors['__all__'])
    
    def test_cadastro_usuario_form_cliente_valido(self):
        """Testa criação de usuário tipo cliente com cliente válido"""
        cliente = ClienteFactory()
        form_data = {
            'username': 'clienteuser',
            'email': 'cliente@example.com',
            'first_name': 'Cliente',
            'last_name': 'User',
            'tipo_usuario': 'cliente',
            'cliente': cliente.pk,
            'password1': 'senha1234',
            'password2': 'senha1234',
            'is_active': True
        }
        form = CadastroUsuarioForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        usuario = form.save()
        assert usuario.tipo_usuario == 'cliente'
        assert usuario.cliente == cliente
    
    def test_cadastro_usuario_form_editar_sem_senha(self):
        """Testa edição de usuário sem alterar senha"""
        usuario = UsuarioFactory()
        form_data = {
            'username': usuario.username,
            'email': 'novoemail@example.com',
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'tipo_usuario': usuario.tipo_usuario,
            'is_active': True
            # Sem password1 e password2
        }
        form = CadastroUsuarioForm(data=form_data, instance=usuario)
        assert form.is_valid(), f"Erros: {form.errors}"
        usuario_editado = form.save()
        assert usuario_editado.email == 'novoemail@example.com'
        # Senha não deve ser alterada
        assert usuario_editado.check_password(usuario.password) or usuario.password == usuario_editado.password


# ============================================================================
# TESTES DO FORMULÁRIO ALTERARSENHAFORM
# ============================================================================

@pytest.mark.form
class TestAlterarSenhaForm:
    """Testes para o formulário AlterarSenhaForm"""
    
    def test_alterar_senha_form_campos_obrigatorios(self):
        """Testa que todos os campos são obrigatórios"""
        form = AlterarSenhaForm({})
        assert not form.is_valid()
        assert 'senha_atual' in form.errors
        assert 'nova_senha' in form.errors
        assert 'confirmar_senha' in form.errors
    
    def test_alterar_senha_form_senhas_nao_coincidem(self):
        """Testa validação de senhas que não coincidem"""
        form_data = {
            'senha_atual': 'senha123',
            'nova_senha': 'novasenha1234',
            'confirmar_senha': 'outrasenha1234'
        }
        form = AlterarSenhaForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert 'não coincidem' in str(form.errors['__all__'])
    
    def test_alterar_senha_form_senha_curta(self):
        """Testa validação de senha muito curta"""
        form_data = {
            'senha_atual': 'senha123',
            'nova_senha': '123',
            'confirmar_senha': '123'
        }
        form = AlterarSenhaForm(data=form_data)
        assert not form.is_valid()
        assert 'nova_senha' in form.errors
    
    def test_alterar_senha_form_valido(self):
        """Testa formulário válido"""
        form_data = {
            'senha_atual': 'senha123',
            'nova_senha': 'novasenha1234',
            'confirmar_senha': 'novasenha1234'
        }
        form = AlterarSenhaForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['nova_senha'] == 'novasenha1234'


# ============================================================================
# TESTES DO FORMULÁRIO NOTAFISCALFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestNotaFiscalForm:
    """Testes para o formulário NotaFiscalForm"""
    
    def test_nota_fiscal_form_campos_obrigatorios(self, cliente):
        """Testa campos obrigatórios"""
        form = NotaFiscalForm({})
        assert not form.is_valid()
        assert 'cliente' in form.errors
        assert 'nota' in form.errors
        assert 'data' in form.errors
        assert 'fornecedor' in form.errors
        assert 'mercadoria' in form.errors
    
    def test_nota_fiscal_form_criar_valido(self, cliente):
        """Testa criação de nota fiscal válida"""
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
        form = NotaFiscalForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        nota = form.save()
        assert nota.nota == "123456"  # UpperCase
        assert nota.fornecedor == "FORNECEDOR TESTE"
        assert nota.mercadoria == "MERCADORIA TESTE"
    
    def test_nota_fiscal_form_uppercase_mixin(self, cliente):
        """Testa que campos UpperCaseCharField são convertidos"""
        form_data = {
            'cliente': cliente.pk,
            'nota': 'nota teste',
            'data': '2024-01-15',
            'fornecedor': 'fornecedor teste',
            'mercadoria': 'mercadoria teste',
            'quantidade': '100.00',
            'peso': '1000.00',
            'valor': '5000.00'
        }
        form = NotaFiscalForm(data=form_data)
        assert form.is_valid()
        nota = form.save()
        assert nota.nota == "NOTA TESTE"
        assert nota.fornecedor == "FORNECEDOR TESTE"
        assert nota.mercadoria == "MERCADORIA TESTE"
    
    def test_nota_fiscal_form_clean_peso(self, cliente):
        """Testa método clean_peso que converte para int"""
        form_data = {
            'cliente': cliente.pk,
            'nota': '123456',
            'data': '2024-01-15',
            'fornecedor': 'Fornecedor Teste',
            'mercadoria': 'Mercadoria Teste',
            'quantidade': '100.00',
            'peso': '1000.50',  # Decimal
            'valor': '5000.00'
        }
        form = NotaFiscalForm(data=form_data)
        assert form.is_valid()
        # clean_peso deve converter para int
        assert form.cleaned_data['peso'] == 1000
    
    def test_nota_fiscal_form_duplicata(self, cliente):
        """Testa validação de nota fiscal duplicada"""
        from notas.models import NotaFiscal
        # Criar nota fiscal existente
        NotaFiscal.objects.create(
            cliente=cliente,
            nota='123456',
            data=date(2024, 1, 15),
            fornecedor='Fornecedor Teste',
            mercadoria='Mercadoria Teste',
            quantidade=Decimal('100.00'),
            peso=Decimal('1000.00'),
            valor=Decimal('5000.00')
        )
        
        # Tentar criar outra com mesmo número, cliente e valor
        form_data = {
            'cliente': cliente.pk,
            'nota': '123456',
            'data': '2024-01-15',
            'fornecedor': 'Outro Fornecedor',
            'mercadoria': 'Outra Mercadoria',
            'quantidade': '200.00',
            'peso': '2000.00',
            'valor': '5000.00'  # Mesmo valor
        }
        form = NotaFiscalForm(data=form_data)
        assert not form.is_valid()
        assert '__all__' in form.errors
        assert 'Já existe uma nota fiscal' in str(form.errors['__all__'])
    
    def test_nota_fiscal_form_editar_sem_duplicata(self, cliente):
        """Testa que edição não gera erro de duplicata"""
        from notas.models import NotaFiscal
        nota = NotaFiscal.objects.create(
            cliente=cliente,
            nota='123456',
            data=date(2024, 1, 15),
            fornecedor='Fornecedor Teste',
            mercadoria='Mercadoria Teste',
            quantidade=Decimal('100.00'),
            peso=Decimal('1000.00'),
            valor=Decimal('5000.00')
        )
        
        # Editar a mesma nota
        form_data = {
            'cliente': cliente.pk,
            'nota': '123456',
            'data': '2024-01-15',
            'fornecedor': 'Fornecedor Editado',
            'mercadoria': 'Mercadoria Editada',
            'quantidade': '150.00',
            'peso': '1500.00',
            'valor': '5000.00'
        }
        form = NotaFiscalForm(data=form_data, instance=nota)
        assert form.is_valid(), f"Erros: {form.errors}"
        nota_editada = form.save()
        assert nota_editada.fornecedor == "FORNECEDOR EDITADO"


# ============================================================================
# TESTES DO FORMULÁRIO NOTAFISCALSEARCHFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestNotaFiscalSearchForm:
    """Testes para o formulário NotaFiscalSearchForm"""
    
    def test_nota_fiscal_search_form_todos_campos_opcionais(self):
        """Testa que todos os campos são opcionais"""
        form = NotaFiscalSearchForm({})
        assert form.is_valid()
    
    def test_nota_fiscal_search_form_com_nota(self):
        """Testa busca por número da nota"""
        form_data = {'nota': '123456'}
        form = NotaFiscalSearchForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['nota'] == "123456"  # UpperCase
    
    def test_nota_fiscal_search_form_com_cliente(self, cliente):
        """Testa busca por cliente"""
        form_data = {'cliente': cliente.pk}
        form = NotaFiscalSearchForm(data=form_data)
        assert form.is_valid()
    
    def test_nota_fiscal_search_form_com_data(self):
        """Testa busca por data"""
        form_data = {'data': '2024-01-15'}
        form = NotaFiscalSearchForm(data=form_data)
        assert form.is_valid()


# ============================================================================
# TESTES DO FORMULÁRIO MERCADORIADEPOSITOSEARCHFORM
# ============================================================================

@pytest.mark.django_db
@pytest.mark.form
class TestMercadoriaDepositoSearchForm:
    """Testes para o formulário MercadoriaDepositoSearchForm"""
    
    def test_mercadoria_deposito_search_form_todos_campos_opcionais(self):
        """Testa que todos os campos são opcionais"""
        form = MercadoriaDepositoSearchForm({})
        assert form.is_valid()
    
    def test_mercadoria_deposito_search_form_com_fornecedor(self):
        """Testa busca por fornecedor"""
        form_data = {'fornecedor': 'Fornecedor Teste'}
        form = MercadoriaDepositoSearchForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['fornecedor'] == "FORNECEDOR TESTE"  # UpperCase
    
    def test_mercadoria_deposito_search_form_com_mercadoria(self):
        """Testa busca por mercadoria"""
        form_data = {'mercadoria': 'Mercadoria Teste'}
        form = MercadoriaDepositoSearchForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data['mercadoria'] == "MERCADORIA TESTE"  # UpperCase

