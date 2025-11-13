from django.db import models
from django.db.models import UniqueConstraint, Q
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.core.exceptions import ValidationError

# --------------------------------------------------------------------------------------
# Mixin para Soft Delete (Exclusão Suave)
# --------------------------------------------------------------------------------------
class SoftDeleteManager(models.Manager):
    """Manager que exclui automaticamente registros com deleted_at não nulo"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteMixin(models.Model):
    """Mixin que adiciona funcionalidade de soft delete aos modelos"""
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Data de Exclusão")
    deleted_by = models.ForeignKey(
        'Usuario', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_excluidos',
        verbose_name="Excluído por"
    )
    
    # Managers
    objects = SoftDeleteManager()  # Manager padrão (exclui soft deleted)
    all_objects = models.Manager()  # Manager para ver todos (incluindo soft deleted)
    
    class Meta:
        abstract = True
    
    @property
    def is_deleted(self):
        """Retorna True se o registro foi excluído (soft delete)"""
        return self.deleted_at is not None
    
    def soft_delete(self, user=None):
        """Marca o registro como excluído sem removê-lo do banco"""
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restaura um registro soft deleted"""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['deleted_at', 'deleted_by'])
    
    def delete(self, *args, **kwargs):
        """Override do delete padrão - usa soft delete por padrão"""
        # Se usar force_delete=True, exclui permanentemente
        if kwargs.pop('force_delete', False):
            return super().delete(*args, **kwargs)
        # Senão, usa soft delete
        self.soft_delete(user=kwargs.pop('user', None))

# Custom save method mixin for uppercase text fields
class UpperCaseMixin:
    def save(self, *args, **kwargs):
        # Detectar campos CharField automaticamente e converter para maiúsculo
        for field in self._meta.fields:
            if hasattr(field, 'max_length') and hasattr(self, field.name):
                value = getattr(self, field.name)
                if value and isinstance(value, str):
                    # Campos que NÃO devem ser convertidos para maiúsculo
                    exclude_fields = [
                        'email', 'password', 'username', 'cpf', 'cnpj', 
                        'cnh', 'chassi', 'renavam', 'placa', 'cep',
                        'telefone', 'rntrc', 'numero_consulta', 'tipo_usuario',
                        'status'  # Adicionado para não converter status para maiúsculo
                    ]
                    if field.name not in exclude_fields:
                        setattr(self, field.name, value.upper())
        
        super().save(*args, **kwargs)

# Manager customizado para o modelo Usuario
class UsuarioManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('O nome de usuário é obrigatório')
        if not email:
            raise ValueError('O email é obrigatório')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('tipo_usuario', 'admin')
        
        return self.create_user(username, email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        return self.get(username=username)

# --------------------------------------------------------------------------------------
# Clientes
# --------------------------------------------------------------------------------------
class Cliente(UpperCaseMixin, SoftDeleteMixin, models.Model):
    razao_social = models.CharField(max_length=255, unique=True, verbose_name="Razão Social") # Adicionado unique=True
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True, verbose_name="CNPJ")
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True, verbose_name="Inscrição Estadual")

    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=255, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado (UF)")
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")

    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")

    STATUS_CHOICES = [
        ('Ativo', 'Ativo'),
        ('Inativo', 'Inativo'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Ativo', verbose_name="Status")

    def __str__(self):
        return self.razao_social

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razao_social']

# --------------------------------------------------------------------------------------
# Notas Fiscal
# --------------------------------------------------------------------------------------
class NotaFiscal(UpperCaseMixin, SoftDeleteMixin, models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='notas_fiscais', verbose_name="Cliente")
    nota = models.CharField(max_length=50, verbose_name="Número da Nota")
    data = models.DateField(verbose_name="Data de Emissão") # Nome 'data' mantido, era o que o Django esperava
    fornecedor = models.CharField(max_length=200, verbose_name="Fornecedor")
    mercadoria = models.CharField(max_length=200, verbose_name="Mercadoria")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantidade")
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso (kg)")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")

    STATUS_NF_CHOICES = [ # Renomeado para evitar conflito com Cliente.STATUS_CHOICES
        ('Depósito', 'Depósito'),
        ('Enviada', 'Enviada'),
    ]
    status = models.CharField(max_length=20, default='Depósito', choices=STATUS_NF_CHOICES, verbose_name="Status da NF")
    
    # Campo para localização no depósito
    LOCAL_CHOICES = [
        ('1', 'Galpão 1'),
        ('2', 'Galpão 2'),
        ('3', 'Galpão 3'),
        ('4', 'Galpão 4'),
        ('5', 'Galpão 5'),
    ]
    local = models.CharField(max_length=10, choices=LOCAL_CHOICES, blank=True, null=True, verbose_name="Local")

    # Relação ManyToMany com RomaneioViagem (para que uma nota possa estar em vários romaneios)
    romaneios = models.ManyToManyField(
        'RomaneioViagem',
        related_name='notas_vinculadas', # Related_name para evitar conflito
        blank=True,
        verbose_name="Romaneios Vinculados"
    )

    def __str__(self):
        return f"Nota {self.nota} - Cliente: {self.cliente.razao_social}"
    
    @property
    def status_calculado(self):
        """Retorna o status correto baseado nos romaneios vinculados"""
        # Verificar através do related_name 'romaneios_vinculados' (do campo notas_fiscais no RomaneioViagem)
        # Este é o campo usado no template e no código
        try:
            # Usar romaneios_vinculados primeiro (related_name do campo notas_fiscais no RomaneioViagem)
            if hasattr(self, 'romaneios_vinculados') and self.romaneios_vinculados.exists():
                return 'Enviada'
            # Fallback para o campo romaneios direto (ManyToMany no NotaFiscal)
            if hasattr(self, 'romaneios') and self.romaneios.exists():
                return 'Enviada'
        except:
            pass
        
        # Caso contrário, status deve ser "Depósito"
        return 'Depósito'
    
    def corrigir_status(self):
        """Corrige o status da nota fiscal baseado nos romaneios vinculados"""
        status_correto = self.status_calculado
        if self.status != status_correto:
            self.status = status_correto
            self.save(update_fields=['status'])
            return True  # Retorna True se foi corrigido
        return False  # Retorna False se já estava correto

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ['-data', 'nota']
        constraints = [
            UniqueConstraint(fields=['nota', 'cliente', 'mercadoria', 'quantidade', 'peso'], 
                             name='unique_nota_fiscal_por_campos_chave')
        ]
# --------------------------------------------------------------------------------------
# Motorista
# --------------------------------------------------------------------------------------
class Motorista(UpperCaseMixin, SoftDeleteMixin, models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF") # Ex: 000.000.000-00
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG/RNE")
    cnh = models.CharField(max_length=11, unique=True, blank=True, null=True, verbose_name="CNH")
    codigo_seguranca = models.CharField(max_length=10, blank=True, null=True, verbose_name="Código de Segurança CNH")
    vencimento_cnh = models.DateField(blank=True, null=True, verbose_name="Vencimento CNH")
    uf_emissao_cnh = models.CharField(max_length=2, blank=True, null=True, verbose_name="UF Emissão CNH")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço")
    numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número")
    complemento = models.CharField(max_length=255, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado (UF)")
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento") 
    numero_consulta = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número da Última Consulta")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    # >>> NOVOS CAMPOS PARA A COMPOSIÇÃO VEICULAR NO MOTORISTA <<<
    TIPO_COMPOSICAO_MOTORISTA_CHOICES = [
        ('Carro', 'Carro'),
        ('Van', 'Van'),
        ('Caminhão', 'Caminhão'),
        ('Carreta', 'Carreta (Cavalo + 1 Reboque/Semi-reboque)'),
        ('Bitrem', 'Bitrem (Cavalo + 2 Reboques/Semi-reboques)'),
    ]
    tipo_composicao_motorista = models.CharField(
        max_length=50,
        choices=TIPO_COMPOSICAO_MOTORISTA_CHOICES,
        default='Caminhão',
        verbose_name="Tipo de Composição que Dirige"
    )

    veiculo_principal = models.ForeignKey( # Caminhão Trator, Carro ou Van
        'Veiculo',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='motoristas_veiculo_principal',
        verbose_name="Veículo Principal (Placa 1)"
    )
    reboque_1 = models.ForeignKey( # Primeiro Reboque/Semi-reboque (se Carreta ou Bi-trem)
        'Veiculo',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='motoristas_reboque_1',
        verbose_name="Reboque 1 (Placa 2)"
    )
    reboque_2 = models.ForeignKey( # Segundo Reboque/Semi-reboque (se Bi-trem)
        'Veiculo',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='motoristas_reboque_2',
        verbose_name="Reboque 2 (Placa 3)"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"
        ordering = ['nome']    

# --------------------------------------------------------------------------------------
# Tipos de Veículos
# --------------------------------------------------------------------------------------
class TipoVeiculo(models.Model):
    """
    Modelo para gerenciar os tipos de veículos disponíveis no sistema
    """
    nome = models.CharField(max_length=50, unique=True, verbose_name="Nome do Tipo")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Tipo de Veículo"
        verbose_name_plural = "Tipos de Veículos"
        ordering = ['nome']

# --------------------------------------------------------------------------------------
# Placas de Veículos
# --------------------------------------------------------------------------------------
class PlacaVeiculo(models.Model):
    """
    Modelo para gerenciar as placas dos veículos de forma organizada
    """
    placa = models.CharField(max_length=7, unique=True, verbose_name="Placa")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado (UF)")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    pais = models.CharField(max_length=50, default='Brasil', verbose_name="País")
    ativa = models.BooleanField(default=True, verbose_name="Placa Ativa")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    def __str__(self):
        return f"{self.placa} - {self.estado or 'N/A'}"
    
    class Meta:
        verbose_name = "Placa de Veículo"
        verbose_name_plural = "Placas de Veículos"
        ordering = ['placa']

# --------------------------------------------------------------------------------------
# Veículos
# --------------------------------------------------------------------------------------
class Veiculo(UpperCaseMixin, SoftDeleteMixin, models.Model):
    # Tipo da UNIDADE de Veículo (para menubar)
    TIPO_UNIDADE_CHOICES = [
        ('Carro', 'Carro'),
        ('Van', 'Van'),
        ('Caminhão', 'Caminhão'),
        ('Cavalo', 'Cavalo'),
        ('Reboque', 'Reboque'),
        ('Semi-reboque', 'Semi-reboque'),
    ]
    tipo_unidade = models.CharField(
        max_length=50,
        choices=TIPO_UNIDADE_CHOICES,
        default='Caminhão',
        verbose_name="Tipo da Unidade de Veículo"
    )

    placa = models.CharField(max_length=7, unique=True, verbose_name="Placa") # Max_length ajustado para 7 (Mercosul)
    pais = models.CharField(max_length=50, default='Brasil', verbose_name="País")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado (UF)")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    chassi = models.CharField(max_length=17, unique=True, blank=True, null=True, verbose_name="Chassi") # Max_length ajustado para 17
    renavam = models.CharField(max_length=11, unique=True, blank=True, null=True, verbose_name="Renavam")
    rntrc = models.CharField(max_length=12, blank=True, null=True, verbose_name="RNTRC") 
    ano_fabricacao = models.IntegerField(blank=True, null=True, verbose_name="Ano de Fabricação")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modelo")

    # Campos de Medidas do Baú
    largura = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Largura (m)")
    altura = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Altura (m)")
    comprimento = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, verbose_name="Comprimento (m)")
    cubagem = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cubagem (m³)")

    # Campos do Proprietário (diretamente no Veiculo)
    proprietario_cpf_cnpj = models.CharField(max_length=18, blank=True, null=True, verbose_name="CPF/CNPJ do Proprietário")
    proprietario_nome_razao_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome/Razão Social do Proprietário")
    proprietario_rg_ie = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG/IE do Proprietário")
    proprietario_telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone do Proprietário")
    proprietario_endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Endereço do Proprietário")
    proprietario_numero = models.CharField(max_length=10, blank=True, null=True, verbose_name="Número do Proprietário")
    proprietario_bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro do Proprietário")
    proprietario_cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade do Proprietário")
    proprietario_estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado do Proprietário (UF)")
    proprietario_cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP do Proprietário")

    def __str__(self):
        # Usar get_tipo_unidade_display() para o nome amigável das escolhas
        return f"{self.placa} ({self.get_tipo_unidade_display()})"

    class Meta:
        verbose_name = "Unidade de Veículo"
        verbose_name_plural = "Unidades de Veículos"
        ordering = ['placa']

# --------------------------------------------------------------------------------------
# NOVO MODELO: Romaneio de Viagem
# --------------------------------------------------------------------------------------
class RomaneioViagem(UpperCaseMixin, SoftDeleteMixin, models.Model):
    """
    Novo modelo de Romaneio de Viagem com estrutura mais robusta
    """
    
    # =============================================================================
    # INFORMAÇÕES BÁSICAS DO ROMANEIO
    # =============================================================================
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Código do Romaneio",
        help_text="Código único do romaneio (ex: ROM-001, ROM-002, ROM-003...)"
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
    
    # =============================================================================
    # RELACIONAMENTOS PRINCIPAIS
    # =============================================================================
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
    
    # =============================================================================
    # COMPOSIÇÃO VEICULAR
    # =============================================================================
    # Veículo principal (caminhão trator, carro, van)
    veiculo_principal = models.ForeignKey(
        Veiculo,
        on_delete=models.PROTECT,
        related_name='romaneios_veiculo_principal',
        verbose_name="Veículo Principal",
        help_text="Caminhão trator, carro ou van"
    )
    
    # Reboques (opcionais)
    reboque_1 = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='romaneios_reboque_1',
        verbose_name="Reboque 1",
        help_text="Primeiro reboque (opcional)"
    )
    
    reboque_2 = models.ForeignKey(
        Veiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='romaneios_reboque_2',
        verbose_name="Reboque 2",
        help_text="Segundo reboque (opcional)"
    )
    
    # =============================================================================
    # CARGA E MERCADORIAS
    # =============================================================================
    notas_fiscais = models.ManyToManyField(
        NotaFiscal,
        related_name='romaneios_vinculados',
        blank=True,
        verbose_name="Notas Fiscais"
    )
    
    # Campos para totalização da carga
    peso_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Peso Total (kg)",
        help_text="Peso total da carga em quilogramas"
    )
    
    valor_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor Total (R$)",
        help_text="Valor total da carga em reais"
    )
    
    quantidade_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Quantidade Total",
        help_text="Quantidade total de itens"
    )
    
    # =============================================================================
    # ROTAS E DESTINOS
    # =============================================================================
    origem_cidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Cidade de Origem"
    )
    
    origem_estado = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        verbose_name="Estado de Origem (UF)"
    )
    
    destino_cidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Cidade de Destino"
    )
    
    destino_estado = models.CharField(
        max_length=2, 
        blank=True, 
        null=True,
        verbose_name="Estado de Destino (UF)"
    )
    
    # =============================================================================
    # DATAS E PRAZOS
    # =============================================================================
    data_emissao = models.DateTimeField(
        default=timezone.now, 
        verbose_name="Data de Emissão"
    )
    
    data_saida = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Data de Saída",
        help_text="Data e hora de saída para a viagem"
    )
    
    data_chegada_prevista = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Data de Chegada Prevista",
        help_text="Data e hora prevista de chegada ao destino"
    )
    
    data_chegada_real = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Data de Chegada Real",
        help_text="Data e hora real de chegada ao destino"
    )
    
    # =============================================================================
    # INFORMAÇÕES ADICIONAIS
    # =============================================================================
    observacoes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Observações"
    )
    
    # Campos para controle de segurança
    seguro_obrigatorio = models.BooleanField(
        default=True,
        verbose_name="Seguro Obrigatório",
        help_text="Indica se o seguro é obrigatório para esta viagem"
    )
    
    percentual_seguro = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Percentual de Seguro (%)",
        help_text="Percentual de seguro aplicado baseado no estado de destino"
    )
    
    valor_seguro = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Valor do Seguro (R$)",
        help_text="Valor calculado do seguro"
    )
    
    # =============================================================================
    # CONTROLE DE ACESSO
    # =============================================================================
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
    
    data_ultima_edicao = models.DateTimeField(
        auto_now=True,
        verbose_name="Data da Última Edição"
    )
    
    # =============================================================================
    # MÉTODOS
    # =============================================================================
    def __str__(self):
        return f"Romaneio {self.codigo} - {self.cliente.razao_social}"
    
    def get_composicao_veicular(self):
        """Retorna a composição veicular completa"""
        composicao = [self.veiculo_principal.placa]
        if self.reboque_1:
            composicao.append(self.reboque_1.placa)
        if self.reboque_2:
            composicao.append(self.reboque_2.placa)
        return " + ".join(composicao)
    
    def get_tipo_composicao(self):
        """Retorna o tipo de composição veicular"""
        if self.reboque_2:
            return "Bi-trem"
        elif self.reboque_1:
            return "Carreta"
        else:
            return "Simples"
    
    def calcular_totais(self):
        """Calcula os totais baseado nas notas fiscais vinculadas"""
        if not self.notas_fiscais.exists():
            # Se não há notas fiscais, zerar os totais
            self.peso_total = 0
            self.valor_total = 0
            self.quantidade_total = 0
            self.save(update_fields=['peso_total', 'valor_total', 'quantidade_total'])
            return
        
        # Calcular totais com tratamento de valores None
        peso_total = sum(nf.peso or 0 for nf in self.notas_fiscais.all())
        valor_total = sum(nf.valor or 0 for nf in self.notas_fiscais.all())
        quantidade_total = sum(nf.quantidade or 0 for nf in self.notas_fiscais.all())
        
        # Verificar se os valores mudaram para evitar saves desnecessários
        if (self.peso_total != peso_total or 
            self.valor_total != valor_total or 
            self.quantidade_total != quantidade_total):
            
            self.peso_total = peso_total
            self.valor_total = valor_total
            self.quantidade_total = quantidade_total
            self.save(update_fields=['peso_total', 'valor_total', 'quantidade_total'])
            
            # Recalcular seguro se necessário
            if self.destino_estado and self.valor_total:
                self.calcular_seguro()
    
    def calcular_seguro(self):
        """Calcula o valor do seguro baseado no estado de destino"""
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
        """Valida se o peso total da carga não excede a capacidade do veículo"""
        if not self.peso_total or not self.veiculo_principal:
            return True, ""
        
        # Capacidades padrão por tipo de veículo (em kg)
        capacidades = {
            'Carro': 1000,
            'Van': 1500,
            'Caminhão': 10000,
            'Cavalo': 25000,  # Cavalo + reboque
            'Reboque': 25000,
            'Semi-reboque': 25000,
        }
        
        capacidade_principal = capacidades.get(self.veiculo_principal.tipo_unidade, 0)
        capacidade_reboque_1 = capacidades.get(self.reboque_1.tipo_unidade, 0) if self.reboque_1 else 0
        capacidade_reboque_2 = capacidades.get(self.reboque_2.tipo_unidade, 0) if self.reboque_2 else 0
        
        capacidade_total = capacidade_principal + capacidade_reboque_1 + capacidade_reboque_2
        
        if self.peso_total > capacidade_total:
            return False, f"Peso total da carga ({self.peso_total:.2f} kg) excede a capacidade total dos veículos ({capacidade_total} kg)."
        
        return True, ""
    
    def get_resumo_carga(self):
        """Retorna um resumo da carga do romaneio"""
        if not self.notas_fiscais.exists():
            return {
                'total_notas': 0,
                'peso_total': 0,
                'valor_total': 0,
                'quantidade_total': 0,
                'capacidade_utilizada': 0,
                'capacidade_maxima': 0,
            }
        
        # Calcular capacidade total
        capacidades = {
            'Carro': 1000,
            'Van': 1500,
            'Caminhão': 10000,
            'Cavalo': 25000,
            'Reboque': 25000,
            'Semi-reboque': 25000,
        }
        
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
            'percentual_capacidade': (self.peso_total / capacidade_maxima * 100) if capacidade_maxima > 0 else 0,
        }
    
    def gerar_codigo_automatico(self):
        """Gera código automático para o romaneio no formato ROM-NNN (sequencial sem resetar)"""
        if self.codigo:
            return
        
        # Buscar todos os romaneios (exceto genéricos ROM-100-XXX)
        romaneios = RomaneioViagem.objects.exclude(
            codigo__startswith="ROM-100-"
        ).exclude(
            codigo__isnull=True
        ).exclude(
            codigo=""
        )
        
        max_sequence = 0
        
        # Extrair números de todos os formatos possíveis
        for romaneio in romaneios:
            if not romaneio.codigo:
                continue
                
            try:
                parts = romaneio.codigo.split('-')
                
                # Formato ROM-XXX (formato simples)
                if len(parts) == 2 and parts[0] == 'ROM':
                    num = int(parts[1])
                    max_sequence = max(max_sequence, num)
                
                # Formato ROM-YYYY-MM-XXXX (formato com data)
                elif len(parts) == 4 and parts[0] == 'ROM':
                    num = int(parts[3])
                    max_sequence = max(max_sequence, num)
                
                # Formato ROM-YYYY-MM-XXXX (caso tenha menos partes mas ainda seja numérico)
                elif len(parts) >= 2 and parts[0] == 'ROM':
                    # Tentar extrair o último número
                    for part in reversed(parts[1:]):
                        if part.isdigit():
                            num = int(part)
                            max_sequence = max(max_sequence, num)
                            break
                            
            except (ValueError, IndexError):
                continue
        
        # Próximo número sequencial (nunca reseta)
        next_sequence = max_sequence + 1
        
        self.codigo = f"ROM-{next_sequence:03d}"
    
    def save(self, *args, **kwargs):
        # Gerar código automático se não existir
        if not self.codigo:
            self.gerar_codigo_automatico()
        
        # Verificar se é uma atualização de campos específicos (para evitar recursão)
        update_fields = kwargs.get('update_fields')
        
        # Calcular totais se há notas fiscais e não é uma atualização de campos específicos
        super().save(*args, **kwargs)
        
        if not update_fields and self.notas_fiscais.exists():
            self.calcular_totais()
        
        # Calcular seguro se há destino e valor e não é uma atualização de campos específicos
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

# --------------------------------------------------------------------------------------
# MODELO: DespesaCarregamento (para gerenciar despesas de carregamento)
# --------------------------------------------------------------------------------------
class DespesaCarregamento(models.Model):
    """
    Modelo para gerenciar despesas de carregamento (Carregamento, CTE/Manifesto)
    vinculadas a um romaneio
    """
    TIPO_DESPESA_CHOICES = [
        ('Carregamento', 'Carregamento'),
        ('CTE/Manifesto', 'CTE/Manifesto'),
    ]
    
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Baixado', 'Baixado'),
    ]
    
    romaneio = models.ForeignKey(
        RomaneioViagem,
        on_delete=models.CASCADE,
        related_name='despesas',
        verbose_name="Romaneio"
    )
    
    tipo_despesa = models.CharField(
        max_length=20,
        choices=TIPO_DESPESA_CHOICES,
        verbose_name="Tipo de Despesa"
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendente',
        verbose_name="Status"
    )
    
    data_vencimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Vencimento"
    )
    
    data_baixa = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Baixa"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Despesa de Carregamento"
        verbose_name_plural = "Despesas de Carregamento"
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['romaneio']),
            models.Index(fields=['status']),
            models.Index(fields=['tipo_despesa']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_despesa_display()} - {self.romaneio.codigo} - R$ {self.valor}"

# --------------------------------------------------------------------------------------
# MODELO: CobrancaCarregamento (Nova estrutura - agrupa múltiplos romaneios)
# --------------------------------------------------------------------------------------
class CobrancaCarregamento(models.Model):
    """
    Modelo para gerenciar cobranças de carregamento agrupando múltiplos romaneios
    de um cliente (que pode ter múltiplos CNPJs)
    """
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Baixado', 'Baixado'),
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
        verbose_name="Romaneios",
        help_text="Selecione os romaneios que fazem parte desta cobrança"
    )
    
    valor_carregamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Carregamento (R$)"
    )
    
    valor_cte_manifesto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor CTE/Manifesto (R$)"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendente',
        verbose_name="Status"
    )
    
    data_vencimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Vencimento"
    )
    
    data_baixa = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Baixa"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
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
        romaneios_str = ", ".join([r.codigo for r in self.romaneios.all()[:3]])
        if self.romaneios.count() > 3:
            romaneios_str += f" (+{self.romaneios.count() - 3} mais)"
        return f"Cobrança {self.id} - {self.cliente.razao_social} - {romaneios_str}"
    
    @property
    def valor_total(self):
        """Calcula o valor total da cobrança"""
        carregamento = self.valor_carregamento or 0
        cte_manifesto = self.valor_cte_manifesto or 0
        return carregamento + cte_manifesto
    
    def get_romaneios_display(self):
        """Retorna string com os códigos dos romaneios"""
        return ", ".join([r.codigo for r in self.romaneios.all()])

# --------------------------------------------------------------------------------------
# NOVO MODELO: HistoricoConsulta (para registrar cada consulta de risco)
# --------------------------------------------------------------------------------------
class HistoricoConsulta(UpperCaseMixin, models.Model):
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.CASCADE, # Se o motorista for excluído, o histórico de consulta também é
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

# --------------------------------------------------------------------------------------
# Modelo de Usuário do Sistema
# --------------------------------------------------------------------------------------
class Usuario(UpperCaseMixin, AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('funcionario', 'Funcionário'),
        ('cliente', 'Cliente'),
    ]
    
    # Campos básicos já existem no AbstractUser
    # username, email, first_name, last_name, is_active, is_staff, date_joined, password
    
    # Tipo de usuário
    tipo_usuario = models.CharField(
        max_length=20, 
        choices=TIPO_USUARIO_CHOICES,
        default='funcionario',
        verbose_name="Tipo de Usuário"
    )
    
    # Relacionamento com Cliente (apenas para usuários do tipo 'cliente')
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Cliente Vinculado"
    )
    
    # Campos adicionais
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    ultimo_acesso = models.DateTimeField(null=True, blank=True, verbose_name="Último Acesso")
    
    # Atributos obrigatórios para modelo de usuário customizado
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    USERNAME_FIELD = 'username'
    is_authenticated = True
    is_anonymous = False
    
    # Manager customizado
    objects = UsuarioManager()
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} ({self.get_tipo_usuario_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    @property
    def is_admin(self):
        return self.tipo_usuario == 'admin'
    
    @property
    def is_funcionario(self):
        return self.tipo_usuario == 'funcionario'
    
    @property
    def is_cliente(self):
        return self.tipo_usuario == 'cliente'
    
    def can_access_all(self):
        """Administradores têm acesso a tudo"""
        return self.is_admin
    
    def can_access_funcionalidades(self):
        """Funcionários têm acesso às funcionalidades principais"""
        return self.is_admin or self.is_funcionario
    
    def can_access_client_data(self):
        """Clientes só podem acessar seus próprios dados"""
        return self.is_admin or self.is_funcionario or self.is_cliente
    
    # Métodos de autenticação já existem no AbstractUser
    # set_password, check_password, get_username, natural_key, is_anonymous, is_authenticated

# --------------------------------------------------------------------------------------
# Agenda de Entregas
# --------------------------------------------------------------------------------------
class AgendaEntrega(UpperCaseMixin, models.Model):
    """
    Modelo para agendar entregas de mercadorias futuras
    """
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='agenda_entregas',
        verbose_name="Cliente"
    )
    
    data_entrega = models.DateField(
        verbose_name="Data da Entrega",
        help_text="Data prevista para a entrega"
    )
    
    empresa_entrega = models.CharField(
        max_length=255,
        verbose_name="Empresa que vai Entregar",
        help_text="Nome da empresa responsável pela entrega"
    )
    
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Quantidade",
        help_text="Quantidade de mercadorias a serem entregues"
    )
    
    volume = models.CharField(
        max_length=100,
        verbose_name="Volume",
        help_text="Volume ou tipo de embalagem (ex: 10 caixas, 5 pallets)"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações",
        help_text="Observações adicionais sobre a entrega"
    )
    
    STATUS_ENTREGA_CHOICES = [
        ('Agendada', 'Agendada'),
        ('Entregue', 'Entregue'),
        ('Cancelada', 'Cancelada'),
    ]
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_ENTREGA_CHOICES,
        default='Agendada',
        verbose_name="Status da Entrega"
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='agenda_entregas_criadas',
        verbose_name="Usuário de Criação",
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"Entrega para {self.cliente.razao_social} - {self.data_entrega.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Agenda de Entrega"
        verbose_name_plural = "Agenda de Entregas"
        ordering = ['data_entrega', 'cliente']
        indexes = [
            models.Index(fields=['data_entrega']),
            models.Index(fields=['status']),
            models.Index(fields=['cliente']),
        ]

# --------------------------------------------------------------------------------------
# Tabela de Seguros
# --------------------------------------------------------------------------------------
class TabelaSeguro(models.Model):
    ESTADOS_BRASIL = [
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AP', 'Amapá'),
        ('AM', 'Amazonas'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'),
        ('PA', 'Pará'),
        ('PB', 'Paraíba'),
        ('PR', 'Paraná'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'),
        ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]
    
    estado = models.CharField(
        max_length=2, 
        choices=ESTADOS_BRASIL, 
        unique=True, 
        verbose_name="Estado (UF)"
    )
    percentual_seguro = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Percentual de Seguro (%)"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True, 
        verbose_name="Data de Atualização"
    )
    
    def __str__(self):
        return f"{self.get_estado_display()} - {self.percentual_seguro}%"
    
    class Meta:
        verbose_name = "Tabela de Seguro"
        verbose_name_plural = "Tabela de Seguros"
        ordering = ['estado']


# --------------------------------------------------------------------------------------
# Log de Auditoria
# --------------------------------------------------------------------------------------
class AuditoriaLog(models.Model):
    """Registra todas as ações importantes do sistema para auditoria"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Edição'),
        ('DELETE', 'Exclusão'),
        ('SOFT_DELETE', 'Exclusão Suave'),
        ('RESTORE', 'Restauração'),
        ('VIEW', 'Visualização'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Exportação'),
        ('IMPORT', 'Importação'),
        ('IMPERSONATE', 'Impersonação'),
        ('END_IMPERSONATE', 'Fim de Impersonação'),
    ]
    
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acoes_auditadas',
        verbose_name="Usuário"
    )
    
    acao = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name="Ação"
    )
    
    modelo = models.CharField(
        max_length=100,
        verbose_name="Modelo",
        help_text="Nome do modelo afetado (ex: Cliente, NotaFiscal)"
    )
    
    objeto_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="ID do Objeto",
        help_text="ID do registro afetado"
    )
    
    descricao = models.TextField(
        verbose_name="Descrição",
        help_text="Descrição detalhada da ação realizada"
    )
    
    dados_anteriores = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Anteriores",
        help_text="Estado do objeto antes da mudança (para updates/deletes)"
    )
    
    dados_novos = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Dados Novos",
        help_text="Estado do objeto depois da mudança (para creates/updates)"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP"
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="User Agent",
        help_text="Informações do navegador/cliente"
    )
    
    data_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e Hora"
    )
    
    def __str__(self):
        usuario_nome = self.usuario.username if self.usuario else "Sistema"
        return f"{self.get_acao_display()} - {self.modelo} - {usuario_nome} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
    
    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['usuario', 'data_hora']),
            models.Index(fields=['modelo', 'acao']),
            models.Index(fields=['objeto_id', 'modelo']),
            models.Index(fields=['acao', 'data_hora']),
        ]


