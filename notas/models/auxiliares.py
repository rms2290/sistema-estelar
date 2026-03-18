"""
Modelos auxiliares: histórico de consulta, auditoria, cobrança, fechamento de frete.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from .mixins import UpperCaseMixin
from .cliente import Cliente
from .motorista import Motorista
from .usuario import Usuario
from .romaneio import RomaneioViagem


class HistoricoConsulta(UpperCaseMixin, models.Model):
    """Histórico de consultas de risco de motoristas."""
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.CASCADE,
        related_name='historico_consultas',
        verbose_name="Motorista"
    )
    numero_consulta = models.CharField(max_length=50, unique=True, verbose_name="Número da Consulta")
    data_consulta = models.DateField(default=timezone.now, verbose_name="Data da Consulta")
    gerenciadora = models.CharField(max_length=100, blank=True, null=True, verbose_name="Gerenciadora")
    status_consulta = models.CharField(
        max_length=20,
        choices=[('Apto', 'Apto'), ('Inapto', 'Inapto'), ('Pendente', 'Pendente')],
        default='Pendente',
        verbose_name="Status da Consulta"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações da Consulta")

    class Meta:
        verbose_name = "Histórico de Consulta"
        verbose_name_plural = "Históricos de Consultas"
        ordering = ['-data_consulta', 'motorista']

    def __str__(self):
        return f"Consulta {self.numero_consulta} de {self.motorista.nome} em {self.data_consulta.strftime('%d/%m/%Y')}"


class AuditoriaLog(models.Model):
    """Log de auditoria para criação, edição e exclusão."""
    ACAO_CHOICES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Edição'),
        ('DELETE', 'Exclusão'),
        ('RESTORE', 'Restauração'),
    ]

    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    objeto_id = models.IntegerField(verbose_name="ID do Objeto")
    acao = models.CharField(max_length=10, choices=ACAO_CHOICES, verbose_name="Ação")
    dados_anteriores = models.JSONField(null=True, blank=True, verbose_name="Dados Anteriores")
    dados_novos = models.JSONField(null=True, blank=True, verbose_name="Dados Novos")
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_auditoria',
        verbose_name="Usuário"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    user_agent = models.TextField(null=True, blank=True, verbose_name="User Agent")
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['-data_hora']),
            models.Index(fields=['usuario']),
        ]

    def __str__(self):
        return f"{self.get_acao_display()} de {self.modelo} #{self.objeto_id} em {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class CobrancaCarregamento(UpperCaseMixin, models.Model):
    """Cobranças de carregamento e CTE/Manifesto."""
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Baixado', 'Baixado'),
    ]
    TIPO_CLIENTE_CHOICES = [
        ('Mensalista', 'Mensalista'),
        ('Por_Cubagem', 'Por Cubagem'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='cobrancas_carregamento',
        verbose_name="Cliente"
    )
    romaneios = models.ManyToManyField(
        RomaneioViagem,
        related_name='cobrancas_vinculadas',
        verbose_name="Romaneios"
    )
    valor_carregamento = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor Carregamento (R$)"
    )
    valor_cte_manifesto = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Valor CTE/Manifesto (R$)"
    )
    valor_distribuicao_trabalhadores = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True,
        verbose_name="Valor para distribuição trabalhadores (R$)",
        help_text="Valor que entra no acerto diário para divisão entre trabalhadores. Se vazio, usa o valor do carregamento."
    )
    tipo_cliente = models.CharField(
        max_length=20, choices=TIPO_CLIENTE_CHOICES, default='Mensalista', verbose_name="Tipo de Cliente"
    )
    cubagem = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, blank=True, null=True, verbose_name="Cubagem (m³)"
    )
    valor_cubagem = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, blank=True, null=True, verbose_name="Valor da Cubagem (R$/m³)"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='Pendente', verbose_name="Status"
    )
    data_vencimento = models.DateField(blank=True, null=True, verbose_name="Data de Vencimento")
    data_baixa = models.DateField(blank=True, null=True, verbose_name="Data de Baixa")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Cobrança de Carregamento"
        verbose_name_plural = "Cobranças de Carregamento"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['cliente']),
            models.Index(fields=['status']),
            models.Index(fields=['data_vencimento']),
        ]

    def __str__(self):
        return f"Cobrança #{self.id} - {self.cliente.razao_social} - {self.get_status_display()}"

    @property
    def valor_armazenamento(self):
        tipo = str(self.tipo_cliente).upper() if self.tipo_cliente else ''
        if tipo == 'POR_CUBAGEM' and self.cubagem and self.valor_cubagem:
            return self.cubagem * self.valor_cubagem
        return Decimal('0.00')

    @property
    def valor_total(self):
        total = (self.valor_carregamento or 0) + (self.valor_cte_manifesto or 0)
        tipo = str(self.tipo_cliente).upper() if self.tipo_cliente else ''
        if tipo == 'POR_CUBAGEM':
            total += self.valor_armazenamento
        return total

    @property
    def margem_carregamento(self):
        """Margem Estelar (valor cobrado ao cliente menos valor para trabalhadores)."""
        v_cobrado = self.valor_carregamento or Decimal('0.00')
        v_dist = self.valor_distribuicao_trabalhadores
        if v_dist is None:
            return Decimal('0.00')
        return max(Decimal('0.00'), v_cobrado - v_dist)

    def baixar(self):
        self.status = 'Baixado'
        self.data_baixa = timezone.now().date()
        self.save()


class FechamentoFrete(UpperCaseMixin, models.Model):
    """Fechamento de frete consolidando romaneios."""
    romaneios = models.ManyToManyField(
        RomaneioViagem,
        related_name='fechamentos_frete',
        verbose_name="Romaneios Associados"
    )
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        related_name='fechamentos_frete',
        verbose_name="Motorista"
    )
    data = models.DateField(verbose_name="Data do Fechamento", default=timezone.now)
    frete_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Frete Total (R$)")
    ctr_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CTR Total (R$)")
    carregamento_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Carregamento Total (R$)")

    cubagem_bau_a = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cubagem Baú A (m³)")
    cubagem_bau_b = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cubagem Baú B (m³)")
    cubagem_bau_c = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cubagem Baú C (m³)")
    cubagem_bau_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        verbose_name="Cubagem Baú Total (m³)"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    usuario_criacao = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='fechamentos_criados',
        verbose_name="Usuário de Criação",
        null=True,
        blank=True
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    origem_romaneio = models.BooleanField(default=False, verbose_name="Criado a partir de Romaneios")

    def calcular_cubagem_total(self):
        total = 0
        if self.cubagem_bau_a:
            total += self.cubagem_bau_a
        if self.cubagem_bau_b:
            total += self.cubagem_bau_b
        if self.cubagem_bau_c:
            total += self.cubagem_bau_c
        self.cubagem_bau_total = total
        return total

    def save(self, *args, **kwargs):
        if self.cubagem_bau_a or self.cubagem_bau_b or self.cubagem_bau_c:
            self.calcular_cubagem_total()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Fechamento {self.data.strftime('%d/%m/%Y')} - {self.motorista.nome}"

    class Meta:
        verbose_name = "Fechamento de Frete"
        verbose_name_plural = "Fechamentos de Frete"
        ordering = ['-data', '-data_criacao']


class ItemFechamentoFrete(models.Model):
    """Item (cliente) em um fechamento de frete."""
    fechamento = models.ForeignKey(
        FechamentoFrete,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Fechamento"
    )
    cliente_consolidado = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='itens_fechamento_consolidado',
        verbose_name="Cliente Consolidado"
    )
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso Total (kg)")
    cubagem = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cubagem (m³)")
    valor_mercadoria = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total (R$)")

    romaneios = models.ManyToManyField(
        RomaneioViagem,
        related_name='itens_fechamento',
        verbose_name="Romaneios que Compõem"
    )

    valor_por_cubagem = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor por Cubagem (R$)")
    percentual_cubagem = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Percentual sobre Cubagem (%)")
    percentual_escolhido = models.DecimalField(
        max_digits=5, decimal_places=2, default=6.00,
        verbose_name="Percentual Escolhido (%)"
    )
    valor_por_percentual = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor por Percentual (R$)")
    valor_ideal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Ideal (R$)")
    percentual_ajustado = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        verbose_name="Percentual Ajustado Manual (R$)"
    )

    frete_proporcional = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Frete Proporcional (R$)")
    ctr_proporcional = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CTR Proporcional (R$)")
    carregamento_proporcional = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Carregamento Proporcional (R$)"
    )
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Final a Cobrar (R$)")
    usar_ajuste_manual = models.BooleanField(default=False, verbose_name="Usar Ajuste Manual")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    def calcular_valor_por_cubagem(self):
        if not self.fechamento.cubagem_bau_total or self.fechamento.cubagem_bau_total == 0:
            return 0
        if not self.cubagem:
            return 0
        return (self.cubagem / self.fechamento.cubagem_bau_total) * self.fechamento.frete_total

    def calcular_percentual_cubagem(self):
        if not self.valor_mercadoria or self.valor_mercadoria == 0:
            return 0
        valor_cub = self.calcular_valor_por_cubagem()
        return (valor_cub / self.valor_mercadoria) * 100

    def calcular_valor_por_percentual(self):
        if not self.valor_mercadoria or not self.percentual_escolhido:
            return 0
        return self.valor_mercadoria * (self.percentual_escolhido / 100)

    def calcular_valor_ideal(self):
        if not self.valor_mercadoria or self.valor_mercadoria == 0:
            return 0
        if not self.fechamento.frete_total or self.fechamento.frete_total == 0:
            return 0
        valor_total_mercadorias = self.fechamento.itens.aggregate(total=Sum('valor_mercadoria'))['total'] or 0
        if valor_total_mercadorias == 0:
            return 0
        percentual_geral = (self.fechamento.frete_total / valor_total_mercadorias) * 100
        return self.valor_mercadoria * (percentual_geral / 100)

    def calcular_distribuicoes(self):
        if not self.fechamento.cubagem_bau_total or self.fechamento.cubagem_bau_total == 0:
            return {}
        if not self.cubagem:
            return {}
        proporcao = self.cubagem / self.fechamento.cubagem_bau_total
        return {
            'frete': proporcao * self.fechamento.frete_total,
            'ctr': proporcao * self.fechamento.ctr_total,
            'carregamento': proporcao * self.fechamento.carregamento_total,
        }

    def calcular_todos(self):
        self.valor_por_cubagem = self.calcular_valor_por_cubagem()
        self.percentual_cubagem = self.calcular_percentual_cubagem()
        self.valor_por_percentual = self.calcular_valor_por_percentual()
        self.valor_ideal = self.calcular_valor_ideal()
        distribuicoes = self.calcular_distribuicoes()
        self.frete_proporcional = distribuicoes.get('frete', 0)
        self.ctr_proporcional = distribuicoes.get('ctr', 0)
        self.carregamento_proporcional = distribuicoes.get('carregamento', 0)
        if self.usar_ajuste_manual and self.percentual_ajustado:
            self.valor_final = self.percentual_ajustado
        else:
            self.valor_final = self.valor_por_cubagem

    def save(self, *args, **kwargs):
        self.calcular_todos()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cliente_consolidado.razao_social} - {self.fechamento}"

    class Meta:
        verbose_name = "Item de Fechamento de Frete"
        verbose_name_plural = "Itens de Fechamento de Frete"
        ordering = ['cliente_consolidado__razao_social']


class DetalheItemFechamento(models.Model):
    """Detalhe de romaneio por item de fechamento."""
    item = models.ForeignKey(
        ItemFechamentoFrete,
        on_delete=models.CASCADE,
        related_name='detalhes',
        verbose_name="Item"
    )
    romaneio = models.ForeignKey(
        RomaneioViagem,
        on_delete=models.PROTECT,
        related_name='detalhes_fechamento',
        verbose_name="Romaneio"
    )
    cliente_original = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='detalhes_fechamento',
        verbose_name="Cliente Original"
    )
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso (kg)")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")

    def __str__(self):
        return f"{self.romaneio.codigo} - {self.cliente_original.razao_social}"

    class Meta:
        verbose_name = "Detalhe de Item de Fechamento"
        verbose_name_plural = "Detalhes de Item de Fechamento"
        ordering = ['romaneio__codigo']
