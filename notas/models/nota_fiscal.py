"""
Modelos de Nota Fiscal e ocorrências.
"""
from django.db import models
from django.db.models import UniqueConstraint

from .mixins import UpperCaseMixin
from .cliente import Cliente


class NotaFiscal(UpperCaseMixin, models.Model):
    """Nota Fiscal de entrada no sistema."""
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name='notas_fiscais', verbose_name="Cliente"
    )
    nota = models.CharField(max_length=50, verbose_name="Número da Nota")
    data = models.DateField(verbose_name="Data de Emissão")
    fornecedor = models.CharField(max_length=200, verbose_name="Fornecedor")
    mercadoria = models.CharField(max_length=200, verbose_name="Mercadoria")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso (kg)")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")

    STATUS_NF_CHOICES = [
        ('Depósito', 'Depósito'),
        ('Enviada', 'Enviada'),
    ]
    status = models.CharField(
        max_length=20, default='Depósito', choices=STATUS_NF_CHOICES, verbose_name="Status da NF"
    )

    LOCAL_CHOICES = [
        ('1', 'Galpão 1'),
        ('2', 'Galpão 2'),
        ('3', 'Galpão 3'),
        ('4', 'Galpão 4'),
        ('5', 'Galpão 5'),
    ]
    local = models.CharField(
        max_length=10, choices=LOCAL_CHOICES, blank=True, null=True, verbose_name="Local"
    )

    romaneios = models.ManyToManyField(
        'RomaneioViagem',
        related_name='notas_vinculadas',
        blank=True,
        verbose_name="Romaneios Vinculados"
    )

    def __str__(self):
        return f"Nota {self.nota} - Cliente: {self.cliente.razao_social}"

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ['-data', 'nota']
        indexes = [
            models.Index(fields=['data'], name='nota_fiscal_data_idx'),
            models.Index(fields=['status'], name='nota_fiscal_status_idx'),
            models.Index(fields=['status', 'data'], name='nota_fiscal_status_data_idx'),
            models.Index(fields=['cliente', 'status'], name='nota_fiscal_cliente_status_idx'),
        ]
        constraints = [
            UniqueConstraint(
                fields=['nota', 'cliente', 'mercadoria', 'quantidade', 'peso'],
                name='unique_nota_fiscal_por_campos_chave'
            )
        ]


class OcorrenciaNotaFiscal(models.Model):
    """Ocorrência registrada para uma nota fiscal."""
    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name='ocorrencias',
        verbose_name="Nota Fiscal"
    )
    observacoes = models.TextField(
        verbose_name="Observações",
        help_text="Descreva a ocorrência relacionada à nota fiscal"
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias_notas_criadas',
        verbose_name="Usuário que Registrou"
    )

    def __str__(self):
        return f"Ocorrência #{self.id} - Nota {self.nota_fiscal.nota} - {self.data_criacao.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Ocorrência de Nota Fiscal"
        verbose_name_plural = "Ocorrências de Notas Fiscais"
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['nota_fiscal', 'data_criacao'], name='ocorrencia_nota_fiscal_idx'),
        ]


class FotoOcorrencia(models.Model):
    """Foto anexada a uma ocorrência de nota fiscal."""
    ocorrencia = models.ForeignKey(
        OcorrenciaNotaFiscal,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Ocorrência"
    )
    foto = models.ImageField(
        upload_to='ocorrencias_notas/%Y/%m/',
        verbose_name="Foto",
        help_text="Foto relacionada à ocorrência"
    )
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name="Data de Upload")

    def __str__(self):
        return f"Foto #{self.id} - Ocorrência #{self.ocorrencia.id}"

    class Meta:
        verbose_name = "Foto de Ocorrência"
        verbose_name_plural = "Fotos de Ocorrências"
        ordering = ['-data_upload']
        indexes = [
            models.Index(fields=['ocorrencia', 'data_upload'], name='foto_ocorrencia_idx'),
        ]
