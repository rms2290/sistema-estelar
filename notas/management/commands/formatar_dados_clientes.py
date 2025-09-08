from django.core.management.base import BaseCommand
from django.db import transaction
from notas.models import Cliente, Motorista, Veiculo
import re


class Command(BaseCommand):
    help = 'Formata os dados dos clientes, motoristas e veículos para os padrões corretos de CNPJ, telefone, CPF e CEP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações no banco de dados',
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['cliente', 'motorista', 'veiculo', 'all'],
            default='all',
            help='Especifica qual modelo formatar (padrão: all)',
        )

    def formatar_cnpj(self, cnpj):
        """Formata CNPJ para o padrão 00.000.000/0000-00"""
        if not cnpj:
            return cnpj
        
        # Remove tudo que não é número
        numeros = re.sub(r'[^0-9]', '', str(cnpj))
        
        # Verifica se tem 14 dígitos
        if len(numeros) != 14:
            return cnpj  # Retorna original se não tiver 14 dígitos
        
        # Aplica a formatação
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"

    def formatar_telefone(self, telefone):
        """Formata telefone para o padrão (00) 00000-0000 ou (00) 0000-0000"""
        if not telefone:
            return telefone
        
        # Remove tudo que não é número
        numeros = re.sub(r'[^0-9]', '', str(telefone))
        
        # Verifica se tem entre 10 e 11 dígitos
        if len(numeros) < 10 or len(numeros) > 11:
            return telefone  # Retorna original se não tiver dígitos suficientes
        
        # Aplica a formatação baseada no número de dígitos
        if len(numeros) == 10:
            # Telefone fixo: (00) 0000-0000
            return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
        else:
            # Celular: (00) 00000-0000
            return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"

    def formatar_cpf(self, cpf):
        """Formata CPF para o padrão 000.000.000-00"""
        if not cpf:
            return cpf
        
        # Remove tudo que não é número
        numeros = re.sub(r'[^0-9]', '', str(cpf))
        
        # Verifica se tem 11 dígitos
        if len(numeros) != 11:
            return cpf  # Retorna original se não tiver 11 dígitos
        
        # Aplica a formatação
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"

    def formatar_cep(self, cep):
        """Formata CEP para o padrão 00000-000"""
        if not cep:
            return cep
        
        # Remove tudo que não é número
        numeros = re.sub(r'[^0-9]', '', str(cep))
        
        # Verifica se tem 8 dígitos
        if len(numeros) != 8:
            return cep  # Retorna original se não tiver 8 dígitos
        
        # Aplica a formatação
        return f"{numeros[:5]}-{numeros[5:]}"

    def formatar_clientes(self, dry_run=False):
        """Formata os dados dos clientes"""
        self.stdout.write("Formatando dados dos clientes...")
        
        clientes = Cliente.objects.all()
        atualizados = 0
        
        for cliente in clientes:
            alteracoes = []
            
            # Formatar CNPJ
            if cliente.cnpj:
                cnpj_formatado = self.formatar_cnpj(cliente.cnpj)
                if cnpj_formatado != cliente.cnpj:
                    if not dry_run:
                        cliente.cnpj = cnpj_formatado
                    alteracoes.append(f"CNPJ: {cliente.cnpj} → {cnpj_formatado}")
            
            # Formatar telefone
            if cliente.telefone:
                telefone_formatado = self.formatar_telefone(cliente.telefone)
                if telefone_formatado != cliente.telefone:
                    if not dry_run:
                        cliente.telefone = telefone_formatado
                    alteracoes.append(f"Telefone: {cliente.telefone} → {telefone_formatado}")
            
            # Formatar CEP
            if cliente.cep:
                cep_formatado = self.formatar_cep(cliente.cep)
                if cep_formatado != cliente.cep:
                    if not dry_run:
                        cliente.cep = cep_formatado
                    alteracoes.append(f"CEP: {cliente.cep} → {cep_formatado}")
            
            if alteracoes:
                if not dry_run:
                    cliente.save()
                atualizados += 1
                self.stdout.write(f"Cliente '{cliente.razao_social}':")
                for alteracao in alteracoes:
                    self.stdout.write(f"  - {alteracao}")
        
        self.stdout.write(f"Total de clientes atualizados: {atualizados}")

    def formatar_motoristas(self, dry_run=False):
        """Formata os dados dos motoristas"""
        self.stdout.write("Formatando dados dos motoristas...")
        
        motoristas = Motorista.objects.all()
        atualizados = 0
        
        for motorista in motoristas:
            alteracoes = []
            
            # Formatar CPF
            if motorista.cpf:
                cpf_formatado = self.formatar_cpf(motorista.cpf)
                if cpf_formatado != motorista.cpf:
                    if not dry_run:
                        motorista.cpf = cpf_formatado
                    alteracoes.append(f"CPF: {motorista.cpf} → {cpf_formatado}")
            
            # Formatar telefone
            if motorista.telefone:
                telefone_formatado = self.formatar_telefone(motorista.telefone)
                if telefone_formatado != motorista.telefone:
                    if not dry_run:
                        motorista.telefone = telefone_formatado
                    alteracoes.append(f"Telefone: {motorista.telefone} → {telefone_formatado}")
            
            # Formatar CEP
            if motorista.cep:
                cep_formatado = self.formatar_cep(motorista.cep)
                if cep_formatado != motorista.cep:
                    if not dry_run:
                        motorista.cep = cep_formatado
                    alteracoes.append(f"CEP: {motorista.cep} → {cep_formatado}")
            
            if alteracoes:
                if not dry_run:
                    motorista.save()
                atualizados += 1
                self.stdout.write(f"Motorista '{motorista.nome}':")
                for alteracao in alteracoes:
                    self.stdout.write(f"  - {alteracao}")
        
        self.stdout.write(f"Total de motoristas atualizados: {atualizados}")

    def formatar_veiculos(self, dry_run=False):
        """Formata os dados dos veículos"""
        self.stdout.write("Formatando dados dos veículos...")
        
        veiculos = Veiculo.objects.all()
        atualizados = 0
        
        for veiculo in veiculos:
            alteracoes = []
            
            # Formatar CPF/CNPJ do proprietário
            if veiculo.proprietario_cpf_cnpj:
                # Tenta formatar como CPF primeiro (11 dígitos)
                numeros = re.sub(r'[^0-9]', '', str(veiculo.proprietario_cpf_cnpj))
                if len(numeros) == 11:
                    cpf_formatado = self.formatar_cpf(veiculo.proprietario_cpf_cnpj)
                    if cpf_formatado != veiculo.proprietario_cpf_cnpj:
                        if not dry_run:
                            veiculo.proprietario_cpf_cnpj = cpf_formatado
                        alteracoes.append(f"CPF/CNPJ: {veiculo.proprietario_cpf_cnpj} → {cpf_formatado}")
                elif len(numeros) == 14:
                    cnpj_formatado = self.formatar_cnpj(veiculo.proprietario_cpf_cnpj)
                    if cnpj_formatado != veiculo.proprietario_cpf_cnpj:
                        if not dry_run:
                            veiculo.proprietario_cpf_cnpj = cnpj_formatado
                        alteracoes.append(f"CPF/CNPJ: {veiculo.proprietario_cpf_cnpj} → {cnpj_formatado}")
            
            # Formatar telefone do proprietário
            if veiculo.proprietario_telefone:
                telefone_formatado = self.formatar_telefone(veiculo.proprietario_telefone)
                if telefone_formatado != veiculo.proprietario_telefone:
                    if not dry_run:
                        veiculo.proprietario_telefone = telefone_formatado
                    alteracoes.append(f"Telefone: {veiculo.proprietario_telefone} → {telefone_formatado}")
            
            # Formatar CEP do proprietário
            if veiculo.proprietario_cep:
                cep_formatado = self.formatar_cep(veiculo.proprietario_cep)
                if cep_formatado != veiculo.proprietario_cep:
                    if not dry_run:
                        veiculo.proprietario_cep = cep_formatado
                    alteracoes.append(f"CEP: {veiculo.proprietario_cep} → {cep_formatado}")
            
            if alteracoes:
                if not dry_run:
                    veiculo.save()
                atualizados += 1
                self.stdout.write(f"Veículo '{veiculo.placa}':")
                for alteracao in alteracoes:
                    self.stdout.write(f"  - {alteracao}")
        
        self.stdout.write(f"Total de veículos atualizados: {atualizados}")

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        model = options['model']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: Nenhuma alteração será feita no banco de dados"))
        
        try:
            with transaction.atomic():
                if model in ['cliente', 'all']:
                    self.formatar_clientes(dry_run)
                
                if model in ['motorista', 'all']:
                    self.formatar_motoristas(dry_run)
                
                if model in ['veiculo', 'all']:
                    self.formatar_veiculos(dry_run)
                
                if dry_run:
                    self.stdout.write(self.style.SUCCESS("DRY-RUN concluído. Execute sem --dry-run para aplicar as alterações"))
                else:
                    self.stdout.write(self.style.SUCCESS("Formatação concluída com sucesso!"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro durante a formatação: {e}"))
            raise 