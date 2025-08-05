from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractUser

# Custom save method mixin for uppercase text fields
class UpperCaseMixin:
    def save(self, *args, **kwargs):
        # List of fields that should be converted to uppercase
        uppercase_fields = [
            'razao_social', 'nome_fantasia', 'inscricao_estadual', 'endereco', 
            'complemento', 'bairro', 'cidade',
            'nome', 'codigo_seguranca', 'endereco', 'complemento', 'bairro', 'cidade',
            'numero_consulta',
            'fornecedor', 'mercadoria',
            'marca', 'modelo', 'cidade',
            'proprietario_nome_razao_social', 'proprietario_rg_ie', 'proprietario_endereco',
            'proprietario_bairro', 'proprietario_cidade',
            'first_name', 'last_name',
            'numero_consulta', 'gerenciadora',
        ]
        
        # Convert text fields to uppercase
        for field_name in uppercase_fields:
            if hasattr(self, field_name) and getattr(self, field_name):
                current_value = getattr(self, field_name)
                if isinstance(current_value, str):
                    setattr(self, field_name, current_value.upper())
        
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
class Cliente(UpperCaseMixin, models.Model):
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
class NotaFiscal(UpperCaseMixin, models.Model):
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

    # Relação ManyToMany com RomaneioViagem (para que uma nota possa estar em vários romaneios)
    romaneios = models.ManyToManyField(
        'RomaneioViagem',
        related_name='notas_vinculadas', # Related_name específico para evitar conflitos
        blank=True,
        verbose_name="Romaneios Vinculados"
    )

    def __str__(self):
        return f"Nota {self.nota} - Cliente: {self.cliente.razao_social}"

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
class Motorista(UpperCaseMixin, models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF") # Ex: 000.000.000-00
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

    # >>> NOVOS CAMPOS PARA A COMPOSIÇÃO VEICULAR NO MOTORISTA <<<
    TIPO_COMPOSICAO_MOTORISTA_CHOICES = [
        ('Simples', 'Simples (Carro/Van/Truck)'),
        ('Carreta', 'Carreta (Caminhão Trator + 1 Reboque/Semi-reboque)'),
        ('Bi-trem', 'Bi-trem (Caminhão Trator + 2 Reboques/Semi-reboques)'),
    ]
    tipo_composicao_motorista = models.CharField(
        max_length=50,
        choices=TIPO_COMPOSICAO_MOTORISTA_CHOICES,
        default='Simples',
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
# Veiculo
# --------------------------------------------------------------------------------------
class Veiculo(UpperCaseMixin, models.Model):
    # Tipo da UNIDADE de Veículo (para menubar)
    TIPO_UNIDADE_CHOICES = [
        ('Carro', 'Carro'),
        ('Van', 'Van'),
        ('Truck', 'Caminhão Trator'),
        ('Reboque', 'Reboque'),
        ('Semi-reboque', 'Semi-reboque'),
    ]
    tipo_unidade = models.CharField(
        max_length=50,
        choices=TIPO_UNIDADE_CHOICES,
        default='Truck',
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
# Romaneio
# --------------------------------------------------------------------------------------
class RomaneioViagem(models.Model):
    # Alterado para CharField para código sequencial tipo ROM-AAAA-MM-NNNN
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código do Romaneio") 
    
    # Status do Romaneio
    STATUS_ROMANEIO_CHOICES = [
        ('Rascunho', 'Rascunho'),
        ('Emitido', 'Emitido'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_ROMANEIO_CHOICES, default='Rascunho', verbose_name="Status do Romaneio")

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='romaneios_cliente',
        verbose_name="Cliente"
    )
    # Apontando para Veiculo (unidade)
    veiculo = models.ForeignKey( 
        Veiculo,
        on_delete=models.PROTECT,
        related_name='romaneios_veiculo',
        verbose_name="Unidade de Veículo"
    )
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        related_name='romaneios_motorista',
        verbose_name="Motorista"
    )
    # ManyToManyField para Notas Fiscais
    notas_fiscais = models.ManyToManyField(
        NotaFiscal,
        related_name='romaneios_vinculados',
        blank=True,
        verbose_name="Notas Fiscais"
    )

    data_emissao = models.DateTimeField(default=timezone.now, verbose_name="Data de Emissão")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    def __str__(self):
        return f"Romaneio {self.codigo} - Cliente: {self.cliente.razao_social}"

    class Meta:
        verbose_name = "Romaneio de Viagem"
        verbose_name_plural = "Romaneios de Viagem"
        ordering = ['-data_emissao', 'codigo']

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
