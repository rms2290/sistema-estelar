"""
Modelos do app Financeiro (fluxo de caixa, receitas, movimentos bancários, etc.)
Depende de: notas (Usuario, Cliente, CobrancaCarregamento)
"""
import re

from django.db import models
from django.conf import settings
from django.utils import timezone

from notas.models import UpperCaseMixin


class FuncionarioFluxoCaixa(UpperCaseMixin, models.Model):
    """Modelo simples para funcionários do fluxo de caixa (apenas nome)"""

    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Funcionário")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Funcionário (Fluxo de Caixa)"
        verbose_name_plural = "Funcionários (Fluxo de Caixa)"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class AcertoDiarioCarregamento(UpperCaseMixin, models.Model):
    """Registra o acerto diário de carregamentos"""

    data = models.DateField(verbose_name="Data", unique=True)
    valor_estelar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Estelar (R$)"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='acertos_diarios_criados'
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Acerto Diário de Carregamento"
        verbose_name_plural = "Acertos Diários de Carregamento"
        ordering = ['-data']
        indexes = [
            models.Index(fields=['data']),
        ]

    @property
    def total_carregamentos(self):
        from django.db.models import Sum
        from decimal import Decimal
        return self.carregamentos_cliente.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    @property
    def total_funcionarios(self):
        from django.db.models import Sum
        from decimal import Decimal
        return self.distribuicoes_funcionario.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    @property
    def total_distribuido(self):
        return self.valor_estelar + self.total_funcionarios

    @property
    def diferenca(self):
        """Diferença entre total de carregamentos e total distribuído (Estelar + funcionários)."""
        from decimal import Decimal
        return (self.total_carregamentos - self.total_distribuido).quantize(Decimal('0.01'))

    def __str__(self):
        return f"Acerto - {self.data}"


class CarregamentoCliente(UpperCaseMixin, models.Model):
    """Valores de carregamento por cliente ou descarga no acerto diário"""

    acerto_diario = models.ForeignKey(
        AcertoDiarioCarregamento,
        on_delete=models.CASCADE,
        related_name='carregamentos_cliente',
        verbose_name="Acerto Diário"
    )
    cliente = models.ForeignKey(
        'notas.Cliente',
        on_delete=models.PROTECT,
        related_name='carregamentos_diarios',
        verbose_name="Cliente",
        null=True,
        blank=True,
        help_text="Deixe em branco para registrar uma descarga"
    )
    cobranca_carregamento = models.ForeignKey(
        'notas.CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carregamentos_acerto',
        verbose_name="Cobrança de Carregamento",
        help_text="Vincule quando o carregamento vier de uma cobrança"
    )
    descricao = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição da descarga (quando não houver cliente)"
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    observacoes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observações")

    TIPO_PAGAMENTO_CHOICES = [
        ('Dinheiro', 'Dinheiro'),
        ('Deposito', 'Depósito'),
    ]
    tipo_pagamento = models.CharField(
        max_length=10,
        choices=TIPO_PAGAMENTO_CHOICES,
        default='Dinheiro',
        blank=True,
        null=True,
        verbose_name="Tipo de Pagamento",
        help_text="Apenas para descargas. Se for depósito, não será contabilizado no movimento de caixa."
    )

    class Meta:
        verbose_name = "Carregamento/Descarga"
        verbose_name_plural = "Carregamentos e Descargas"
        ordering = ['cliente__razao_social', 'descricao']

    @property
    def tipo(self):
        return "Descarga" if not self.cliente else "Carregamento"

    @property
    def nome_display(self):
        if self.cliente:
            return self.cliente.razao_social
        return self.descricao or "Descarga"

    def __str__(self):
        nome = self.nome_display
        return f"{nome} - R$ {self.valor}"


class DistribuicaoFuncionario(UpperCaseMixin, models.Model):
    """Distribuição de valores para funcionários no acerto diário"""

    acerto_diario = models.ForeignKey(
        AcertoDiarioCarregamento,
        on_delete=models.CASCADE,
        related_name='distribuicoes_funcionario',
        verbose_name="Acerto Diário"
    )
    funcionario = models.ForeignKey(
        FuncionarioFluxoCaixa,
        on_delete=models.PROTECT,
        related_name='distribuicoes',
        verbose_name="Funcionário"
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")

    class Meta:
        verbose_name = "Distribuição para Funcionário"
        verbose_name_plural = "Distribuições para Funcionários"
        unique_together = [['acerto_diario', 'funcionario']]
        ordering = ['funcionario__nome']

    def __str__(self):
        return f"{self.funcionario.nome} - R$ {self.valor}"


class AcumuladoFuncionario(UpperCaseMixin, models.Model):
    """Acumulado semanal de valores para cada funcionário"""

    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Depositado', 'Depositado'),
    ]

    funcionario = models.ForeignKey(
        FuncionarioFluxoCaixa,
        on_delete=models.PROTECT,
        related_name='acumulados',
        verbose_name="Funcionário"
    )
    semana_inicio = models.DateField(verbose_name="Início da Semana")
    semana_fim = models.DateField(verbose_name="Fim da Semana")
    valor_acumulado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Acumulado (R$)"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendente',
        verbose_name="Status"
    )
    data_deposito = models.DateField(blank=True, null=True, verbose_name="Data do Depósito")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Acumulado de Funcionário"
        verbose_name_plural = "Acumulados de Funcionários"
        ordering = ['-semana_inicio', 'funcionario']
        unique_together = [['funcionario', 'semana_inicio', 'semana_fim']]
        indexes = [
            models.Index(fields=['funcionario', 'status']),
            models.Index(fields=['semana_inicio', 'semana_fim']),
        ]

    def calcular_acumulado(self):
        from django.db.models import Sum
        from decimal import Decimal
        acertos = AcertoDiarioCarregamento.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        )
        self.valor_acumulado = DistribuicaoFuncionario.objects.filter(
            acerto_diario__in=acertos,
            funcionario=self.funcionario
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        self.save()
        return self.valor_acumulado

    def marcar_depositado(self, data_deposito=None):
        self.status = 'Depositado'
        self.data_deposito = data_deposito or timezone.now().date()
        self.save()

    def __str__(self):
        return f"{self.funcionario.nome} - Semana {self.semana_inicio} a {self.semana_fim} - R$ {self.valor_acumulado}"


class ReceitaEmpresa(UpperCaseMixin, models.Model):
    """Registra receitas arrecadadas pela empresa"""

    TIPO_RECEITA_CHOICES = [
        ('Estelar', 'Estelar'),
        ('CTE', 'CTE'),
        ('Manifesto', 'Manifesto'),
        ('Manutencao', 'Manutenção'),
        ('Outro', 'Outro'),
    ]

    data = models.DateField(verbose_name="Data")
    tipo_receita = models.CharField(max_length=20, choices=TIPO_RECEITA_CHOICES, verbose_name="Tipo de Receita")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    cobranca_carregamento = models.ForeignKey(
        'notas.CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas_empresa',
        verbose_name="Cobrança de Carregamento",
        help_text="Opcional: vincular a uma cobrança de carregamento"
    )
    cliente = models.ForeignKey(
        'notas.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas_empresa',
        verbose_name="Cliente"
    )
    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='receitas_criadas'
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Receita da Empresa"
        verbose_name_plural = "Receitas da Empresa"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo_receita']),
            models.Index(fields=['cobranca_carregamento']),
        ]

    def __str__(self):
        return f"{self.get_tipo_receita_display()} - R$ {self.valor} - {self.data}"


class SetorBancario(models.Model):
    """Dados bancários de cada setor da empresa (Carregamento, Armazenagem)."""

    SETOR_CHOICES = [
        ('Armazenagem', 'Armazenagem'),
        ('Carregamento', 'Carregamento'),
    ]
    TIPO_CHAVE_PIX_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
        ('Email', 'Email'),
        ('Telefone', 'Telefone'),
        ('Chave Aleatória', 'Chave Aleatória'),
    ]

    setor = models.CharField(max_length=20, choices=SETOR_CHOICES, unique=True, verbose_name="Setor")
    nome_responsavel = models.CharField(max_length=255, verbose_name="Nome do Responsável/Beneficiário")
    banco = models.CharField(max_length=100, verbose_name="Banco")
    agencia = models.CharField(max_length=20, verbose_name="Agência")
    conta_corrente = models.CharField(max_length=20, verbose_name="Conta Corrente")
    chave_pix = models.CharField(max_length=255, verbose_name="Chave PIX")
    tipo_chave_pix = models.CharField(
        max_length=50,
        choices=TIPO_CHAVE_PIX_CHOICES,
        verbose_name="Tipo de Chave PIX"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Dados Bancários do Setor"
        verbose_name_plural = "Dados Bancários dos Setores"
        ordering = ['setor']

    def __str__(self):
        return f"{self.get_setor_display()} - {self.nome_responsavel}"

    def get_chave_pix_formatada(self):
        tipo_formatado = self.get_tipo_chave_pix_display().lower()
        return f"{self.chave_pix} ({tipo_formatado})"


class CaixaFuncionario(UpperCaseMixin, models.Model):
    """Controla valores coletados pelos funcionários (diário ou semanal)"""

    PERIODO_CHOICES = [
        ('Diario', 'Diário'),
        ('Semanal', 'Semanal'),
    ]
    STATUS_CHOICES = [
        ('Em_Aberto', 'Em Aberto'),
        ('Acertado', 'Acertado'),
    ]

    funcionario = models.ForeignKey(
        FuncionarioFluxoCaixa,
        on_delete=models.PROTECT,
        related_name='caixas_funcionario',
        verbose_name="Funcionário"
    )
    periodo_tipo = models.CharField(
        max_length=10,
        choices=PERIODO_CHOICES,
        default='Semanal',
        verbose_name="Tipo de Período"
    )
    semana_inicio = models.DateField(blank=True, null=True, verbose_name="Início da Semana")
    semana_fim = models.DateField(blank=True, null=True, verbose_name="Fim da Semana")
    data = models.DateField(blank=True, null=True, verbose_name="Data (período diário)")
    valor_coletado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Coletado (R$)"
    )
    valor_acertado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Acertado (R$)"
    )
    data_acerto = models.DateField(blank=True, null=True, verbose_name="Data do Acerto")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Em_Aberto', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Caixa de Funcionário"
        verbose_name_plural = "Caixas de Funcionários"
        ordering = ['-semana_inicio', '-data', 'funcionario']
        indexes = [
            models.Index(fields=['funcionario', 'status']),
            models.Index(fields=['semana_inicio', 'semana_fim']),
            models.Index(fields=['data']),
        ]

    @property
    def nome_funcionario(self):
        return self.funcionario.nome

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.periodo_tipo == 'Semanal':
            if not self.semana_inicio or not self.semana_fim:
                raise ValidationError('Período semanal requer início e fim da semana')
        elif self.periodo_tipo == 'Diario':
            if not self.data:
                raise ValidationError('Período diário requer uma data')

    def __str__(self):
        if self.periodo_tipo == 'Semanal':
            return f"{self.funcionario.nome} - Semana {self.semana_inicio} a {self.semana_fim}"
        return f"{self.funcionario.nome} - {self.data}"


class MovimentoCaixaFuncionario(UpperCaseMixin, models.Model):
    """Registra movimentos individuais do caixa do funcionário"""

    caixa_funcionario = models.ForeignKey(
        CaixaFuncionario,
        on_delete=models.CASCADE,
        related_name='movimentos',
        verbose_name="Caixa do Funcionário"
    )
    data = models.DateField(verbose_name="Data")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(verbose_name="Descrição")
    cobranca_carregamento = models.ForeignKey(
        'notas.CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa_funcionario',
        verbose_name="Cobrança de Carregamento"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    class Meta:
        verbose_name = "Movimento de Caixa do Funcionário"
        verbose_name_plural = "Movimentos de Caixa dos Funcionários"
        ordering = ['-data', '-criado_em']

    def __str__(self):
        return f"Movimento - {self.data} - R$ {self.valor}"


class MovimentoBancario(UpperCaseMixin, models.Model):
    """Registra movimentos da conta corrente do banco"""

    TIPO_CHOICES = [
        ('Credito', 'Crédito (Entrada)'),
        ('Debito', 'Débito (Saída)'),
    ]
    ORIGEM_CHOICES = [
        ('Manual', 'Manual'),
        ('Importado', 'Importado'),
    ]

    data = models.DateField(verbose_name="Data")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(verbose_name="Descrição")
    origem = models.CharField(
        max_length=10,
        choices=ORIGEM_CHOICES,
        default='Manual',
        verbose_name="Origem"
    )
    numero_documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Nº Documento/Extrato"
    )
    hash_importacao = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Hash de Importação",
        help_text="Hash para evitar duplicatas na importação"
    )
    receita_empresa = models.ForeignKey(
        'ReceitaEmpresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_bancarios',
        verbose_name="Receita da Empresa"
    )
    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimentos_bancarios_criados'
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Movimento Bancário"
        verbose_name_plural = "Movimentos Bancários"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo']),
            models.Index(fields=['hash_importacao']),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data} - R$ {self.valor}"


class ControleSaldoSemanal(UpperCaseMixin, models.Model):
    """Controla e valida o saldo total do sistema (semanal)"""

    semana_inicio = models.DateField(verbose_name="Início da Semana")
    semana_fim = models.DateField(verbose_name="Fim da Semana")
    saldo_inicial_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial em Caixa (R$)"
    )
    saldo_inicial_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial no Banco (R$)"
    )
    total_receitas_empresa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Receitas Empresa (R$)"
    )
    total_caixa_funcionarios = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Caixa Funcionários (R$)"
    )
    total_entradas_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Entradas Banco (R$)"
    )
    total_saidas_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Saídas Banco (R$)"
    )
    total_pendentes_receber = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Pendentes a Receber (R$)"
    )
    saldo_final_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Calculado (R$)"
    )
    saldo_final_real_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Real em Caixa (R$)"
    )
    saldo_final_real_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Real no Banco (R$)"
    )
    diferenca = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Diferença (R$)"
    )
    validado = models.BooleanField(
        default=False,
        verbose_name="Validado",
        help_text="Marcar quando a diferença for zero"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    usuario_validacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saldos_validados',
        verbose_name="Usuário que Validou"
    )
    data_validacao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Validação")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Controle de Saldo Semanal"
        verbose_name_plural = "Controles de Saldo Semanal"
        ordering = ['-semana_inicio']
        unique_together = [['semana_inicio', 'semana_fim']]

    def calcular_totais(self):
        from django.db.models import Sum
        from decimal import Decimal
        from notas.models import CobrancaCarregamento

        self.total_receitas_empresa = ReceitaEmpresa.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        caixas_semanal = CaixaFuncionario.objects.filter(
            periodo_tipo='Semanal',
            semana_inicio__lte=self.semana_fim,
            semana_fim__gte=self.semana_inicio,
            status='Em_Aberto'
        ).select_related('funcionario')
        caixas_diario = CaixaFuncionario.objects.filter(
            periodo_tipo='Diario',
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim,
            status='Em_Aberto'
        ).select_related('funcionario')
        total_semanal = caixas_semanal.aggregate(total=Sum('valor_coletado'))['total'] or Decimal('0.00')
        total_diario = caixas_diario.aggregate(total=Sum('valor_coletado'))['total'] or Decimal('0.00')
        self.total_caixa_funcionarios = total_semanal + total_diario

        movimentos_banco = MovimentoBancario.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        )
        self.total_entradas_banco = movimentos_banco.filter(tipo='Credito').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        self.total_saidas_banco = movimentos_banco.filter(tipo='Debito').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        self.total_pendentes_receber = CobrancaCarregamento.objects.filter(
            status='Pendente',
            data_vencimento__lte=self.semana_fim
        ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')

        self.saldo_final_calculado = (
            self.saldo_inicial_caixa
            + self.saldo_inicial_banco
            + self.total_receitas_empresa
            + self.total_caixa_funcionarios
            + self.total_entradas_banco
            - self.total_saidas_banco
        )
        saldo_final_real = self.saldo_final_real_caixa + self.saldo_final_real_banco
        self.diferenca = self.saldo_final_calculado - saldo_final_real
        self.save()

    def validar(self, usuario):
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        if self.diferenca != Decimal('0.00'):
            raise ValidationError(
                f'Não é possível validar. Diferença de R$ {self.diferenca:.2f} deve ser zero.'
            )
        self.validado = True
        self.usuario_validacao = usuario
        self.data_validacao = timezone.now()
        self.save()

    def __str__(self):
        return f"Controle Semanal - {self.semana_inicio} a {self.semana_fim}"


class MovimentoCaixa(UpperCaseMixin, models.Model):
    """Modelo unificado para gerenciamento de todos os movimentos de caixa."""

    TIPO_CHOICES = [
        ('AcertoFuncionario', 'Acerto de Funcionário'),
        ('Entrada', 'Entrada de Dinheiro'),
        ('Saida', 'Saída de Dinheiro'),
    ]
    CATEGORIA_ENTRADA_CHOICES = [
        ('RecebimentoCarregamento', 'Recebimento de carregamento'),
        ('RecebimentoDescarga', 'Recebimento de descarga'),
        ('Reembolso', 'Reembolso'),
        ('Outros', 'Outros'),
    ]
    CATEGORIA_SAIDA_CHOICES = [
        ('Estelar', 'Estelar'),
        ('Manutencao', 'Manutenção'),
        ('ValeTransporte', 'Vale transporte'),
        ('Outros', 'Outros'),
    ]

    data = models.DateField(verbose_name="Data")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Movimento")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(verbose_name="Descrição")
    categoria = models.CharField(max_length=30, blank=True, null=True, verbose_name="Categoria")
    funcionario = models.ForeignKey(
        FuncionarioFluxoCaixa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Funcionário"
    )
    acerto_diario = models.ForeignKey(
        AcertoDiarioCarregamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Acerto Diário"
    )
    cliente = models.ForeignKey(
        'notas.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Cliente"
    )
    periodo = models.ForeignKey(
        'PeriodoMovimentoCaixa',
        on_delete=models.PROTECT,
        related_name='movimentos',
        null=True,
        blank=True,
        verbose_name="Período",
        help_text="Período ao qual este movimento pertence"
    )
    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimentos_caixa_criados',
        verbose_name="Usuário que Criou"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Movimento de Caixa"
        verbose_name_plural = "Movimentos de Caixa"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo']),
            models.Index(fields=['tipo', 'categoria']),
            models.Index(fields=['funcionario', 'data']),
        ]

    def get_categoria_display(self):
        if not self.categoria:
            return '-'
        if self.tipo == 'Entrada':
            for val, label in self.CATEGORIA_ENTRADA_CHOICES:
                if val == self.categoria:
                    return label
        elif self.tipo == 'Saida':
            for val, label in self.CATEGORIA_SAIDA_CHOICES:
                if val == self.categoria:
                    return label
        return self.categoria

    def __str__(self):
        tipo_display = self.get_tipo_display()
        if self.funcionario:
            return f"{tipo_display} - {self.funcionario.nome} - {self.data} - R$ {self.valor}"
        return f"{tipo_display} - {self.data} - R$ {self.valor}"

    @property
    def valor_formatado(self):
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    @property
    def descricao_exibicao(self):
        """Para exibição na lista: se descricao for 'Carregamento: Cliente', retorna (Cliente, 'Carregamento')."""
        if not self.descricao:
            return (self.descricao or '', None)
        d = self.descricao.strip()
        # Remover marcador interno da baixa de "descarga (Depósito)".
        # Ex.: "Recebimento de Descarga: ... [DESCARGA_DEPOSITO:5]"
        d = re.sub(r'\s*\[DESCARGA_DEPOSITO:\s*\d+\]\s*', ' ', d, flags=re.IGNORECASE)
        d = re.sub(r'\s+', ' ', d).strip()
        if d.upper().startswith('CARREGAMENTO:'):
            parte = d.split(':', 1)[1].strip() if ':' in d else d
            return (parte, 'CARREGAMENTO')
        return (d, None)

    @property
    def is_entrada(self):
        return self.tipo in ['AcertoFuncionario', 'Entrada']

    @property
    def is_saida(self):
        return self.tipo == 'Saida'


class PeriodoMovimentoCaixa(UpperCaseMixin, models.Model):
    """Representa um período de controle de movimentos de caixa."""

    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Fechado', 'Fechado'),
    ]

    nome = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nome do Período",
        help_text="Opcional. Se não informado, será gerado automaticamente pela data de início."
    )
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(
        verbose_name="Data de Fim",
        null=True,
        blank=True,
        help_text="Opcional. Deixe em branco se o período ainda está aberto."
    )
    valor_inicial_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Inicial em Caixa (R$)",
        help_text="Valor inicial disponível em caixa no início do período"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Aberto', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    usuario_criacao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='periodos_movimento_caixa_criados',
        verbose_name="Usuário que Criou"
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Período de Movimento de Caixa"
        verbose_name_plural = "Períodos de Movimento de Caixa"
        ordering = ['-data_inicio', '-criado_em']
        indexes = [
            models.Index(fields=['status', 'data_inicio']),
        ]

    def __str__(self):
        if self.nome:
            return f"{self.nome} - {self.data_inicio.strftime('%d/%m/%Y')}"
        return f"Período de {self.data_inicio.strftime('%d/%m/%Y')}"

    @property
    def total_entradas(self):
        from django.db.models import Sum
        from decimal import Decimal
        return MovimentoCaixa.objects.filter(
            periodo=self,
            tipo__in=['AcertoFuncionario', 'Entrada']
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    @property
    def total_saidas(self):
        from django.db.models import Sum
        from decimal import Decimal
        return MovimentoCaixa.objects.filter(periodo=self, tipo='Saida').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    @property
    def saldo_atual(self):
        return self.valor_inicial_caixa + self.total_entradas - self.total_saidas

    @property
    def movimentos_count(self):
        return self.movimentos.count()

    def fechar_periodo(self):
        if self.status == 'Aberto':
            self.status = 'Fechado'
            if not self.data_fim:
                self.data_fim = timezone.now().date()
            self.save()
