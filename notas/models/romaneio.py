"""
Modelo Romaneio de Viagem.
"""
from django.db import models
from django.utils import timezone

from .mixins import UpperCaseMixin
from .cliente import Cliente
from .motorista import Motorista
from .veiculo import Veiculo
from .nota_fiscal import NotaFiscal
from .tabela_seguro import TabelaSeguro


class RomaneioViagem(UpperCaseMixin, models.Model):
    """Romaneio de viagem - agrupa notas, motorista, veículos e rota."""
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código do Romaneio",
        help_text="Código único do romaneio (ex: ROM-2024-01-0001)"
    )

    STATUS_ROMANEIO_CHOICES = [
        ('Salvo', 'Salvo'),
        ('Emitido', 'Emitido'),
    ]
    status = models.CharField(
        max_length=15,
        choices=STATUS_ROMANEIO_CHOICES,
        default='Salvo',
        verbose_name="Status do Romaneio"
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='romaneios_cliente',
        verbose_name="Cliente"
    )

    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        related_name='romaneios_motorista',
        verbose_name="Motorista"
    )

    veiculo_principal = models.ForeignKey(
        Veiculo,
        on_delete=models.PROTECT,
        related_name='romaneios_veiculo_principal',
        verbose_name="Veículo Principal"
    )
    reboque_1 = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='romaneios_reboque_1',
        verbose_name="Reboque 1"
    )
    reboque_2 = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='romaneios_reboque_2',
        verbose_name="Reboque 2"
    )

    notas_fiscais = models.ManyToManyField(
        NotaFiscal,
        related_name='romaneios_vinculados',
        blank=True,
        verbose_name="Notas Fiscais"
    )

    peso_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Peso Total (kg)"
    )
    valor_total = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor Total (R$)"
    )
    quantidade_total = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Quantidade Total"
    )

    origem_cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade de Origem")
    origem_estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado de Origem (UF)")
    destino_cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade de Destino")
    destino_estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado de Destino (UF)")

    data_emissao = models.DateTimeField(default=timezone.now, verbose_name="Data de Emissão")
    data_saida = models.DateTimeField(blank=True, null=True, verbose_name="Data de Saída")
    data_chegada_prevista = models.DateTimeField(blank=True, null=True, verbose_name="Data de Chegada Prevista")
    data_chegada_real = models.DateTimeField(blank=True, null=True, verbose_name="Data de Chegada Real")

    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    seguro_obrigatorio = models.BooleanField(default=True, verbose_name="Seguro Obrigatório")
    percentual_seguro = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00, verbose_name="Percentual de Seguro (%)"
    )
    valor_seguro = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor do Seguro (R$)"
    )

    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='romaneios_criados',
        verbose_name="Usuário de Criação",
        null=True,
        blank=True
    )
    usuario_ultima_edicao = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='romaneios_editados',
        verbose_name="Usuário da Última Edição"
    )
    data_ultima_edicao = models.DateTimeField(auto_now=True, verbose_name="Data da Última Edição")

    def __str__(self):
        return f"Romaneio {self.codigo} - {self.cliente.razao_social}"

    def get_composicao_veicular(self):
        composicao = [self.veiculo_principal.placa]
        if self.reboque_1:
            composicao.append(self.reboque_1.placa)
        if self.reboque_2:
            composicao.append(self.reboque_2.placa)
        return " + ".join(composicao)

    def get_tipo_composicao(self):
        if self.reboque_2:
            return "Bi-trem"
        elif self.reboque_1:
            return "Carreta"
        return "Simples"

    def calcular_totais(self):
        if not self.notas_fiscais.exists():
            self.peso_total = 0
            self.valor_total = 0
            self.quantidade_total = 0
            self.save(update_fields=['peso_total', 'valor_total', 'quantidade_total'])
            return

        peso_total = sum(nf.peso or 0 for nf in self.notas_fiscais.all())
        valor_total = sum(nf.valor or 0 for nf in self.notas_fiscais.all())
        quantidade_total = sum(nf.quantidade or 0 for nf in self.notas_fiscais.all())

        if (self.peso_total != peso_total or self.valor_total != valor_total or
                self.quantidade_total != quantidade_total):
            self.peso_total = peso_total
            self.valor_total = valor_total
            self.quantidade_total = quantidade_total
            self.save(update_fields=['peso_total', 'valor_total', 'quantidade_total'])
            if self.destino_estado and self.valor_total:
                self.calcular_seguro()

    def calcular_seguro(self):
        if not self.destino_estado or not self.valor_total:
            return
        try:
            tabela_seguro = TabelaSeguro.objects.get(estado=self.destino_estado)
            self.percentual_seguro = tabela_seguro.percentual_seguro
            self.valor_seguro = (self.valor_total * self.percentual_seguro) / 100
            self.save(update_fields=['percentual_seguro', 'valor_seguro'])
        except TabelaSeguro.DoesNotExist:
            pass

    def validar_capacidade_veiculo(self):
        if not self.peso_total or not self.veiculo_principal:
            return True, ""
        from notas.utils.constants import CAPACIDADES_VEICULOS
        capacidades = CAPACIDADES_VEICULOS
        capacidade_principal = capacidades.get(self.veiculo_principal.tipo_unidade, 0)
        capacidade_reboque_1 = capacidades.get(self.reboque_1.tipo_unidade, 0) if self.reboque_1 else 0
        capacidade_reboque_2 = capacidades.get(self.reboque_2.tipo_unidade, 0) if self.reboque_2 else 0
        capacidade_total = capacidade_principal + capacidade_reboque_1 + capacidade_reboque_2
        if self.peso_total > capacidade_total:
            return False, (
                f"Peso total da carga ({self.peso_total:.2f} kg) excede a capacidade total "
                f"dos veículos ({capacidade_total} kg)."
            )
        return True, ""

    def get_resumo_carga(self):
        if not self.notas_fiscais.exists():
            return {
                'total_notas': 0,
                'peso_total': 0,
                'valor_total': 0,
                'quantidade_total': 0,
                'capacidade_utilizada': 0,
                'capacidade_maxima': 0,
            }
        from notas.utils.constants import CAPACIDADES_VEICULOS
        capacidades = CAPACIDADES_VEICULOS
        capacidade_principal = capacidades.get(self.veiculo_principal.tipo_unidade, 0) if self.veiculo_principal else 0
        capacidade_reboque_1 = capacidades.get(self.reboque_1.tipo_unidade, 0) if self.reboque_1 else 0
        capacidade_reboque_2 = capacidades.get(self.reboque_2.tipo_unidade, 0) if self.reboque_2 else 0
        capacidade_maxima = capacidade_principal + capacidade_reboque_1 + capacidade_reboque_2
        return {
            'total_notas': self.notas_fiscais.count(),
            'peso_total': self.peso_total or 0,
            'valor_total': self.valor_total or 0,
            'quantidade_total': self.quantidade_total or 0,
            'capacidade_utilizada': self.peso_total or 0,
            'capacidade_maxima': capacidade_maxima,
            'percentual_capacidade': (
                (self.peso_total / capacidade_maxima * 100) if capacidade_maxima > 0 else 0
            ),
        }

    def gerar_codigo_automatico(self):
        if self.codigo:
            return
        ano_atual = timezone.now().year
        mes_atual = timezone.now().month
        ultimo_romaneio = RomaneioViagem.objects.filter(
            codigo__startswith=f"ROM-{ano_atual}-{mes_atual:02d}"
        ).order_by('-codigo').first()
        if ultimo_romaneio:
            try:
                numero_atual = int(ultimo_romaneio.codigo.split('-')[-1])
                novo_numero = numero_atual + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        self.codigo = f"ROM-{ano_atual}-{mes_atual:02d}-{novo_numero:04d}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.gerar_codigo_automatico()
        update_fields = kwargs.get('update_fields')
        super().save(*args, **kwargs)
        if not update_fields and self.notas_fiscais.exists():
            self.calcular_totais()
        if not update_fields and self.destino_estado and self.valor_total:
            self.calcular_seguro()

    class Meta:
        verbose_name = "Romaneio de Viagem"
        verbose_name_plural = "Romaneios de Viagem"
        ordering = ['-data_emissao', 'codigo']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['status']),
            models.Index(fields=['cliente']),
            models.Index(fields=['motorista']),
            models.Index(fields=['data_emissao']),
        ]
