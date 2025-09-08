from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import json
import gzip
import os
from pathlib import Path
import glob


class Command(BaseCommand):
    help = 'Consulta dados arquivados com busca e restauração'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            choices=['romaneios', 'notas', 'clientes', 'motoristas', 'todos'],
            default='todos',
            help='Tipo de dados para consultar',
        )
        parser.add_argument(
            '--ano',
            type=int,
            help='Ano específico para consultar',
        )
        parser.add_argument(
            '--buscar',
            type=str,
            help='Termo de busca (código, nome, etc.)',
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista arquivos disponíveis',
        )
        parser.add_argument(
            '--restaurar',
            type=str,
            help='Restaura dados de um arquivo específico',
        )

    def handle(self, *args, **options):
        self.tipo = options['tipo']
        self.ano = options['ano']
        self.buscar = options['buscar']
        self.listar = options['listar']
        self.restaurar = options['restaurar']
        
        if self.listar:
            self.listar_arquivos_disponiveis()
        elif self.restaurar:
            self.restaurar_dados(self.restaurar)
        else:
            self.consultar_dados()

    def listar_arquivos_disponiveis(self):
        """Lista todos os arquivos de arquivo disponíveis"""
        self.stdout.write('📁 ARQUIVOS DISPONÍVEIS:')
        
        base_dir = Path('dados_arquivados')
        if not base_dir.exists():
            self.stdout.write(self.style.ERROR('❌ Diretório de arquivo não encontrado'))
            return
        
        for subdir in ['romaneios', 'notas_fiscais', 'clientes', 'motoristas', 'veiculos']:
            dir_path = base_dir / subdir
            if dir_path.exists():
                arquivos = list(dir_path.glob('*.json.gz'))
                if arquivos:
                    self.stdout.write(f'\n📦 {subdir.upper()}:')
                    for arquivo in sorted(arquivos):
                        tamanho = arquivo.stat().st_size / 1024  # KB
                        self.stdout.write(f'   📄 {arquivo.name} ({tamanho:.1f} KB)')

    def consultar_dados(self):
        """Consulta dados arquivados"""
        self.stdout.write('🔍 CONSULTANDO DADOS ARQUIVADOS...')
        
        if self.tipo == 'todos' or self.tipo == 'romaneios':
            self.consultar_romaneios()
        
        if self.tipo == 'todos' or self.tipo == 'notas':
            self.consultar_notas_fiscais()
        
        if self.tipo == 'todos' or self.tipo == 'clientes':
            self.consultar_clientes()
        
        if self.tipo == 'todos' or self.tipo == 'motoristas':
            self.consultar_motoristas()

    def consultar_romaneios(self):
        """Consulta romaneios arquivados"""
        self.stdout.write('\n📦 CONSULTANDO ROMANEIOS ARQUIVADOS:')
        
        arquivos = self.get_arquivos_por_tipo('romaneios')
        total_encontrados = 0
        
        for arquivo in arquivos:
            if self.ano and str(self.ano) not in arquivo.name:
                continue
            
            try:
                with gzip.open(arquivo, 'rt', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for romaneio in dados:
                    if self.buscar and self.buscar.lower() not in romaneio['codigo'].lower():
                        continue
                    
                    total_encontrados += 1
                    self.stdout.write(f'   📦 {romaneio["codigo"]} - {romaneio["data_emissao"][:10]} - Status: {romaneio["status"]}')
                    
                    if self.buscar:
                        self.mostrar_detalhes_romaneio(romaneio)
                
            except Exception as e:
                self.stdout.write(f'   ⚠️  Erro ao ler {arquivo.name}: {e}')
        
        self.stdout.write(f'   📊 Total encontrado: {total_encontrados} romaneios')

    def consultar_notas_fiscais(self):
        """Consulta notas fiscais arquivadas"""
        self.stdout.write('\n📄 CONSULTANDO NOTAS FISCAIS ARQUIVADAS:')
        
        arquivos = self.get_arquivos_por_tipo('notas_fiscais')
        total_encontradas = 0
        
        for arquivo in arquivos:
            if self.ano and str(self.ano) not in arquivo.name:
                continue
            
            try:
                with gzip.open(arquivo, 'rt', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for nota in dados:
                    if self.buscar and self.buscar.lower() not in nota['nota'].lower():
                        continue
                    
                    total_encontradas += 1
                    self.stdout.write(f'   📄 NF {nota["nota"]} - {nota["data"][:10]} - {nota["fornecedor"]}')
                    
                    if self.buscar:
                        self.mostrar_detalhes_nota(nota)
                
            except Exception as e:
                self.stdout.write(f'   ⚠️  Erro ao ler {arquivo.name}: {e}')
        
        self.stdout.write(f'   📊 Total encontrado: {total_encontradas} notas')

    def consultar_clientes(self):
        """Consulta clientes arquivados"""
        self.stdout.write('\n🏢 CONSULTANDO CLIENTES ARQUIVADOS:')
        
        arquivos = self.get_arquivos_por_tipo('clientes')
        total_encontrados = 0
        
        for arquivo in arquivos:
            try:
                with gzip.open(arquivo, 'rt', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for cliente in dados:
                    if self.buscar and self.buscar.lower() not in cliente['razao_social'].lower():
                        continue
                    
                    total_encontrados += 1
                    self.stdout.write(f'   🏢 {cliente["razao_social"]} - {cliente["cidade"]}/{cliente["estado"]}')
                    
                    if self.buscar:
                        self.mostrar_detalhes_cliente(cliente)
                
            except Exception as e:
                self.stdout.write(f'   ⚠️  Erro ao ler {arquivo.name}: {e}')
        
        self.stdout.write(f'   📊 Total encontrado: {total_encontrados} clientes')

    def consultar_motoristas(self):
        """Consulta motoristas arquivados"""
        self.stdout.write('\n👤 CONSULTANDO MOTORISTAS ARQUIVADOS:')
        
        arquivos = self.get_arquivos_por_tipo('motoristas')
        total_encontrados = 0
        
        for arquivo in arquivos:
            try:
                with gzip.open(arquivo, 'rt', encoding='utf-8') as f:
                    dados = json.load(f)
                
                for motorista in dados:
                    if self.buscar and self.buscar.lower() not in motorista['nome'].lower():
                        continue
                    
                    total_encontrados += 1
                    self.stdout.write(f'   👤 {motorista["nome"]} - CNH: {motorista["cnh"]}')
                    
                    if self.buscar:
                        self.mostrar_detalhes_motorista(motorista)
                
            except Exception as e:
                self.stdout.write(f'   ⚠️  Erro ao ler {arquivo.name}: {e}')
        
        self.stdout.write(f'   📊 Total encontrado: {total_encontrados} motoristas')

    def get_arquivos_por_tipo(self, tipo):
        """Retorna lista de arquivos por tipo"""
        base_dir = Path('dados_arquivados') / tipo
        if not base_dir.exists():
            return []
        
        return sorted(base_dir.glob('*.json.gz'))

    def mostrar_detalhes_romaneio(self, romaneio):
        """Mostra detalhes de um romaneio"""
        self.stdout.write(f'      📋 Código: {romaneio["codigo"]}')
        self.stdout.write(f'      📅 Data: {romaneio["data_emissao"]}')
        self.stdout.write(f'      📊 Status: {romaneio["status"]}')
        self.stdout.write(f'      📝 Observações: {romaneio.get("observacoes", "N/A")}')

    def mostrar_detalhes_nota(self, nota):
        """Mostra detalhes de uma nota fiscal"""
        self.stdout.write(f'      📄 Número: {nota["nota"]}')
        self.stdout.write(f'      📅 Data: {nota["data"]}')
        self.stdout.write(f'      🏢 Fornecedor: {nota["fornecedor"]}')
        self.stdout.write(f'      📦 Mercadoria: {nota["mercadoria"]}')

    def mostrar_detalhes_cliente(self, cliente):
        """Mostra detalhes de um cliente"""
        self.stdout.write(f'      🏢 Razão Social: {cliente["razao_social"]}')
        self.stdout.write(f'      📋 CNPJ: {cliente["cnpj"]}')
        self.stdout.write(f'      📍 Endereço: {cliente["endereco"]}')
        self.stdout.write(f'      🏙️  Cidade: {cliente["cidade"]}/{cliente["estado"]}')

    def mostrar_detalhes_motorista(self, motorista):
        """Mostra detalhes de um motorista"""
        self.stdout.write(f'      👤 Nome: {motorista["nome"]}')
        self.stdout.write(f'      📋 CPF: {motorista["cpf"]}')
        self.stdout.write(f'      🚗 CNH: {motorista["cnh"]}')

    def restaurar_dados(self, arquivo_path):
        """Restaura dados de um arquivo específico"""
        self.stdout.write(f'🔄 RESTAURANDO DADOS DE: {arquivo_path}')
        
        if not os.path.exists(arquivo_path):
            self.stdout.write(self.style.ERROR(f'❌ Arquivo não encontrado: {arquivo_path}'))
            return
        
        try:
            with gzip.open(arquivo_path, 'rt', encoding='utf-8') as f:
                dados = json.load(f)
            
            self.stdout.write(f'📊 Dados encontrados: {len(dados)} registros')
            
            # Aqui você pode implementar a lógica de restauração
            # Por enquanto, apenas mostra os dados
            for i, registro in enumerate(dados[:5]):  # Mostra apenas os primeiros 5
                self.stdout.write(f'   {i+1}. {registro}')
            
            if len(dados) > 5:
                self.stdout.write(f'   ... e mais {len(dados) - 5} registros')
            
            self.stdout.write(self.style.WARNING('⚠️  Funcionalidade de restauração em desenvolvimento'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao restaurar dados: {e}')) 