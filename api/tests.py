"""
Testes da API REST (Fase 6) – pelo menos um recurso exposto e documentação.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from notas.models import Cliente, Usuario


class ClienteAPITestCase(TestCase):
    """Testes do endpoint GET /api/v1/clientes/."""

    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(
            username='apiuser',
            password='senha123',
            email='api@teste.local',
            first_name='Api',
            last_name='User',
            tipo_usuario='admin',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.cliente = Cliente.objects.create(
            razao_social='EMPRESA TESTE API LTDA',
            nome_fantasia='Teste API',
            cnpj='00.000.000/0001-00',
            cidade='São Paulo',
            estado='SP',
            status='Ativo',
        )

    def test_list_clientes_requer_autenticacao(self):
        """Sem token, listagem retorna 401."""
        self.client.credentials()
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_clientes_com_token(self):
        """Com token, listagem retorna 200 e lista de clientes."""
        response = self.client.get(reverse('cliente-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreaterEqual(len(response.data['results']), 1)
        razoes = [c['razao_social'] for c in response.data['results']]
        self.assertIn(self.cliente.razao_social, razoes)

    def test_retrieve_cliente(self):
        """Detalhe de um cliente retorna 200 e dados corretos."""
        url = reverse('cliente-detail', args=[self.cliente.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['razao_social'], self.cliente.razao_social)
        self.assertEqual(response.data['cnpj'], self.cliente.cnpj)
        self.assertEqual(response.data['status'], 'Ativo')

    def test_search_clientes(self):
        """Parâmetro search filtra por razao_social, nome_fantasia, cnpj, cidade."""
        response = self.client.get(reverse('cliente-list'), {'search': 'TESTE API'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
