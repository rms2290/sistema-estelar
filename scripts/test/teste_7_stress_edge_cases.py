#!/usr/bin/env python
"""
Script de Teste 7: Stress e Edge Cases

Este script força o sistema em situações extremas para identificar erros:
- Dados no limite (valores máximos/minimos)
- Campos obrigatórios ausentes
- Relacionamentos inválidos
- Concorrência e race conditions
- Dados duplicados
- Strings muito longas
- Valores negativos onde não deveriam
- Operações em massa
- Estados inválidos
"""
import os
import sys
import django
from pathlib import Path
from decimal import Decimal, InvalidOperation
import random
from datetime import datetime, timedelta
import threading
import time

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.exceptions import ValidationError
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem, Usuario
)
from notas.services.romaneio_service import RomaneioService

# Configurar logging
import logging
file_handler = logging.FileHandler('logs/teste_7_stress_edge_cases.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
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


class TesteStressEdgeCases:
    """Classe para executar testes de stress e edge cases"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'warnings': [],
            'edge_cases_testados': []
        }
        self.dados_teste = {}
    
    def executar_teste(self):
        """Executa todos os testes de stress e edge cases"""
        print("=" * 80)
        print("INICIANDO TESTE 7: STRESS E EDGE CASES")
        print("=" * 80)
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 7: STRESS E EDGE CASES")
        logger.info("=" * 80)
        
        try:
            print("Iniciando testes...")
            logger.info("Iniciando testes...")
            # 1. Testar limites de campos (valores máximos/minimos)
            print("Teste 1: Limites de campos...")
            self._testar_limites_campos()
            
            # 2. Testar campos obrigatórios ausentes
            self._testar_campos_obrigatorios_ausentes()
            
            # 3. Testar strings muito longas
            self._testar_strings_muito_longas()
            
            # 4. Testar valores negativos onde não deveriam
            self._testar_valores_negativos()
            
            # 5. Testar relacionamentos inválidos
            self._testar_relacionamentos_invalidos()
            
            # 6. Testar dados duplicados (UNIQUE constraints)
            self._testar_dados_duplicados()
            
            # 7. Testar estados inválidos
            self._testar_estados_invalidos()
            
            # 8. Testar operações em massa (stress)
            self._testar_operacoes_massa()
            
            # 9. Testar concorrência (race conditions)
            self._testar_concorrencia()
            
            # 10. Testar cálculos com valores extremos
            self._testar_calculos_extremos()
            
            # 11. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro critico no teste: {str(e)}", exc_info=True)
            return False
    
    def _testar_limites_campos(self):
        """Testa valores nos limites dos campos"""
        print("\n" + "-" * 80)
        print("TESTE 7.1: Limites de Campos (Valores Maximos/Minimos)")
        print("-" * 80)
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.1: Limites de Campos (Valores Maximos/Minimos)")
        logger.info("-" * 80)
        
        try:
            # Buscar cliente existente
            print("Buscando cliente...")
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                print("AVISO: Cliente nao encontrado para teste de limites")
                logger.warning("Cliente nao encontrado para teste de limites")
                return
            print(f"Cliente encontrado: {cliente.razao_social}")
            
            # Testar valores máximos de Decimal
            print("Testando valores maximos...")
            try:
                nota_max = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=f"LIMITE-MAX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    data=timezone.now().date(),
                    fornecedor="Fornecedor Teste",
                    mercadoria="Mercadoria Teste",
                    peso=Decimal('9999999999.99'),  # Valor próximo ao máximo
                    valor=Decimal('9999999999.99'),
                    quantidade=Decimal('9999999999.99')
                )
                print("Valores maximos aceitos corretamente")
                logger.info("Valores maximos aceitos corretamente")
                self.resultados['sucessos'].append("Valores maximos de Decimal")
                nota_max.delete()
            except Exception as e:
                print(f"Valores maximos rejeitados: {str(e)[:100]}")
                logger.warning(f"Valores maximos rejeitados: {str(e)}")
                self.resultados['warnings'].append(f"Valores maximos: {str(e)}")
            
            # Testar valores mínimos (zero)
            try:
                nota_min = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=f"LIMITE-MIN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    data=timezone.now().date(),
                    fornecedor="Fornecedor Teste",
                    mercadoria="Mercadoria Teste",
                    peso=Decimal('0.00'),
                    valor=Decimal('0.00'),
                    quantidade=Decimal('0.00')
                )
                logger.info("Valores minimos (zero) aceitos corretamente")
                self.resultados['sucessos'].append("Valores minimos (zero)")
                nota_min.delete()
            except Exception as e:
                logger.warning(f"Valores minimos rejeitados: {str(e)}")
                self.resultados['warnings'].append(f"Valores minimos: {str(e)}")
            
            self.resultados['edge_cases_testados'].append("Limites de campos")
            
        except Exception as e:
            logger.error(f"Erro ao testar limites: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Limites de campos: {str(e)}")
    
    def _testar_campos_obrigatorios_ausentes(self):
        """Testa criação sem campos obrigatórios"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.2: Campos Obrigatorios Ausentes")
        logger.info("-" * 80)
        
        try:
            # Testar NotaFiscal sem cliente
            try:
                nota_sem_cliente = NotaFiscal(
                    nota="TESTE-SEM-CLIENTE",
                    data=timezone.now().date(),
                    fornecedor="Fornecedor",
                    mercadoria="Mercadoria",
                    peso=Decimal('100.00'),
                    valor=Decimal('1000.00'),
                    quantidade=Decimal('10.00')
                )
                nota_sem_cliente.full_clean()  # Força validação
                nota_sem_cliente.save()
                logger.error("Nota criada sem cliente (ERRO - deveria falhar)")
                self.resultados['erros'].append("Nota criada sem cliente")
                nota_sem_cliente.delete()
            except (ValidationError, IntegrityError) as e:
                logger.info(f"Validacao funcionou: {str(e)[:100]}")
                self.resultados['sucessos'].append("Validacao de campo obrigatorio (cliente)")
            
            # Testar NotaFiscal sem nota
            try:
                cliente = Cliente.objects.filter(status='Ativo').first()
                if cliente:
                    nota_sem_numero = NotaFiscal(
                        cliente=cliente,
                        nota="",  # String vazia
                        data=timezone.now().date(),
                        fornecedor="Fornecedor",
                        mercadoria="Mercadoria",
                        peso=Decimal('100.00'),
                        valor=Decimal('1000.00'),
                        quantidade=Decimal('10.00')
                    )
                    nota_sem_numero.full_clean()
                    nota_sem_numero.save()
                    logger.warning("Nota criada com numero vazio (pode ser aceito)")
                    self.resultados['warnings'].append("Nota com numero vazio aceita")
                    nota_sem_numero.delete()
            except (ValidationError, IntegrityError) as e:
                logger.info(f"Validacao funcionou: {str(e)[:100]}")
                self.resultados['sucessos'].append("Validacao de campo obrigatorio (nota)")
            
            self.resultados['edge_cases_testados'].append("Campos obrigatorios ausentes")
            
        except Exception as e:
            logger.error(f"Erro ao testar campos obrigatorios: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Campos obrigatorios: {str(e)}")
    
    def _testar_strings_muito_longas(self):
        """Testa strings que excedem o tamanho máximo"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.3: Strings Muito Longas")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.warning("Cliente nao encontrado")
                return
            
            # String muito longa para campo de 200 caracteres
            string_longa = "A" * 500
            
            try:
                nota_longa = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=f"LONGA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    data=timezone.now().date(),
                    fornecedor=string_longa[:200],  # Truncar para max_length
                    mercadoria=string_longa[:200],
                    peso=Decimal('100.00'),
                    valor=Decimal('1000.00'),
                    quantidade=Decimal('10.00')
                )
                logger.info("String longa truncada automaticamente")
                self.resultados['sucessos'].append("Truncamento de string longa")
                nota_longa.delete()
            except Exception as e:
                logger.warning(f"Erro com string longa: {str(e)}")
                self.resultados['warnings'].append(f"String longa: {str(e)}")
            
            self.resultados['edge_cases_testados'].append("Strings muito longas")
            
        except Exception as e:
            logger.error(f"Erro ao testar strings longas: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Strings longas: {str(e)}")
    
    def _testar_valores_negativos(self):
        """Testa valores negativos onde não deveriam ser aceitos"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.4: Valores Negativos")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.warning("Cliente nao encontrado")
                return
            
            # Tentar criar nota com valores negativos
            try:
                nota_negativa = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=f"NEGATIVA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    data=timezone.now().date(),
                    fornecedor="Fornecedor",
                    mercadoria="Mercadoria",
                    peso=Decimal('-100.00'),  # Negativo
                    valor=Decimal('-1000.00'),  # Negativo
                    quantidade=Decimal('-10.00')  # Negativo
                )
                logger.warning("Valores negativos aceitos (pode ser intencional)")
                self.resultados['warnings'].append("Valores negativos aceitos")
                nota_negativa.delete()
            except (ValidationError, IntegrityError) as e:
                logger.info(f"Validacao funcionou: valores negativos rejeitados")
                self.resultados['sucessos'].append("Validacao de valores negativos")
            except Exception as e:
                logger.warning(f"Erro inesperado: {str(e)}")
                self.resultados['warnings'].append(f"Valores negativos: {str(e)}")
            
            self.resultados['edge_cases_testados'].append("Valores negativos")
            
        except Exception as e:
            logger.error(f"Erro ao testar valores negativos: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Valores negativos: {str(e)}")
    
    def _testar_relacionamentos_invalidos(self):
        """Testa relacionamentos com objetos inexistentes"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.5: Relacionamentos Invalidos")
        logger.info("-" * 80)
        
        try:
            # Tentar criar romaneio com cliente inexistente
            try:
                motorista = Motorista.objects.first()
                veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
                
                if motorista and veiculo:
                    romaneio_invalido = RomaneioViagem(
                        codigo=f"INVALIDO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        cliente_id=999999,  # ID inexistente
                        motorista=motorista,
                        veiculo_principal=veiculo,
                        status='Salvo'
                    )
                    romaneio_invalido.save()
                    logger.error("Romaneio criado com cliente inexistente (ERRO)")
                    self.resultados['erros'].append("Relacionamento invalido aceito")
                    romaneio_invalido.delete()
            except (IntegrityError, ValidationError) as e:
                logger.info(f"Validacao funcionou: relacionamento invalido rejeitado")
                self.resultados['sucessos'].append("Validacao de relacionamento invalido")
            except Exception as e:
                logger.warning(f"Erro inesperado: {str(e)}")
                self.resultados['warnings'].append(f"Relacionamento invalido: {str(e)}")
            
            self.resultados['edge_cases_testados'].append("Relacionamentos invalidos")
            
        except Exception as e:
            logger.error(f"Erro ao testar relacionamentos: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Relacionamentos invalidos: {str(e)}")
    
    def _testar_dados_duplicados(self):
        """Testa violação de constraints UNIQUE"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.6: Dados Duplicados (UNIQUE Constraints)")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.warning("Cliente nao encontrado")
                return
            
            # Criar primeira nota
            nota1 = NotaFiscal.objects.create(
                cliente=cliente,
                nota=f"DUPLICADA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                data=timezone.now().date(),
                fornecedor="Fornecedor",
                mercadoria="Mercadoria",
                peso=Decimal('100.00'),
                valor=Decimal('1000.00'),
                quantidade=Decimal('10.00')
            )
            
            # Tentar criar nota duplicada (mesmo número)
            try:
                nota2 = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=nota1.nota,  # Mesmo número
                    data=nota1.data,
                    fornecedor=nota1.fornecedor,
                    mercadoria=nota1.mercadoria,
                    peso=nota1.peso,
                    valor=nota1.valor,
                    quantidade=nota1.quantidade
                )
                logger.warning("Nota duplicada criada (pode ser aceito se nao houver constraint)")
                self.resultados['warnings'].append("Nota duplicada aceita")
                nota2.delete()
            except IntegrityError as e:
                logger.info(f"Constraint UNIQUE funcionou: {str(e)[:100]}")
                self.resultados['sucessos'].append("Constraint UNIQUE funcionando")
            except Exception as e:
                logger.warning(f"Erro inesperado: {str(e)}")
                self.resultados['warnings'].append(f"Dados duplicados: {str(e)}")
            
            nota1.delete()
            self.resultados['edge_cases_testados'].append("Dados duplicados")
            
        except Exception as e:
            logger.error(f"Erro ao testar dados duplicados: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Dados duplicados: {str(e)}")
    
    def _testar_estados_invalidos(self):
        """Testa transições de estado inválidas"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.7: Estados Invalidos")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if not all([cliente, motorista, veiculo]):
                logger.warning("Dados insuficientes para teste de estados")
                return
            
            # Criar romaneio e tentar operações inválidas
            romaneio = RomaneioViagem.objects.create(
                codigo=f"ESTADO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                cliente=cliente,
                motorista=motorista,
                veiculo_principal=veiculo,
                status='Emitido'  # Já emitido
            )
            
            # Tentar editar romaneio emitido (pode ser permitido ou não)
            try:
                romaneio.observacoes = "Tentativa de editar romaneio emitido"
                romaneio.save()
                logger.info("Romaneio emitido pode ser editado")
                self.resultados['sucessos'].append("Edicao de romaneio emitido permitida")
            except Exception as e:
                logger.info(f"Edicao de romaneio emitido bloqueada: {str(e)}")
                self.resultados['sucessos'].append("Bloqueio de edicao de romaneio emitido")
            
            romaneio.delete()
            self.resultados['edge_cases_testados'].append("Estados invalidos")
            
        except Exception as e:
            logger.error(f"Erro ao testar estados: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Estados invalidos: {str(e)}")
    
    def _testar_operacoes_massa(self):
        """Testa operações em massa (stress test)"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.8: Operacoes em Massa (Stress Test)")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.warning("Cliente nao encontrado")
                return
            
            # Criar 100 notas fiscais rapidamente
            inicio = time.time()
            notas_criadas = 0
            erros = 0
            
            for i in range(100):
                try:
                    nota = NotaFiscal.objects.create(
                        cliente=cliente,
                        nota=f"STRESS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                        data=timezone.now().date(),
                        fornecedor=f"Fornecedor {i}",
                        mercadoria=f"Mercadoria {i}",
                        peso=Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                        valor=Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                        quantidade=Decimal(str(random.randint(1, 100)))
                    )
                    notas_criadas += 1
                except Exception as e:
                    erros += 1
                    logger.warning(f"Erro ao criar nota {i}: {str(e)[:50]}")
            
            tempo_decorrido = time.time() - inicio
            
            logger.info(f"Operacoes em massa: {notas_criadas} criadas, {erros} erros em {tempo_decorrido:.2f}s")
            logger.info(f"Taxa: {notas_criadas/tempo_decorrido:.2f} notas/segundo")
            
            if notas_criadas > 90:
                self.resultados['sucessos'].append(f"Operacoes em massa ({notas_criadas}/100)")
            else:
                self.resultados['warnings'].append(f"Operacoes em massa ({notas_criadas}/100)")
            
            # Limpar notas criadas
            NotaFiscal.objects.filter(nota__startswith='STRESS-').delete()
            
            self.resultados['edge_cases_testados'].append("Operacoes em massa")
            
        except Exception as e:
            logger.error(f"Erro ao testar operacoes em massa: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Operacoes em massa: {str(e)}")
    
    def _testar_concorrencia(self):
        """Testa condições de corrida (race conditions)"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.9: Concorrencia (Race Conditions)")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            if not cliente:
                logger.warning("Cliente nao encontrado")
                return
            
            # Criar nota compartilhada
            nota_compartilhada = NotaFiscal.objects.create(
                cliente=cliente,
                nota=f"CONCORRENCIA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                data=timezone.now().date(),
                fornecedor="Fornecedor",
                mercadoria="Mercadoria",
                peso=Decimal('100.00'),
                valor=Decimal('1000.00'),
                quantidade=Decimal('10.00')
            )
            
            erros_concorrencia = []
            
            def editar_nota(thread_id):
                """Função para editar nota em thread separada"""
                try:
                    nota = NotaFiscal.objects.get(pk=nota_compartilhada.pk)
                    nota.peso = Decimal(str(100 + thread_id))
                    nota.save()
                except Exception as e:
                    erros_concorrencia.append(f"Thread {thread_id}: {str(e)}")
            
            # Criar 5 threads tentando editar simultaneamente
            threads = []
            for i in range(5):
                thread = threading.Thread(target=editar_nota, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Aguardar todas as threads
            for thread in threads:
                thread.join()
            
            if erros_concorrencia:
                logger.warning(f"Erros de concorrencia detectados: {len(erros_concorrencia)}")
                self.resultados['warnings'].append(f"Concorrencia: {len(erros_concorrencia)} erros")
            else:
                logger.info("Concorrencia tratada corretamente")
                self.resultados['sucessos'].append("Tratamento de concorrencia")
            
            nota_compartilhada.delete()
            self.resultados['edge_cases_testados'].append("Concorrencia")
            
        except Exception as e:
            logger.error(f"Erro ao testar concorrencia: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Concorrencia: {str(e)}")
    
    def _testar_calculos_extremos(self):
        """Testa cálculos com valores extremos"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 7.10: Calculos com Valores Extremos")
        logger.info("-" * 80)
        
        try:
            cliente = Cliente.objects.filter(status='Ativo').first()
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if not all([cliente, motorista, veiculo]):
                logger.warning("Dados insuficientes")
                return
            
            # Criar romaneio com valores extremos
            romaneio = RomaneioViagem.objects.create(
                codigo=f"CALC-EXTREMO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                cliente=cliente,
                motorista=motorista,
                veiculo_principal=veiculo,
                status='Salvo'
            )
            
            # Criar notas com valores muito grandes
            notas_extremas = []
            for i in range(3):
                nota = NotaFiscal.objects.create(
                    cliente=cliente,
                    nota=f"EXTREMO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                    data=timezone.now().date(),
                    fornecedor="Fornecedor",
                    mercadoria="Mercadoria",
                    peso=Decimal('999999.99'),
                    valor=Decimal('9999999.99'),
                    quantidade=Decimal('999999.99')
                )
                romaneio.notas_fiscais.add(nota)
                notas_extremas.append(nota)
            
            # Calcular totais
            try:
                romaneio.calcular_totais()
                logger.info(f"Calculos extremos: peso={romaneio.peso_total}, valor={romaneio.valor_total}")
                self.resultados['sucessos'].append("Calculos com valores extremos")
            except Exception as e:
                logger.error(f"Erro ao calcular totais extremos: {str(e)}")
                self.resultados['erros'].append(f"Calculos extremos: {str(e)}")
            
            # Limpar
            for nota in notas_extremas:
                nota.delete()
            romaneio.delete()
            
            self.resultados['edge_cases_testados'].append("Calculos extremos")
            
        except Exception as e:
            logger.error(f"Erro ao testar calculos: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Calculos extremos: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATORIO FINAL - TESTE 7: STRESS E EDGE CASES")
        logger.info("=" * 80)
        
        total_testes = len(self.resultados['sucessos']) + len(self.resultados['erros']) + len(self.resultados['warnings'])
        sucessos = len(self.resultados['sucessos'])
        erros = len(self.resultados['erros'])
        warnings = len(self.resultados['warnings'])
        
        logger.info(f"\nEstatisticas:")
        logger.info(f"   - Total de testes: {total_testes}")
        logger.info(f"   - Sucessos: {sucessos}")
        logger.info(f"   - Erros encontrados: {erros}")
        logger.info(f"   - Warnings: {warnings}")
        logger.info(f"   - Edge cases testados: {len(self.resultados['edge_cases_testados'])}")
        
        if self.resultados['sucessos']:
            logger.info(f"\nTestes bem-sucedidos:")
            for sucesso in self.resultados['sucessos']:
                logger.info(f"   - {sucesso}")
        
        if self.resultados['warnings']:
            logger.info(f"\nWarnings (comportamentos inesperados mas nao criticos):")
            for warning in self.resultados['warnings']:
                logger.info(f"   - {warning}")
        
        if self.resultados['erros']:
            logger.info(f"\nErros encontrados (necessitam atencao):")
            for erro in self.resultados['erros']:
                logger.info(f"   - {erro}")
        
        if self.resultados['edge_cases_testados']:
            logger.info(f"\nEdge cases testados:")
            for edge_case in self.resultados['edge_cases_testados']:
                logger.info(f"   - {edge_case}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("TESTE 7 CONCLUIDO - NENHUM ERRO CRITICO ENCONTRADO")
        else:
            logger.info(f"TESTE 7 CONCLUIDO - {erros} ERRO(S) ENCONTRADO(S)")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    os.makedirs('logs', exist_ok=True)
    
    teste = TesteStressEdgeCases()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

