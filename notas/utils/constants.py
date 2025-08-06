"""
Constantes do sistema
"""

# Estados brasileiros
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

# Tipos de composição de motorista
TIPO_COMPOSICAO_MOTORISTA_CHOICES = [
    ('Simples', 'Simples (Carro/Van/Truck)'),
    ('Carreta', 'Carreta (Caminhão Trator + 1 Reboque/Semi-reboque)'),
    ('Bi-trem', 'Bi-trem (Caminhão Trator + 2 Reboques/Semi-reboques)'),
]

# Tipos de unidade de veículo
TIPO_UNIDADE_CHOICES = [
    ('Carro', 'Carro'),
    ('Van', 'Van'),
    ('Truck', 'Caminhão Trator'),
    ('Reboque', 'Reboque'),
    ('Semi-reboque', 'Semi-reboque'),
]

# Status de cliente
STATUS_CLIENTE_CHOICES = [
    ('Ativo', 'Ativo'),
    ('Inativo', 'Inativo'),
]

# Status de nota fiscal
STATUS_NF_CHOICES = [
    ('Depósito', 'Depósito'),
    ('Enviada', 'Enviada'),
]

# Status de romaneio
STATUS_ROMANEIO_CHOICES = [
    ('Rascunho', 'Rascunho'),
    ('Emitido', 'Emitido'),
]

# Status de consulta
STATUS_CONSULTA_CHOICES = [
    ('Apto', 'Apto'),
    ('Inapto', 'Inapto'),
    ('Pendente', 'Pendente'),
]

# Tipos de usuário
TIPO_USUARIO_CHOICES = [
    ('admin', 'Administrador'),
    ('funcionario', 'Funcionário'),
    ('cliente', 'Cliente'),
]

# Marcas de veículos comuns
MARCAS_VEICULOS = [
    ('FORD', 'FORD'),
    ('CHEVROLET', 'CHEVROLET'),
    ('VOLKSWAGEN', 'VOLKSWAGEN'),
    ('FIAT', 'FIAT'),
    ('MERCEDES-BENZ', 'MERCEDES-BENZ'),
    ('SCANIA', 'SCANIA'),
    ('VOLVO', 'VOLVO'),
    ('IVECO', 'IVECO'),
    ('MAN', 'MAN'),
    ('DAF', 'DAF'),
    ('RENAULT', 'RENAULT'),
    ('PEUGEOT', 'PEUGEOT'),
    ('CITROEN', 'CITROEN'),
    ('HYUNDAI', 'HYUNDAI'),
    ('TOYOTA', 'TOYOTA'),
    ('NISSAN', 'NISSAN'),
    ('HONDA', 'HONDA'),
    ('MITSUBISHI', 'MITSUBISHI'),
    ('MAZDA', 'MAZDA'),
    ('SUBARU', 'SUBARU'),
    ('AUDI', 'AUDI'),
    ('BMW', 'BMW'),
    ('OUTROS', 'OUTROS'),
]

# Países do Mercosul
PAISES_MERCOSUL = [
    ('Brasil', 'Brasil'),
    ('Argentina', 'Argentina'),
    ('Paraguai', 'Paraguai'),
    ('Uruguai', 'Uruguai'),
    ('Bolívia', 'Bolívia'),
    ('Chile', 'Chile'),
    ('Peru', 'Peru'),
    ('Colômbia', 'Colômbia'),
    ('Venezuela', 'Venezuela'),
    ('Equador', 'Equador'),
    ('Guiana', 'Guiana'),
    ('Suriname', 'Suriname'),
    ('Guiana Francesa', 'Guiana Francesa'),
]

# Configurações de paginação
ITENS_POR_PAGINA = 20

# Configurações de upload
TAMANHO_MAX_UPLOAD = 5 * 1024 * 1024  # 5MB
TIPOS_PERMITIDOS_UPLOAD = ['image/jpeg', 'image/png', 'application/pdf']

# Mensagens de erro padrão
MENSAGENS_ERRO = {
    'campo_obrigatorio': 'Este campo é obrigatório.',
    'cpf_invalido': 'CPF inválido.',
    'cnpj_invalido': 'CNPJ inválido.',
    'placa_invalida': 'Placa inválida.',
    'telefone_invalido': 'Telefone inválido.',
    'cep_invalido': 'CEP inválido.',
    'email_invalido': 'Email inválido.',
    'chassi_invalido': 'Chassi inválido.',
    'renavam_invalido': 'RENAVAM inválido.',
    'arquivo_muito_grande': 'Arquivo muito grande. Máximo 5MB.',
    'tipo_arquivo_invalido': 'Tipo de arquivo não permitido.',
}

# Configurações de formatação
FORMATOS_DATA = {
    'display': '%d/%m/%Y',
    'input': '%Y-%m-%d',
    'datetime': '%d/%m/%Y %H:%M',
}

FORMATOS_MOEDA = {
    'simbolo': 'R$',
    'separador_milhares': '.',
    'separador_decimal': ',',
    'casas_decimais': 2,
} 