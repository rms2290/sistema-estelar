"""
Comando: python manage.py adicionar_clientes_rondonia

Adiciona 7 clientes fictícios com dados realistas para o estado de Rondônia (RO).
"""
from django.core.management.base import BaseCommand
from notas.models import Cliente


CLIENTES_RO = [
    {
        "cnpj": "03.445.112/0001-87",
        "razao_social": "TRANSPORTES E LOGÍSTICA RONDONIA LTDA",
        "nome_fantasia": "TransRondônia",
        "inscricao_estadual": "811.234.567-0",
        "cidade": "Porto Velho",
        "estado": "RO",
        "endereco": "Av. Presidente Dutra",
        "numero": "3450",
        "bairro": "Industrial",
        "cep": "76804-120",
        "telefone": "(69) 3225-4400",
        "email": "contato@transrondonia.com.br",
    },
    {
        "cnpj": "04.556.223/0001-91",
        "razao_social": "COMÉRCIO DE GRÃOS NORTE LTDA",
        "nome_fantasia": "Grãos Norte",
        "inscricao_estadual": "811.345.678-1",
        "cidade": "Ji-Paraná",
        "estado": "RO",
        "endereco": "Rodovia BR-364, Km 365",
        "numero": "S/N",
        "bairro": "Zona Rural",
        "cep": "76960-000",
        "telefone": "(69) 3421-5500",
        "email": "vendas@graosnorte.com.br",
    },
    {
        "cnpj": "05.667.334/0001-02",
        "razao_social": "CARGA E DESCARGA ARIQUEMES S/A",
        "nome_fantasia": "Carga Ariquemes",
        "inscricao_estadual": "811.456.789-2",
        "cidade": "Ariquemes",
        "estado": "RO",
        "endereco": "Rua das Palmeiras",
        "numero": "1200",
        "bairro": "Centro",
        "cep": "76870-000",
        "telefone": "(69) 3535-6600",
        "email": "contato@cargaariquemes.com.br",
    },
    {
        "cnpj": "06.778.445/0001-18",
        "razao_social": "TRANSPORTES VILHENA LTDA",
        "nome_fantasia": "TransVilhena",
        "inscricao_estadual": "811.567.890-3",
        "cidade": "Vilhena",
        "estado": "RO",
        "endereco": "Av. Major Amarante",
        "numero": "2890",
        "bairro": "Centro",
        "cep": "76980-000",
        "telefone": "(69) 3322-7700",
        "email": "frota@transvilhena.com.br",
    },
    {
        "cnpj": "07.889.556/0001-24",
        "razao_social": "COOPERATIVA AGRÍCOLA CACOAL LTDA",
        "nome_fantasia": "Coop Cacoal",
        "inscricao_estadual": "811.678.901-4",
        "cidade": "Cacoal",
        "estado": "RO",
        "endereco": "Rodovia RO-010",
        "numero": "Km 12",
        "bairro": "Distrito Industrial",
        "cep": "76980-000",
        "telefone": "(69) 3441-8800",
        "email": "cooperativa@coopcacoal.com.br",
    },
    {
        "cnpj": "08.990.667/0001-30",
        "razao_social": "DISTRIBUIDORA JARU LTDA",
        "nome_fantasia": "DistriJaru",
        "inscricao_estadual": "811.789.012-5",
        "cidade": "Jaru",
        "estado": "RO",
        "endereco": "Rua Rui Barbosa",
        "numero": "456",
        "bairro": "Jardim dos Migrantes",
        "cep": "76890-000",
        "telefone": "(69) 3552-9900",
        "email": "comercial@distrijaru.com.br",
    },
    {
        "cnpj": "09.001.778/0001-46",
        "razao_social": "ROLIM DE MOURA CARGA E FRETE LTDA",
        "nome_fantasia": "RMF Cargas",
        "inscricao_estadual": "811.890.123-6",
        "cidade": "Rolim de Moura",
        "estado": "RO",
        "endereco": "Av. Tiradentes",
        "numero": "780",
        "bairro": "Centro",
        "cep": "76940-000",
        "telefone": "(69) 3442-1010",
        "email": "fretes@rmfcargas.com.br",
    },
]


class Command(BaseCommand):
    help = "Adiciona 7 clientes fictícios para o estado de Rondônia (RO)."

    def handle(self, *args, **options):
        criados = 0
        for dados in CLIENTES_RO:
            _, created = Cliente.objects.get_or_create(
                cnpj=dados["cnpj"],
                defaults={
                    "razao_social": dados["razao_social"],
                    "nome_fantasia": dados.get("nome_fantasia"),
                    "inscricao_estadual": dados.get("inscricao_estadual"),
                    "estado": dados["estado"],
                    "cidade": dados.get("cidade"),
                    "endereco": dados.get("endereco"),
                    "numero": dados.get("numero"),
                    "bairro": dados.get("bairro"),
                    "cep": dados.get("cep"),
                    "telefone": dados.get("telefone"),
                    "email": dados.get("email"),
                    "status": "Ativo",
                },
            )
            if created:
                criados += 1
                self.stdout.write(self.style.SUCCESS(f"Cliente criado: {dados['razao_social']}"))
        self.stdout.write(self.style.SUCCESS(f"\nTotal: {criados} cliente(s) criado(s) para Rondônia."))
