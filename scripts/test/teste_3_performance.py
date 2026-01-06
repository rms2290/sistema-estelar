#!/usr/bin/env python
"""
Script de Teste 3: Performance do Sistema

Este script testa:
- Criação de 1000+ notas fiscais
- Criação de 100+ romaneios simultâneos
- Validação de queries com índices
- Medição de tempo de execução
"""
import os
import sys
import django
from pathlib import Path
from decimal import Decimal
import random
from datetime import datetime, timedelta
import time

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction, connection
from django.utils import timezone
from django.db.models import Q, Count, Sum
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem
)
from notas.services.romaneio_service import RomaneioService

# Configurar logging
import logging
# Configurar handler de arquivo com UTF-8
file_handler = logging.FileHandler('logs/teste_3_performance.log', encoding='utf-8')
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


class TestePerformance:
    """Classe para executar testes de performance"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'metricas': []
        }
        self.tempos = {}
    
    def executar_teste(self):
        """Executa todos os testes de performance"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 3: PERFORMANCE DO SISTEMA")
        logger.info("=" * 80)
        
        try:
            # 1. Testar criação de 1000+ notas fiscais
            self._testar_criacao_notas_fiscais(quantidade=1000)
            
            # 2. Testar criação de 100+ romaneios simultâneos
            self._testar_criacao_romaneios(quantidade=100)
            
            # 3. Testar queries com índices
            self._testar_queries_com_indices()
            
            # 4. Testar queries otimizadas (select_related/prefetch_related)
            self._testar_queries_otimizadas()
            
            # 5. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro crítico no teste: {str(e)}", exc_info=True)
            return False
    
    def _medir_tempo(self, operacao_nome):
        """Context manager para medir tempo de execução"""
        class MedidorTempo:
            def __init__(self, nome, resultados):
                self.nome = nome
                self.resultados = resultados
                self.inicio = None
            
            def __enter__(self):
                self.inicio = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                tempo_decorrido = time.time() - self.inicio
                if self.nome not in self.resultados:
                    self.resultados[self.nome] = []
                self.resultados[self.nome].append(tempo_decorrido)
        
        return MedidorTempo(operacao_nome, self.tempos)
    
    def _testar_criacao_notas_fiscais(self, quantidade=1000):
        """Testa criação de múltiplas notas fiscais"""
        logger.info("\n" + "-" * 80)
        logger.info(f"TESTE 3.1: Criação de {quantidade} Notas Fiscais")
        logger.info("-" * 80)
        
        try:
            # Buscar cliente existente
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.error("❌ Nenhum cliente ativo encontrado")
                self.resultados['erros'].append("Cliente não encontrado para teste de notas")
                return
            
            notas_criadas = 0
            notas_existentes = 0
            
            with self._medir_tempo('criacao_notas_fiscais'):
                for i in range(quantidade):
                    try:
                        nota_numero = f"PERF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}"
                        
                        # Verificar se já existe
                        if NotaFiscal.objects.filter(nota=nota_numero).exists():
                            notas_existentes += 1
                            continue
                        
                        nota = NotaFiscal.objects.create(
                            cliente=cliente,
                            nota=nota_numero,
                            data=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                            fornecedor=f"Fornecedor {i}",
                            mercadoria=f"Mercadoria {i}",
                            peso=Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                            valor=Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                            quantidade=random.randint(1, 100),
                            status=random.choice(['Depósito', 'Enviada'])
                        )
                        notas_criadas += 1
                        
                        if (i + 1) % 100 == 0:
                            logger.info(f"   Progresso: {i + 1}/{quantidade} notas processadas...")
                    
                    except Exception as e:
                        logger.warning(f"   Erro ao criar nota {i}: {str(e)}")
            
            tempo_total = sum(self.tempos.get('criacao_notas_fiscais', []))
            tempo_medio = tempo_total / quantidade if quantidade > 0 else 0
            
            logger.info(f"✅ Criação de notas fiscais concluída:")
            logger.info(f"   - Notas criadas: {notas_criadas}")
            logger.info(f"   - Notas já existentes: {notas_existentes}")
            logger.info(f"   - Tempo total: {tempo_total:.2f} segundos")
            logger.info(f"   - Tempo médio por nota: {tempo_medio*1000:.2f} ms")
            logger.info(f"   - Notas por segundo: {notas_criadas/tempo_total if tempo_total > 0 else 0:.2f}")
            
            self.resultados['sucessos'].append(f"Criação de {notas_criadas} notas fiscais")
            self.resultados['metricas'].append({
                'teste': 'Criação de notas fiscais',
                'quantidade': notas_criadas,
                'tempo_total': tempo_total,
                'tempo_medio': tempo_medio,
                'notas_por_segundo': notas_criadas/tempo_total if tempo_total > 0 else 0
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar criação de notas fiscais: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Criação de notas fiscais: {str(e)}")
    
    def _testar_criacao_romaneios(self, quantidade=100):
        """Testa criação de múltiplos romaneios simultâneos"""
        logger.info("\n" + "-" * 80)
        logger.info(f"TESTE 3.2: Criação de {quantidade} Romaneios Simultâneos")
        logger.info("-" * 80)
        
        try:
            # Buscar dados necessários
            cliente = Cliente.objects.filter(status='Ativo').first()
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if not all([cliente, motorista, veiculo]):
                logger.error("❌ Dados insuficientes para criar romaneios")
                self.resultados['erros'].append("Dados insuficientes para romaneios")
                return
            
            # Buscar notas fiscais em depósito
            notas_disponiveis = list(NotaFiscal.objects.filter(
                cliente=cliente,
                status='Depósito'
            )[:quantidade * 3])  # 3 notas por romaneio
            
            if len(notas_disponiveis) < quantidade:
                logger.warning(f"⚠️ Apenas {len(notas_disponiveis)} notas disponíveis, criando mais...")
                # Criar mais notas se necessário
                for i in range(quantidade * 3 - len(notas_disponiveis)):
                    nota = NotaFiscal.objects.create(
                        cliente=cliente,
                        nota=f"PERF-ROM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                        data=timezone.now().date(),
                        fornecedor=f"Fornecedor ROM {i}",
                        mercadoria=f"Mercadoria ROM {i}",
                        peso=Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                        valor=Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                        quantidade=random.randint(1, 100),
                        status='Depósito'
                    )
                    notas_disponiveis.append(nota)
            
            romaneios_criados = 0
            romaneios_existentes = 0
            
            with self._medir_tempo('criacao_romaneios'):
                for i in range(quantidade):
                    try:
                        codigo_romaneio = f"PERF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}"
                        
                        # Verificar se já existe
                        if RomaneioViagem.objects.filter(codigo=codigo_romaneio).exists():
                            romaneios_existentes += 1
                            continue
                        
                        # Selecionar 2-3 notas para o romaneio
                        notas_romaneio = random.sample(notas_disponiveis, min(3, len(notas_disponiveis)))
                        
                        romaneio = RomaneioViagem.objects.create(
                            codigo=codigo_romaneio,
                            cliente=cliente,
                            motorista=motorista,
                            veiculo_principal=veiculo,
                            origem_cidade="SÃO PAULO",
                            destino_cidade="RIO DE JANEIRO",
                            status='Salvo'
                        )
                        
                        # Vincular notas
                        for nota in notas_romaneio:
                            romaneio.notas_fiscais.add(nota)
                        
                        # Calcular totais
                        romaneio.calcular_totais()
                        
                        romaneios_criados += 1
                        
                        if (i + 1) % 20 == 0:
                            logger.info(f"   Progresso: {i + 1}/{quantidade} romaneios criados...")
                    
                    except Exception as e:
                        logger.warning(f"   Erro ao criar romaneio {i}: {str(e)}")
            
            tempo_total = sum(self.tempos.get('criacao_romaneios', []))
            tempo_medio = tempo_total / quantidade if quantidade > 0 else 0
            
            logger.info(f"✅ Criação de romaneios concluída:")
            logger.info(f"   - Romaneios criados: {romaneios_criados}")
            logger.info(f"   - Romaneios já existentes: {romaneios_existentes}")
            logger.info(f"   - Tempo total: {tempo_total:.2f} segundos")
            logger.info(f"   - Tempo médio por romaneio: {tempo_medio*1000:.2f} ms")
            logger.info(f"   - Romaneios por segundo: {romaneios_criados/tempo_total if tempo_total > 0 else 0:.2f}")
            
            self.resultados['sucessos'].append(f"Criação de {romaneios_criados} romaneios")
            self.resultados['metricas'].append({
                'teste': 'Criação de romaneios',
                'quantidade': romaneios_criados,
                'tempo_total': tempo_total,
                'tempo_medio': tempo_medio,
                'romaneios_por_segundo': romaneios_criados/tempo_total if tempo_total > 0 else 0
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar criação de romaneios: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Criação de romaneios: {str(e)}")
    
    def _testar_queries_com_indices(self):
        """Testa queries que utilizam índices do banco de dados"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 3.3: Queries com Índices")
        logger.info("-" * 80)
        
        try:
            # 1. Query com índice em NotaFiscal.status
            with self._medir_tempo('query_notas_status'):
                notas_deposito = NotaFiscal.objects.filter(status='Depósito').count()
            
            tempo_status = sum(self.tempos.get('query_notas_status', []))
            
            # 2. Query com índice em NotaFiscal.data
            with self._medir_tempo('query_notas_data'):
                data_limite = timezone.now().date() - timedelta(days=30)
                notas_recentes = NotaFiscal.objects.filter(data__gte=data_limite).count()
            
            tempo_data = sum(self.tempos.get('query_notas_data', []))
            
            # 3. Query com índice composto (status, data)
            with self._medir_tempo('query_notas_status_data'):
                notas_deposito_recentes = NotaFiscal.objects.filter(
                    status='Depósito',
                    data__gte=data_limite
                ).count()
            
            tempo_status_data = sum(self.tempos.get('query_notas_status_data', []))
            
            # 4. Query com índice em Cliente.razao_social
            with self._medir_tempo('query_clientes_razao'):
                clientes_ativos = Cliente.objects.filter(
                    status='Ativo',
                    razao_social__icontains='TEST'
                ).count()
            
            tempo_razao = sum(self.tempos.get('query_clientes_razao', []))
            
            logger.info(f"✅ Queries com índices executadas:")
            logger.info(f"   - Notas em depósito: {notas_deposito} ({tempo_status*1000:.2f} ms)")
            logger.info(f"   - Notas recentes: {notas_recentes} ({tempo_data*1000:.2f} ms)")
            logger.info(f"   - Notas depósito recentes: {notas_deposito_recentes} ({tempo_status_data*1000:.2f} ms)")
            logger.info(f"   - Clientes ativos: {clientes_ativos} ({tempo_razao*1000:.2f} ms)")
            
            self.resultados['sucessos'].append("Queries com índices executadas")
            self.resultados['metricas'].append({
                'teste': 'Queries com índices',
                'query_notas_status': tempo_status,
                'query_notas_data': tempo_data,
                'query_notas_status_data': tempo_status_data,
                'query_clientes_razao': tempo_razao
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar queries com índices: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Queries com índices: {str(e)}")
    
    def _testar_queries_otimizadas(self):
        """Testa queries otimizadas com select_related e prefetch_related"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 3.4: Queries Otimizadas (select_related/prefetch_related)")
        logger.info("-" * 80)
        
        try:
            # 1. Query sem otimização
            with self._medir_tempo('query_romaneios_sem_otimizacao'):
                romaneios_sem_opt = list(RomaneioViagem.objects.all()[:100])
                # Acessar relacionamentos para forçar queries
                for r in romaneios_sem_opt:
                    _ = r.cliente.razao_social
                    _ = r.motorista.nome
                    _ = r.veiculo_principal.placa
                    _ = list(r.notas_fiscais.all()[:5])
            
            tempo_sem_opt = sum(self.tempos.get('query_romaneios_sem_otimizacao', []))
            num_queries_sem_opt = len(connection.queries)
            
            # Limpar queries
            connection.queries_log.clear()
            
            # 2. Query com otimização
            with self._medir_tempo('query_romaneios_com_otimizacao'):
                romaneios_com_opt = list(
                    RomaneioViagem.objects.select_related(
                        'cliente', 'motorista', 'veiculo_principal'
                    ).prefetch_related('notas_fiscais')[:100]
                )
                # Acessar relacionamentos (já carregados)
                for r in romaneios_com_opt:
                    _ = r.cliente.razao_social
                    _ = r.motorista.nome
                    _ = r.veiculo_principal.placa
                    _ = list(r.notas_fiscais.all()[:5])
            
            tempo_com_opt = sum(self.tempos.get('query_romaneios_com_otimizacao', []))
            num_queries_com_opt = len(connection.queries)
            
            melhoria = ((tempo_sem_opt - tempo_com_opt) / tempo_sem_opt * 100) if tempo_sem_opt > 0 else 0
            
            logger.info(f"✅ Comparação de queries:")
            logger.info(f"   - Sem otimização: {tempo_sem_opt:.2f}s ({num_queries_sem_opt} queries)")
            logger.info(f"   - Com otimização: {tempo_com_opt:.2f}s ({num_queries_com_opt} queries)")
            logger.info(f"   - Melhoria: {melhoria:.1f}% mais rápido")
            logger.info(f"   - Redução de queries: {num_queries_sem_opt - num_queries_com_opt}")
            
            self.resultados['sucessos'].append("Queries otimizadas testadas")
            self.resultados['metricas'].append({
                'teste': 'Queries otimizadas',
                'tempo_sem_otimizacao': tempo_sem_opt,
                'tempo_com_otimizacao': tempo_com_opt,
                'melhoria_percentual': melhoria,
                'queries_sem_otimizacao': num_queries_sem_opt,
                'queries_com_otimizacao': num_queries_com_opt
            })
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar queries otimizadas: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Queries otimizadas: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL - TESTE 3: PERFORMANCE")
        logger.info("=" * 80)
        
        total_testes = len(self.resultados['sucessos']) + len(self.resultados['erros'])
        sucessos = len(self.resultados['sucessos'])
        erros = len(self.resultados['erros'])
        
        logger.info(f"\n📊 Estatísticas:")
        logger.info(f"   - Total de testes: {total_testes}")
        logger.info(f"   - Sucessos: {sucessos} ✅")
        logger.info(f"   - Erros: {erros} ❌")
        logger.info(f"   - Taxa de sucesso: {(sucessos/total_testes*100) if total_testes > 0 else 0:.1f}%")
        
        if self.resultados['metricas']:
            logger.info(f"\n📈 Métricas de Performance:")
            for metrica in self.resultados['metricas']:
                logger.info(f"\n   {metrica['teste']}:")
                for key, value in metrica.items():
                    if key != 'teste':
                        if isinstance(value, float):
                            if 'tempo' in key.lower() or 'segundo' in key.lower():
                                logger.info(f"     - {key}: {value:.2f}s")
                            elif 'ms' in key.lower() or 'milissegundo' in key.lower():
                                logger.info(f"     - {key}: {value:.2f}ms")
                            elif 'percentual' in key.lower() or 'melhoria' in key.lower():
                                logger.info(f"     - {key}: {value:.1f}%")
                            else:
                                logger.info(f"     - {key}: {value:.2f}")
                        else:
                            logger.info(f"     - {key}: {value}")
        
        if self.resultados['sucessos']:
            logger.info(f"\n✅ Testes bem-sucedidos:")
            for sucesso in self.resultados['sucessos']:
                logger.info(f"   - {sucesso}")
        
        if self.resultados['erros']:
            logger.info(f"\n❌ Testes com erro:")
            for erro in self.resultados['erros']:
                logger.info(f"   - {erro}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("✅ TESTE 3 CONCLUÍDO COM SUCESSO!")
        else:
            logger.info("⚠️ TESTE 3 CONCLUÍDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    teste = TestePerformance()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

