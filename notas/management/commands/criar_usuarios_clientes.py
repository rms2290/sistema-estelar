"""
Comando Django para criar usuários de acesso ao sistema para os dois clientes PJ.
Uso: python manage.py criar_usuarios_clientes
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notas.models import Cliente

Usuario = get_user_model()

# Senha padrão para os usuários criados (o cliente pode alterar após o primeiro login)
SENHA_PADRAO = 'Estelar@2025'


class Command(BaseCommand):
    help = 'Cria dois usuários (tipo cliente) vinculados aos clientes TRANSPORTES E LOGISTICA SUL LTDA e COMERCIO DE GRAOS NORDESTE S/A'

    def handle(self, *args, **options):
        pares = [
            {
                'razao_social': 'TRANSPORTES E LOGISTICA SUL LTDA',
                'username': 'sullog',
                'email': 'contato@sullog.com.br',
                'first_name': 'SUL LOG',
                'last_name': 'ACESSO CLIENTE',
                'telefone': '(41) 3333-4444',
            },
            {
                'razao_social': 'COMERCIO DE GRAOS NORDESTE S/A',
                'username': 'graosne',
                'email': 'fiscal@graosne.com.br',
                'first_name': 'GRAOS NE',
                'last_name': 'ACESSO CLIENTE',
                'telefone': '(81) 3456-7890',
            },
        ]

        for item in pares:
            cliente = Cliente.objects.filter(razao_social=item['razao_social']).first()
            if not cliente:
                self.stdout.write(
                    self.style.WARNING(f'Cliente "{item["razao_social"]}" não encontrado. Pulando.')
                )
                continue
            if Usuario.objects.filter(username=item['username']).exists():
                self.stdout.write(
                    self.style.WARNING(f'Usuário "{item["username"]}" já existe. Pulando.')
                )
                continue

            usuario = Usuario.objects.create_user(
                username=item['username'],
                email=item['email'],
                password=SENHA_PADRAO,
                first_name=item['first_name'],
                last_name=item['last_name'],
                tipo_usuario='cliente',
                cliente=cliente,
                telefone=item.get('telefone', ''),
                is_active=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Usuário criado: {usuario.username} (cliente: {cliente.nome_fantasia or cliente.razao_social})'
                )
            )

        self.stdout.write(self.style.SUCCESS(f'\nSenha padrão para os usuários: {SENHA_PADRAO}'))
        self.stdout.write('Concluído.')
