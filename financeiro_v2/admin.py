"""Admin do Financeiro V2 - permite inspecionar e ajustar registros manualmente."""
from django.contrib import admin

from .models import Carteira, Bolso, Lancamento


@admin.register(Carteira)
class CarteiraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'saldo_inicial', 'data_saldo_inicial', 'ativa']
    list_filter = ['ativa']
    search_fields = ['nome', 'codigo']


@admin.register(Bolso)
class BolsoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'codigo', 'eh_terceiro', 'ordem', 'ativo']
    list_filter = ['eh_terceiro', 'ativo']
    search_fields = ['nome', 'codigo']
    list_editable = ['ordem', 'ativo']


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = [
        'data',
        'tipo',
        'valor',
        'carteira',
        'bolso',
        'descricao',
        'categoria',
        'criado_por',
    ]
    list_filter = ['tipo', 'carteira', 'bolso', 'data', 'categoria']
    search_fields = ['descricao', 'categoria']
    autocomplete_fields = ['cliente', 'funcionario']
    readonly_fields = ['criado_em', 'atualizado_em']
    date_hierarchy = 'data'
