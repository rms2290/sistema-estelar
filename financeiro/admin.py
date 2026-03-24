"""Admin para modelos do app financeiro."""
from django.contrib import admin
from .models import (
    FuncionarioFluxoCaixa,
    SetorBancario,
    ReceitaEmpresa,
    CaixaFuncionario,
    MovimentoCaixaFuncionario,
    MovimentoBancario,
    ControleSaldoSemanal,
    AcertoDiarioCarregamento,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    AcumuladoFuncionario,
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
)


@admin.register(FuncionarioFluxoCaixa)
class FuncionarioFluxoCaixaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome']
    list_editable = ['ativo']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Informações', {'fields': ('nome', 'ativo')}),
        ('Controle', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )


@admin.register(SetorBancario)
class SetorBancarioAdmin(admin.ModelAdmin):
    list_display = ['setor', 'nome_responsavel', 'banco', 'agencia', 'conta_corrente', 'chave_pix', 'tipo_chave_pix', 'ativo']
    list_filter = ['setor', 'ativo', 'banco']
    search_fields = ['setor', 'nome_responsavel', 'banco', 'chave_pix']
    list_editable = ['ativo']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Informações do Setor', {'fields': ('setor', 'nome_responsavel', 'ativo')}),
        ('Dados Bancários', {'fields': ('banco', 'agencia', 'conta_corrente', 'chave_pix', 'tipo_chave_pix')}),
        ('Controle', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )


@admin.register(ReceitaEmpresa)
class ReceitaEmpresaAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo_receita', 'valor', 'cliente', 'usuario_criacao', 'criado_em']
    list_filter = ['tipo_receita', 'data', 'cliente']
    search_fields = ['descricao', 'rotulo_personalizado', 'cliente__razao_social', 'tipo_receita']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']
    fieldsets = (
        (
            'Informações da Receita',
            {'fields': ('data', 'tipo_receita', 'valor', 'rotulo_personalizado', 'descricao')},
        ),
        ('Relacionamentos', {'fields': ('cliente', 'cobranca_carregamento')}),
        ('Controle', {'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criacao = request.user
        super().save_model(request, obj, form, change)


@admin.register(CaixaFuncionario)
class CaixaFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'periodo_tipo', 'periodo_display', 'valor_coletado', 'status', 'data_acerto']
    list_filter = ['status', 'periodo_tipo', 'funcionario']
    search_fields = ['funcionario__nome', 'observacoes']
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Informações do Caixa', {'fields': ('funcionario', 'periodo_tipo', 'semana_inicio', 'semana_fim', 'data', 'valor_coletado', 'observacoes')}),
        ('Acerto', {'fields': ('status', 'valor_acertado', 'data_acerto')}),
        ('Controle', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def periodo_display(self, obj):
        if obj.periodo_tipo == 'Semanal':
            return f"{obj.semana_inicio} a {obj.semana_fim}"
        return str(obj.data)
    periodo_display.short_description = 'Período'


@admin.register(MovimentoCaixaFuncionario)
class MovimentoCaixaFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['caixa_funcionario', 'data', 'valor', 'descricao_curta']
    list_filter = ['data', 'caixa_funcionario']
    search_fields = ['descricao', 'caixa_funcionario__funcionario__nome']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em']

    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'


@admin.register(MovimentoBancario)
class MovimentoBancarioAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo', 'valor', 'descricao_curta', 'numero_documento', 'origem', 'usuario_criacao']
    list_filter = ['tipo', 'origem', 'data', 'usuario_criacao']
    search_fields = ['descricao', 'numero_documento', 'hash_importacao']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']
    fieldsets = (
        ('Informações do Movimento', {'fields': ('data', 'tipo', 'valor', 'descricao', 'numero_documento')}),
        ('Origem e Relacionamentos', {'fields': ('origem', 'hash_importacao', 'receita_empresa')}),
        ('Controle', {'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criacao = request.user
        super().save_model(request, obj, form, change)


@admin.register(ControleSaldoSemanal)
class ControleSaldoSemanalAdmin(admin.ModelAdmin):
    list_display = ['semana_inicio', 'semana_fim', 'saldo_final_calculado', 'diferenca', 'validado', 'usuario_validacao']
    list_filter = ['validado', 'semana_inicio']
    search_fields = ['observacoes']
    date_hierarchy = 'semana_inicio'
    readonly_fields = ['criado_em', 'atualizado_em', 'data_validacao']
    fieldsets = (
        ('Período', {'fields': ('semana_inicio', 'semana_fim')}),
        ('Saldos Iniciais', {'fields': ('saldo_inicial_caixa', 'saldo_inicial_banco')}),
        ('Totais Calculados', {'fields': ('total_receitas_empresa', 'total_caixa_funcionarios', 'total_entradas_banco', 'total_saidas_banco', 'total_pendentes_receber', 'saldo_final_calculado')}),
        ('Saldos Finais Reais', {'fields': ('saldo_final_real_caixa', 'saldo_final_real_banco', 'diferenca')}),
        ('Validação', {'fields': ('validado', 'usuario_validacao', 'data_validacao')}),
        ('Observações', {'fields': ('observacoes',)}),
        ('Controle', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )


class CarregamentoClienteInline(admin.TabularInline):
    model = CarregamentoCliente
    extra = 1
    fields = ['cliente', 'descricao', 'valor', 'observacoes']


class DistribuicaoFuncionarioInline(admin.TabularInline):
    model = DistribuicaoFuncionario
    extra = 1
    fields = ['funcionario', 'valor']


@admin.register(AcertoDiarioCarregamento)
class AcertoDiarioCarregamentoAdmin(admin.ModelAdmin):
    list_display = ['data', 'total_carregamentos_display', 'valor_estelar', 'total_funcionarios_display', 'total_distribuido_display']
    list_filter = ['data']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']
    inlines = [CarregamentoClienteInline, DistribuicaoFuncionarioInline]
    fieldsets = (
        ('Informações do Acerto', {'fields': ('data', 'valor_estelar', 'observacoes')}),
        ('Controle', {'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def total_carregamentos_display(self, obj):
        return f"R$ {obj.total_carregamentos:.2f}".replace('.', ',')
    total_carregamentos_display.short_description = 'Total Carregamentos'

    def total_funcionarios_display(self, obj):
        return f"R$ {obj.total_funcionarios:.2f}".replace('.', ',')
    total_funcionarios_display.short_description = 'Total Funcionários'

    def total_distribuido_display(self, obj):
        return f"R$ {obj.total_distribuido:.2f}".replace('.', ',')
    total_distribuido_display.short_description = 'Total Distribuído'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criacao = request.user
        super().save_model(request, obj, form, change)


@admin.register(CarregamentoCliente)
class CarregamentoClienteAdmin(admin.ModelAdmin):
    list_display = ['acerto_diario', 'tipo_display', 'nome_display', 'valor', 'observacoes']
    list_filter = ['acerto_diario__data', 'cliente']
    search_fields = ['cliente__razao_social', 'descricao', 'observacoes']
    date_hierarchy = 'acerto_diario__data'

    def tipo_display(self, obj):
        return obj.tipo
    tipo_display.short_description = 'Tipo'

    def nome_display(self, obj):
        return obj.nome_display
    nome_display.short_description = 'Cliente/Descrição'


@admin.register(DistribuicaoFuncionario)
class DistribuicaoFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['acerto_diario', 'funcionario', 'valor']
    list_filter = ['acerto_diario__data', 'funcionario']
    search_fields = ['funcionario__nome']
    date_hierarchy = 'acerto_diario__data'


@admin.register(AcumuladoFuncionario)
class AcumuladoFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'semana_inicio', 'semana_fim', 'valor_acumulado', 'status', 'data_deposito']
    list_filter = ['status', 'semana_inicio', 'funcionario']
    search_fields = ['funcionario__nome', 'observacoes']
    date_hierarchy = 'semana_inicio'
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Informações do Acumulado', {'fields': ('funcionario', 'semana_inicio', 'semana_fim', 'valor_acumulado', 'status', 'data_deposito', 'observacoes')}),
        ('Controle', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo', 'valor', 'descricao_curta', 'funcionario', 'periodo']
    list_filter = ['tipo', 'data', 'categoria']
    search_fields = ['descricao', 'funcionario__nome']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']

    def descricao_curta(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_curta.short_description = 'Descrição'


@admin.register(PeriodoMovimentoCaixa)
class PeriodoMovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data_inicio', 'data_fim', 'status', 'valor_inicial_caixa', 'saldo_atual']
    list_filter = ['status', 'data_inicio']
    search_fields = ['nome', 'observacoes']
    date_hierarchy = 'data_inicio'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']
