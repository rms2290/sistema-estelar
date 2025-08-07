from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import json
import gzip
import os
from pathlib import Path

from notas.models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem


class Command(BaseCommand):
    help = 'Arquiva dados antigos (5+ anos) com compressão e backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a operação sem executar',
        )
        parser.add_argument(
            '--anos',
            type=int,
            default=5,
            help='Idade mínima dos dados para arquivamento (padrão: 5 anos)',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Cria backup antes do arquivamento',
        )

    def handle(self, *args, **options):
        self.anos_limite = options['anos']
        self.dry_run = options['dry_run']
        self.fazer_backup = options['backup']
        
        # Calcular data limite
        data_limite = timezone.now() - timedelta(days=365 * self.anos_limite)
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Iniciando arquivamento de dados antigos (>{self.anos_limite} anos)')
        )
        self.stdout.write(f'📅 Data limite: {data_limite.strftime("%d/%m/%Y")}')
        
        # Criar diretórios de arquivo
        self.criar_diretorios_arquivo()
        
        # Estatísticas antes do arquivamento
        self.mostrar_estatisticas_antes()
        
        if self.fazer_backup:
            self.criar_backup_completo()
        
        # Executar arquivamento
        if not self.dry_run:
            self.arquivar_dados(data_limite)
        else:
            self.stdout.write(
                self.style.WARNING('🔍 MODO DRY-RUN: Simulando operação...')
            )
            self.simular_arquivamento(data_limite)
        
        # Estatísticas após arquivamento
        self.mostrar_estatisticas_depois()

    def criar_diretorios_arquivo(self):
        """Cria estrutura de diretórios para arquivamento"""
        base_dir = Path('dados_arquivados')
        subdirs = ['notas_fiscais', 'romaneios', 'clientes', 'motoristas', 'veiculos', 'backups']
        
        for subdir in subdirs:
            (base_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        self.stdout.write('📁 Diretórios de arquivo criados/verificados')

    def mostrar_estatisticas_antes(self):
        """Mostra estatísticas dos dados antes do arquivamento"""
        self.stdout.write('\n📊 ESTATÍSTICAS ANTES DO ARQUIVAMENTO:')
        self.stdout.write(f'   - Notas Fiscais: {NotaFiscal.objects.count()}')
        self.stdout.write(f'   - Romaneios: {RomaneioViagem.objects.count()}')
        self.stdout.write(f'   - Clientes: {Cliente.objects.count()}')
        self.stdout.write(f'   - Motoristas: {Motorista.objects.count()}')
        self.stdout.write(f'   - Veículos: {Veiculo.objects.count()}')

    def criar_backup_completo(self):
        """Cria backup completo antes do arquivamento"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'dados_arquivados/backups/backup_completo_{timestamp}.json.gz'
        
        self.stdout.write(f'💾 Criando backup completo: {backup_file}')
        
        dados_backup = {
            'notas_fiscais': list(NotaFiscal.objects.values()),
            'romaneios': list(RomaneioViagem.objects.values()),
            'clientes': list(Cliente.objects.values()),
            'motoristas': list(Motorista.objects.values()),
            'veiculos': list(Veiculo.objects.values()),
            'metadata': {
                'data_backup': timestamp,
                'total_registros': {
                    'notas_fiscais': NotaFiscal.objects.count(),
                    'romaneios': RomaneioViagem.objects.count(),
                    'clientes': Cliente.objects.count(),
                    'motoristas': Motorista.objects.count(),
                    'veiculos': Veiculo.objects.count(),
                }
            }
        }
        
        # Comprimir e salvar backup
        with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
            json.dump(dados_backup, f, indent=2, default=str)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Backup criado: {backup_file}')
        )

    def arquivar_dados(self, data_limite):
        """Executa o arquivamento real dos dados"""
        self.stdout.write('\n🗂️  INICIANDO ARQUIVAMENTO...')
        
        # 1. Arquivar Romaneios antigos
        self.arquivar_romaneios(data_limite)
        
        # 2. Arquivar Notas Fiscais antigas
        self.arquivar_notas_fiscais(data_limite)
        
        # 3. Arquivar dados relacionados (se não referenciados)
        self.arquivar_dados_relacionados()

    def simular_arquivamento(self, data_limite):
        """Simula o arquivamento sem executar"""
        self.stdout.write('\n🔍 SIMULANDO ARQUIVAMENTO...')
        
        # Contar registros que seriam arquivados
        romaneios_antigos = RomaneioViagem.objects.filter(data_emissao__lt=data_limite).count()
        notas_antigas = NotaFiscal.objects.filter(data__lt=data_limite).count()
        
        self.stdout.write(f'   - Romaneios que seriam arquivados: {romaneios_antigos}')
        self.stdout.write(f'   - Notas Fiscais que seriam arquivadas: {notas_antigas}')

    def arquivar_romaneios(self, data_limite):
        """Arquiva romaneios antigos"""
        romaneios_antigos = RomaneioViagem.objects.filter(data_emissao__lt=data_limite)
        total = romaneios_antigos.count()
        
        if total == 0:
            self.stdout.write('   ⚠️  Nenhum romaneio antigo encontrado')
            return
        
        self.stdout.write(f'   📦 Arquivando {total} romaneios antigos...')
        
        # Agrupar por ano para arquivamento organizado
        for ano in range(data_limite.year, 2000, -1):  # Até 2000
            romaneios_ano = romaneios_antigos.filter(data_emissao__year=ano)
            if romaneios_ano.exists():
                self.arquivar_romaneios_por_ano(romaneios_ano, ano)

    def arquivar_romaneios_por_ano(self, romaneios, ano):
        """Arquiva romaneios de um ano específico"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo = f'dados_arquivados/romaneios/romaneios_{ano}_{timestamp}.json.gz'
        
        dados_romaneios = []
        for romaneio in romaneios:
            dados_romaneios.append({
                'id': romaneio.id,
                'codigo': romaneio.codigo,
                'data_emissao': romaneio.data_emissao.isoformat(),
                'status': romaneio.status,
                'cliente_id': romaneio.cliente_id,
                'motorista_id': romaneio.motorista_id,
                'veiculo_principal_id': romaneio.veiculo_principal_id,
                'reboque_1_id': romaneio.reboque_1_id,
                'reboque_2_id': romaneio.reboque_2_id,
                'observacoes': romaneio.observacoes,
                'notas_fiscais_ids': list(romaneio.notas_fiscais.values_list('id', flat=True)),
                'metadata': {
                    'ano': ano,
                    'data_arquivamento': timestamp,
                    'total_notas': romaneio.notas_fiscais.count()
                }
            })
        
        # Comprimir e salvar
        with gzip.open(arquivo, 'wt', encoding='utf-8') as f:
            json.dump(dados_romaneios, f, indent=2, default=str)
        
        # Excluir do banco principal
        with transaction.atomic():
            romaneios.delete()
        
        self.stdout.write(f'      ✅ {len(dados_romaneios)} romaneios de {ano} arquivados em {arquivo}')

    def arquivar_notas_fiscais(self, data_limite):
        """Arquiva notas fiscais antigas"""
        notas_antigas = NotaFiscal.objects.filter(data__lt=data_limite)
        total = notas_antigas.count()
        
        if total == 0:
            self.stdout.write('   ⚠️  Nenhuma nota fiscal antiga encontrada')
            return
        
        self.stdout.write(f'   📄 Arquivando {total} notas fiscais antigas...')
        
        # Agrupar por ano
        for ano in range(data_limite.year, 2000, -1):
            notas_ano = notas_antigas.filter(data__year=ano)
            if notas_ano.exists():
                self.arquivar_notas_por_ano(notas_ano, ano)

    def arquivar_notas_por_ano(self, notas, ano):
        """Arquiva notas fiscais de um ano específico"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo = f'dados_arquivados/notas_fiscais/notas_{ano}_{timestamp}.json.gz'
        
        dados_notas = []
        for nota in notas:
            dados_notas.append({
                'id': nota.id,
                'nota': nota.nota,
                'data': nota.data.isoformat(),
                'fornecedor': nota.fornecedor,
                'mercadoria': nota.mercadoria,
                'quantidade': str(nota.quantidade),
                'peso': str(nota.peso),
                'valor': str(nota.valor),
                'cliente_id': nota.cliente_id,
                'metadata': {
                    'ano': ano,
                    'data_arquivamento': timestamp
                }
            })
        
        # Comprimir e salvar
        with gzip.open(arquivo, 'wt', encoding='utf-8') as f:
            json.dump(dados_notas, f, indent=2, default=str)
        
        # Excluir do banco principal
        with transaction.atomic():
            notas.delete()
        
        self.stdout.write(f'      ✅ {len(dados_notas)} notas de {ano} arquivadas em {arquivo}')

    def arquivar_dados_relacionados(self):
        """Arquiva dados relacionados que não são mais referenciados"""
        self.stdout.write('   🔍 Verificando dados relacionados não utilizados...')
        
        # Verificar clientes sem romaneios recentes
        clientes_sem_romaneios = Cliente.objects.filter(
            romaneioviagem__isnull=True
        ).distinct()
        
        if clientes_sem_romaneios.exists():
            self.arquivar_clientes_isolados(clientes_sem_romaneios)
        
        # Verificar motoristas sem romaneios recentes
        motoristas_sem_romaneios = Motorista.objects.filter(
            romaneioviagem__isnull=True
        ).distinct()
        
        if motoristas_sem_romaneios.exists():
            self.arquivar_motoristas_isolados(motoristas_sem_romaneios)

    def arquivar_clientes_isolados(self, clientes):
        """Arquiva clientes que não têm romaneios"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo = f'dados_arquivados/clientes/clientes_isolados_{timestamp}.json.gz'
        
        dados_clientes = []
        for cliente in clientes:
            dados_clientes.append({
                'id': cliente.id,
                'razao_social': cliente.razao_social,
                'cnpj': cliente.cnpj,
                'endereco': cliente.endereco,
                'cidade': cliente.cidade,
                'estado': cliente.estado,
                'status': cliente.status,
                'metadata': {
                    'data_arquivamento': timestamp,
                    'motivo': 'Cliente sem romaneios'
                }
            })
        
        # Comprimir e salvar
        with gzip.open(arquivo, 'wt', encoding='utf-8') as f:
            json.dump(dados_clientes, f, indent=2, default=str)
        
        # Excluir do banco principal
        with transaction.atomic():
            clientes.delete()
        
        self.stdout.write(f'      ✅ {len(dados_clientes)} clientes isolados arquivados')

    def arquivar_motoristas_isolados(self, motoristas):
        """Arquiva motoristas que não têm romaneios"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        arquivo = f'dados_arquivados/motoristas/motoristas_isolados_{timestamp}.json.gz'
        
        dados_motoristas = []
        for motorista in motoristas:
            dados_motoristas.append({
                'id': motorista.id,
                'nome': motorista.nome,
                'cpf': motorista.cpf,
                'cnh': motorista.cnh,
                'metadata': {
                    'data_arquivamento': timestamp,
                    'motivo': 'Motorista sem romaneios'
                }
            })
        
        # Comprimir e salvar
        with gzip.open(arquivo, 'wt', encoding='utf-8') as f:
            json.dump(dados_motoristas, f, indent=2, default=str)
        
        # Excluir do banco principal
        with transaction.atomic():
            motoristas.delete()
        
        self.stdout.write(f'      ✅ {len(dados_motoristas)} motoristas isolados arquivados')

    def mostrar_estatisticas_depois(self):
        """Mostra estatísticas após o arquivamento"""
        self.stdout.write('\n📊 ESTATÍSTICAS APÓS O ARQUIVAMENTO:')
        self.stdout.write(f'   - Notas Fiscais: {NotaFiscal.objects.count()}')
        self.stdout.write(f'   - Romaneios: {RomaneioViagem.objects.count()}')
        self.stdout.write(f'   - Clientes: {Cliente.objects.count()}')
        self.stdout.write(f'   - Motoristas: {Motorista.objects.count()}')
        self.stdout.write(f'   - Veículos: {Veiculo.objects.count()}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Arquivamento concluído com sucesso!')
        )
        self.stdout.write('📁 Dados arquivados em: dados_arquivados/')
        self.stdout.write('💾 Backups em: dados_arquivados/backups/') 