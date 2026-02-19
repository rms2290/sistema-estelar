#!/usr/bin/env python
"""
Script de Teste 1: Edição de Romaneios e Notas Fiscais

Este script testa:
- Editar romaneios existentes
- Editar notas fiscais vinculadas
- Verificar atualização de totais após edições
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
file_handler = logging.FileHandler('logs/teste_1_edicao.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configurar handler de console com encoding seguro
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# Configurar encoding do console para UTF-8 se possível
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


class TesteEdicao:
    """Classe para executar testes de edição"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'validacoes': []
        }
    
    def executar_teste(self):
        """Executa todos os testes de edição"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 1: EDIÇÃO DE ROMANEIOS E NOTAS FISCAIS")
        logger.info("=" * 80)
        
        try:
            # 1. Buscar romaneio existente
            romaneio = self._buscar_romaneio_teste()
            if not romaneio:
                logger.error("❌ Nenhum romaneio encontrado para teste. Execute primeiro o teste completo.")
                return False
            
            # 2. Testar edição de romaneio
            self._testar_edicao_romaneio(romaneio)
            
            # 3. Testar edição de notas fiscais vinculadas
            self._testar_edicao_notas_fiscais(romaneio)
            
            # 4. Testar atualização de totais
            self._testar_atualizacao_totais(romaneio)
            
            # 5. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro crítico no teste: {str(e)}", exc_info=True)
            return False
    
    def _buscar_romaneio_teste(self):
        """Busca um romaneio existente para teste"""
        try:
            romaneio = RomaneioViagem.objects.select_related(
                'cliente', 'motorista', 'veiculo_principal'
            ).prefetch_related('notas_fiscais').first()
            
            if romaneio:
                logger.info(f"✅ Romaneio encontrado: {romaneio.codigo}")
                logger.info(f"   - Cliente: {romaneio.cliente.razao_social}")
                logger.info(f"   - Notas vinculadas: {romaneio.notas_fiscais.count()}")
                logger.info(f"   - Peso total: {romaneio.peso_total}")
                logger.info(f"   - Valor total: {romaneio.valor_total}")
                return romaneio
            else:
                logger.warning("⚠️ Nenhum romaneio encontrado no banco")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar romaneio: {str(e)}", exc_info=True)
            return None
    
    def _testar_edicao_romaneio(self, romaneio):
        """Testa edição de campos do romaneio"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 1.1: Edição de Campos do Romaneio")
        logger.info("-" * 80)
        
        try:
            # Salvar valores originais
            origem_cidade_original = romaneio.origem_cidade
            destino_cidade_original = romaneio.destino_cidade
            observacoes_original = romaneio.observacoes
            
            # Editar campos
            nova_origem = "SÃO PAULO"
            novo_destino = "RIO DE JANEIRO"
            nova_observacao = f"Teste de edição - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            with transaction.atomic():
                romaneio.origem_cidade = nova_origem
                romaneio.destino_cidade = novo_destino
                romaneio.observacoes = nova_observacao
                romaneio.save()
            
            # Verificar se a edição foi salva
            romaneio.refresh_from_db()
            
            if (romaneio.origem_cidade == nova_origem and 
                romaneio.destino_cidade == novo_destino and
                romaneio.observacoes == nova_observacao):
                
                logger.info("✅ Edição de campos do romaneio: SUCESSO")
                logger.info(f"   - Origem alterada: {origem_cidade_original} → {nova_origem}")
                logger.info(f"   - Destino alterado: {destino_cidade_original} → {novo_destino}")
                self.resultados['sucessos'].append("Edição de campos do romaneio")
                
                # Restaurar valores originais
                romaneio.origem_cidade = origem_cidade_original
                romaneio.destino_cidade = destino_cidade_original
                romaneio.observacoes = observacoes_original
                romaneio.save()
                logger.info("   - Valores originais restaurados")
                
            else:
                logger.error("❌ Edição de campos do romaneio: FALHOU")
                logger.error(f"   - Origem esperada: {nova_origem}, obtida: {romaneio.origem_cidade}")
                logger.error(f"   - Destino esperado: {novo_destino}, obtido: {romaneio.destino_cidade}")
                self.resultados['erros'].append("Edição de campos do romaneio")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar edição de romaneio: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Edição de romaneio: {str(e)}")
    
    def _testar_edicao_notas_fiscais(self, romaneio):
        """Testa edição de notas fiscais vinculadas ao romaneio"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 1.2: Edição de Notas Fiscais Vinculadas")
        logger.info("-" * 80)
        
        try:
            notas_vinculadas = list(romaneio.notas_fiscais.all())
            
            if not notas_vinculadas:
                logger.warning("⚠️ Romaneio não possui notas fiscais vinculadas")
                return
            
            # Pegar primeira nota para teste
            nota_teste = notas_vinculadas[0]
            peso_original = nota_teste.peso
            valor_original = nota_teste.valor
            
            # Editar nota fiscal
            novo_peso = Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01'))
            novo_valor = Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01'))
            
            with transaction.atomic():
                nota_teste.peso = novo_peso
                nota_teste.valor = novo_valor
                nota_teste.save()
            
            # Verificar se a edição foi salva
            nota_teste.refresh_from_db()
            
            if (nota_teste.peso == novo_peso and nota_teste.valor == novo_valor):
                logger.info("✅ Edição de nota fiscal: SUCESSO")
                logger.info(f"   - Nota: {nota_teste.nota}")
                logger.info(f"   - Peso alterado: {peso_original} → {novo_peso}")
                logger.info(f"   - Valor alterado: {valor_original} → {novo_valor}")
                self.resultados['sucessos'].append("Edição de nota fiscal")
                
                # Restaurar valores originais
                nota_teste.peso = peso_original
                nota_teste.valor = valor_original
                nota_teste.save()
                logger.info("   - Valores originais restaurados")
                
            else:
                logger.error("❌ Edição de nota fiscal: FALHOU")
                self.resultados['erros'].append("Edição de nota fiscal")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar edição de notas fiscais: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Edição de notas fiscais: {str(e)}")
    
    def _testar_atualizacao_totais(self, romaneio):
        """Testa atualização de totais após edição de notas fiscais"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 1.3: Atualização de Totais após Edição")
        logger.info("-" * 80)
        
        try:
            notas_vinculadas = list(romaneio.notas_fiscais.all())
            
            if not notas_vinculadas:
                logger.warning("⚠️ Romaneio não possui notas fiscais vinculadas")
                return
            
            # Salvar totais originais
            peso_total_original = romaneio.peso_total
            valor_total_original = romaneio.valor_total
            
            # Editar uma nota fiscal
            nota_teste = notas_vinculadas[0]
            peso_original_nota = nota_teste.peso or Decimal('0')
            valor_original_nota = nota_teste.valor or Decimal('0')
            
            # Calcular novos valores esperados
            novo_peso_nota = Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01'))
            novo_valor_nota = Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01'))
            
            diferenca_peso = novo_peso_nota - peso_original_nota
            diferenca_valor = novo_valor_nota - valor_original_nota
            
            peso_total_esperado = (peso_total_original or Decimal('0')) + diferenca_peso
            valor_total_esperado = (valor_total_original or Decimal('0')) + diferenca_valor
            
            # Editar nota e recalcular totais
            with transaction.atomic():
                nota_teste.peso = novo_peso_nota
                nota_teste.valor = novo_valor_nota
                nota_teste.save()
                
                # Recalcular totais do romaneio
                romaneio.calcular_totais()
            
            # Verificar se os totais foram atualizados corretamente
            romaneio.refresh_from_db()
            
            # Comparar com margem de erro (devido a arredondamentos)
            margem_erro = Decimal('0.01')
            peso_correto = abs((romaneio.peso_total or Decimal('0')) - peso_total_esperado) <= margem_erro
            valor_correto = abs((romaneio.valor_total or Decimal('0')) - valor_total_esperado) <= margem_erro
            
            if peso_correto and valor_correto:
                logger.info("✅ Atualização de totais: SUCESSO")
                logger.info(f"   - Peso total: {peso_total_original} → {romaneio.peso_total}")
                logger.info(f"   - Valor total: {valor_total_original} → {romaneio.valor_total}")
                logger.info(f"   - Diferença esperada (peso): {diferenca_peso}")
                logger.info(f"   - Diferença esperada (valor): {diferenca_valor}")
                self.resultados['sucessos'].append("Atualização de totais")
                self.resultados['validacoes'].append({
                    'teste': 'Atualização de totais',
                    'peso_original': float(peso_total_original or 0),
                    'peso_atual': float(romaneio.peso_total or 0),
                    'valor_original': float(valor_total_original or 0),
                    'valor_atual': float(romaneio.valor_total or 0)
                })
                
                # Restaurar valores originais
                nota_teste.peso = peso_original_nota
                nota_teste.valor = valor_original_nota
                nota_teste.save()
                romaneio.calcular_totais()
                logger.info("   - Valores originais restaurados")
                
            else:
                logger.error("❌ Atualização de totais: FALHOU")
                logger.error(f"   - Peso esperado: {peso_total_esperado}, obtido: {romaneio.peso_total}")
                logger.error(f"   - Valor esperado: {valor_total_esperado}, obtido: {romaneio.valor_total}")
                self.resultados['erros'].append("Atualização de totais")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar atualização de totais: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Atualização de totais: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL - TESTE 1: EDIÇÃO")
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
                if 'peso_original' in validacao:
                    logger.info(f"     Peso: {validacao['peso_original']} → {validacao['peso_atual']}")
                    logger.info(f"     Valor: {validacao['valor_original']} → {validacao['valor_atual']}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("✅ TESTE 1 CONCLUÍDO COM SUCESSO!")
        else:
            logger.info("⚠️ TESTE 1 CONCLUÍDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    teste = TesteEdicao()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

