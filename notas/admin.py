from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cliente, NotaFiscal, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, Usuario, TabelaSeguro, TipoVeiculo, PlacaVeiculo

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