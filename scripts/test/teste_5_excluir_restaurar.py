#!/usr/bin/env python
"""
Script de Teste 5: Excluir e Restaurar Dados

Este script testa:
- Criar backup de dados antes da exclusão
- Excluir dados (romaneios, notas fiscais)
- Restaurar dados do backup
- Validar integridade após restauração
"""
import os
import sys
import django
from pathlib import Path
from decimal import Decimal
import random
import json
import gzip
from datetime import datetime, timedelta

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction
from django.utils import timezone
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem, Usuario
)
from notas.services.romaneio_service import RomaneioService
from notas.utils.auditoria import registrar_exclusao, registrar_restauracao

# Configurar logging
import logging
# Configurar handler de arquivo com UTF-8
file_handler = logging.FileHandler('logs/teste_5_excluir_restaurar.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configurar handler de console com encoding seguro
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
if hasattr(console_handler.stream, 'reconfigure'):
    try:
        console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


class TesteExcluirRestaurar:
    """Classe para executar testes de exclusão e restauração"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'validacoes': []
        }
        self.dados_backup = {}
        self.arquivo_backup = None
    
    def executar_teste(self):
        """Executa todos os testes de exclusão e restauração"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 5: EXCLUIR E RESTAURAR DADOS")
        logger.info("=" * 80)
        
        try:
            # 1. Criar dados de teste
            dados_teste = self._criar_dados_teste()
            if not dados_teste:
                logger.error("Nao foi possivel criar dados de teste")
                return False
            
            # 2. Criar backup dos dados
            self._criar_backup_dados(dados_teste)
            
            # 3. Excluir dados
            self._excluir_dados(dados_teste)
            
            # 4. Verificar exclusão
            self._verificar_exclusao(dados_teste)
            
            # 5. Restaurar dados do backup
            self._restaurar_dados()
            
            # 6. Verificar restauração
            self._verificar_restauracao(dados_teste)
            
            # 7. Limpar arquivo de backup
            self._limpar_backup()
            
            # 8. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro critico no teste: {str(e)}", exc_info=True)
            return False
    
    def _criar_dados_teste(self):
        """Cria dados de teste para exclusão e restauração"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Dados de Teste")
        logger.info("-" * 80)
        
        try:
            # Buscar ou criar cliente
            cliente, _ = Cliente.objects.get_or_create(
                razao_social="CLIENTE TESTE RESTAURACAO",
                defaults={
                    'cnpj': '12345678000199',
                    'status': 'Ativo'
                }
            )
            
            # Buscar motorista e veículo
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if not motorista or not veiculo:
                logger.error("Motorista ou veiculo nao encontrado")
                return None
            
            # Criar notas fiscais de teste
            notas_criadas = []
            for i in range(3):
                nota, created = NotaFiscal.objects.get_or_create(
                    nota=f"RESTORE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                    defaults={
                        'cliente': cliente,
                        'data': timezone.now().date(),
                        'fornecedor': f"Fornecedor Restore {i}",
                        'mercadoria': f"Mercadoria Restore {i}",
                        'peso': Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                        'valor': Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                        'quantidade': random.randint(1, 100),
                        'status': 'Depósito'
                    }
                )
                if created:
                    notas_criadas.append(nota)
            
            # Criar romaneio de teste
            romaneio, created = RomaneioViagem.objects.get_or_create(
                codigo=f"RESTORE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                defaults={
                    'cliente': cliente,
                    'motorista': motorista,
                    'veiculo_principal': veiculo,
                    'origem_cidade': 'SAO PAULO',
                    'destino_cidade': 'RIO DE JANEIRO',
                    'status': 'Salvo'
                }
            )
            
            if created:
                # Vincular notas ao romaneio
                for nota in notas_criadas:
                    romaneio.notas_fiscais.add(nota)
                romaneio.calcular_totais()
            
            dados = {
                'cliente': cliente,
                'motorista': motorista,
                'veiculo': veiculo,
                'notas': notas_criadas if created else list(romaneio.notas_fiscais.all()),
                'romaneio': romaneio
            }
            
            logger.info(f"Dados de teste criados:")
            logger.info(f"   - Cliente: {cliente.razao_social}")
            logger.info(f"   - Notas: {len(dados['notas'])}")
            logger.info(f"   - Romaneio: {romaneio.codigo}")
            
            return dados
            
        except Exception as e:
            logger.error(f"Erro ao criar dados de teste: {str(e)}", exc_info=True)
            return None
    
    def _criar_backup_dados(self, dados_teste):
        """Cria backup dos dados antes da exclusão"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Backup dos Dados")
        logger.info("-" * 80)
        
        try:
            # Criar diretório de backup se não existir
            os.makedirs('logs/backups', exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.arquivo_backup = f'logs/backups/backup_teste_{timestamp}.json.gz'
            
            # Preparar dados para backup
            romaneio = dados_teste['romaneio']
            notas = dados_teste['notas']
            
            # Serializar romaneio
            romaneio_data = {
                'id': romaneio.id,
                'codigo': romaneio.codigo,
                'cliente_id': romaneio.cliente_id,
                'motorista_id': romaneio.motorista_id,
                'veiculo_principal_id': romaneio.veiculo_principal_id,
                'origem_cidade': romaneio.origem_cidade,
                'destino_cidade': romaneio.destino_cidade,
                'status': romaneio.status,
                'peso_total': str(romaneio.peso_total) if romaneio.peso_total else None,
                'valor_total': str(romaneio.valor_total) if romaneio.valor_total else None,
                'observacoes': romaneio.observacoes,
                'notas_fiscais_ids': [nota.id for nota in notas]
            }
            
            # Serializar notas fiscais
            notas_data = []
            for nota in notas:
                notas_data.append({
                    'id': nota.id,
                    'nota': nota.nota,
                    'cliente_id': nota.cliente_id,
                    'data': nota.data.isoformat() if nota.data else None,
                    'fornecedor': nota.fornecedor,
                    'mercadoria': nota.mercadoria,
                    'peso': str(nota.peso) if nota.peso else None,
                    'valor': str(nota.valor) if nota.valor else None,
                    'quantidade': str(nota.quantidade) if nota.quantidade else None,
                    'status': nota.status,
                    'local': nota.local
                })
            
            self.dados_backup = {
                'romaneio': romaneio_data,
                'notas_fiscais': notas_data,
                'metadata': {
                    'data_backup': timestamp,
                    'total_notas': len(notas_data),
                    'total_romaneios': 1
                }
            }
            
            # Salvar backup comprimido
            with gzip.open(self.arquivo_backup, 'wt', encoding='utf-8') as f:
                json.dump(self.dados_backup, f, indent=2, default=str)
            
            logger.info(f"Backup criado: {self.arquivo_backup}")
            logger.info(f"   - Romaneio: {romaneio_data['codigo']}")
            logger.info(f"   - Notas: {len(notas_data)}")
            self.resultados['sucessos'].append("Backup criado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Criacao de backup: {str(e)}")
            raise
    
    def _excluir_dados(self, dados_teste):
        """Exclui os dados de teste"""
        logger.info("\n" + "-" * 80)
        logger.info("Excluindo Dados")
        logger.info("-" * 80)
        
        try:
            romaneio = dados_teste['romaneio']
            notas = dados_teste['notas']
            
            # Salvar IDs antes da exclusão
            romaneio_id = romaneio.id
            notas_ids = [nota.id for nota in notas]
            
            # Buscar ou criar usuário para auditoria
            usuario_auditoria, _ = Usuario.objects.get_or_create(
                username='sistema_teste',
                defaults={
                    'email': 'sistema_teste@teste.com',
                    'tipo_usuario': 'admin',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            # Registrar exclusão na auditoria ANTES de excluir
            try:
                registrar_exclusao(
                    usuario=usuario_auditoria,
                    instancia=romaneio,
                    request=None,
                    descricao=f"Exclusao de teste: Romaneio {romaneio.codigo}"
                )
                logger.info("Exclusao registrada na auditoria")
                self.resultados['sucessos'].append("Registro de exclusao na auditoria")
            except Exception as audit_error:
                logger.warning(f"Erro ao registrar exclusao na auditoria: {str(audit_error)}")
                self.resultados['erros'].append(f"Registro de auditoria: {str(audit_error)}")
            
            # Excluir romaneio (isso deve atualizar status das notas)
            sucesso, mensagem = RomaneioService.excluir_romaneio(romaneio)
            
            if sucesso:
                logger.info(f"Romaneio {romaneio.codigo} excluido com sucesso")
                self.resultados['sucessos'].append("Exclusao de romaneio")
            else:
                logger.error(f"Erro ao excluir romaneio: {mensagem}")
                self.resultados['erros'].append(f"Exclusao de romaneio: {mensagem}")
                return
            
            # Verificar se romaneio foi excluído
            if RomaneioViagem.objects.filter(id=romaneio_id).exists():
                logger.error("Romaneio ainda existe apos exclusao")
                self.resultados['erros'].append("Romaneio nao foi excluido")
            else:
                logger.info("Romaneio excluido do banco de dados")
            
            # Verificar status das notas
            notas_restauradas = 0
            for nota_id in notas_ids:
                try:
                    nota = NotaFiscal.objects.get(id=nota_id)
                    if nota.status == 'Deposito':
                        notas_restauradas += 1
                except NotaFiscal.DoesNotExist:
                    logger.warning(f"Nota {nota_id} nao encontrada")
            
            logger.info(f"Notas com status atualizado: {notas_restauradas}/{len(notas_ids)}")
            
        except Exception as e:
            logger.error(f"Erro ao excluir dados: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Exclusao de dados: {str(e)}")
    
    def _verificar_exclusao(self, dados_teste):
        """Verifica se os dados foram excluídos corretamente"""
        logger.info("\n" + "-" * 80)
        logger.info("Verificando Exclusao")
        logger.info("-" * 80)
        
        try:
            romaneio_id = dados_teste['romaneio'].id
            
            # Verificar se romaneio foi excluído
            existe = RomaneioViagem.objects.filter(id=romaneio_id).exists()
            
            if not existe:
                logger.info("Romaneio excluido corretamente")
                self.resultados['sucessos'].append("Verificacao de exclusao")
            else:
                logger.error("Romaneio ainda existe")
                self.resultados['erros'].append("Verificacao de exclusao")
            
        except Exception as e:
            logger.error(f"Erro ao verificar exclusao: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Verificacao de exclusao: {str(e)}")
    
    def _restaurar_dados(self):
        """Restaura dados do backup"""
        logger.info("\n" + "-" * 80)
        logger.info("Restaurando Dados do Backup")
        logger.info("-" * 80)
        
        try:
            if not self.arquivo_backup or not os.path.exists(self.arquivo_backup):
                logger.error("Arquivo de backup nao encontrado")
                self.resultados['erros'].append("Arquivo de backup nao encontrado")
                return
            
            # Carregar backup
            with gzip.open(self.arquivo_backup, 'rt', encoding='utf-8') as f:
                dados_backup = json.load(f)
            
            romaneio_data = dados_backup['romaneio']
            notas_data = dados_backup['notas_fiscais']
            
            # Restaurar notas fiscais
            notas_restauradas = []
            for nota_data in notas_data:
                try:
                    # Verificar se nota já existe
                    nota = NotaFiscal.objects.filter(id=nota_data['id']).first()
                    
                    if not nota:
                        # Criar nota se não existir
                        cliente = Cliente.objects.get(id=nota_data['cliente_id'])
                        nota = NotaFiscal.objects.create(
                            id=nota_data['id'],
                            cliente=cliente,
                            nota=nota_data['nota'],
                            data=datetime.fromisoformat(nota_data['data']) if nota_data['data'] else timezone.now().date(),
                            fornecedor=nota_data['fornecedor'],
                            mercadoria=nota_data['mercadoria'],
                            peso=Decimal(nota_data['peso']) if nota_data['peso'] else None,
                            valor=Decimal(nota_data['valor']) if nota_data['valor'] else None,
                            quantidade=Decimal(nota_data['quantidade']) if nota_data['quantidade'] else None,
                            status=nota_data['status'],
                            local=nota_data.get('local')
                        )
                    else:
                        # Atualizar nota existente
                        nota.status = nota_data['status']
                        nota.save()
                    
                    notas_restauradas.append(nota)
                    
                except Exception as e:
                    logger.warning(f"Erro ao restaurar nota {nota_data.get('nota', 'N/A')}: {str(e)}")
            
            # Restaurar romaneio
            try:
                # Verificar se romaneio já existe
                romaneio = RomaneioViagem.objects.filter(id=romaneio_data['id']).first()
                
                # Buscar ou criar usuário para auditoria
                usuario_auditoria, _ = Usuario.objects.get_or_create(
                    username='sistema_teste',
                    defaults={
                        'email': 'sistema_teste@teste.com',
                        'tipo_usuario': 'admin',
                        'is_staff': True,
                        'is_superuser': True
                    }
                )
                
                if not romaneio:
                    cliente = Cliente.objects.get(id=romaneio_data['cliente_id'])
                    motorista = Motorista.objects.get(id=romaneio_data['motorista_id'])
                    veiculo = Veiculo.objects.get(id=romaneio_data['veiculo_principal_id'])
                    
                    romaneio = RomaneioViagem.objects.create(
                        id=romaneio_data['id'],
                        codigo=romaneio_data['codigo'],
                        cliente=cliente,
                        motorista=motorista,
                        veiculo_principal=veiculo,
                        origem_cidade=romaneio_data['origem_cidade'],
                        destino_cidade=romaneio_data['destino_cidade'],
                        status=romaneio_data['status'],
                        peso_total=Decimal(romaneio_data['peso_total']) if romaneio_data['peso_total'] else None,
                        valor_total=Decimal(romaneio_data['valor_total']) if romaneio_data['valor_total'] else None,
                        observacoes=romaneio_data.get('observacoes')
                    )
                    
                    # Vincular notas
                    for nota in notas_restauradas:
                        romaneio.notas_fiscais.add(nota)
                    
                    # Registrar restauração na auditoria
                    try:
                        registrar_restauracao(
                            usuario=usuario_auditoria,
                            instancia=romaneio,
                            request=None,
                            descricao=f"Restauracao de teste: Romaneio {romaneio.codigo}"
                        )
                        logger.info("Restauracao registrada na auditoria")
                        self.resultados['sucessos'].append("Registro de restauracao na auditoria")
                    except Exception as audit_error:
                        logger.warning(f"Erro ao registrar restauracao na auditoria: {str(audit_error)}")
                        self.resultados['erros'].append(f"Registro de auditoria (restauracao): {str(audit_error)}")
                    
                    logger.info(f"Romaneio {romaneio.codigo} restaurado com sucesso")
                    self.resultados['sucessos'].append("Restauracao de romaneio")
                else:
                    logger.info(f"Romaneio {romaneio.codigo} ja existe")
                    
            except Exception as e:
                logger.error(f"Erro ao restaurar romaneio: {str(e)}", exc_info=True)
                self.resultados['erros'].append(f"Restauracao de romaneio: {str(e)}")
            
            logger.info(f"Restauracao concluida:")
            logger.info(f"   - Notas restauradas: {len(notas_restauradas)}")
            
        except Exception as e:
            logger.error(f"Erro ao restaurar dados: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Restauracao de dados: {str(e)}")
    
    def _verificar_restauracao(self, dados_teste):
        """Verifica se os dados foram restaurados corretamente"""
        logger.info("\n" + "-" * 80)
        logger.info("Verificando Restauracao")
        logger.info("-" * 80)
        
        try:
            romaneio_backup = self.dados_backup['romaneio']
            notas_backup = self.dados_backup['notas_fiscais']
            
            # Verificar se romaneio foi restaurado
            romaneio = RomaneioViagem.objects.filter(id=romaneio_backup['id']).first()
            
            if romaneio:
                logger.info(f"Romaneio {romaneio.codigo} restaurado corretamente")
                
                # Verificar dados do romaneio
                if romaneio.codigo == romaneio_backup['codigo']:
                    logger.info("   - Codigo correto")
                if romaneio.origem_cidade == romaneio_backup['origem_cidade']:
                    logger.info("   - Origem correta")
                if romaneio.destino_cidade == romaneio_backup['destino_cidade']:
                    logger.info("   - Destino correto")
                
                # Verificar notas vinculadas
                notas_vinculadas = list(romaneio.notas_fiscais.all())
                logger.info(f"   - Notas vinculadas: {len(notas_vinculadas)}")
                
                if len(notas_vinculadas) == len(notas_backup):
                    logger.info("   - Numero de notas correto")
                    self.resultados['sucessos'].append("Verificacao de restauracao")
                else:
                    logger.warning(f"   - Numero de notas diferente: esperado {len(notas_backup)}, obtido {len(notas_vinculadas)}")
            else:
                logger.error("Romaneio nao foi restaurado")
                self.resultados['erros'].append("Verificacao de restauracao")
            
        except Exception as e:
            logger.error(f"Erro ao verificar restauracao: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Verificacao de restauracao: {str(e)}")
    
    def _limpar_backup(self):
        """Limpa arquivo de backup de teste"""
        try:
            if self.arquivo_backup and os.path.exists(self.arquivo_backup):
                os.remove(self.arquivo_backup)
                logger.info(f"Arquivo de backup removido: {self.arquivo_backup}")
        except Exception as e:
            logger.warning(f"Erro ao remover backup: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATORIO FINAL - TESTE 5: EXCLUIR E RESTAURAR")
        logger.info("=" * 80)
        
        total_testes = len(self.resultados['sucessos']) + len(self.resultados['erros'])
        sucessos = len(self.resultados['sucessos'])
        erros = len(self.resultados['erros'])
        
        logger.info(f"\nEstatisticas:")
        logger.info(f"   - Total de testes: {total_testes}")
        logger.info(f"   - Sucessos: {sucessos}")
        logger.info(f"   - Erros: {erros}")
        logger.info(f"   - Taxa de sucesso: {(sucessos/total_testes*100) if total_testes > 0 else 0:.1f}%")
        
        if self.resultados['sucessos']:
            logger.info(f"\nTestes bem-sucedidos:")
            for sucesso in self.resultados['sucessos']:
                logger.info(f"   - {sucesso}")
        
        if self.resultados['erros']:
            logger.info(f"\nTestes com erro:")
            for erro in self.resultados['erros']:
                logger.info(f"   - {erro}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("TESTE 5 CONCLUIDO COM SUCESSO!")
        else:
            logger.info("TESTE 5 CONCLUIDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/backups', exist_ok=True)
    
    teste = TesteExcluirRestaurar()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

