"""
Configuração global de testes e fixtures compartilhadas
"""
import pytest
import random
import string
from django.contrib.auth import get_user_model
from django.test import Client
from factory import Faker, SubFactory, LazyAttribute, Sequence
from factory.django import DjangoModelFactory
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, 
    RomaneioViagem, TabelaSeguro, AgendaEntrega
)

Usuario = get_user_model()


# ============================================================================
# FACTORIES - Para criar objetos de teste facilmente
# ============================================================================

class UsuarioFactory(DjangoModelFactory):
    """Factory para criar usuários de teste"""
    class Meta:
        model = Usuario
        django_get_or_create = ('username',)
    
    username = Faker('user_name')
    email = Faker('email')
    password = 'testpass123'
    tipo_usuario = 'admin'
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override para usar set_password corretamente"""
        password = kwargs.pop('password', None)
        user = super()._create(model_class, *args, **kwargs)
        if password:
            user.set_password(password)
            user.save()
        return user


class ClienteFactory(DjangoModelFactory):
    """Factory para criar clientes de teste"""
    class Meta:
        model = Cliente
        django_get_or_create = ('razao_social',)
    
    razao_social = Faker('company', locale='pt_BR')
    cnpj = Faker('numerify', text='##############')  # CNPJ único para cada teste
    nome_fantasia = Faker('company', locale='pt_BR')
    cidade = Faker('city', locale='pt_BR')
    estado = 'SP'
    status = 'Ativo'


class MotoristaFactory(DjangoModelFactory):
    """Factory para criar motoristas de teste"""
    class Meta:
        model = Motorista
        django_get_or_create = ('cpf',)
    
    nome = Faker('name', locale='pt_BR')
    cpf = Faker('numerify', text='###########')  # CPF único para cada teste
    rg = Faker('numerify', text='########')
    cnh = Faker('numerify', text='###########')
    telefone = Faker('phone_number', locale='pt_BR')


class VeiculoFactory(DjangoModelFactory):
    """Factory para criar veículos de teste"""
    class Meta:
        model = Veiculo
        django_get_or_create = ('placa',)
    
    placa = Sequence(lambda n: f"{''.join(random.choices(string.ascii_uppercase, k=3))}{random.randint(1000, 9999)}")
    tipo_unidade = 'Caminhão'
    marca = Faker('company', locale='pt_BR')
    modelo = Faker('word', locale='pt_BR')
    ano_fabricacao = 2020


class TabelaSeguroFactory(DjangoModelFactory):
    """Factory para criar tabelas de seguro de teste"""
    class Meta:
        model = TabelaSeguro
        django_get_or_create = ('estado',)
    
    estado = 'SP'
    percentual_seguro = Decimal('2.50')


class NotaFiscalFactory(DjangoModelFactory):
    """Factory para criar notas fiscais de teste"""
    class Meta:
        model = NotaFiscal
    
    cliente = SubFactory(ClienteFactory)
    nota = Faker('numerify', text='########')
    data = date.today()
    fornecedor = Faker('company', locale='pt_BR')
    mercadoria = Faker('word', locale='pt_BR')
    quantidade = Decimal('100.00')
    peso = Decimal('1000.00')
    valor = Decimal('5000.00')
    status = 'Depósito'


class RomaneioViagemFactory(DjangoModelFactory):
    """Factory para criar romaneios de teste"""
    class Meta:
        model = RomaneioViagem
    
    cliente = SubFactory(ClienteFactory)
    motorista = SubFactory(MotoristaFactory)
    veiculo_principal = SubFactory(VeiculoFactory)
    data_saida = LazyAttribute(lambda obj: timezone.now())
    data_chegada_prevista = LazyAttribute(lambda obj: timezone.now() + timedelta(days=1))
    status = 'Salvo'


# ============================================================================
# FIXTURES - Para uso em testes
# ============================================================================

@pytest.fixture
def user_admin(db):
    """Cria um usuário administrador"""
    return UsuarioFactory(tipo_usuario='admin', username='admin_test')


@pytest.fixture
def user_funcionario(db):
    """Cria um usuário funcionário"""
    return UsuarioFactory(tipo_usuario='funcionario', username='func_test')


@pytest.fixture
def user_cliente(db):
    """Cria um usuário cliente"""
    return UsuarioFactory(tipo_usuario='cliente', username='cliente_test')


@pytest.fixture
def cliente(db):
    """Cria um cliente de teste"""
    return ClienteFactory()


@pytest.fixture
def motorista(db):
    """Cria um motorista de teste"""
    return MotoristaFactory()


@pytest.fixture
def veiculo(db):
    """Cria um veículo de teste"""
    return VeiculoFactory()


@pytest.fixture
def nota_fiscal(db, cliente):
    """Cria uma nota fiscal de teste"""
    return NotaFiscalFactory(cliente=cliente)


@pytest.fixture
def romaneio(db, cliente, motorista, veiculo):
    """Cria um romaneio de teste"""
    return RomaneioViagemFactory(
        cliente=cliente,
        motorista=motorista,
        veiculo_principal=veiculo
    )


@pytest.fixture
def tabela_seguro(db):
    """Cria uma tabela de seguro de teste"""
    return TabelaSeguroFactory()


@pytest.fixture
def client():
    """Retorna um cliente HTTP de teste"""
    return Client()


@pytest.fixture
def authenticated_client(client, user_admin):
    """Retorna um cliente HTTP autenticado como admin"""
    client.force_login(user_admin)
    return client


@pytest.fixture
def authenticated_client_funcionario(client, user_funcionario):
    """Retorna um cliente HTTP autenticado como funcionário"""
    client.force_login(user_funcionario)
    return client


@pytest.fixture
def authenticated_client_cliente(client, user_cliente):
    """Retorna um cliente HTTP autenticado como cliente"""
    client.force_login(user_cliente)
    return client


# ============================================================================
# HELPERS - Funções auxiliares para testes
# ============================================================================

def criar_cliente_completo(**kwargs):
    """Helper para criar um cliente completo com todos os campos"""
    defaults = {
        'razao_social': 'Cliente Teste LTDA',
        'cnpj': '12345678000190',
        'nome_fantasia': 'Cliente Teste',
        'cidade': 'São Paulo',
        'estado': 'SP',
        'status': 'Ativo',
    }
    defaults.update(kwargs)
    return ClienteFactory(**defaults)


def criar_romaneio_completo(cliente=None, motorista=None, veiculo=None, **kwargs):
    """Helper para criar um romaneio completo"""
    if not cliente:
        cliente = ClienteFactory()
    if not motorista:
        motorista = MotoristaFactory()
    if not veiculo:
        veiculo = VeiculoFactory()
    
    defaults = {
        'cliente': cliente,
        'motorista': motorista,
        'veiculo_principal': veiculo,
        'data_saida': timezone.now(),
        'status': 'Salvo',
    }
    defaults.update(kwargs)
    return RomaneioViagemFactory(**defaults)

