from django.core.management.base import BaseCommand
from notas.models import Motorista
from datetime import date


class Command(BaseCommand):
    help = 'Cria um motorista de teste com dados completos incluindo RG'

    def handle(self, *args, **options):
        # Verificar se já existe um motorista com esse CPF
        if Motorista.objects.filter(cpf='12345678901').exists():
            self.stdout.write(
                self.style.WARNING('Motorista com CPF 12345678901 já existe. Pulando criação.')
            )
            return

        # Criar motorista de teste com dados completos
        motorista = Motorista.objects.create(
            nome='JOAO PEDRO SANTOS SILVA',
            cpf='12345678901',
            rg='123456789',  # RG para teste
            cnh='98765432100',
            codigo_seguranca='ABC123',
            telefone='11987654321',
            endereco='RUA DAS FLORES',
            numero='123',
            complemento='APTO 45',
            bairro='CENTRO',
            cidade='SAO PAULO',
            estado='SP',
            cep='01234567',
            data_nascimento=date(1990, 5, 15),
            uf_emissao_cnh='SP',
            vencimento_cnh=date(2026, 12, 31),
            observacoes='Motorista de teste criado para validar o campo RG'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Motorista criado com sucesso!')
        )
        self.stdout.write(f'ID: {motorista.pk}')
        self.stdout.write(f'Nome: {motorista.nome}')
        self.stdout.write(f'CPF: {motorista.cpf}')
        self.stdout.write(f'RG: {motorista.rg}')
        self.stdout.write(f'CNH: {motorista.cnh}')
        self.stdout.write(f'Telefone: {motorista.telefone}')


