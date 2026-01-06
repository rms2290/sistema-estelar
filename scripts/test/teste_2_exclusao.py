#!/usr/bin/env python
"""
Script de Teste 2: Exclusão de Romaneios

Este script testa:
- Excluir romaneios com notas vinculadas
- Verificar atualização de status das notas fiscais
- Validar integridade referencial
"""
import os
import sys
import django
from pathlib import Path
from decimal import Decimal
import random
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
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem
)
from notas.services.romaneio_service import RomaneioService

# Configurar logging
import logging
# Configurar handler de arquivo com UTF-8
file_handler = logging.FileHandler('logs/teste_2_exclusao.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configurar handler de console com encoding seguro
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# Configurar encoding do console para UTF-8 se possível
if hasattr(console_handler.stream, 'reconfigure'):
    try:
        console_handler.stream.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


class TesteExclusao:
    """Classe para executar testes de exclusão"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'validacoes': []
        }
        self.romaneio_teste = None
        self.dados_backup = {}
    
    def executar_teste(self):
        """Executa todos os testes de exclusão"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 2: EXCLUSÃO DE ROMANEIOS")
        logger.info("=" * 80)
        
        try:
            # 1. Criar romaneio de teste
            self.romaneio_teste = self._criar_romaneio_teste()
            if not self.romaneio_teste:
                logger.error("❌ Não foi possível criar romaneio de teste")
                return False
            
            # 2. Fazer backup dos dados
            self._fazer_backup_dados()
            
            # 3. Testar exclusão de romaneio
            self._testar_exclusao_romaneio()
            
            # 4. Verificar atualização de status das notas
            self._verificar_status_notas()
            
            # 5. Validar integridade referencial
            self._validar_integridade_referencial()
            
            # 6. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro crítico no teste: {str(e)}", exc_info=True)
            return False
    
    def _criar_romaneio_teste(self):
        """Cria um romaneio de teste com notas fiscais"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Romaneio de Teste")
        logger.info("-" * 80)
        
        try:
            # Buscar cliente existente
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.error("❌ Nenhum cliente ativo encontrado")
                return None
            
            # Buscar motorista existente
            motorista = Motorista.objects.first()
            if not motorista:
                logger.error("❌ Nenhum motorista encontrado")
                return None
            
            # Buscar veículo existente
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            if not veiculo:
                logger.error("❌ Nenhum veículo do tipo Cavalo encontrado")
                return None
            
            # Buscar ou criar notas fiscais em depósito
            notas = NotaFiscal.objects.filter(
                cliente=cliente,
                status='Depósito'
            )[:3]  # Pegar até 3 notas
            
            if notas.count() < 2:
                # Criar notas fiscais de teste
                logger.info("   Criando notas fiscais de teste...")
                for i in range(2):
                    nota = NotaFiscal.objects.create(
                        cliente=cliente,
                        nota=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                        data=timezone.now().date(),
                        fornecedor="Fornecedor Teste",
                        mercadoria="Mercadoria Teste",
                        peso=Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                        valor=Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                        quantidade=random.randint(1, 100),
                        status='Depósito'
                    )
                    notas = notas | NotaFiscal.objects.filter(pk=nota.pk)
            
            # Criar romaneio
            romaneio = RomaneioViagem.objects.create(
                codigo=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                cliente=cliente,
                motorista=motorista,
                veiculo_principal=veiculo,
                origem_cidade="SÃO PAULO",
                destino_cidade="RIO DE JANEIRO",
                status='Salvo'
            )
            
            # Vincular notas fiscais
            for nota in notas:
                romaneio.notas_fiscais.add(nota)
            
            # Calcular totais
            romaneio.calcular_totais()
            
            logger.info(f"✅ Romaneio de teste criado: {romaneio.codigo}")
            logger.info(f"   - Cliente: {cliente.razao_social}")
            logger.info(f"   - Notas vinculadas: {romaneio.notas_fiscais.count()}")
            logger.info(f"   - Status: {romaneio.status}")
            
            return romaneio
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar romaneio de teste: {str(e)}", exc_info=True)
            return None
    
    def _fazer_backup_dados(self):
        """Faz backup dos dados do romaneio antes da exclusão"""
        logger.info("\n" + "-" * 80)
        logger.info("Fazendo Backup dos Dados")
        logger.info("-" * 80)
        
        try:
            self.romaneio_teste.refresh_from_db()
            
            # Backup do romaneio
            self.dados_backup['romaneio'] = {
                'codigo': self.romaneio_teste.codigo,
                'cliente_id': self.romaneio_teste.cliente_id,
                'motorista_id': self.romaneio_teste.motorista_id,
                'veiculo_principal_id': self.romaneio_teste.veiculo_principal_id,
            }
            
            # Backup das notas fiscais e seus status
            notas_backup = []
            for nota in self.romaneio_teste.notas_fiscais.all():
                notas_backup.append({
                    'id': nota.id,
                    'nota': nota.nota,
                    'status_antes': nota.status,
                    'peso': float(nota.peso or 0),
                    'valor': float(nota.valor or 0)
                })
            
            self.dados_backup['notas_fiscais'] = notas_backup
            
            logger.info(f"✅ Backup realizado:")
            logger.info(f"   - Romaneio: {self.dados_backup['romaneio']['codigo']}")
            logger.info(f"   - Notas: {len(notas_backup)}")
            for nota_backup in notas_backup:
                logger.info(f"     * {nota_backup['nota']} - Status: {nota_backup['status_antes']}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup: {str(e)}", exc_info=True)
    
    def _testar_exclusao_romaneio(self):
        """Testa exclusão de romaneio"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 2.1: Exclusão de Romaneio")
        logger.info("-" * 80)
        
        try:
            romaneio_id = self.romaneio_teste.id
            codigo_romaneio = self.romaneio_teste.codigo
            
            # Verificar se romaneio existe antes da exclusão
            existe_antes = RomaneioViagem.objects.filter(id=romaneio_id).exists()
            if not existe_antes:
                logger.error("❌ Romaneio não encontrado antes da exclusão")
                self.resultados['erros'].append("Romaneio não encontrado antes da exclusão")
                return
            
            # Excluir romaneio usando o serviço
            sucesso, mensagem = RomaneioService.excluir_romaneio(self.romaneio_teste)
            
            if sucesso:
                # Verificar se romaneio foi excluído
                existe_depois = RomaneioViagem.objects.filter(id=romaneio_id).exists()
                
                if not existe_depois:
                    logger.info("✅ Exclusão de romaneio: SUCESSO")
                    logger.info(f"   - Romaneio {codigo_romaneio} foi excluído")
                    self.resultados['sucessos'].append("Exclusão de romaneio")
                else:
                    logger.error("❌ Exclusão de romaneio: FALHOU - Romaneio ainda existe")
                    self.resultados['erros'].append("Romaneio não foi excluído")
            else:
                logger.error(f"❌ Exclusão de romaneio: FALHOU - {mensagem}")
                self.resultados['erros'].append(f"Exclusão falhou: {mensagem}")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar exclusão: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Exclusão: {str(e)}")
    
    def _verificar_status_notas(self):
        """Verifica se o status das notas fiscais foi atualizado corretamente"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 2.2: Verificação de Status das Notas Fiscais")
        logger.info("-" * 80)
        
        try:
            notas_backup = self.dados_backup.get('notas_fiscais', [])
            
            if not notas_backup:
                logger.warning("⚠️ Nenhuma nota fiscal no backup")
                return
            
            todas_atualizadas = True
            
            for nota_backup in notas_backup:
                try:
                    nota = NotaFiscal.objects.get(id=nota_backup['id'])
                    status_atual = nota.status
                    status_esperado = 'Depósito'  # Status deve voltar para Depósito após exclusão
                    
                    if status_atual == status_esperado:
                        logger.info(f"✅ Nota {nota_backup['nota']}: Status atualizado corretamente")
                        logger.info(f"   - Status antes: {nota_backup['status_antes']}")
                        logger.info(f"   - Status depois: {status_atual}")
                    else:
                        logger.error(f"❌ Nota {nota_backup['nota']}: Status não atualizado")
                        logger.error(f"   - Status esperado: {status_esperado}")
                        logger.error(f"   - Status obtido: {status_atual}")
                        todas_atualizadas = False
                        
                except NotaFiscal.DoesNotExist:
                    logger.error(f"❌ Nota {nota_backup['nota']} não encontrada após exclusão")
                    todas_atualizadas = False
            
            if todas_atualizadas:
                logger.info("✅ Todas as notas fiscais tiveram status atualizado corretamente")
                self.resultados['sucessos'].append("Atualização de status das notas fiscais")
                self.resultados['validacoes'].append({
                    'teste': 'Atualização de status',
                    'notas_verificadas': len(notas_backup),
                    'todas_atualizadas': True
                })
            else:
                logger.error("❌ Algumas notas fiscais não tiveram status atualizado")
                self.resultados['erros'].append("Atualização de status das notas fiscais")
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status das notas: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Verificação de status: {str(e)}")
    
    def _validar_integridade_referencial(self):
        """Valida integridade referencial após exclusão"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 2.3: Validação de Integridade Referencial")
        logger.info("-" * 80)
        
        try:
            romaneio_id = self.romaneio_teste.id
            
            # Verificar se não há referências órfãs
            # 1. Verificar se notas fiscais não têm mais referência ao romaneio
            notas_backup = self.dados_backup.get('notas_fiscais', [])
            referencias_orfas = 0
            
            for nota_backup in notas_backup:
                try:
                    nota = NotaFiscal.objects.get(id=nota_backup['id'])
                    # Verificar se a nota ainda está vinculada ao romaneio excluído
                    if nota.romaneios_vinculados.filter(id=romaneio_id).exists():
                        logger.error(f"❌ Nota {nota_backup['nota']} ainda está vinculada ao romaneio excluído")
                        referencias_orfas += 1
                except NotaFiscal.DoesNotExist:
                    pass
            
            # 2. Verificar se cliente, motorista e veículo ainda existem
            cliente_id = self.dados_backup['romaneio']['cliente_id']
            motorista_id = self.dados_backup['romaneio']['motorista_id']
            veiculo_id = self.dados_backup['romaneio']['veiculo_principal_id']
            
            cliente_existe = Cliente.objects.filter(id=cliente_id).exists()
            motorista_existe = Motorista.objects.filter(id=motorista_id).exists()
            veiculo_existe = Veiculo.objects.filter(id=veiculo_id).exists()
            
            if (cliente_existe and motorista_existe and veiculo_existe and referencias_orfas == 0):
                logger.info("✅ Integridade referencial: OK")
                logger.info(f"   - Cliente existe: {cliente_existe}")
                logger.info(f"   - Motorista existe: {motorista_existe}")
                logger.info(f"   - Veículo existe: {veiculo_existe}")
                logger.info(f"   - Referências órfãs: {referencias_orfas}")
                self.resultados['sucessos'].append("Integridade referencial")
                self.resultados['validacoes'].append({
                    'teste': 'Integridade referencial',
                    'cliente_existe': cliente_existe,
                    'motorista_existe': motorista_existe,
                    'veiculo_existe': veiculo_existe,
                    'referencias_orfas': referencias_orfas
                })
            else:
                logger.error("❌ Integridade referencial: FALHOU")
                logger.error(f"   - Cliente existe: {cliente_existe}")
                logger.error(f"   - Motorista existe: {motorista_existe}")
                logger.error(f"   - Veículo existe: {veiculo_existe}")
                logger.error(f"   - Referências órfãs: {referencias_orfas}")
                self.resultados['erros'].append("Integridade referencial")
                
        except Exception as e:
            logger.error(f"❌ Erro ao validar integridade referencial: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Integridade referencial: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL - TESTE 2: EXCLUSÃO")
        logger.info("=" * 80)
        
        total_testes = len(self.resultados['sucessos']) + len(self.resultados['erros'])
        sucessos = len(self.resultados['sucessos'])
        erros = len(self.resultados['erros'])
        
        logger.info(f"\n📊 Estatísticas:")
        logger.info(f"   - Total de testes: {total_testes}")
        logger.info(f"   - Sucessos: {sucessos} ✅")
        logger.info(f"   - Erros: {erros} ❌")
        logger.info(f"   - Taxa de sucesso: {(sucessos/total_testes*100) if total_testes > 0 else 0:.1f}%")
        
        if self.resultados['sucessos']:
            logger.info(f"\n✅ Testes bem-sucedidos:")
            for sucesso in self.resultados['sucessos']:
                logger.info(f"   - {sucesso}")
        
        if self.resultados['erros']:
            logger.info(f"\n❌ Testes com erro:")
            for erro in self.resultados['erros']:
                logger.info(f"   - {erro}")
        
        if self.resultados['validacoes']:
            logger.info(f"\n📋 Validações realizadas:")
            for validacao in self.resultados['validacoes']:
                logger.info(f"   - {validacao['teste']}")
                if 'notas_verificadas' in validacao:
                    logger.info(f"     Notas verificadas: {validacao['notas_verificadas']}")
                if 'referencias_orfas' in validacao:
                    logger.info(f"     Referências órfãs: {validacao['referencias_orfas']}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("✅ TESTE 2 CONCLUÍDO COM SUCESSO!")
        else:
            logger.info("⚠️ TESTE 2 CONCLUÍDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    teste = TesteExclusao()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

