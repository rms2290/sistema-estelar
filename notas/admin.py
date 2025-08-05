from django.contrib import admin
from .models import Cliente, NotaFiscal, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, Usuario, TabelaSeguro

admin.site.register(NotaFiscal)
admin.site.register(Cliente)
admin.site.register(Motorista)
admin.site.register(Veiculo)

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