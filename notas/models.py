from django.db import models

class Cliente(models.Model): # Garanta que Cliente esteja definido
    razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.razao_social

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['razao_social']

class NotaFiscal(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='notas_fiscais')
    nota = models.CharField(max_length=50, unique=True)
    data = models.DateField()
    fornecedor = models.CharField(max_length=200)
    mercadoria = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    # >>> ADICIONE ESTA LINHA <<<
    status = models.CharField(max_length=20, default='Pendente', choices=[('Pendente', 'Pendente'), ('Romaneada', 'Romaneada')])

    def __str__(self):
        return f"Nota {self.nota} - Cliente: {self.cliente.razao_social}"

    class Meta:
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"
        ordering = ['-data', 'nota']

# Certifique-se de que os modelos Motorista, Veiculo e RomaneioViagem estão corretos também,
# incluindo a ManyToManyField em RomaneioViagem como abaixo:
class Motorista(models.Model):
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    # MODIFIQUE ESTA LINHA:
    cnh = models.CharField(max_length=20, unique=True, blank=True, null=True) # <--- ADICIONE blank=True, null=True
    telefone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Motorista"
        verbose_name_plural = "Motoristas"
        ordering = ['nome']

class Veiculo(models.Model):
    placa = models.CharField(max_length=8, unique=True)
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    ano = models.IntegerField(blank=True, null=True) # Manteve a modificação anterior, se não a reverteu
    # MODIFIQUE ESTA LINHA:
    capacidade_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Capacidade de carga em KG", blank=True, null=True) # <--- ADICIONE blank=True, null=True

    def __str__(self):
        return f"{self.placa} - {self.modelo}"

    class Meta:
        verbose_name = "Veículo"
        verbose_name_plural = "Veículos"
        ordering = ['placa']

class RomaneioViagem(models.Model):
    codigo = models.IntegerField(unique=True, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='romaneios_cliente')
    motorista = models.ForeignKey(Motorista, on_delete=models.CASCADE)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    data_emissao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    
    # Esta é a ManyToManyField que cria a relação inversa 'romaneios' em NotaFiscal
    notas_fiscais = models.ManyToManyField(
        'NotaFiscal',
        related_name='romaneios', # <-- ESSA É A CHAVE!
        blank=True
    )

    def __str__(self):
        return f"Romaneio {self.codigo} - {self.cliente.razao_social}"

    class Meta:
        verbose_name_plural = "Romaneios de Viagem"
        ordering = ['-data_emissao']