from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cliente, NotaFiscal, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, Usuario, TabelaSeguro, TipoVeiculo, PlacaVeiculo, AuditoriaLog, CobrancaCarregamento, FechamentoFrete, ItemFechamentoFrete, DetalheItemFechamento, OcorrenciaNotaFiscal, FotoOcorrencia, FuncionarioFluxoCaixa, ReceitaEmpresa, CaixaFuncionario, MovimentoCaixaFuncionario, MovimentoBancario, ControleSaldoSemanal, AcertoDiarioCarregamento, CarregamentoCliente, DistribuicaoFuncionario, AcumuladoFuncionario, MovimentoCaixa, PeriodoMovimentoCaixa, SetorBancario

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['razao_social', 'nome_fantasia', 'cnpj', 'cidade', 'estado', 'status', 'telefone']
    list_filter = ['status', 'estado', 'cidade']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'cidade']
    list_editable = ['status']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'status')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
    )

@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ['nota', 'cliente', 'fornecedor', 'data', 'valor', 'peso', 'status']
    list_filter = ['status', 'data', 'cliente']
    search_fields = ['nota', 'fornecedor', 'mercadoria', 'cliente__razao_social']
    list_editable = ['status']
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cliente', 'nota', 'data', 'status')
        }),
        ('Mercadoria', {
            'fields': ('fornecedor', 'mercadoria', 'quantidade', 'peso', 'valor')
        }),
    )

@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf', 'cnh', 'cidade', 'estado', 'telefone']
    list_filter = ['estado', 'tipo_composicao_motorista']
    search_fields = ['nome', 'cpf', 'cnh', 'cidade']
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'cpf', 'data_nascimento')
        }),
        ('CNH', {
            'fields': ('cnh', 'codigo_seguranca', 'vencimento_cnh', 'uf_emissao_cnh')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Contato', {
            'fields': ('telefone',)
        }),
        ('Composição Veicular', {
            'fields': ('tipo_composicao_motorista', 'veiculo_principal', 'reboque_1', 'reboque_2')
        }),
    )

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'tipo_unidade', 'marca', 'modelo', 'proprietario_nome_razao_social']
    list_filter = ['tipo_unidade', 'marca', 'estado']
    search_fields = ['placa', 'chassi', 'renavam', 'proprietario_nome_razao_social']
    
    fieldsets = (
        ('Informações do Veículo', {
            'fields': ('tipo_unidade', 'placa', 'marca', 'modelo', 'ano_fabricacao')
        }),
        ('Documentação', {
            'fields': ('chassi', 'renavam', 'rntrc')
        }),
        ('Localização', {
            'fields': ('pais', 'estado', 'cidade')
        }),
        ('Medidas', {
            'fields': ('largura', 'altura', 'comprimento', 'cubagem')
        }),
        ('Proprietário', {
            'fields': ('proprietario_cpf_cnpj', 'proprietario_nome_razao_social', 'proprietario_rg_ie')
        }),
        ('Endereço do Proprietário', {
            'fields': ('proprietario_endereco', 'proprietario_numero', 'proprietario_bairro', 'proprietario_cidade', 'proprietario_estado', 'proprietario_cep')
        }),
        ('Contato do Proprietário', {
            'fields': ('proprietario_telefone',)
        }),
    )

@admin.register(RomaneioViagem)
class RomaneioViagemAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'cliente', 'motorista', 'get_composicao_veicular', 'data_emissao', 'status']
    list_filter = ['status', 'data_emissao', 'cliente', 'destino_estado']
    search_fields = ['codigo', 'cliente__razao_social', 'motorista__nome', 'origem_cidade', 'destino_cidade']
    date_hierarchy = 'data_emissao'
    filter_horizontal = ['notas_fiscais']
    readonly_fields = ['data_ultima_edicao', 'usuario_criacao', 'usuario_ultima_edicao']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('codigo', 'status', 'data_emissao')
        }),
        ('Participantes', {
            'fields': ('cliente', 'motorista')
        }),
        ('Composição Veicular', {
            'fields': ('veiculo_principal', 'reboque_1', 'reboque_2')
        }),
        ('Rota', {
            'fields': ('origem_cidade', 'origem_estado', 'destino_cidade', 'destino_estado')
        }),
        ('Datas', {
            'fields': ('data_saida', 'data_chegada_prevista', 'data_chegada_real')
        }),
        ('Carga', {
            'fields': ('notas_fiscais', 'peso_total', 'valor_total', 'quantidade_total')
        }),
        ('Seguro', {
            'fields': ('seguro_obrigatorio', 'percentual_seguro', 'valor_seguro')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle de Acesso', {
            'fields': ('usuario_criacao', 'usuario_ultima_edicao', 'data_ultima_edicao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_composicao_veicular(self, obj):
        return obj.get_composicao_veicular()
    get_composicao_veicular.short_description = 'Composição Veicular'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo romaneio
            obj.usuario_criacao = request.user
        obj.usuario_ultima_edicao = request.user
        super().save_model(request, obj, form, change)

@admin.register(HistoricoConsulta)
class HistoricoConsultaAdmin(admin.ModelAdmin):
    list_display = ['motorista', 'numero_consulta', 'data_consulta', 'gerenciadora', 'status_consulta']
    list_filter = ['status_consulta', 'data_consulta', 'gerenciadora']
    search_fields = ['motorista__nome', 'numero_consulta', 'gerenciadora']
    date_hierarchy = 'data_consulta'
    
    fieldsets = (
        ('Informações da Consulta', {
            'fields': ('motorista', 'numero_consulta', 'data_consulta', 'gerenciadora')
        }),
        ('Resultado', {
            'fields': ('status_consulta', 'observacoes')
        }),
    )

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_active', 'date_joined']
    list_filter = ['tipo_usuario', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['date_joined', 'ultimo_acesso']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'password')
        }),
        ('Tipo e Status', {
            'fields': ('tipo_usuario', 'is_active', 'is_staff')
        }),
        ('Cliente Vinculado', {
            'fields': ('cliente',),
            'description': 'Apenas para usuários do tipo Cliente'
        }),
        ('Informações Adicionais', {
            'fields': ('telefone', 'date_joined', 'ultimo_acesso')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Se é um novo usuário
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)

@admin.register(TabelaSeguro)
class TabelaSeguroAdmin(admin.ModelAdmin):
    list_display = ['estado', 'percentual_seguro', 'data_atualizacao']
    list_editable = ['percentual_seguro']
    list_filter = ['estado']
    search_fields = ['estado']
    readonly_fields = ['data_atualizacao']
    ordering = ['estado']
    
    fieldsets = (
        ('Informações do Estado', {
            'fields': ('estado',)
        }),
        ('Configuração de Seguro', {
            'fields': ('percentual_seguro',)
        }),
        ('Informações do Sistema', {
            'fields': ('data_atualizacao',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Permite adicionar apenas se não existir registro para o estado
        return True
    
    def has_delete_permission(self, request, obj=None):
        # Não permite deletar registros da tabela de seguros
        return False

@admin.register(TipoVeiculo)
class TipoVeiculoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações do Tipo', {
            'fields': ('nome', 'descricao', 'ativo')
        }),
    )

@admin.register(PlacaVeiculo)
class PlacaVeiculoAdmin(admin.ModelAdmin):
    list_display = ['placa', 'estado', 'cidade', 'pais', 'ativa', 'data_registro']
    list_filter = ['ativa', 'estado', 'pais', 'data_registro']
    search_fields = ['placa', 'estado', 'cidade']
    list_editable = ['ativa']
    readonly_fields = ['data_registro']
    
    fieldsets = (
        ('Informações da Placa', {
            'fields': ('placa', 'estado', 'cidade', 'pais', 'ativa')
        }),
        ('Informações do Sistema', {
            'fields': ('data_registro', 'observacoes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CobrancaCarregamento)
class CobrancaCarregamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'valor_total', 'status', 'data_vencimento', 'criado_em']
    list_filter = ['status', 'criado_em', 'data_vencimento']
    search_fields = ['cliente__razao_social', 'cliente__cnpj', 'observacoes']
    filter_horizontal = ['romaneios']
    readonly_fields = ['criado_em', 'atualizado_em', 'data_baixa']
    date_hierarchy = 'criado_em'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('cliente', 'romaneios', 'status')
        }),
        ('Valores', {
            'fields': ('valor_carregamento', 'valor_cte_manifesto')
        }),
        ('Datas', {
            'fields': ('data_vencimento', 'data_baixa')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Informações do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def valor_total(self, obj):
        return f"R$ {obj.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    valor_total.short_description = 'Valor Total'

@admin.register(AuditoriaLog)
class AuditoriaLogAdmin(admin.ModelAdmin):
    list_display = ['data_hora', 'modelo', 'objeto_id', 'acao', 'usuario', 'ip_address']
    list_filter = ['acao', 'modelo', 'data_hora', 'usuario']
    search_fields = ['modelo', 'objeto_id', 'usuario__username', 'ip_address', 'observacoes']
    readonly_fields = ['data_hora', 'modelo', 'objeto_id', 'acao', 'dados_anteriores', 'dados_novos', 'usuario', 'ip_address', 'user_agent']
    date_hierarchy = 'data_hora'
    ordering = ['-data_hora']
    
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('modelo', 'objeto_id', 'acao', 'data_hora')
        }),
        ('Usuário e Requisição', {
            'fields': ('usuario', 'ip_address', 'user_agent')
        }),
        ('Dados', {
            'fields': ('dados_anteriores', 'dados_novos'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    def has_add_permission(self, request):
        # Não permitir adicionar logs manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Não permitir editar logs
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Logs não devem ser deletados para manter auditoria
        return False

@admin.register(FechamentoFrete)
class FechamentoFreteAdmin(admin.ModelAdmin):
    list_display = ['id', 'data', 'motorista', 'frete_total', 'get_quantidade_romaneios', 'get_quantidade_clientes', 'usuario_criacao', 'data_criacao']
    list_filter = ['data', 'data_criacao', 'motorista', 'origem_romaneio']
    search_fields = ['motorista__nome', 'observacoes']
    filter_horizontal = ['romaneios']
    readonly_fields = ['data_criacao', 'usuario_criacao', 'cubagem_bau_total']
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('motorista', 'data', 'origem_romaneio')
        }),
        ('Romaneios', {
            'fields': ('romaneios',)
        }),
        ('Valores', {
            'fields': ('frete_total', 'ctr_total', 'carregamento_total')
        }),
        ('Cubagem do Baú', {
            'fields': ('cubagem_bau_a', 'cubagem_bau_b', 'cubagem_bau_c', 'cubagem_bau_total')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('usuario_criacao', 'data_criacao'),
            'classes': ('collapse',)
        }),
    )
    
    def get_quantidade_romaneios(self, obj):
        return obj.romaneios.count()
    get_quantidade_romaneios.short_description = 'Romaneios'
    
    def get_quantidade_clientes(self, obj):
        return obj.itens.count()
    get_quantidade_clientes.short_description = 'Clientes'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criacao = request.user
        super().save_model(request, obj, form, change)

@admin.register(ItemFechamentoFrete)
class ItemFechamentoFreteAdmin(admin.ModelAdmin):
    list_display = ['id', 'fechamento', 'cliente_consolidado', 'peso', 'cubagem', 'valor_mercadoria', 'valor_final']
    list_filter = ['fechamento__data', 'fechamento']
    search_fields = ['cliente_consolidado__razao_social', 'fechamento__id']
    filter_horizontal = ['romaneios']
    readonly_fields = ['valor_por_cubagem', 'percentual_cubagem', 'valor_por_percentual', 'valor_ideal', 'frete_proporcional', 'ctr_proporcional', 'carregamento_proporcional', 'valor_final']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('fechamento', 'cliente_consolidado', 'romaneios')
        }),
        ('Valores Consolidados', {
            'fields': ('peso', 'cubagem', 'valor_mercadoria')
        }),
        ('Cálculos Automáticos', {
            'fields': ('valor_por_cubagem', 'percentual_cubagem', 'frete_proporcional', 'ctr_proporcional', 'carregamento_proporcional')
        }),
        ('Percentual e Valor Ideal', {
            'fields': ('percentual_escolhido', 'valor_por_percentual', 'valor_ideal')
        }),
        ('Ajuste Manual', {
            'fields': ('percentual_ajustado', 'usar_ajuste_manual', 'valor_final')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )

@admin.register(DetalheItemFechamento)
class DetalheItemFechamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'item', 'romaneio', 'cliente_original', 'peso', 'valor']
    list_filter = ['item__fechamento__data', 'item__fechamento']
    search_fields = ['romaneio__codigo', 'cliente_original__razao_social', 'item__fechamento__id']
    readonly_fields = ['item', 'romaneio', 'cliente_original', 'peso', 'valor']
    
    fieldsets = (
        ('Informações', {
            'fields': ('item', 'romaneio', 'cliente_original')
        }),
        ('Valores', {
            'fields': ('peso', 'valor')
        }),
    )
    
    def has_add_permission(self, request):
        # Detalhes são criados automaticamente
        return False
    
    def has_change_permission(self, request, obj=None):
        # Detalhes não devem ser editados manualmente
        return False

@admin.register(OcorrenciaNotaFiscal)
class OcorrenciaNotaFiscalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nota_fiscal', 'usuario_criacao', 'data_criacao', 'get_quantidade_fotos']
    list_filter = ['data_criacao', 'usuario_criacao', 'nota_fiscal']
    search_fields = ['nota_fiscal__nota', 'observacoes', 'usuario_criacao__username']
    readonly_fields = ['data_criacao', 'usuario_criacao']
    date_hierarchy = 'data_criacao'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nota_fiscal', 'usuario_criacao', 'data_criacao')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    def get_quantidade_fotos(self, obj):
        return obj.fotos.count()
    get_quantidade_fotos.short_description = 'Fotos'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_criacao = request.user
        super().save_model(request, obj, form, change)

@admin.register(FotoOcorrencia)
class FotoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ['id', 'ocorrencia', 'data_upload', 'foto_preview']
    list_filter = ['data_upload', 'ocorrencia']
    search_fields = ['ocorrencia__id', 'ocorrencia__nota_fiscal__nota']
    readonly_fields = ['data_upload', 'foto_preview']
    date_hierarchy = 'data_upload'
    
    fieldsets = (
        ('Informações', {
            'fields': ('ocorrencia', 'foto', 'data_upload')
        }),
        ('Preview', {
            'fields': ('foto_preview',)
        }),
    )
    
    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.foto.url)
        return '-'
    foto_preview.short_description = 'Preview'


@admin.register(FuncionarioFluxoCaixa)
class FuncionarioFluxoCaixaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome']
    list_editable = ['ativo']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações', {
            'fields': ('nome', 'ativo')
        }),
        ('Controle', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SetorBancario)
class SetorBancarioAdmin(admin.ModelAdmin):
    list_display = ['setor', 'nome_responsavel', 'banco', 'agencia', 'conta_corrente', 'chave_pix', 'tipo_chave_pix', 'ativo']
    list_filter = ['setor', 'ativo', 'banco']
    search_fields = ['setor', 'nome_responsavel', 'banco', 'chave_pix']
    list_editable = ['ativo']
    
    fieldsets = (
        ('Informações do Setor', {
            'fields': ('setor', 'nome_responsavel', 'ativo')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta_corrente', 'chave_pix', 'tipo_chave_pix')
        }),
        ('Controle', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(ReceitaEmpresa)
class ReceitaEmpresaAdmin(admin.ModelAdmin):
    list_display = ['data', 'tipo_receita', 'valor', 'cliente', 'usuario_criacao', 'criado_em']
    list_filter = ['tipo_receita', 'data', 'cliente']
    search_fields = ['descricao', 'cliente__razao_social', 'tipo_receita']
    date_hierarchy = 'data'
    readonly_fields = ['criado_em', 'atualizado_em', 'usuario_criacao']
    
    fieldsets = (
        ('Informações da Receita', {
            'fields': ('data', 'tipo_receita', 'valor', 'descricao')
        }),
        ('Relacionamentos', {
            'fields': ('cliente', 'cobranca_carregamento')
        }),
        ('Controle', {
            'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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
        ('Informações do Caixa', {
            'fields': ('funcionario', 'periodo_tipo', 'semana_inicio', 'semana_fim', 'data', 'valor_coletado', 'observacoes')
        }),
        ('Acerto', {
            'fields': ('status', 'valor_acertado', 'data_acerto')
        }),
        ('Controle', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def periodo_display(self, obj):
        if obj.periodo_tipo == 'Semanal':
            return f"{obj.semana_inicio} a {obj.semana_fim}"
        else:
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
        ('Informações do Movimento', {
            'fields': ('data', 'tipo', 'valor', 'descricao', 'numero_documento')
        }),
        ('Origem e Relacionamentos', {
            'fields': ('origem', 'hash_importacao', 'receita_empresa')
        }),
        ('Controle', {
            'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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
        ('Período', {
            'fields': ('semana_inicio', 'semana_fim')
        }),
        ('Saldos Iniciais', {
            'fields': ('saldo_inicial_caixa', 'saldo_inicial_banco')
        }),
        ('Totais Calculados', {
            'fields': ('total_receitas_empresa', 'total_caixa_funcionarios', 'total_entradas_banco', 'total_saidas_banco', 'total_pendentes_receber', 'saldo_final_calculado')
        }),
        ('Saldos Finais Reais', {
            'fields': ('saldo_final_real_caixa', 'saldo_final_real_banco', 'diferenca')
        }),
        ('Validação', {
            'fields': ('validado', 'usuario_validacao', 'data_validacao')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Controle', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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
        ('Informações do Acerto', {
            'fields': ('data', 'valor_estelar', 'observacoes')
        }),
        ('Controle', {
            'fields': ('usuario_criacao', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
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
        ('Informações do Acumulado', {
            'fields': ('funcionario', 'semana_inicio', 'semana_fim', 'valor_acumulado', 'status', 'data_deposito', 'observacoes')
        }),
        ('Controle', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
