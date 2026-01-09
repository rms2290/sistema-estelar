"""
=============================================================================
MODELOS DO SISTEMA ESTELAR
=============================================================================

Este módulo contém todos os modelos de dados do sistema de gestão de 
transportes e logística da Agência Estelar.

Estrutura:
----------
1. Mixins e Utilitários
   - UpperCaseMixin: Converte campos de texto para maiúsculas automaticamente
   - UsuarioManager: Gerenciador customizado para usuários

2. Modelos Principais
   - Usuario: Sistema de autenticação e autorização
   - Cliente: Empresas clientes do sistema
   - NotaFiscal: Notas fiscais de entrada
   - Motorista: Cadastro de motoristas
   - Veiculo: Cadastro de veículos e unidades
   - RomaneioViagem: Romaneios de viagem

3. Modelos Auxiliares
   - TabelaSeguro: Tabela de percentuais de seguro por estado
   - HistoricoConsulta: Histórico de consultas de motoristas
   - AgendaEntrega: Agenda de entregas
   - CobrancaCarregamento: Cobranças de carregamento
   - AuditoriaLog: Logs de auditoria do sistema

Autor: Sistema Estelar
Data: 2025
Versão: 2.0
=============================================================================
"""
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone
from django.contrib.auth.models import BaseUserManager, AbstractUser


# ============================================================================
# MIXINS E UTILITÁRIOS
# ============================================================================

class UpperCaseMixin:
    """
    Mixin que converte automaticamente campos de texto para maiúsculas.
    
    Aplica-se a todos os campos CharField do modelo, exceto aqueles
    especificados na lista de exclusão (emails, senhas, CPF/CNPJ, etc.).
    
    Uso:
        class MeuModelo(UpperCaseMixin, models.Model):
            nome = models.CharField(max_length=100)
            # 'nome' será automaticamente convertido para maiúsculas
    
    Campos Excluídos da Conversão:
        - email, password, username
        - cpf, cnpj, cnh, chassi, renavam, placa, cep
        - telefone, rntrc, numero_consulta
        - tipo_usuario, status, rg
    """
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
                        'status', 'rg', 'tipo', 'categoria', 'tipo_pagamento', 'tipo_cliente'  # Adicionado tipo_cliente para não converter
                    ]
                    if field.name not in exclude_fields:
                        setattr(self, field.name, value.upper())
        
        super().save(*args, **kwargs)

class UsuarioManager(BaseUserManager):
    """
    Gerenciador customizado para o modelo Usuario.
    
    Fornece métodos para criar usuários normais e superusuários,
    seguindo as melhores práticas do Django.
    
    Métodos:
        create_user: Cria um usuário normal
        create_superuser: Cria um superusuário (admin)
        get_by_natural_key: Busca usuário por username
    """
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

# ============================================================================
# MODELOS PRINCIPAIS
# ============================================================================

# -----------------------------------------------------------------------------
# CLIENTE
# -----------------------------------------------------------------------------

class Cliente(UpperCaseMixin, models.Model):
    """
    Modelo que representa uma empresa cliente do sistema.
    
    Armazena informações completas da empresa, incluindo dados cadastrais,
    endereço, contatos e status de ativação.
    
    Campos Principais:
        - razao_social: Nome oficial da empresa (obrigatório, único)
        - cnpj: CNPJ da empresa (opcional, único se informado)
        - nome_fantasia: Nome comercial (opcional)
        - status: Ativo ou Inativo
    
    Relacionamentos:
        - notas_fiscais: Notas fiscais do cliente (ForeignKey reverso)
        - romaneios_cliente: Romaneios do cliente (ForeignKey reverso)
    
    Ordenação Padrão: Por razão social (alfabética)
    
    Exemplo:
        cliente = Cliente.objects.create(
            razao_social='Empresa XYZ LTDA',
            cnpj='12345678000190',
            status='Ativo'
        )
    """
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
        indexes = [
            models.Index(fields=['razao_social'], name='cliente_razao_social_idx'),
            models.Index(fields=['status'], name='cliente_status_idx'),
        ]

# -----------------------------------------------------------------------------
# NOTA FISCAL
# -----------------------------------------------------------------------------

class NotaFiscal(UpperCaseMixin, models.Model):
    """
    Modelo que representa uma Nota Fiscal de entrada no sistema.
    
    Armazena informações completas da nota fiscal, incluindo dados do
    fornecedor, mercadoria, quantidades, pesos e valores. Pode estar
    vinculada a um ou mais romaneios de viagem.
    
    Campos Principais:
        - cliente: Cliente proprietário da nota (obrigatório)
        - nota: Número da nota fiscal (obrigatório)
        - data: Data de emissão (obrigatório)
        - fornecedor: Nome do fornecedor (obrigatório)
        - mercadoria: Descrição da mercadoria (obrigatório)
        - quantidade, peso, valor: Valores numéricos (obrigatórios)
        - status: Depósito ou Enviada
        - local: Galpão onde está armazenada (opcional)
    
    Relacionamentos:
        - cliente: Cliente proprietário (ForeignKey)
        - romaneios_vinculados: Romaneios que contêm esta nota (ManyToMany)
    
    Constraints:
        - UniqueConstraint: Evita duplicação de notas com mesmos dados chave
    
    Status:
        - 'Depósito': Nota está no depósito, disponível para romaneio
        - 'Enviada': Nota foi incluída em romaneio emitido
    
    Ordenação Padrão: Por data (mais recente primeiro), depois por número
    
    Exemplo:
        nota = NotaFiscal.objects.create(
            cliente=cliente,
            nota='NF001',
            data=date.today(),
            fornecedor='Fornecedor ABC',
            mercadoria='Produto XYZ',
            quantidade=100,
            peso=1000,
            valor=5000.00
        )
    """
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
            UniqueConstraint(fields=['nota', 'cliente', 'mercadoria', 'quantidade', 'peso'], 
                             name='unique_nota_fiscal_por_campos_chave')
        ]


# -----------------------------------------------------------------------------
# OCORRÊNCIA DE NOTA FISCAL
# -----------------------------------------------------------------------------

class OcorrenciaNotaFiscal(models.Model):
    """
    Modelo que representa uma ocorrência registrada para uma nota fiscal.
    
    Permite registrar observações e anexar múltiplas fotos relacionadas a problemas,
    avarias ou outras situações relacionadas à nota fiscal.
    
    Campos Principais:
        - nota_fiscal: Nota fiscal relacionada (ForeignKey)
        - observacoes: Descrição da ocorrência (obrigatório)
        - data_criacao: Data e hora de criação (automático)
        - usuario_criacao: Usuário que registrou a ocorrência (ForeignKey)
    
    Relacionamentos:
        - nota_fiscal: Nota fiscal à qual a ocorrência pertence
        - usuario_criacao: Usuário que criou a ocorrência
        - fotos: Fotos relacionadas à ocorrência (ForeignKey reverso)
    
    Ordenação Padrão: Por data de criação (mais recente primeiro)
    
    Exemplo:
        ocorrencia = OcorrenciaNotaFiscal.objects.create(
            nota_fiscal=nota,
            observacoes='Mercadoria com avaria na embalagem',
            usuario_criacao=usuario
        )
    """
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
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
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
    """
    Modelo que representa uma foto anexada a uma ocorrência de nota fiscal.
    
    Permite anexar múltiplas fotos a uma mesma ocorrência.
    
    Campos Principais:
        - ocorrencia: Ocorrência à qual a foto pertence (ForeignKey)
        - foto: Arquivo de imagem anexado (obrigatório)
        - data_upload: Data e hora do upload (automático)
    
    Relacionamentos:
        - ocorrencia: Ocorrência à qual a foto pertence
    
    Ordenação Padrão: Por data de upload (mais recente primeiro)
    """
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
    
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Upload"
    )
    
    def __str__(self):
        return f"Foto #{self.id} - Ocorrência #{self.ocorrencia.id}"
    
    class Meta:
        verbose_name = "Foto de Ocorrência"
        verbose_name_plural = "Fotos de Ocorrências"
        ordering = ['-data_upload']
        indexes = [
            models.Index(fields=['ocorrencia', 'data_upload'], name='foto_ocorrencia_idx'),
        ]


# -----------------------------------------------------------------------------
# MOTORISTA
# -----------------------------------------------------------------------------

class Motorista(UpperCaseMixin, models.Model):
    """
    Modelo que representa um motorista cadastrado no sistema.
    
    Armazena informações pessoais, documentos, endereço e composição
    veicular que o motorista está habilitado a dirigir.
    
    Campos Principais:
        - nome: Nome completo (obrigatório)
        - cpf: CPF do motorista (obrigatório, único)
        - cnh: Número da CNH (opcional, único se informado)
        - tipo_composicao_motorista: Tipo de composição que dirige
    
    Composição Veicular:
        - veiculo_principal: Veículo principal (caminhão, carro, van)
        - reboque_1: Primeiro reboque (opcional, para carretas)
        - reboque_2: Segundo reboque (opcional, para bitrens)
    
    Relacionamentos:
        - romaneios_motorista: Romaneios onde este motorista atuou
    
    Ordenação Padrão: Por nome (alfabética)
    
    Exemplo:
        motorista = Motorista.objects.create(
            nome='João Silva',
            cpf='12345678909',
            tipo_composicao_motorista='Caminhão'
        )
    """
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
        ('Carreta', 'Carreta (Cavalo + 1 Reboque)'),
        ('Bitrem', 'Bitrem (Cavalo + 2 Reboques)'),
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
    reboque_1 = models.ForeignKey( # Primeiro Reboque (se Carreta ou Bi-trem)
        'Veiculo',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='motoristas_reboque_1',
        verbose_name="Reboque 1 (Placa 2)"
    )
    reboque_2 = models.ForeignKey( # Segundo Reboque (se Bi-trem)
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
        indexes = [
            models.Index(fields=['nome'], name='motorista_nome_idx'),
            models.Index(fields=['tipo_composicao_motorista'], name='motorista_tipo_composicao_idx'),
        ]    

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

# -----------------------------------------------------------------------------
# VEÍCULO
# -----------------------------------------------------------------------------

class Veiculo(UpperCaseMixin, models.Model):
    """
    Modelo que representa uma unidade de veículo cadastrada no sistema.
    
    Pode ser um caminhão, carro, van, cavalo mecânico ou reboque.
    Armazena informações completas do veículo, incluindo dados do proprietário.
    
    Campos Principais:
        - tipo_unidade: Tipo da unidade (Carro, Van, Caminhão, Cavalo, Reboque)
        - placa: Placa do veículo (obrigatório, único)
        - chassi: Chassi do veículo (opcional, único se informado)
        - renavam: RENAVAM do veículo (opcional, único se informado)
        - marca, modelo, ano_fabricacao: Dados do veículo
    
    Medidas do Baú:
        - largura, altura, comprimento: Dimensões em metros
        - cubagem: Capacidade cúbica em m³
    
    Dados do Proprietário:
        - proprietario_*: Campos com informações do proprietário do veículo
    
    Relacionamentos:
        - motoristas_veiculo_principal: Motoristas que usam este veículo como principal
        - motoristas_reboque_1: Motoristas que usam este veículo como reboque 1
        - motoristas_reboque_2: Motoristas que usam este veículo como reboque 2
        - romaneios_veiculo_principal: Romaneios onde este veículo é o principal
        - romaneios_reboque_1: Romaneios onde este veículo é o reboque 1
        - romaneios_reboque_2: Romaneios onde este veículo é o reboque 2
    
    Ordenação Padrão: Por placa (alfabética)
    
    Exemplo:
        veiculo = Veiculo.objects.create(
            tipo_unidade='Caminhão',
            placa='ABC1234',
            marca='Volvo',
            modelo='FH 540',
            ano_fabricacao=2020
        )
    """
    # Tipo da UNIDADE de Veículo (para menubar)
    TIPO_UNIDADE_CHOICES = [
        ('Carro', 'Carro'),
        ('Van', 'Van'),
        ('Caminhão', 'Caminhão'),
        ('Cavalo', 'Cavalo'),
        ('Reboque', 'Reboque'),
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

# -----------------------------------------------------------------------------
# ROMANEIO DE VIAGEM
# -----------------------------------------------------------------------------

class RomaneioViagem(UpperCaseMixin, models.Model):
    """
    Modelo central do sistema que representa um romaneio de viagem.
    
    Um romaneio agrupa notas fiscais para transporte, vinculando cliente,
    motorista, veículos e informações de rota. É o documento principal
    para controle de carregamentos e entregas.
    
    Estrutura:
    ----------
    1. Informações Básicas
       - codigo: Código único do romaneio (ex: ROM-001, ROM-100-001)
       - status: Salvo ou Emitido
    
    2. Relacionamentos Principais
       - cliente: Cliente proprietário da carga
       - motorista: Motorista responsável pela viagem
       - veiculo_principal: Veículo principal da composição
       - reboque_1, reboque_2: Reboques opcionais
       - notas_fiscais: Notas fiscais incluídas no romaneio (ManyToMany)
    
    3. Carga e Mercadorias
       - peso_total, valor_total, quantidade_total: Totais calculados
    
    4. Rotas e Destinos
       - origem_cidade, origem_estado: Local de origem
       - destino_cidade, destino_estado: Local de destino
    
    5. Datas e Prazos
       - data_emissao: Data/hora de criação do romaneio
       - data_saida: Data/hora de saída para viagem
       - data_chegada_prevista: Data/hora prevista de chegada
       - data_chegada_real: Data/hora real de chegada
    
    6. Seguro
       - seguro_obrigatorio: Se seguro é obrigatório
       - percentual_seguro: Percentual baseado no estado de destino
       - valor_seguro: Valor calculado do seguro
    
    7. Controle de Acesso
       - usuario_criacao: Usuário que criou o romaneio
       - usuario_ultima_edicao: Usuário que editou por último
       - data_ultima_edicao: Data da última edição
    
    Métodos:
    --------
    - get_composicao_veicular(): Retorna string com placas da composição
    - get_tipo_composicao(): Retorna tipo (Simples, Carreta, Bi-trem)
    - calcular_totais(): Calcula totais baseado nas notas fiscais
    - calcular_seguro(): Calcula valor do seguro baseado no destino
    
    Status:
    -------
    - 'Salvo': Romaneio criado mas não emitido (pode ser editado)
    - 'Emitido': Romaneio emitido e notas marcadas como 'Enviada'
    
    Exemplo:
    --------
        romaneio = RomaneioViagem.objects.create(
            codigo='ROM-001',
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            status='Salvo'
        )
        romaneio.notas_fiscais.add(nota1, nota2)
        romaneio.calcular_totais()
    """
    
    # =============================================================================
    # INFORMAÇÕES BÁSICAS DO ROMANEIO
    # =============================================================================
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
        """
        Retorna a composição veicular completa em formato de string.
        
        Returns:
            str: String com placas da composição separadas por " + "
                 Exemplo: "ABC1234 + DEF5678 + GHI9012"
        
        Exemplo:
            >>> romaneio.get_composicao_veicular()
            'ABC1234 + DEF5678'
        """
        composicao = [self.veiculo_principal.placa]
        if self.reboque_1:
            composicao.append(self.reboque_1.placa)
        if self.reboque_2:
            composicao.append(self.reboque_2.placa)
        return " + ".join(composicao)
    
    def get_tipo_composicao(self):
        """
        Retorna o tipo de composição veicular baseado nos reboques.
        
        Returns:
            str: Tipo da composição:
                 - "Simples": Apenas veículo principal
                 - "Carreta": Veículo principal + 1 reboque
                 - "Bi-trem": Veículo principal + 2 reboques
        
        Exemplo:
            >>> romaneio.get_tipo_composicao()
            'Carreta'
        """
        if self.reboque_2:
            return "Bi-trem"
        elif self.reboque_1:
            return "Carreta"
        else:
            return "Simples"
    
    def calcular_totais(self):
        """
        Calcula os totais (peso, valor, quantidade) baseado nas notas fiscais vinculadas.
        
        Este método:
        1. Soma os valores de todas as notas fiscais vinculadas
        2. Atualiza os campos peso_total, valor_total e quantidade_total
        3. Recalcula o seguro se necessário (se houver destino e valor)
        4. Salva apenas os campos atualizados (otimização)
        
        Nota:
            Se não houver notas fiscais vinculadas, os totais são zerados.
        
        Exemplo:
            >>> romaneio.notas_fiscais.add(nota1, nota2)
            >>> romaneio.calcular_totais()
            >>> print(romaneio.peso_total)
            2000.00
        """
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
        """
        Calcula o valor do seguro baseado no estado de destino e valor total.
        
        Busca a tabela de seguro para o estado de destino e calcula:
        valor_seguro = valor_total * (percentual_seguro / 100)
        
        Pré-requisitos:
            - destino_estado deve estar preenchido
            - valor_total deve estar calculado
            - Deve existir TabelaSeguro para o estado de destino
        
        Atualiza:
            - percentual_seguro: Percentual da tabela
            - valor_seguro: Valor calculado
        
        Exemplo:
            >>> romaneio.destino_estado = 'SP'
            >>> romaneio.valor_total = 10000.00
            >>> romaneio.calcular_seguro()
            >>> print(romaneio.valor_seguro)
            250.00  # Se percentual for 2.5%
        """
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
        """
        Valida se o peso total da carga não excede a capacidade dos veículos.
        
        Calcula a capacidade total baseada no tipo de cada veículo da composição
        e compara com o peso total da carga.
        
        Returns:
            tuple: (valido: bool, mensagem: str)
                - valido: True se peso está dentro da capacidade, False caso contrário
                - mensagem: Mensagem de erro se inválido, string vazia se válido
        
        Capacidades Padrão (em kg):
            - Carro: 1.000 kg
            - Van: 1.500 kg
            - Caminhão: 10.000 kg
            - Cavalo: 25.000 kg
            - Reboque: 25.000 kg
        
        Exemplo:
            >>> valido, msg = romaneio.validar_capacidade_veiculo()
            >>> if not valido:
            ...     print(msg)
        """
        if not self.peso_total or not self.veiculo_principal:
            return True, ""
        
        # Capacidades padrão por tipo de veículo (em kg)
        from notas.utils.constants import CAPACIDADES_VEICULOS
        capacidades = CAPACIDADES_VEICULOS
        
        capacidade_principal = capacidades.get(self.veiculo_principal.tipo_unidade, 0)
        capacidade_reboque_1 = capacidades.get(self.reboque_1.tipo_unidade, 0) if self.reboque_1 else 0
        capacidade_reboque_2 = capacidades.get(self.reboque_2.tipo_unidade, 0) if self.reboque_2 else 0
        
        capacidade_total = capacidade_principal + capacidade_reboque_1 + capacidade_reboque_2
        
        if self.peso_total > capacidade_total:
            return False, f"Peso total da carga ({self.peso_total:.2f} kg) excede a capacidade total dos veículos ({capacidade_total} kg)."
        
        return True, ""
    
    def get_resumo_carga(self):
        """
        Retorna um dicionário com resumo completo da carga do romaneio.
        
        Inclui informações sobre notas fiscais, totais, capacidade utilizada
        e percentual de ocupação.
        
        Returns:
            dict: Dicionário com as seguintes chaves:
                - total_notas: Quantidade de notas fiscais vinculadas
                - peso_total: Peso total em kg
                - valor_total: Valor total em R$
                - quantidade_total: Quantidade total de itens
                - capacidade_utilizada: Peso total (igual a peso_total)
                - capacidade_maxima: Capacidade total dos veículos em kg
                - percentual_capacidade: Percentual de ocupação (0-100)
        
        Exemplo:
            >>> resumo = romaneio.get_resumo_carga()
            >>> print(f"Capacidade: {resumo['percentual_capacidade']:.1f}%")
            Capacidade: 75.5%
        """
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
            'percentual_capacidade': (self.peso_total / capacidade_maxima * 100) if capacidade_maxima > 0 else 0,
        }
    
    def gerar_codigo_automatico(self):
        """
        Gera código automático sequencial para o romaneio.
        
        Formato: ROM-YYYY-MM-NNNN
        - YYYY: Ano atual (4 dígitos)
        - MM: Mês atual (2 dígitos)
        - NNNN: Número sequencial do mês (4 dígitos)
        
        Exemplo: ROM-2025-11-0001
        
        Nota:
            Este método só gera código se o campo 'codigo' estiver vazio.
            Não sobrescreve códigos existentes.
        
        Exemplo:
            >>> romaneio = RomaneioViagem()
            >>> romaneio.gerar_codigo_automatico()
            >>> print(romaneio.codigo)
            'ROM-2025-11-0001'
        """
        if self.codigo:
            return
        
        ano_atual = timezone.now().year
        mes_atual = timezone.now().month
        
        # Buscar último romaneio do mês
        ultimo_romaneio = RomaneioViagem.objects.filter(
            codigo__startswith=f"ROM-{ano_atual}-{mes_atual:02d}"
        ).order_by('-codigo').first()
        
        if ultimo_romaneio:
            # Extrair número sequencial
            try:
                numero_atual = int(ultimo_romaneio.codigo.split('-')[-1])
                novo_numero = numero_atual + 1
            except (ValueError, IndexError):
                novo_numero = 1
        else:
            novo_numero = 1
        
        self.codigo = f"ROM-{ano_atual}-{mes_atual:02d}-{novo_numero:04d}"
    
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

# ============================================================================
# MODELOS AUXILIARES
# ============================================================================

# -----------------------------------------------------------------------------
# HISTÓRICO DE CONSULTA
# -----------------------------------------------------------------------------

class HistoricoConsulta(UpperCaseMixin, models.Model):
    """
    Modelo que registra o histórico de consultas de risco de motoristas.
    
    Cada consulta realizada em gerenciadoras de risco é registrada aqui,
    permitindo rastreamento completo do histórico do motorista.
    
    Campos Principais:
        - motorista: Motorista consultado (obrigatório)
        - numero_consulta: Número único da consulta (obrigatório, único)
        - data_consulta: Data em que a consulta foi realizada
        - gerenciadora: Nome da gerenciadora que realizou a consulta
        - status_consulta: Apto, Inapto ou Pendente
        - observacoes: Observações adicionais sobre a consulta
    
    Relacionamentos:
        - motorista: Motorista consultado (ForeignKey)
    
    Ordenação Padrão: Por data (mais recente primeiro), depois por motorista
    
    Exemplo:
        consulta = HistoricoConsulta.objects.create(
            motorista=motorista,
            numero_consulta='CONS-2025-001',
            gerenciadora='Serasa',
            status_consulta='Apto'
        )
    """
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

# -----------------------------------------------------------------------------
# USUÁRIO
# -----------------------------------------------------------------------------

class Usuario(UpperCaseMixin, AbstractUser):
    """
    Modelo de usuário customizado do sistema.
    
    Estende o AbstractUser do Django para adicionar funcionalidades
    específicas do sistema, incluindo tipos de usuário e relacionamento
    com clientes.
    
    Tipos de Usuário:
        - admin: Administrador do sistema (acesso total)
        - funcionario: Funcionário da agência (acesso operacional)
        - cliente: Cliente do sistema (acesso limitado aos próprios dados)
    
    Campos Adicionais:
        - tipo_usuario: Tipo do usuário (obrigatório)
        - cliente: Cliente vinculado (apenas para tipo 'cliente')
        - telefone: Telefone de contato
        - ultimo_acesso: Data/hora do último acesso ao sistema
    
    Métodos:
        - is_admin: Retorna True se usuário é administrador
        - is_funcionario: Retorna True se usuário é funcionário
        - is_cliente: Retorna True se usuário é cliente
    
    Relacionamentos:
        - cliente: Cliente vinculado (ForeignKey, opcional)
        - romaneios_criados: Romaneios criados por este usuário
        - romaneios_editados: Romaneios editados por este usuário
    
    Exemplo:
        usuario = Usuario.objects.create_user(
            username='joao.silva',
            email='joao@example.com',
            tipo_usuario='funcionario',
            first_name='João',
            last_name='Silva'
        )
    """
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
        """
        Verifica se o usuário é administrador.
        
        Returns:
            bool: True se tipo_usuario == 'admin', False caso contrário
        
        Exemplo:
            >>> if usuario.is_admin():
            ...     print("Acesso total permitido")
        """
        return self.tipo_usuario == 'admin'
    
    @property
    def is_funcionario(self):
        """
        Propriedade que verifica se o usuário é funcionário.
        
        Returns:
            bool: True se tipo_usuario == 'funcionario', False caso contrário
        
        Exemplo:
            >>> if usuario.is_funcionario:
            ...     print("Acesso operacional permitido")
        """
        return self.tipo_usuario == 'funcionario'
    
    @property
    def is_cliente(self):
        """
        Propriedade que verifica se o usuário é cliente.
        
        Returns:
            bool: True se tipo_usuario == 'cliente', False caso contrário
        
        Exemplo:
            >>> if usuario.is_cliente:
            ...     print("Acesso limitado aos próprios dados")
        """
        return self.tipo_usuario == 'cliente'
    
    def can_access_all(self):
        """
        Verifica se o usuário tem acesso total ao sistema.
        
        Apenas administradores têm acesso total. Funcionários e clientes
        têm acessos limitados.
        
        Returns:
            bool: True se usuário é administrador, False caso contrário
        
        Exemplo:
            >>> if usuario.can_access_all():
            ...     # Permitir acesso a todas as funcionalidades
        """
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
# Auditoria
# --------------------------------------------------------------------------------------
class AuditoriaLog(models.Model):
    """Modelo para registrar todas as ações de criação, edição e exclusão de registros"""
    
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


# --------------------------------------------------------------------------------------
# Cobrança de Carregamento
# --------------------------------------------------------------------------------------
class CobrancaCarregamento(UpperCaseMixin, models.Model):
    """Modelo para gerenciar cobranças de carregamento e CTE/Manifesto"""
    
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
    
    TIPO_CLIENTE_CHOICES = [
        ('Mensalista', 'Mensalista'),
        ('Por_Cubagem', 'Por Cubagem'),
    ]
    
    tipo_cliente = models.CharField(
        max_length=20,
        choices=TIPO_CLIENTE_CHOICES,
        default='Mensalista',
        verbose_name="Tipo de Cliente"
    )
    
    cubagem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True,
        verbose_name="Cubagem (m³)"
    )
    
    valor_cubagem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True,
        verbose_name="Valor da Cubagem (R$/m³)"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendente',
        verbose_name="Status"
    )
    
    data_vencimento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Vencimento"
    )
    
    data_baixa = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Baixa"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
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
        """Calcula o valor de armazenamento (cubagem * valor_cubagem)"""
        from decimal import Decimal
        # Verificar tipo_cliente de forma case-insensitive
        tipo = str(self.tipo_cliente).upper() if self.tipo_cliente else ''
        if tipo == 'POR_CUBAGEM' and self.cubagem and self.valor_cubagem:
            return self.cubagem * self.valor_cubagem
        return Decimal('0.00')
    
    @property
    def valor_total(self):
        """Calcula o valor total da cobrança"""
        total = (self.valor_carregamento or 0) + (self.valor_cte_manifesto or 0)
        # Verificar tipo_cliente de forma case-insensitive
        tipo = str(self.tipo_cliente).upper() if self.tipo_cliente else ''
        if tipo == 'POR_CUBAGEM':
            total += self.valor_armazenamento
        return total
    
    def baixar(self):
        """Marca a cobrança como baixada"""
        self.status = 'Baixado'
        self.data_baixa = timezone.now().date()
        self.save()


# --------------------------------------------------------------------------------------
# FECHAMENTO DE FRETE
# --------------------------------------------------------------------------------------

class FechamentoFrete(UpperCaseMixin, models.Model):
    """
    Modelo que representa um fechamento de frete.
    
    Um fechamento de frete consolida múltiplos romaneios e distribui
    o valor do frete, CTR e carregamento entre os clientes de forma
    proporcional à cubagem ou através de percentuais sobre o valor.
    
    Campos Principais:
        - romaneios: Romaneios associados ao fechamento (ManyToMany)
        - motorista: Motorista responsável
        - data: Data do fechamento
        - frete_total, ctr_total, carregamento_total: Valores totais
        - cubagem_bau: Medidas do baú (A, B, C)
    
    Relacionamentos:
        - romaneios: Múltiplos romaneios podem compor um fechamento
        - itens: Itens do fechamento (ItemFechamentoFrete)
        - motorista: Motorista responsável
        - usuario_criacao: Usuário que criou o fechamento
    """
    # Relacionamento com múltiplos romaneios
    romaneios = models.ManyToManyField(
        RomaneioViagem,
        related_name='fechamentos_frete',
        verbose_name="Romaneios Associados",
        help_text="Romaneios que compõem este fechamento"
    )
    
    motorista = models.ForeignKey(
        Motorista,
        on_delete=models.PROTECT,
        related_name='fechamentos_frete',
        verbose_name="Motorista"
    )
    
    data = models.DateField(
        verbose_name="Data do Fechamento",
        default=timezone.now
    )
    
    # Valores totais
    frete_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Frete Total (R$)"
    )
    
    ctr_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="CTR Total (R$)"
    )
    
    carregamento_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Carregamento Total (R$)"
    )
    
    # Cubagem do baú
    cubagem_bau_a = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cubagem Baú A (m³)"
    )
    
    cubagem_bau_b = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cubagem Baú B (m³)"
    )
    
    cubagem_bau_c = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cubagem Baú C (m³)"
    )
    
    cubagem_bau_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cubagem Baú Total (m³)",
        help_text="Calculado automaticamente (A + B + C)"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    # Controle
    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='fechamentos_criados',
        verbose_name="Usuário de Criação",
        null=True,
        blank=True
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    origem_romaneio = models.BooleanField(
        default=False,
        verbose_name="Criado a partir de Romaneios"
    )
    
    def calcular_cubagem_total(self):
        """Calcula a cubagem total do baú"""
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
        """Sobrescreve save para calcular cubagem total"""
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
    """
    Modelo que representa um item (cliente) em um fechamento de frete.
    
    Um item consolida um ou mais clientes/romaneios em um único cliente
    para efeito de cobrança. Por exemplo, pode agrupar "Atacado Tradição",
    "Atacado Total" e "Tx Mix" como um único cliente "Atacado Tradição".
    
    Campos Principais:
        - fechamento: Fechamento ao qual pertence
        - cliente_consolidado: Cliente consolidado (nome final)
        - peso, valor_mercadoria: Valores consolidados
        - cubagem: Cubagem do cliente
        - romaneios: Romaneios que compõem este item
    
    Cálculos:
        - valor_por_cubagem: (cubagem_cliente / cubagem_total) * frete_total
        - percentual_cubagem: (valor_por_cubagem / valor_mercadoria) * 100
        - percentuais: valor_mercadoria * percentual
        - distribuicoes: proporcional à cubagem
    """
    fechamento = models.ForeignKey(
        FechamentoFrete,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Fechamento"
    )
    
    # Cliente consolidado (pode ser diferente dos clientes originais)
    cliente_consolidado = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='itens_fechamento_consolidado',
        verbose_name="Cliente Consolidado"
    )
    
    # Valores consolidados
    peso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Peso Total (kg)",
        help_text="Soma dos pesos de todos os romaneios agrupados"
    )
    
    cubagem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cubagem (m³)"
    )
    
    valor_mercadoria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor Total (R$)",
        help_text="Soma dos valores de todos os romaneios agrupados"
    )
    
    # Relacionamento com romaneios que compõem este item
    romaneios = models.ManyToManyField(
        RomaneioViagem,
        related_name='itens_fechamento',
        verbose_name="Romaneios que Compõem"
    )
    
    # Cálculos automáticos
    valor_por_cubagem = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor por Cubagem (R$)"
    )
    
    percentual_cubagem = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Percentual sobre Cubagem (%)"
    )
    
    # Percentual escolhido (1% a 20%)
    percentual_escolhido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=6.00,
        verbose_name="Percentual Escolhido (%)",
        help_text="Percentual de 1% a 20% para cálculo"
    )
    
    valor_por_percentual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor por Percentual (R$)"
    )
    
    # Valor ideal = frete_total / valor_mercadoria
    valor_ideal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Ideal (R$)",
        help_text="Valor do frete dividido pelo valor da mercadoria"
    )
    
    percentual_ajustado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Percentual Ajustado Manual (R$)"
    )
    
    # Distribuição proporcional
    frete_proporcional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Frete Proporcional (R$)"
    )
    
    ctr_proporcional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="CTR Proporcional (R$)"
    )
    
    carregamento_proporcional = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Carregamento Proporcional (R$)"
    )
    
    # Valor final escolhido
    valor_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor Final a Cobrar (R$)"
    )
    
    usar_ajuste_manual = models.BooleanField(
        default=False,
        verbose_name="Usar Ajuste Manual"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    def calcular_valor_por_cubagem(self):
        """Calcula valor proporcional à cubagem"""
        if not self.fechamento.cubagem_bau_total or self.fechamento.cubagem_bau_total == 0:
            return 0
        if not self.cubagem:
            return 0
        return (self.cubagem / self.fechamento.cubagem_bau_total) * self.fechamento.frete_total
    
    def calcular_percentual_cubagem(self):
        """Calcula percentual sobre cubagem"""
        if not self.valor_mercadoria or self.valor_mercadoria == 0:
            return 0
        valor_cub = self.calcular_valor_por_cubagem()
        return (valor_cub / self.valor_mercadoria) * 100
    
    def calcular_valor_por_percentual(self):
        """Calcula valor baseado no percentual escolhido"""
        if not self.valor_mercadoria or not self.percentual_escolhido:
            return 0
        return self.valor_mercadoria * (self.percentual_escolhido / 100)
    
    def calcular_valor_ideal(self):
        """
        Calcula valor ideal baseado no percentual geral do frete sobre o valor total de mercadorias.
        
        Fórmula:
        1. Percentual Geral = (Frete Total / Valor Total de Mercadorias de TODOS os clientes) × 100
        2. Valor Ideal = Valor da Mercadoria do Cliente × Percentual Geral
        """
        if not self.valor_mercadoria or self.valor_mercadoria == 0:
            return 0
        
        if not self.fechamento.frete_total or self.fechamento.frete_total == 0:
            return 0
        
        # Calcular valor total de mercadorias de TODOS os clientes do fechamento
        from django.db.models import Sum
        valor_total_mercadorias = self.fechamento.itens.aggregate(
            total=Sum('valor_mercadoria')
        )['total'] or 0
        
        if valor_total_mercadorias == 0:
            return 0
        
        # Calcular percentual geral: (Frete Total / Valor Total Mercadorias) × 100
        percentual_geral = (self.fechamento.frete_total / valor_total_mercadorias) * 100
        
        # Aplicar percentual ao valor da mercadoria do cliente
        valor_ideal = self.valor_mercadoria * (percentual_geral / 100)
        
        return valor_ideal
    
    def calcular_distribuicoes(self):
        """Calcula distribuições proporcionais"""
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
        """Calcula todos os valores automaticamente"""
        self.valor_por_cubagem = self.calcular_valor_por_cubagem()
        self.percentual_cubagem = self.calcular_percentual_cubagem()
        
        # Calcular valor por percentual escolhido
        self.valor_por_percentual = self.calcular_valor_por_percentual()
        
        # Calcular valor ideal
        self.valor_ideal = self.calcular_valor_ideal()
        
        distribuicoes = self.calcular_distribuicoes()
        self.frete_proporcional = distribuicoes.get('frete', 0)
        self.ctr_proporcional = distribuicoes.get('ctr', 0)
        self.carregamento_proporcional = distribuicoes.get('carregamento', 0)
        
        # Valor final: usar ajuste manual se marcado, senão usar valor por cubagem
        if self.usar_ajuste_manual and self.percentual_ajustado:
            self.valor_final = self.percentual_ajustado
        else:
            self.valor_final = self.valor_por_cubagem
    
    def save(self, *args, **kwargs):
        """Sobrescreve save para calcular valores"""
        self.calcular_todos()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.cliente_consolidado.razao_social} - {self.fechamento}"
    
    class Meta:
        verbose_name = "Item de Fechamento de Frete"
        verbose_name_plural = "Itens de Fechamento de Frete"
        ordering = ['cliente_consolidado__razao_social']


class DetalheItemFechamento(models.Model):
    """
    Modelo que armazena detalhes de cada romaneio que compõe um item.
    
    Permite rastreabilidade de quais romaneios e clientes originais
    foram agrupados em cada item do fechamento.
    """
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
    
    peso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Peso (kg)"
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    
    def __str__(self):
        return f"{self.romaneio.codigo} - {self.cliente_original.razao_social}"
    
    class Meta:
        verbose_name = "Detalhe de Item de Fechamento"
        verbose_name_plural = "Detalhes de Item de Fechamento"
        ordering = ['romaneio__codigo']


# --------------------------------------------------------------------------------------
# FLUXO DE CAIXA
# --------------------------------------------------------------------------------------

class FuncionarioFluxoCaixa(UpperCaseMixin, models.Model):
    """Modelo simples para funcionários do fluxo de caixa (apenas nome)"""
    
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome do Funcionário")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Funcionário (Fluxo de Caixa)"
        verbose_name_plural = "Funcionários (Fluxo de Caixa)"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class AcertoDiarioCarregamento(UpperCaseMixin, models.Model):
    """Registra o acerto diário de carregamentos"""
    
    data = models.DateField(verbose_name="Data", unique=True)
    valor_estelar = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Estelar (R$)"
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    usuario_criacao = models.ForeignKey('Usuario', on_delete=models.PROTECT, related_name='acertos_diarios_criados')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Acerto Diário de Carregamento"
        verbose_name_plural = "Acertos Diários de Carregamento"
        ordering = ['-data']
        indexes = [
            models.Index(fields=['data']),
        ]
    
    @property
    def total_carregamentos(self):
        """Soma todos os valores de carregamento dos clientes"""
        from django.db.models import Sum
        from decimal import Decimal
        return self.carregamentos_cliente.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
    
    @property
    def total_funcionarios(self):
        """Soma todos os valores distribuídos aos funcionários"""
        from django.db.models import Sum
        from decimal import Decimal
        return self.distribuicoes_funcionario.aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')
    
    @property
    def total_distribuido(self):
        """Total distribuído (estelar + funcionários)"""
        return self.valor_estelar + self.total_funcionarios
    
    def __str__(self):
        return f"Acerto - {self.data}"


class CarregamentoCliente(UpperCaseMixin, models.Model):
    """Valores de carregamento por cliente ou descarga no acerto diário"""
    
    acerto_diario = models.ForeignKey(
        'AcertoDiarioCarregamento',
        on_delete=models.CASCADE,
        related_name='carregamentos_cliente',
        verbose_name="Acerto Diário"
    )
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.PROTECT,
        related_name='carregamentos_diarios',
        verbose_name="Cliente",
        null=True,
        blank=True,
        help_text="Deixe em branco para registrar uma descarga"
    )
    
    descricao = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição da descarga (quando não houver cliente)"
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    
    observacoes = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observações")
    
    TIPO_PAGAMENTO_CHOICES = [
        ('Dinheiro', 'Dinheiro'),
        ('Deposito', 'Depósito'),
    ]
    
    tipo_pagamento = models.CharField(
        max_length=10,
        choices=TIPO_PAGAMENTO_CHOICES,
        default='Dinheiro',
        blank=True,
        null=True,
        verbose_name="Tipo de Pagamento",
        help_text="Apenas para descargas. Se for depósito, não será contabilizado no movimento de caixa."
    )
    
    class Meta:
        verbose_name = "Carregamento/Descarga"
        verbose_name_plural = "Carregamentos e Descargas"
        ordering = ['cliente__razao_social', 'descricao']
    
    @property
    def tipo(self):
        """Retorna se é carregamento ou descarga"""
        return "Descarga" if not self.cliente else "Carregamento"
    
    @property
    def nome_display(self):
        """Retorna o nome do cliente ou descrição da descarga"""
        if self.cliente:
            return self.cliente.razao_social
        return self.descricao or "Descarga"
    
    def __str__(self):
        nome = self.nome_display
        return f"{nome} - R$ {self.valor}"


class DistribuicaoFuncionario(UpperCaseMixin, models.Model):
    """Distribuição de valores para funcionários no acerto diário"""
    
    acerto_diario = models.ForeignKey(
        'AcertoDiarioCarregamento',
        on_delete=models.CASCADE,
        related_name='distribuicoes_funcionario',
        verbose_name="Acerto Diário"
    )
    
    funcionario = models.ForeignKey(
        'FuncionarioFluxoCaixa',
        on_delete=models.PROTECT,
        related_name='distribuicoes',
        verbose_name="Funcionário"
    )
    
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    
    class Meta:
        verbose_name = "Distribuição para Funcionário"
        verbose_name_plural = "Distribuições para Funcionários"
        unique_together = [['acerto_diario', 'funcionario']]
        ordering = ['funcionario__nome']
    
    def __str__(self):
        return f"{self.funcionario.nome} - R$ {self.valor}"


class AcumuladoFuncionario(UpperCaseMixin, models.Model):
    """Acumulado semanal de valores para cada funcionário"""
    
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Depositado', 'Depositado'),
    ]
    
    funcionario = models.ForeignKey(
        'FuncionarioFluxoCaixa',
        on_delete=models.PROTECT,
        related_name='acumulados',
        verbose_name="Funcionário"
    )
    
    semana_inicio = models.DateField(verbose_name="Início da Semana")
    semana_fim = models.DateField(verbose_name="Fim da Semana")
    
    valor_acumulado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Acumulado (R$)"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pendente',
        verbose_name="Status"
    )
    
    data_deposito = models.DateField(blank=True, null=True, verbose_name="Data do Depósito")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Acumulado de Funcionário"
        verbose_name_plural = "Acumulados de Funcionários"
        ordering = ['-semana_inicio', 'funcionario']
        unique_together = [['funcionario', 'semana_inicio', 'semana_fim']]
        indexes = [
            models.Index(fields=['funcionario', 'status']),
            models.Index(fields=['semana_inicio', 'semana_fim']),
        ]
    
    def calcular_acumulado(self):
        """Calcula o valor acumulado da semana baseado nas distribuições"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Buscar todos os acertos diários da semana
        acertos = AcertoDiarioCarregamento.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        )
        
        # Somar todas as distribuições deste funcionário na semana
        self.valor_acumulado = DistribuicaoFuncionario.objects.filter(
            acerto_diario__in=acertos,
            funcionario=self.funcionario
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        self.save()
        return self.valor_acumulado
    
    def marcar_depositado(self, data_deposito=None):
        """Marca o acumulado como depositado"""
        self.status = 'Depositado'
        self.data_deposito = data_deposito or timezone.now().date()
        self.save()
    
    def __str__(self):
        return f"{self.funcionario.nome} - Semana {self.semana_inicio} a {self.semana_fim} - R$ {self.valor_acumulado}"


class ReceitaEmpresa(UpperCaseMixin, models.Model):
    """Registra receitas arrecadadas pela empresa"""
    
    TIPO_RECEITA_CHOICES = [
        ('Estelar', 'Estelar'),
        ('CTE', 'CTE'),
        ('Manifesto', 'Manifesto'),
        ('Manutencao', 'Manutenção'),
        ('Outro', 'Outro'),
    ]
    
    data = models.DateField(verbose_name="Data")
    tipo_receita = models.CharField(max_length=20, choices=TIPO_RECEITA_CHOICES, verbose_name="Tipo de Receita")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    
    # Vínculo apenas com CobrancaCarregamento (quando aplicável)
    cobranca_carregamento = models.ForeignKey(
        'CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas_empresa',
        verbose_name="Cobrança de Carregamento",
        help_text="Opcional: vincular a uma cobrança de carregamento"
    )
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='receitas_empresa',
        verbose_name="Cliente"
    )
    
    usuario_criacao = models.ForeignKey('Usuario', on_delete=models.PROTECT, related_name='receitas_criadas')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Receita da Empresa"
        verbose_name_plural = "Receitas da Empresa"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo_receita']),
            models.Index(fields=['cobranca_carregamento']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_receita_display()} - R$ {self.valor} - {self.data}"


class SetorBancario(models.Model):
    """
    Armazena dados bancários de cada setor da empresa para instruções de pagamento.
    
    Permite configurar dados bancários separados para:
    - Setor de Carregamento
    - Setor de Armazenagem
    
    Esses dados são utilizados nos relatórios de cobrança para indicar ao cliente
    para onde deve ser direcionado cada valor.
    """
    SETOR_CHOICES = [
        ('Armazenagem', 'Armazenagem'),
        ('Carregamento', 'Carregamento'),
    ]
    
    TIPO_CHAVE_PIX_CHOICES = [
        ('CPF', 'CPF'),
        ('CNPJ', 'CNPJ'),
        ('Email', 'Email'),
        ('Telefone', 'Telefone'),
        ('Chave Aleatória', 'Chave Aleatória'),
    ]
    
    setor = models.CharField(
        max_length=20,
        choices=SETOR_CHOICES,
        unique=True,
        verbose_name="Setor"
    )
    
    nome_responsavel = models.CharField(
        max_length=255,
        verbose_name="Nome do Responsável/Beneficiário"
    )
    
    banco = models.CharField(
        max_length=100,
        verbose_name="Banco"
    )
    
    agencia = models.CharField(
        max_length=20,
        verbose_name="Agência"
    )
    
    conta_corrente = models.CharField(
        max_length=20,
        verbose_name="Conta Corrente"
    )
    
    chave_pix = models.CharField(
        max_length=255,
        verbose_name="Chave PIX"
    )
    
    tipo_chave_pix = models.CharField(
        max_length=50,
        choices=TIPO_CHAVE_PIX_CHOICES,
        verbose_name="Tipo de Chave PIX"
    )
    
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    class Meta:
        verbose_name = "Dados Bancários do Setor"
        verbose_name_plural = "Dados Bancários dos Setores"
        ordering = ['setor']
    
    def __str__(self):
        return f"{self.get_setor_display()} - {self.nome_responsavel}"
    
    def get_chave_pix_formatada(self):
        """Retorna a chave PIX formatada com o tipo"""
        tipo_formatado = self.get_tipo_chave_pix_display().lower()
        return f"{self.chave_pix} ({tipo_formatado})"


class CaixaFuncionario(UpperCaseMixin, models.Model):
    """Controla valores coletados pelos funcionários (diário ou semanal)"""
    
    PERIODO_CHOICES = [
        ('Diario', 'Diário'),
        ('Semanal', 'Semanal'),
    ]
    
    STATUS_CHOICES = [
        ('Em_Aberto', 'Em Aberto'),
        ('Acertado', 'Acertado'),
    ]
    
    funcionario = models.ForeignKey(
        'FuncionarioFluxoCaixa',
        on_delete=models.PROTECT,
        related_name='caixas_funcionario',
        verbose_name="Funcionário"
    )
    
    periodo_tipo = models.CharField(
        max_length=10,
        choices=PERIODO_CHOICES,
        default='Semanal',
        verbose_name="Tipo de Período"
    )
    
    # Para período semanal
    semana_inicio = models.DateField(blank=True, null=True, verbose_name="Início da Semana")
    semana_fim = models.DateField(blank=True, null=True, verbose_name="Fim da Semana")
    
    # Para período diário
    data = models.DateField(blank=True, null=True, verbose_name="Data (período diário)")
    
    valor_coletado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Coletado (R$)"
    )
    
    valor_acertado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Acertado (R$)"
    )
    
    data_acerto = models.DateField(blank=True, null=True, verbose_name="Data do Acerto")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Em_Aberto', verbose_name="Status")
    
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Caixa de Funcionário"
        verbose_name_plural = "Caixas de Funcionários"
        ordering = ['-semana_inicio', '-data', 'funcionario']
        indexes = [
            models.Index(fields=['funcionario', 'status']),
            models.Index(fields=['semana_inicio', 'semana_fim']),
            models.Index(fields=['data']),
        ]
    
    @property
    def nome_funcionario(self):
        """Retorna o nome do funcionário"""
        return self.funcionario.nome
    
    def clean(self):
        """Validação: deve ter semana OU data, dependendo do tipo"""
        from django.core.exceptions import ValidationError
        
        if self.periodo_tipo == 'Semanal':
            if not self.semana_inicio or not self.semana_fim:
                raise ValidationError('Período semanal requer início e fim da semana')
        elif self.periodo_tipo == 'Diario':
            if not self.data:
                raise ValidationError('Período diário requer uma data')
    
    def __str__(self):
        if self.periodo_tipo == 'Semanal':
            return f"{self.funcionario.nome} - Semana {self.semana_inicio} a {self.semana_fim}"
        else:
            return f"{self.funcionario.nome} - {self.data}"


class MovimentoCaixaFuncionario(UpperCaseMixin, models.Model):
    """Registra movimentos individuais do caixa do funcionário"""
    
    caixa_funcionario = models.ForeignKey(
        'CaixaFuncionario',
        on_delete=models.CASCADE,
        related_name='movimentos',
        verbose_name="Caixa do Funcionário"
    )
    
    data = models.DateField(verbose_name="Data")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(verbose_name="Descrição")
    
    # Opcional: vincular a uma cobrança
    cobranca_carregamento = models.ForeignKey(
        'CobrancaCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa_funcionario',
        verbose_name="Cobrança de Carregamento"
    )
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    class Meta:
        verbose_name = "Movimento de Caixa do Funcionário"
        verbose_name_plural = "Movimentos de Caixa dos Funcionários"
        ordering = ['-data', '-criado_em']
    
    def __str__(self):
        return f"Movimento - {self.data} - R$ {self.valor}"


class MovimentoBancario(UpperCaseMixin, models.Model):
    """Registra movimentos da conta corrente do banco"""
    
    TIPO_CHOICES = [
        ('Credito', 'Crédito (Entrada)'),
        ('Debito', 'Débito (Saída)'),
    ]
    
    ORIGEM_CHOICES = [
        ('Manual', 'Manual'),
        ('Importado', 'Importado'),
    ]
    
    data = models.DateField(verbose_name="Data")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    descricao = models.TextField(verbose_name="Descrição")
    
    # Campos para importação futura
    origem = models.CharField(
        max_length=10,
        choices=ORIGEM_CHOICES,
        default='Manual',
        verbose_name="Origem"
    )
    
    numero_documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Nº Documento/Extrato"
    )
    
    # Para rastreabilidade de importação
    hash_importacao = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Hash de Importação",
        help_text="Hash para evitar duplicatas na importação"
    )
    
    # Opcional: vincular a receitas
    receita_empresa = models.ForeignKey(
        'ReceitaEmpresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_bancarios',
        verbose_name="Receita da Empresa"
    )
    
    usuario_criacao = models.ForeignKey('Usuario', on_delete=models.PROTECT, related_name='movimentos_bancarios_criados')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Movimento Bancário"
        verbose_name_plural = "Movimentos Bancários"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo']),
            models.Index(fields=['hash_importacao']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data} - R$ {self.valor}"


class ControleSaldoSemanal(UpperCaseMixin, models.Model):
    """Controla e valida o saldo total do sistema (semanal)"""
    
    semana_inicio = models.DateField(verbose_name="Início da Semana")
    semana_fim = models.DateField(verbose_name="Fim da Semana")
    
    # Saldo inicial da semana
    saldo_inicial_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial em Caixa (R$)"
    )
    
    saldo_inicial_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Inicial no Banco (R$)"
    )
    
    # Totais calculados da semana
    total_receitas_empresa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Receitas Empresa (R$)"
    )
    
    total_caixa_funcionarios = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Caixa Funcionários (R$)"
    )
    
    total_entradas_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Entradas Banco (R$)"
    )
    
    total_saidas_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Saídas Banco (R$)"
    )
    
    total_pendentes_receber = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Pendentes a Receber (R$)"
    )
    
    # Saldo final calculado
    saldo_final_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Calculado (R$)"
    )
    
    # Saldo final real (informado manualmente)
    saldo_final_real_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Real em Caixa (R$)"
    )
    
    saldo_final_real_banco = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Final Real no Banco (R$)"
    )
    
    # Diferença (deve ser zero)
    diferenca = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Diferença (R$)"
    )
    
    # Status de validação
    validado = models.BooleanField(
        default=False,
        verbose_name="Validado",
        help_text="Marcar quando a diferença for zero"
    )
    
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    usuario_validacao = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='saldos_validados',
        verbose_name="Usuário que Validou"
    )
    
    data_validacao = models.DateTimeField(blank=True, null=True, verbose_name="Data de Validação")
    
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Controle de Saldo Semanal"
        verbose_name_plural = "Controles de Saldo Semanal"
        ordering = ['-semana_inicio']
        unique_together = [['semana_inicio', 'semana_fim']]
    
    def calcular_totais(self):
        """Calcula todos os totais da semana"""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Receitas da empresa (na semana)
        self.total_receitas_empresa = ReceitaEmpresa.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Caixa dos funcionários (em aberto na semana)
        # Semanal: semana dentro do período
        # Diário: data dentro da semana
        caixas_semanal = CaixaFuncionario.objects.filter(
            periodo_tipo='Semanal',
            semana_inicio__lte=self.semana_fim,
            semana_fim__gte=self.semana_inicio,
            status='Em_Aberto'
        ).select_related('funcionario')
        
        caixas_diario = CaixaFuncionario.objects.filter(
            periodo_tipo='Diario',
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim,
            status='Em_Aberto'
        ).select_related('funcionario')
        
        total_semanal = caixas_semanal.aggregate(total=Sum('valor_coletado'))['total'] or Decimal('0.00')
        total_diario = caixas_diario.aggregate(total=Sum('valor_coletado'))['total'] or Decimal('0.00')
        self.total_caixa_funcionarios = total_semanal + total_diario
        
        # Movimentos bancários (na semana)
        movimentos_banco = MovimentoBancario.objects.filter(
            data__gte=self.semana_inicio,
            data__lte=self.semana_fim
        )
        
        self.total_entradas_banco = movimentos_banco.filter(
            tipo='Credito'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        self.total_saidas_banco = movimentos_banco.filter(
            tipo='Debito'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        # Pendentes a receber (vencidos até o fim da semana)
        self.total_pendentes_receber = CobrancaCarregamento.objects.filter(
            status='Pendente',
            data_vencimento__lte=self.semana_fim
        ).aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        
        # Saldo final calculado
        self.saldo_final_calculado = (
            self.saldo_inicial_caixa +
            self.saldo_inicial_banco +
            self.total_receitas_empresa +
            self.total_caixa_funcionarios +
            self.total_entradas_banco -
            self.total_saidas_banco
        )
        
        # Diferença (deve ser zero)
        saldo_final_real = self.saldo_final_real_caixa + self.saldo_final_real_banco
        self.diferenca = self.saldo_final_calculado - saldo_final_real
        
        # Auto-validação se diferença for zero
        if self.diferenca == Decimal('0.00') and not self.validado:
            # Não auto-validar, apenas marcar como pronto para validação
            pass
        
        self.save()
    
    def validar(self, usuario):
        """Valida o saldo (só permite se diferença for zero)"""
        from django.core.exceptions import ValidationError
        from decimal import Decimal
        
        if self.diferenca != Decimal('0.00'):
            raise ValidationError(
                f'Não é possível validar. Diferença de R$ {self.diferenca:.2f} deve ser zero.'
            )
        
        self.validado = True
        self.usuario_validacao = usuario
        self.data_validacao = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Controle Semanal - {self.semana_inicio} a {self.semana_fim}"


class MovimentoCaixa(UpperCaseMixin, models.Model):
    """
    Modelo unificado para gerenciamento de todos os movimentos de caixa.
    
    Consolida acertos de funcionários, entradas e saídas de dinheiro
    em uma única estrutura para facilitar o controle e relatórios.
    """
    
    TIPO_CHOICES = [
        ('AcertoFuncionario', 'Acerto de Funcionário'),
        ('Entrada', 'Entrada de Dinheiro'),
        ('Saida', 'Saída de Dinheiro'),
    ]
    
    # Categorias para Entradas
    CATEGORIA_ENTRADA_CHOICES = [
        ('RecebimentoCliente', 'Recebimento de Cliente'),
        ('Venda', 'Venda'),
        ('Reembolso', 'Reembolso'),
        ('Outros', 'Outros'),
    ]
    
    # Categorias para Saídas
    CATEGORIA_SAIDA_CHOICES = [
        ('Combustivel', 'Combustível'),
        ('Manutencao', 'Manutenção'),
        ('Alimentacao', 'Alimentação'),
        ('Pedagio', 'Pedágio'),
        ('Multa', 'Multa'),
        ('Salario', 'Salário'),
        ('Fornecedor', 'Fornecedor'),
        ('Imposto', 'Imposto'),
        ('Outros', 'Outros'),
    ]
    
    data = models.DateField(verbose_name="Data")
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimento"
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    descricao = models.TextField(verbose_name="Descrição")
    
    # Categoria (usada para Entradas e Saídas)
    categoria = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Categoria"
    )
    
    def get_categoria_display(self):
        """Retorna o display da categoria baseado no tipo"""
        if not self.categoria:
            return '-'
        
        if self.tipo == 'Entrada':
            for val, label in self.CATEGORIA_ENTRADA_CHOICES:
                if val == self.categoria:
                    return label
        elif self.tipo == 'Saida':
            for val, label in self.CATEGORIA_SAIDA_CHOICES:
                if val == self.categoria:
                    return label
        
        return self.categoria
    
    # Relacionamentos opcionais
    funcionario = models.ForeignKey(
        'FuncionarioFluxoCaixa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Funcionário"
    )
    
    acerto_diario = models.ForeignKey(
        'AcertoDiarioCarregamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Acerto Diário"
    )
    
    cliente = models.ForeignKey(
        'Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentos_caixa',
        verbose_name="Cliente"
    )
    
    # Período de movimento de caixa
    periodo = models.ForeignKey(
        'PeriodoMovimentoCaixa',
        on_delete=models.PROTECT,
        related_name='movimentos',
        null=True,
        blank=True,
        verbose_name="Período",
        help_text="Período ao qual este movimento pertence"
    )
    
    # Controle e auditoria
    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='movimentos_caixa_criados',
        verbose_name="Usuário que Criou"
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    class Meta:
        verbose_name = "Movimento de Caixa"
        verbose_name_plural = "Movimentos de Caixa"
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['data', 'tipo']),
            models.Index(fields=['tipo', 'categoria']),
            models.Index(fields=['funcionario', 'data']),
        ]
    
    def __str__(self):
        tipo_display = self.get_tipo_display()
        if self.funcionario:
            return f"{tipo_display} - {self.funcionario.nome} - {self.data} - R$ {self.valor}"
        return f"{tipo_display} - {self.data} - R$ {self.valor}"
    
    @property
    def valor_formatado(self):
        """Retorna o valor formatado como moeda brasileira"""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def is_entrada(self):
        """Retorna True se for uma entrada"""
        return self.tipo in ['AcertoFuncionario', 'Entrada']
    
    @property
    def is_saida(self):
        """Retorna True se for uma saída"""
        return self.tipo == 'Saida'


class PeriodoMovimentoCaixa(UpperCaseMixin, models.Model):
    """
    Representa um período de controle de movimentos de caixa.
    
    Permite iniciar um novo período com um valor inicial em caixa
    e controlar todos os movimentos dentro desse período.
    """
    
    STATUS_CHOICES = [
        ('Aberto', 'Aberto'),
        ('Fechado', 'Fechado'),
    ]
    
    nome = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nome do Período",
        help_text="Opcional. Se não informado, será gerado automaticamente pela data de início."
    )
    
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_fim = models.DateField(
        verbose_name="Data de Fim",
        null=True,
        blank=True,
        help_text="Opcional. Deixe em branco se o período ainda está aberto."
    )
    
    valor_inicial_caixa = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Inicial em Caixa (R$)",
        help_text="Valor inicial disponível em caixa no início do período"
    )
    
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Aberto',
        verbose_name="Status"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    usuario_criacao = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='periodos_movimento_caixa_criados',
        verbose_name="Usuário que Criou"
    )
    
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    class Meta:
        verbose_name = "Período de Movimento de Caixa"
        verbose_name_plural = "Períodos de Movimento de Caixa"
        ordering = ['-data_inicio', '-criado_em']
        indexes = [
            models.Index(fields=['status', 'data_inicio']),
        ]
    
    def __str__(self):
        if self.nome:
            return f"{self.nome} - {self.data_inicio.strftime('%d/%m/%Y')}"
        return f"Período de {self.data_inicio.strftime('%d/%m/%Y')}"
    
    @property
    def total_entradas(self):
        """Calcula o total de entradas do período"""
        from django.db.models import Sum
        from decimal import Decimal
        total = MovimentoCaixa.objects.filter(
            periodo=self,
            tipo__in=['AcertoFuncionario', 'Entrada']
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        return total
    
    @property
    def total_saidas(self):
        """Calcula o total de saídas do período"""
        from django.db.models import Sum
        from decimal import Decimal
        total = MovimentoCaixa.objects.filter(
            periodo=self,
            tipo='Saida'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        return total
    
    @property
    def saldo_atual(self):
        """Calcula o saldo atual (inicial + entradas - saídas)"""
        return self.valor_inicial_caixa + self.total_entradas - self.total_saidas
    
    @property
    def movimentos_count(self):
        """Retorna a contagem de movimentos do período"""
        return self.movimentos.count()
    
    def fechar_periodo(self):
        """Fecha o período"""
        if self.status == 'Aberto':
            self.status = 'Fechado'
            if not self.data_fim:
                from django.utils import timezone
                self.data_fim = timezone.now().date()
            self.save()

