"""
Testes para validar estrutura de views após refatoração
"""
from django.test import TestCase
from django.urls import reverse, resolve
from notas import urls


class TestURLsStructure(TestCase):
    """Testa se todas as URLs estão configuradas corretamente"""
    
    def test_urls_count(self):
        """Testa se há URLs configuradas"""
        self.assertGreater(len(urls.urlpatterns), 0)
    
    def test_dashboard_url(self):
        """Testa URL do dashboard"""
        url = reverse('notas:dashboard')
        self.assertEqual(url, '/notas/')
    
    def test_login_url(self):
        """Testa URL de login"""
        url = reverse('notas:login')
        self.assertEqual(url, '/notas/login/')
    
    def test_clientes_urls(self):
        """Testa URLs de clientes"""
        url = reverse('notas:listar_clientes')
        self.assertEqual(url, '/notas/clientes/')
    
    def test_romaneios_urls(self):
        """Testa URLs de romaneios"""
        url = reverse('notas:listar_romaneios')
        self.assertEqual(url, '/notas/romaneios/')


class TestViewsExist(TestCase):
    """Testa se todas as views principais existem"""
    
    def test_auth_views_exist(self):
        """Testa se views de autenticação existem"""
        from notas.views import login_view, logout_view, alterar_senha
        self.assertTrue(callable(login_view))
        self.assertTrue(callable(logout_view))
        self.assertTrue(callable(alterar_senha))
    
    def test_cliente_views_exist(self):
        """Testa se views de clientes existem"""
        from notas.views import (
            listar_clientes, adicionar_cliente,
            editar_cliente, excluir_cliente
        )
        self.assertTrue(callable(listar_clientes))
        self.assertTrue(callable(adicionar_cliente))
    
    def test_romaneio_views_exist(self):
        """Testa se views de romaneios existem"""
        from notas.views import (
            listar_romaneios, adicionar_romaneio,
            editar_romaneio, excluir_romaneio
        )
        self.assertTrue(callable(listar_romaneios))
        self.assertTrue(callable(adicionar_romaneio))


