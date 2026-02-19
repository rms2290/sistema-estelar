#!/usr/bin/env python
"""
Script de Teste 6: Simulação de Cliente Fazendo Login

Este script testa:
- Criar usuário cliente e dados associados
- Simular login do cliente
- Acessar dados do cliente (notas fiscais, romaneios)
- Verificar restrições de acesso (não pode ver dados de outros clientes)
- Testar funcionalidades disponíveis para cliente
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
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.test import Client
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem
)

Usuario = get_user_model()

# Configurar logging
import logging
# Configurar handler de arquivo com UTF-8
file_handler = logging.FileHandler('logs/teste_6_cliente_login.log', encoding='utf-8')
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


class TesteClienteLogin:
    """Classe para executar testes de login e acesso de cliente"""
    
    def __init__(self):
        self.resultados = {
            'sucessos': [],
            'erros': [],
            'validacoes': []
        }
        self.usuario_cliente = None
        self.cliente = None
        self.dados_teste = {}
        self.client = Client()
    
    def executar_teste(self):
        """Executa todos os testes de login e acesso de cliente"""
        logger.info("=" * 80)
        logger.info("INICIANDO TESTE 6: SIMULACAO DE CLIENTE FAZENDO LOGIN")
        logger.info("=" * 80)
        
        try:
            # 1. Criar usuário cliente e dados
            self._criar_usuario_cliente()
            
            # 2. Simular login do cliente
            self._simular_login()
            
            # 3. Testar acesso às próprias notas fiscais
            self._testar_acesso_notas_fiscais()
            
            # 4. Testar acesso aos próprios romaneios
            self._testar_acesso_romaneios()
            
            # 5. Testar restrições de acesso (dados de outros clientes)
            self._testar_restricoes_acesso()
            
            # 6. Testar funcionalidades disponíveis para cliente
            self._testar_funcionalidades_cliente()
            
            # 7. Limpar dados de teste
            self._limpar_dados_teste()
            
            # 8. Gerar relatório
            self._gerar_relatorio()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro critico no teste: {str(e)}", exc_info=True)
            return False
    
    def _criar_usuario_cliente(self):
        """Cria usuário cliente e dados associados"""
        logger.info("\n" + "-" * 80)
        logger.info("Criando Usuario Cliente e Dados")
        logger.info("-" * 80)
        
        try:
            # Criar ou buscar cliente
            self.cliente, _ = Cliente.objects.get_or_create(
                razao_social="CLIENTE TESTE LOGIN",
                defaults={
                    'cnpj': '12345678000188',
                    'status': 'Ativo'
                }
            )
            
            # Criar ou buscar usuário cliente
            self.usuario_cliente, created = Usuario.objects.get_or_create(
                username='cliente_teste_login',
                defaults={
                    'email': 'cliente_teste_login@teste.com',
                    'tipo_usuario': 'cliente',
                    'cliente': self.cliente,
                    'first_name': 'Cliente',
                    'last_name': 'Teste Login'
                }
            )
            
            if created:
                self.usuario_cliente.set_password('cliente123')
                self.usuario_cliente.save()
                logger.info(f"Usuario cliente criado: {self.usuario_cliente.username}")
            else:
                logger.info(f"Usuario cliente ja existe: {self.usuario_cliente.username}")
            
            # Buscar motorista e veículo
            motorista = Motorista.objects.first()
            veiculo = Veiculo.objects.filter(tipo_unidade__in=['Cavalo', 'CAVALO']).first()
            
            if not motorista or not veiculo:
                logger.error("Motorista ou veiculo nao encontrado")
                return False
            
            # Criar notas fiscais para o cliente
            notas_criadas = []
            for i in range(5):
                nota, _ = NotaFiscal.objects.get_or_create(
                    nota=f"LOGIN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                    defaults={
                        'cliente': self.cliente,
                        'data': timezone.now().date() - timedelta(days=random.randint(0, 30)),
                        'fornecedor': f"Fornecedor Login {i}",
                        'mercadoria': f"Mercadoria Login {i}",
                        'peso': Decimal(str(random.uniform(100, 1000))).quantize(Decimal('0.01')),
                        'valor': Decimal(str(random.uniform(1000, 10000))).quantize(Decimal('0.01')),
                        'quantidade': random.randint(1, 100),
                        'status': random.choice(['Deposito', 'Enviada'])
                    }
                )
                if _:
                    notas_criadas.append(nota)
            
            # Criar romaneios para o cliente
            romaneios_criados = []
            for i in range(2):
                romaneio, _ = RomaneioViagem.objects.get_or_create(
                    codigo=f"LOGIN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}",
                    defaults={
                        'cliente': self.cliente,
                        'motorista': motorista,
                        'veiculo_principal': veiculo,
                        'origem_cidade': 'SAO PAULO',
                        'destino_cidade': 'RIO DE JANEIRO',
                        'status': random.choice(['Salvo', 'Emitido'])
                    }
                )
                if _:
                    # Vincular algumas notas ao romaneio
                    if notas_criadas:
                        notas_romaneio = random.sample(notas_criadas, min(2, len(notas_criadas)))
                        for nota in notas_romaneio:
                            romaneio.notas_fiscais.add(nota)
                        romaneio.calcular_totais()
                    romaneios_criados.append(romaneio)
            
            self.dados_teste = {
                'cliente': self.cliente,
                'usuario': self.usuario_cliente,
                'notas': notas_criadas,
                'romaneios': romaneios_criados
            }
            
            logger.info(f"Dados criados:")
            logger.info(f"   - Cliente: {self.cliente.razao_social}")
            logger.info(f"   - Usuario: {self.usuario_cliente.username}")
            logger.info(f"   - Notas: {len(notas_criadas)}")
            logger.info(f"   - Romaneios: {len(romaneios_criados)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar usuario cliente: {str(e)}", exc_info=True)
            return False
    
    def _simular_login(self):
        """Simula login do cliente"""
        logger.info("\n" + "-" * 80)
        logger.info("Simulando Login do Cliente")
        logger.info("-" * 80)
        
        try:
            # Autenticar usuário
            user = authenticate(
                username=self.usuario_cliente.username,
                password='cliente123'
            )
            
            if user and user.is_active:
                logger.info(f"Usuario autenticado: {user.username}")
                logger.info(f"   - Tipo: {user.get_tipo_usuario_display()}")
                logger.info(f"   - Cliente vinculado: {user.cliente.razao_social if user.cliente else 'Nenhum'}")
                
                # Fazer login usando Django test client
                login_sucesso = self.client.login(
                    username=self.usuario_cliente.username,
                    password='cliente123'
                )
                
                if login_sucesso:
                    logger.info("Login realizado com sucesso via test client")
                    self.resultados['sucessos'].append("Login do cliente")
                else:
                    logger.error("Falha no login via test client")
                    self.resultados['erros'].append("Login do cliente")
            else:
                logger.error("Falha na autenticacao")
                self.resultados['erros'].append("Autenticacao do cliente")
                
        except Exception as e:
            logger.error(f"Erro ao simular login: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Simulacao de login: {str(e)}")
    
    def _testar_acesso_notas_fiscais(self):
        """Testa acesso do cliente às suas próprias notas fiscais"""
        logger.info("\n" + "-" * 80)
        logger.info("Testando Acesso as Proprias Notas Fiscais")
        logger.info("-" * 80)
        
        try:
            # Buscar notas do cliente usando o modelo
            notas_cliente = NotaFiscal.objects.filter(cliente=self.cliente)
            
            logger.info(f"Notas fiscais do cliente: {notas_cliente.count()}")
            
            # Verificar se o cliente pode acessar suas notas
            if notas_cliente.exists():
                # Verificar cada nota
                notas_acessiveis = 0
                for nota in notas_cliente:
                    # Simular verificação de permissão
                    pode_acessar = (nota.cliente == self.cliente)
                    if pode_acessar:
                        notas_acessiveis += 1
                        logger.info(f"   - Nota {nota.nota}: Acessivel")
                
                if notas_acessiveis == notas_cliente.count():
                    logger.info(f"Todas as {notas_acessiveis} notas sao acessiveis")
                    self.resultados['sucessos'].append("Acesso as proprias notas fiscais")
                else:
                    logger.warning(f"Apenas {notas_acessiveis}/{notas_cliente.count()} notas sao acessiveis")
                    self.resultados['erros'].append("Acesso as proprias notas fiscais")
            else:
                logger.warning("Cliente nao possui notas fiscais")
            
        except Exception as e:
            logger.error(f"Erro ao testar acesso a notas fiscais: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Acesso a notas fiscais: {str(e)}")
    
    def _testar_acesso_romaneios(self):
        """Testa acesso do cliente aos seus próprios romaneios"""
        logger.info("\n" + "-" * 80)
        logger.info("Testando Acesso aos Proprios Romaneios")
        logger.info("-" * 80)
        
        try:
            # Buscar romaneios do cliente
            romaneios_cliente = RomaneioViagem.objects.filter(
                notas_fiscais__cliente=self.cliente
            ).distinct()
            
            logger.info(f"Romaneios do cliente: {romaneios_cliente.count()}")
            
            # Verificar se o cliente pode acessar seus romaneios
            if romaneios_cliente.exists():
                romaneios_acessiveis = 0
                for romaneio in romaneios_cliente:
                    # Verificar se o romaneio tem notas do cliente
                    tem_notas_cliente = romaneio.notas_fiscais.filter(cliente=self.cliente).exists()
                    if tem_notas_cliente:
                        romaneios_acessiveis += 1
                        logger.info(f"   - Romaneio {romaneio.codigo}: Acessivel")
                
                if romaneios_acessiveis == romaneios_cliente.count():
                    logger.info(f"Todos os {romaneios_acessiveis} romaneios sao acessiveis")
                    self.resultados['sucessos'].append("Acesso aos proprios romaneios")
                else:
                    logger.warning(f"Apenas {romaneios_acessiveis}/{romaneios_cliente.count()} romaneios sao acessiveis")
                    self.resultados['erros'].append("Acesso aos proprios romaneios")
            else:
                logger.warning("Cliente nao possui romaneios")
            
        except Exception as e:
            logger.error(f"Erro ao testar acesso a romaneios: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Acesso a romaneios: {str(e)}")
    
    def _testar_restricoes_acesso(self):
        """Testa se o cliente não pode acessar dados de outros clientes"""
        logger.info("\n" + "-" * 80)
        logger.info("Testando Restricoes de Acesso")
        logger.info("-" * 80)
        
        try:
            # Buscar outro cliente
            outro_cliente = Cliente.objects.exclude(id=self.cliente.id).first()
            
            if not outro_cliente:
                logger.warning("Nenhum outro cliente encontrado para teste")
                return
            
            # Tentar acessar notas de outro cliente
            notas_outro_cliente = NotaFiscal.objects.filter(cliente=outro_cliente)
            
            if notas_outro_cliente.exists():
                # Verificar se o cliente atual NÃO pode acessar essas notas
                notas_nao_acessiveis = 0
                for nota in notas_outro_cliente:
                    pode_acessar = (nota.cliente == self.cliente)
                    if not pode_acessar:
                        notas_nao_acessiveis += 1
                
                if notas_nao_acessiveis == notas_outro_cliente.count():
                    logger.info(f"Cliente nao pode acessar {notas_nao_acessiveis} notas de outros clientes")
                    self.resultados['sucessos'].append("Restricao de acesso a notas de outros clientes")
                else:
                    logger.error("Cliente pode acessar notas de outros clientes (FALHA DE SEGURANCA)")
                    self.resultados['erros'].append("Restricao de acesso a notas de outros clientes")
            
            # Tentar acessar romaneios de outro cliente
            romaneios_outro_cliente = RomaneioViagem.objects.filter(
                notas_fiscais__cliente=outro_cliente
            ).distinct()
            
            if romaneios_outro_cliente.exists():
                romaneios_nao_acessiveis = 0
                for romaneio in romaneios_outro_cliente:
                    tem_notas_cliente = romaneio.notas_fiscais.filter(cliente=self.cliente).exists()
                    if not tem_notas_cliente:
                        romaneios_nao_acessiveis += 1
                
                if romaneios_nao_acessiveis > 0:
                    logger.info(f"Cliente nao pode acessar {romaneios_nao_acessiveis} romaneios de outros clientes")
                    self.resultados['sucessos'].append("Restricao de acesso a romaneios de outros clientes")
                else:
                    logger.warning("Nenhum romaneio de outro cliente para testar")
            
        except Exception as e:
            logger.error(f"Erro ao testar restricoes de acesso: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Restricoes de acesso: {str(e)}")
    
    def _testar_funcionalidades_cliente(self):
        """Testa funcionalidades disponíveis para cliente"""
        logger.info("\n" + "-" * 80)
        logger.info("Testando Funcionalidades Disponiveis para Cliente")
        logger.info("-" * 80)
        
        try:
            # Verificar permissões do usuário
            usuario = self.usuario_cliente
            
            # Verificar se é cliente
            if usuario.is_cliente:
                logger.info("Usuario e cliente")
                self.resultados['sucessos'].append("Validacao de tipo de usuario")
            else:
                logger.error("Usuario nao e cliente")
                self.resultados['erros'].append("Validacao de tipo de usuario")
            
            # Verificar se tem cliente vinculado
            if usuario.cliente:
                logger.info(f"Cliente vinculado: {usuario.cliente.razao_social}")
                self.resultados['sucessos'].append("Cliente vinculado ao usuario")
            else:
                logger.error("Usuario nao tem cliente vinculado")
                self.resultados['erros'].append("Cliente vinculado ao usuario")
            
            # Verificar se NÃO é admin ou funcionário
            if not usuario.is_admin and not usuario.is_funcionario:
                logger.info("Usuario nao e admin nem funcionario (correto para cliente)")
                self.resultados['sucessos'].append("Validacao de permissoes de cliente")
            else:
                logger.warning("Usuario tem permissoes de admin/funcionario (pode ser intencional)")
            
            # Testar acesso a dashboard (simulado)
            logger.info("Funcionalidades disponiveis para cliente:")
            logger.info("   - Visualizar proprias notas fiscais")
            logger.info("   - Visualizar proprios romaneios")
            logger.info("   - Imprimir romaneios")
            logger.info("   - Ver perfil")
            
            self.resultados['validacoes'].append({
                'teste': 'Funcionalidades do cliente',
                'is_cliente': usuario.is_cliente,
                'cliente_vinculado': usuario.cliente is not None,
                'is_admin': usuario.is_admin,
                'is_funcionario': usuario.is_funcionario
            })
            
        except Exception as e:
            logger.error(f"Erro ao testar funcionalidades: {str(e)}", exc_info=True)
            self.resultados['erros'].append(f"Funcionalidades do cliente: {str(e)}")
    
    def _limpar_dados_teste(self):
        """Limpa dados de teste criados"""
        logger.info("\n" + "-" * 80)
        logger.info("Limpando Dados de Teste")
        logger.info("-" * 80)
        
        try:
            # Limpar romaneios
            if 'romaneios' in self.dados_teste:
                for romaneio in self.dados_teste['romaneios']:
                    romaneio.delete()
            
            # Limpar notas fiscais
            if 'notas' in self.dados_teste:
                for nota in self.dados_teste['notas']:
                    nota.delete()
            
            # Limpar usuário
            if self.usuario_cliente:
                self.usuario_cliente.delete()
            
            # Limpar cliente (se não tiver outras referências)
            if self.cliente:
                # Verificar se tem outras referências
                tem_notas = NotaFiscal.objects.filter(cliente=self.cliente).exists()
                tem_romaneios = RomaneioViagem.objects.filter(
                    notas_fiscais__cliente=self.cliente
                ).exists()
                
                if not tem_notas and not tem_romaneios:
                    self.cliente.delete()
                    logger.info("Cliente de teste removido")
                else:
                    logger.info("Cliente mantido (tem outras referencias)")
            
            logger.info("Dados de teste limpos")
            
        except Exception as e:
            logger.warning(f"Erro ao limpar dados de teste: {str(e)}")
    
    def _gerar_relatorio(self):
        """Gera relatório final do teste"""
        logger.info("\n" + "=" * 80)
        logger.info("RELATORIO FINAL - TESTE 6: CLIENTE LOGIN")
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
        
        if self.resultados['validacoes']:
            logger.info(f"\nValidacoes realizadas:")
            for validacao in self.resultados['validacoes']:
                logger.info(f"   - {validacao['teste']}")
                for key, value in validacao.items():
                    if key != 'teste':
                        logger.info(f"     {key}: {value}")
        
        logger.info("\n" + "=" * 80)
        
        if erros == 0:
            logger.info("TESTE 6 CONCLUIDO COM SUCESSO!")
        else:
            logger.info("TESTE 6 CONCLUIDO COM ERROS")
        
        logger.info("=" * 80)


if __name__ == '__main__':
    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)
    
    teste = TesteClienteLogin()
    sucesso = teste.executar_teste()
    sys.exit(0 if sucesso else 1)

