"""
Testes unitários dos serviços do financeiro (acerto diário, período, movimento de caixa).
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from notas.models import Cliente
from financeiro.models import (
    AcertoDiarioCarregamento,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
)
from financeiro.services import (
    AcertoDiarioService,
    PeriodoCaixaService,
    MovimentoCaixaService,
)

User = get_user_model()


class PeriodoCaixaServiceTest(TestCase):
    """Testes do PeriodoCaixaService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='teste', email='teste@test.com', password='teste123'
        )

    def test_obter_periodo_aberto_retorna_none_quando_nao_ha_periodo(self):
        self.assertIsNone(PeriodoCaixaService.obter_periodo_aberto())

    def test_obter_periodo_aberto_retorna_periodo_quando_existe_aberto(self):
        periodo = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('100.00'),
            status='Aberto',
            usuario_criacao=self.user,
        )
        self.assertEqual(
            PeriodoCaixaService.obter_periodo_aberto(),
            periodo,
        )

    def test_iniciar_periodo_sem_data_retorna_erro(self):
        periodo, erro = PeriodoCaixaService.iniciar_periodo(
            data_inicio='',
            valor_inicial_caixa=Decimal('0'),
            observacoes='',
            usuario=self.user,
        )
        self.assertIsNone(periodo)
        self.assertIn('obrigatória', erro)

    def test_iniciar_periodo_com_data_cria_periodo(self):
        periodo, erro = PeriodoCaixaService.iniciar_periodo(
            data_inicio='2025-01-01',
            valor_inicial_caixa=Decimal('500.00'),
            observacoes='Teste',
            usuario=self.user,
        )
        self.assertIsNone(erro)
        self.assertIsNotNone(periodo)
        self.assertEqual(periodo.status, 'Aberto')
        self.assertEqual(periodo.valor_inicial_caixa, Decimal('500.00'))

    def test_iniciar_segundo_periodo_retorna_erro_se_ja_existe_aberto(self):
        PeriodoCaixaService.iniciar_periodo(
            data_inicio='2025-01-01',
            valor_inicial_caixa=Decimal('0'),
            observacoes='',
            usuario=self.user,
        )
        periodo2, erro = PeriodoCaixaService.iniciar_periodo(
            data_inicio='2025-01-02',
            valor_inicial_caixa=Decimal('0'),
            observacoes='',
            usuario=self.user,
        )
        self.assertIsNone(periodo2)
        self.assertIn('Já existe um período aberto', erro)

    def test_fechar_periodo_altera_status(self):
        p = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('0'),
            status='Aberto',
            usuario_criacao=self.user,
        )
        ok, erro = PeriodoCaixaService.fechar_periodo(p)
        self.assertIsNone(erro)
        self.assertTrue(ok)
        p.refresh_from_db()
        self.assertEqual(p.status, 'Fechado')

    def test_fechar_periodo_ja_fechado_retorna_erro(self):
        p = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('0'),
            status='Fechado',
            usuario_criacao=self.user,
        )
        ok, erro = PeriodoCaixaService.fechar_periodo(p)
        self.assertFalse(ok)
        self.assertIn('já está fechado', erro)

    def test_excluir_periodo_remove_periodo_e_retorna_quantidade_movimentos(self):
        p = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('0'),
            status='Aberto',
            usuario_criacao=self.user,
        )
        count, erro = PeriodoCaixaService.excluir_periodo(p)
        self.assertIsNone(erro)
        self.assertEqual(count, 0)
        self.assertFalse(PeriodoMovimentoCaixa.objects.filter(pk=p.pk).exists())


class MovimentoCaixaServiceTest(TestCase):
    """Testes do MovimentoCaixaService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testemov', email='mov@test.com', password='teste123'
        )
        self.periodo = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('100.00'),
            status='Aberto',
            usuario_criacao=self.user,
        )

    def test_validar_dados_movimento_rejeita_valor_zero(self):
        ok, err = MovimentoCaixaService.validar_dados_movimento(
            data='2025-01-01', tipo='Entrada', valor=Decimal('0')
        )
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_criar_movimento_sem_periodo_retorna_erro(self):
        PeriodoMovimentoCaixa.objects.filter(pk=self.periodo.pk).update(status='Fechado')
        movimento, erro = MovimentoCaixaService.criar_movimento(
            data='2025-01-01',
            tipo='Entrada',
            valor=Decimal('50.00'),
            descricao='Teste',
            categoria='Outros',
            funcionario_id=None,
            cliente_id=None,
            acerto_diario_id=None,
            usuario=self.user,
        )
        self.assertIsNone(movimento)
        self.assertIn('período', erro)

    def test_criar_movimento_com_periodo_aberto_cria_registro(self):
        movimento, erro = MovimentoCaixaService.criar_movimento(
            data='2025-01-01',
            tipo='Entrada',
            valor=Decimal('50.00'),
            descricao='Teste',
            categoria='Outros',
            funcionario_id=None,
            cliente_id=None,
            acerto_diario_id=None,
            usuario=self.user,
        )
        self.assertIsNone(erro)
        self.assertIsNotNone(movimento)
        self.assertEqual(movimento.valor, Decimal('50.00'))
        self.assertEqual(movimento.periodo_id, self.periodo.pk)

    def test_obter_acumulado_funcionario_sem_registro_retorna_zero(self):
        func = FuncionarioFluxoCaixa.objects.create(nome='Func Teste', ativo=True)
        valor = MovimentoCaixaService.obter_acumulado_funcionario(func.pk)
        self.assertEqual(valor, Decimal('0.00'))


class AcertoDiarioServiceTest(TestCase):
    """Testes do AcertoDiarioService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testeacerto', email='acerto@test.com', password='teste123'
        )
        self.periodo = PeriodoMovimentoCaixa.objects.create(
            data_inicio=date(2025, 1, 1),
            valor_inicial_caixa=Decimal('0'),
            status='Aberto',
            usuario_criacao=self.user,
        )

    def test_salvar_acerto_sem_periodo_retorna_erro(self):
        PeriodoMovimentoCaixa.objects.filter(pk=self.periodo.pk).update(status='Fechado')
        acerto, erro = AcertoDiarioService.salvar_acerto_e_criar_movimentos(
            data=date(2025, 1, 1),
            observacoes='',
            usuario=self.user,
        )
        self.assertIsNone(acerto)
        self.assertIn('período', erro)

    def test_salvar_acerto_com_periodo_cria_acerto_e_movimentos_vazios(self):
        acerto, erro = AcertoDiarioService.salvar_acerto_e_criar_movimentos(
            data=date(2025, 1, 1),
            observacoes='Teste',
            usuario=self.user,
        )
        self.assertIsNone(erro)
        self.assertIsNotNone(acerto)
        self.assertEqual(acerto.data, date(2025, 1, 1))
        self.assertEqual(MovimentoCaixa.objects.filter(acerto_diario=acerto).count(), 0)
