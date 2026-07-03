"""
=============================================================================
Modelos do Financeiro V2 (Onda 1 - Fundação)
=============================================================================

Conceitos centrais (ver docs/PROPOSTA_FINANCEIRO_V2.md):

- Carteira: lugar físico onde o dinheiro está (Dinheiro, Banco).
- Bolso: etiqueta lógica sobre o saldo (Operacional, Estelar, Documentação,
  Fundo Gás dos chapas - este último com eh_terceiro=True).
- Lancamento: cada entrada/saída numa carteira, vinculada a um bolso.

Entidades existentes (Cliente, CobrancaCarregamento, AcumuladoFuncionario,
FuncionarioFluxoCaixa, etc.) NÃO são duplicadas - são referenciadas via FK.

Versão: 1.0 (Onda 1)
=============================================================================
"""
from decimal import Decimal

from django.conf import settings
from django.db import models


class Carteira(models.Model):
    """
    Lugar físico onde o dinheiro está.

    Implantação inicial cria 2 registros: Dinheiro (caixa físico) e Banco
    (conta corrente / PIX). Saldo atual = saldo_inicial + soma dos lançamentos.

    Campos Principais:
        - codigo: identificador interno único (DINHEIRO, BANCO).
        - nome: rótulo exibido nas telas.
        - saldo_inicial: saldo conhecido na data de implantação.
        - data_saldo_inicial: a partir desta data os lançamentos são somados.
        - ativa: permite "desligar" uma carteira sem apagar o histórico.
    """

    CODIGO_CHOICES = [
        ('DINHEIRO', 'Dinheiro (caixa físico)'),
        ('BANCO', 'Banco (conta corrente / PIX)'),
    ]

    codigo = models.CharField(
        max_length=20, unique=True, choices=CODIGO_CHOICES, verbose_name="Código"
    )
    nome = models.CharField(max_length=80, verbose_name="Nome")
    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Saldo Inicial (R$)",
        help_text="Saldo conhecido no dia da implantação. Lançamentos somam a partir daí.",
    )
    data_saldo_inicial = models.DateField(
        null=True, blank=True, verbose_name="Data do Saldo Inicial"
    )
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carteira"
        verbose_name_plural = "Carteiras"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def saldo_atual(self):
        """Calcula o saldo atual = saldo_inicial + entradas - saídas."""
        from django.db.models import Sum, Q

        agg = self.lancamentos.aggregate(
            entradas=Sum('valor', filter=Q(tipo='Entrada')),
            saidas=Sum('valor', filter=Q(tipo='Saida')),
        )
        entradas = agg['entradas'] or Decimal('0.00')
        saidas = agg['saidas'] or Decimal('0.00')
        return (self.saldo_inicial or Decimal('0.00')) + entradas - saidas


class Bolso(models.Model):
    """
    Etiqueta lógica sobre o saldo.

    A empresa opera com 4 bolsos: Operacional, Estelar, Documentação e
    Fundo Gás. O Fundo Gás tem eh_terceiro=True (dinheiro físico que não
    pertence à empresa, é dos chapas).

    Saldo do bolso = soma das entradas - soma das saídas em lançamentos
    desse bolso. Não há "saldo inicial" porque o bolso é apenas uma
    classificação - quando a empresa começar a usar, fica em zero e
    cresce conforme as operações.
    """

    CODIGO_CHOICES = [
        ('OPERACIONAL', 'Operacional'),
        ('ESTELAR', 'Estelar'),
        ('DOCUMENTACAO', 'Documentação'),
        ('FUNDO_GAS', 'Fundo Gás (Chapas)'),
    ]

    codigo = models.CharField(
        max_length=30, unique=True, choices=CODIGO_CHOICES, verbose_name="Código"
    )
    nome = models.CharField(max_length=80, verbose_name="Nome")
    eh_terceiro = models.BooleanField(
        default=False,
        verbose_name="É de terceiros?",
        help_text="Marca dinheiro que está fisicamente no caixa mas não é da empresa.",
    )
    ordem = models.PositiveSmallIntegerField(default=0, verbose_name="Ordem de exibição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bolso"
        verbose_name_plural = "Bolsos"
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome

    def saldo_atual(self):
        """Calcula o saldo do bolso = entradas - saídas."""
        from django.db.models import Sum, Q

        agg = self.lancamentos.aggregate(
            entradas=Sum('valor', filter=Q(tipo='Entrada')),
            saidas=Sum('valor', filter=Q(tipo='Saida')),
        )
        entradas = agg['entradas'] or Decimal('0.00')
        saidas = agg['saidas'] or Decimal('0.00')
        return entradas - saidas


class Lancamento(models.Model):
    """
    Entrada ou saída em uma carteira, vinculada a um bolso.

    Toda movimentação financeira no V2 passa por aqui: recebimento de
    cobrança, pagamento de chapa, despesa avulsa, distribuição aos
    gerentes, lançamento manual, etc.

    Vínculos opcionais (cliente, funcionário, cobrança) servem para
    rastrear a origem do lançamento e construir telas como o Extrato
    do Cliente e o A Receber/A Pagar.
    """

    TIPO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Saida', 'Saída'),
    ]

    data = models.DateField(verbose_name="Data")
    carteira = models.ForeignKey(
        Carteira,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name="Carteira",
    )
    bolso = models.ForeignKey(
        Bolso,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        verbose_name="Bolso",
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    categoria = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name="Categoria",
        help_text="Categoria livre, ex.: 'Xerox', 'Material', 'Acerto chapa'.",
    )

    cliente = models.ForeignKey(
        'notas.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_v2',
        verbose_name="Cliente",
    )
    funcionario = models.ForeignKey(
        'financeiro.FuncionarioFluxoCaixa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_v2',
        verbose_name="Funcionário",
    )
    cobranca_carregamento = models.ForeignKey(
        'notas.CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_v2',
        verbose_name="Cobrança de Carregamento",
    )
    cobranca_cte_avulsa = models.ForeignKey(
        'notas.CobrancaCTEAvulsa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_v2',
        verbose_name="Cobrança CTE Avulsa",
    )
    acerto_diario = models.ForeignKey(
        'financeiro.AcertoDiarioCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_v2',
        verbose_name="Acerto Diário",
        help_text="Lançamentos gerados pelo Acerto Diário V2 (idempotência).",
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lancamentos_v2_criados',
        verbose_name="Usuário que criou",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lançamento (V2)"
        verbose_name_plural = "Lançamentos (V2)"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data']),
            models.Index(fields=['carteira', 'data']),
            models.Index(fields=['bolso']),
            models.Index(fields=['cliente']),
            models.Index(fields=['funcionario']),
            models.Index(fields=['acerto_diario']),
        ]

    def __str__(self):
        sinal = '+' if self.tipo == 'Entrada' else '-'
        return f"{self.data:%d/%m} {sinal} R$ {self.valor} ({self.descricao[:30]})"

    @property
    def valor_signado(self):
        return self.valor if self.tipo == 'Entrada' else -self.valor
