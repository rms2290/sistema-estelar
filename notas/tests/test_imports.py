"""
Testes básicos para validar imports após refatoração
"""
from django.test import TestCase


class TestImports(TestCase):
    """Testa se todos os imports estão funcionando corretamente"""
    
    def test_views_imports(self):
        """Testa imports das views modulares"""
        from notas.views import (
            dashboard, login_view, logout_view,
            listar_clientes, adicionar_cliente,
            listar_motoristas, adicionar_motorista,
            listar_veiculos, adicionar_veiculo,
            listar_notas_fiscais, adicionar_nota_fiscal,
            listar_romaneios, adicionar_romaneio,
            cobranca_carregamento,
            listar_logs_auditoria, totalizador_por_estado,
        )
        self.assertTrue(True)  # Se chegou aqui, imports funcionaram
    
    def test_services_imports(self):
        """Testa imports dos serviços"""
        from notas.services import (
            RomaneioService,
            NotaFiscalService,
            CalculoService,
            ValidacaoService,
        )
        self.assertTrue(True)
    
    def test_forms_imports(self):
        """Testa imports dos formulários modulares"""
        from notas.forms import (
            ClienteForm, ClienteSearchForm,
            NotaFiscalForm, NotaFiscalSearchForm,
            LoginForm, CadastroUsuarioForm,
            MotoristaForm, RomaneioViagemForm,
        )
        self.assertTrue(True)
    
    def test_utils_imports(self):
        """Testa imports dos utilitários"""
        from notas.utils import (
            formatar_valor_brasileiro,
            formatar_peso_brasileiro,
            validar_cnpj,
            validar_cpf,
        )
        self.assertTrue(True)
    
    def test_decorators_imports(self):
        """Testa imports dos decorators"""
        from notas.decorators import (
            admin_required,
            funcionario_required,
            cliente_required,
        )
        self.assertTrue(True)


