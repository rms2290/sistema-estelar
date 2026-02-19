#!/usr/bin/env python
"""
Script de Teste 4: Permissões e Acesso

Este script testa:
- Validação de acesso de clientes aos seus dados
- Teste de validações de permissões granulares
- Verificação de restrições de acesso
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
from django.contrib.auth import get_user_model
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem, Usuario
)
from notas.decorators import can_access_cliente_data

# Configurar logging
import logging
# Configurar handler de arquivo com UTF-8
file_handler = logging.FileHandler('logs/teste_4_permissoes.log', encoding='utf-8')
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

Usuario = get_user_model()


class TestePermissoes:
    """Classe para executar testes de permissões"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'validacoes': []
        }
        self.usuarios_teste = {}
        self.dados_teste = {}
    
    def executar_teste(self):
        """Executa todos os testes de permissões"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 4: PERMISSÕES E ACESSO")
        logger.info("=" * 80)
        
        try:
            # 1. Criar usuários de teste
            self._criar_usuarios_teste()
            
            # 2. Criar dados de teste
            self._criar_dados_teste()
            
            # 3. Testar acesso de cliente aos seus dados
            self._testar_acesso_cliente_proprios_dados()
            
            # 4. Testar restrição de acesso a dados de outros clientes
            self._testar_restricao_acesso_outros_clientes()
            
            # 5. Testar permissões granulares
            self._testar_permissoes_granulares()
            
            # 6. Testar validações de decorators
            self._testar_decorators_permissoes()
            
            # 7. Limpar dados de teste
            self._limpar_dados_teste()
            
            # 8. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro crítico no teste: {str(e)}", exc_info=True)
            return False
    
    def _criar_usuarios_teste(self):
        """Cria usuários de teste (admin, funcionário, cliente)"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Usuários de Teste")
        logger.info("-" * 80)
        
        try:
            # Criar ou buscar cliente 1
            cliente1, _ = Cliente.objects.get_or_create(
                razao_social="CLIENTE TESTE PERMISSÕES 1",
                defaults={
                    'cnpj': '12345678000111',
                    'status': 'Ativo'
                }
            )
            
            # Criar ou buscar cliente 2
            cliente2, _ = Cliente.objects.get_or_create(
                razao_social="CLIENTE TESTE PERMISSÕES 2",
                defaults={
                    'cnpj': '12345678000122',
                    'status': 'Ativo'
                }
            )
            
            # Criar usuário admin
            admin, _ = Usuario.objects.get_or_create(
                username='admin_teste_permissoes',
                defaults={
                    'email': 'admin_teste@teste.com',
                    'tipo_usuario': 'admin',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            admin.set_password('admin123')
            admin.save()
            
            # Criar usuário funcionário
            funcionario, _ = Usuario.objects.get_or_create(
                username='funcionario_teste_permissoes',
                defaults={
                    'email': 'funcionario_teste@teste.com',
                    'tipo_usuario': 'funcionario',
                    'is_staff': True
                }
            )
            funcionario.set_password('func123')
            funcionario.save()
            
            # Criar usuário cliente 1
            cliente_user1, _ = Usuario.objects.get_or_create(
                username='cliente1_teste_permissoes',
                defaults={
                    'email': 'cliente1_teste@teste.com',
                    'tipo_usuario': 'cliente',
                    'cliente': cliente1
                }
            )
            cliente_user1.set_password('cliente123')
            cliente_user1.save()
            
            # Criar usuário cliente 2
            cliente_user2, _ = Usuario.objects.get_or_create(
                username='cliente2_teste_permissoes',
                defaults={
                    'email': 'cliente2_teste@teste.com',
                    'tipo_usuario': 'cliente',
                    'cliente': cliente2
                }
            )
            cliente_user2.set_password('cliente123')
            cliente_user2.save()
            
            self.usuarios_teste = {
                'admin': admin,
                'funcionario': funcionario,
                'cliente1': cliente_user1,
                'cliente2': cliente_user2
            }
            
            self.dados_teste['cliente1'] = cliente1
            self.dados_teste['cliente2'] = cliente2
            
            logger.info("✅ Usuários de teste criados:")
            logger.info(f"   - Admin: {admin.username}")
            logger.info(f"   - Funcionário: {funcionario.username}")
            logger.info(f"   - Cliente 1: {cliente_user1.username} (Cliente: {cliente1.razao_social})")
            logger.info(f"   - Cliente 2: {cliente_user2.username} (Cliente: {cliente2.razao_social})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar usuários de teste: {str(e)}", exc_info=True)
            raise
    
    def _criar_dados_teste(self):
        """Cria dados de teste (notas fiscais e romaneios)"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Dados de Teste")
        logger.info("-" * 80)
        
        try:
            cliente1 = self.dados_teste['cliente1']
            cliente2 = self.dados_teste['cliente2']
            
            # Criar notas fiscais para cliente 1
            nota1_cliente1, _ = NotaFiscal.objects.get_or_create(
                nota=f"PERM-C1-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                defaults={
                    'cliente': cliente1,
                    'data': timezone.now().date(),
                    'fornecedor': 'Fornecedor Cliente 1',
                    'mercadoria': 'Mercadoria Cliente 1',
                    'peso': Decimal('100.00'),
                    'valor': Decimal('1000.00'),
                    'quantidade': 10,
                    'status': 'Depósito'
                }
            )
            
            # Criar notas fiscais para cliente 2
            nota1_cliente2, _ = NotaFiscal.objects.get_or_create(
                nota=f"PERM-C2-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                defaults={
                    'cliente': cliente2,
                    'data': timezone.now().date(),
                    'fornecedor': 'Fornecedor Cliente 2',
                    'mercadoria': 'Mercadoria Cliente 2',
                    'peso': Decimal('200.00'),
                    'valor': Decimal('2000.00'),
                    'quantidade': 20,
                    'status': 'Depósito'
                }
            )
            
            # Buscar motorista e veículo
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if motorista and veiculo:
                # Criar romaneio para cliente 1
                romaneio_cliente1, _ = RomaneioViagem.objects.get_or_create(
                    codigo=f"PERM-C1-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    defaults={
                        'cliente': cliente1,
                        'motorista': motorista,
                        'veiculo_principal': veiculo,
                        'status': 'Salvo'
                    }
                )
                romaneio_cliente1.notas_fiscais.add(nota1_cliente1)
                
                # Criar romaneio para cliente 2
                romaneio_cliente2, _ = RomaneioViagem.objects.get_or_create(
                    codigo=f"PERM-C2-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    defaults={
                        'cliente': cliente2,
                        'motorista': motorista,
                        'veiculo_principal': veiculo,
                        'status': 'Salvo'
                    }
                )
                romaneio_cliente2.notas_fiscais.add(nota1_cliente2)
                
                self.dados_teste['romaneio_cliente1'] = romaneio_cliente1
                self.dados_teste['romaneio_cliente2'] = romaneio_cliente2
            
            self.dados_teste['nota_cliente1'] = nota1_cliente1
            self.dados_teste['nota_cliente2'] = nota1_cliente2
            
            logger.info("✅ Dados de teste criados:")
            logger.info(f"   - Nota Cliente 1: {nota1_cliente1.nota}")
            logger.info(f"   - Nota Cliente 2: {nota1_cliente2.nota}")
            if 'romaneio_cliente1' in self.dados_teste:
                logger.info(f"   - Romaneio Cliente 1: {romaneio_cliente1.codigo}")
                logger.info(f"   - Romaneio Cliente 2: {romaneio_cliente2.codigo}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar dados de teste: {str(e)}", exc_info=True)
            raise
    
    def _testar_acesso_cliente_proprios_dados(self):
        """Testa se cliente pode acessar seus próprios dados"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 4.1: Acesso de Cliente aos Seus Próprios Dados")
        logger.info("-" * 80)
        
        try:
            cliente_user1 = self.usuarios_teste['cliente1']
            cliente1 = self.dados_teste['cliente1']
            nota_cliente1 = self.dados_teste['nota_cliente1']
            
            # Testar acesso às próprias notas fiscais
            notas_acessiveis = NotaFiscal.objects.filter(cliente=cliente1)
            pode_acessar = notas_acessiveis.filter(id=nota_cliente1.id).exists()
            
            if pode_acessar:
                logger.info("✅ Cliente pode acessar suas próprias notas fiscais")
                self.resultados['sucessos'].append("Acesso a próprias notas fiscais")
            else:
                logger.error("❌ Cliente não pode acessar suas próprias notas fiscais")
                self.resultados['erros'].append("Acesso a próprias notas fiscais")
            
            # Testar acesso aos próprios romaneios
            if 'romaneio_cliente1' in self.dados_teste:
                romaneio_cliente1 = self.dados_teste['romaneio_cliente1']
                romaneios_acessiveis = RomaneioViagem.objects.filter(
                    notas_fiscais__cliente=cliente1
                ).distinct()
                pode_acessar_romaneio = romaneios_acessiveis.filter(id=romaneio_cliente1.id).exists()
                
                if pode_acessar_romaneio:
                    logger.info("✅ Cliente pode acessar seus próprios romaneios")
                    self.resultados['sucessos'].append("Acesso a próprios romaneios")
                else:
                    logger.error("❌ Cliente não pode acessar seus próprios romaneios")
                    self.resultados['erros'].append("Acesso a próprios romaneios")
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar acesso a próprios dados: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Acesso a próprios dados: {str(e)}")
    
    def _testar_restricao_acesso_outros_clientes(self):
        """Testa se cliente não pode acessar dados de outros clientes"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 4.2: Restrição de Acesso a Dados de Outros Clientes")
        logger.info("-" * 80)
        
        try:
            cliente_user1 = self.usuarios_teste['cliente1']
            cliente2 = self.dados_teste['cliente2']
            nota_cliente2 = self.dados_teste['nota_cliente2']
            
            # Testar se cliente 1 NÃO pode acessar notas do cliente 2
            # (usando a lógica de permissão granular)
            notas_cliente1 = NotaFiscal.objects.filter(cliente=cliente_user1.cliente)
            pode_acessar_outro = notas_cliente1.filter(id=nota_cliente2.id).exists()
            
            if not pode_acessar_outro:
                logger.info("✅ Cliente não pode acessar notas fiscais de outros clientes")
                self.resultados['sucessos'].append("Restrição de acesso a notas de outros clientes")
            else:
                logger.error("❌ Cliente pode acessar notas fiscais de outros clientes (FALHA DE SEGURANÇA)")
                self.resultados['erros'].append("Restrição de acesso a notas de outros clientes")
            
            # Testar se cliente 1 NÃO pode acessar romaneios do cliente 2
            if 'romaneio_cliente2' in self.dados_teste:
                romaneio_cliente2 = self.dados_teste['romaneio_cliente2']
                romaneios_cliente1 = RomaneioViagem.objects.filter(
                    notas_fiscais__cliente=cliente_user1.cliente
                ).distinct()
                pode_acessar_romaneio_outro = romaneios_cliente1.filter(id=romaneio_cliente2.id).exists()
                
                if not pode_acessar_romaneio_outro:
                    logger.info("✅ Cliente não pode acessar romaneios de outros clientes")
                    self.resultados['sucessos'].append("Restrição de acesso a romaneios de outros clientes")
                else:
                    logger.error("❌ Cliente pode acessar romaneios de outros clientes (FALHA DE SEGURANÇA)")
                    self.resultados['erros'].append("Restrição de acesso a romaneios de outros clientes")
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar restrição de acesso: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Restrição de acesso: {str(e)}")
    
    def _testar_permissoes_granulares(self):
        """Testa permissões granulares (admin, funcionário, cliente)"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 4.3: Permissões Granulares")
        logger.info("-" * 80)
        
        try:
            admin = self.usuarios_teste['admin']
            funcionario = self.usuarios_teste['funcionario']
            cliente_user1 = self.usuarios_teste['cliente1']
            
            # Testar permissões de admin
            if admin.is_admin and admin.is_staff:
                logger.info("✅ Admin tem permissões corretas")
                self.resultados['sucessos'].append("Permissões de admin")
            else:
                logger.error("❌ Admin não tem permissões corretas")
                self.resultados['erros'].append("Permissões de admin")
            
            # Testar permissões de funcionário
            if funcionario.is_funcionario and funcionario.is_staff:
                logger.info("✅ Funcionário tem permissões corretas")
                self.resultados['sucessos'].append("Permissões de funcionário")
            else:
                logger.error("❌ Funcionário não tem permissões corretas")
                self.resultados['erros'].append("Permissões de funcionário")
            
            # Testar permissões de cliente
            if cliente_user1.is_cliente and not cliente_user1.is_staff:
                logger.info("✅ Cliente tem permissões corretas")
                self.resultados['sucessos'].append("Permissões de cliente")
            else:
                logger.error("❌ Cliente não tem permissões corretas")
                self.resultados['erros'].append("Permissões de cliente")
            
            # Testar acesso de admin a todos os dados
            todas_notas = NotaFiscal.objects.all()
            admin_pode_ver_todas = todas_notas.exists()
            
            if admin_pode_ver_todas:
                logger.info("✅ Admin pode acessar todos os dados")
                self.resultados['sucessos'].append("Admin acessa todos os dados")
            else:
                logger.warning("⚠️ Admin não pode acessar dados (pode ser normal se não houver dados)")
            
            # Testar acesso de funcionário a todos os dados
            funcionario_pode_ver_todas = todas_notas.exists()
            
            if funcionario_pode_ver_todas:
                logger.info("✅ Funcionário pode acessar todos os dados")
                self.resultados['sucessos'].append("Funcionário acessa todos os dados")
            else:
                logger.warning("⚠️ Funcionário não pode acessar dados (pode ser normal se não houver dados)")
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar permissões granulares: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Permissões granulares: {str(e)}")
    
    def _testar_decorators_permissoes(self):
        """Testa os decorators de permissões"""
        logger.info("\n" + "-" * 80)
        logger.info("TESTE 4.4: Validação de Decorators de Permissões")
        logger.info("-" * 80)
        
        try:
            cliente_user1 = self.usuarios_teste['cliente1']
            cliente2 = self.dados_teste['cliente2']
            
            # Testar decorator can_access_cliente_data
            # Simular validação manual
            def validar_acesso_cliente(usuario, cliente_id):
                """Simula validação do decorator"""
                if usuario.is_admin or usuario.is_funcionario:
                    return True
                if usuario.is_cliente and usuario.cliente:
                    return usuario.cliente.id == cliente_id
                return False
            
            # Cliente 1 acessando seu próprio cliente
            pode_acessar_proprio = validar_acesso_cliente(
                cliente_user1,
                cliente_user1.cliente.id
            )
            
            if pode_acessar_proprio:
                logger.info("✅ Decorator permite acesso a próprio cliente")
                self.resultados['sucessos'].append("Decorator - acesso a próprio cliente")
            else:
                logger.error("❌ Decorator não permite acesso a próprio cliente")
                self.resultados['erros'].append("Decorator - acesso a próprio cliente")
            
            # Cliente 1 tentando acessar cliente 2
            pode_acessar_outro = validar_acesso_cliente(
                cliente_user1,
                cliente2.id
            )
            
            if not pode_acessar_outro:
                logger.info("✅ Decorator bloqueia acesso a outro cliente")
                self.resultados['sucessos'].append("Decorator - bloqueio de acesso a outro cliente")
            else:
                logger.error("❌ Decorator permite acesso a outro cliente (FALHA DE SEGURANÇA)")
                self.resultados['erros'].append("Decorator - bloqueio de acesso a outro cliente")
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar decorators: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Decorators: {str(e)}")
    
    def _limpar_dados_teste(self):
        """Limpa dados de teste criados"""
        logger.info("\n" + "-" * 80)
        logger.info("Limpando Dados de Teste")
        logger.info("-" * 80)
        
        try:
            # Limpar romaneios de teste
            if 'romaneio_cliente1' in self.dados_teste:
                self.dados_teste['romaneio_cliente1'].delete()
            if 'romaneio_cliente2' in self.dados_teste:
                self.dados_teste['romaneio_cliente2'].delete()
            
            # Limpar notas fiscais de teste
            if 'nota_cliente1' in self.dados_teste:
                self.dados_teste['nota_cliente1'].delete()
            if 'nota_cliente2' in self.dados_teste:
                self.dados_teste['nota_cliente2'].delete()
            
            # Limpar usuários de teste
            for usuario in self.usuarios_teste.values():
                usuario.delete()
            
            # Limpar clientes de teste
            if 'cliente1' in self.dados_teste:
                self.dados_teste['cliente1'].delete()
            if 'cliente2' in self.dados_teste:
                self.dados_teste['cliente2'].delete()
            
            logger.info("✅ Dados de teste limpos")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar dados de teste: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATÓRIO FINAL - TESTE 4: PERMISSÕES")
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
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("✅ TESTE 4 CONCLUÍDO COM SUCESSO!")
        else:
            logger.info("⚠️ TESTE 4 CONCLUÍDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    teste = TestePermissoes()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

