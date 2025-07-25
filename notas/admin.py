from django.contrib import admin
from .models import NotaFiscal, Cliente, Motorista, Veiculo    # Importe Cliente

admin.site.register(NotaFiscal)
admin.site.register(Cliente)
admin.site.register(Motorista)
admin.site.register(Veiculo)