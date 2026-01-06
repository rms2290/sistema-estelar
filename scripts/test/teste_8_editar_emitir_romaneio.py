"""
Teste 8: Editar Romaneio e Emitir
Objetivo: Testar o fluxo completo de edição e emissão de romaneio
"""
import os
import sys
import django
from pathlib import Path

# Configurar encoding para evitar erros Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

import logging
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from notas.models import Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem
from notas.services import RomaneioService
from notas.forms import RomaneioViagemForm

# Configurar logging
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'teste_8_editar_emitir_romaneio.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

User = get_user_model()

def criar_dados_teste():
    """Cria dados necessários para o teste"""
    logger.info("=== Criando dados de teste ===")
    
    # Criar ou obter usuário admin
    usuario, _ = User.objects.get_or_create(
        username='admin_teste',
        defaults={
            'email': 'admin@teste.com',
            'tipo_usuario': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    usuario.set_password('admin123')
    usuario.save()
    
    # Criar ou obter cliente
    cliente, _ = Cliente.objects.get_or_create(
        razao_social='CLIENTE TESTE EDICAO EMISSAO',
        defaults={
            'cnpj': '12345678000199',
            'status': 'Ativo'
        }
    )
    
    # Criar ou obter motorista
    motorista, _ = Motorista.objects.get_or_create(
        nome='MOTORISTA TESTE EDICAO',
        defaults={
            'cpf': '12345678901',
            'cnh': '12345678901',
            'tipo_composicao_motorista': 'Simples',
            'status': 'Ativo'
        }
    )
    
    # Criar ou obter veículo principal
    veiculo_principal, _ = Veiculo.objects.get_or_create(
        placa='TEST001',
        defaults={
            'tipo_unidade': 'Cavalo',
            'marca': 'VOLVO',
            'modelo': 'FH 540',
            'ano_fabricacao': 2020
        }
    )
    
    # Criar ou obter reboque
    reboque, _ = Veiculo.objects.get_or_create(
        placa='TEST002',
        defaults={
            'tipo_unidade': 'Reboque',
            'marca': 'RANDON',
            'modelo': 'SIDER',
            'ano_fabricacao': 2020
        }
    )
    
    # Criar notas fiscais
    notas = []
    for i in range(1, 4):
        nota, _ = NotaFiscal.objects.get_or_create(
            nota=f'TESTE-EDICAO-{i:03d}',
            cliente=cliente,
            defaults={
                'data': datetime.now().date(),
                'fornecedor': f'FORNECEDOR TESTE {i}',
                'mercadoria': f'MERCADORIA TESTE {i}',
                'quantidade': 10 + i,
                'peso': 100.0 + (i * 10),
                'valor': 1000.0 + (i * 100),
                'status': 'Depósito'
            }
        )
        notas.append(nota)
    
    logger.info(f"[OK] Dados criados: Cliente={cliente.razao_social}, Motorista={motorista.nome}, Veiculos={veiculo_principal.placa}/{reboque.placa}, Notas={len(notas)}")
    
    return usuario, cliente, motorista, veiculo_principal, reboque, notas

def criar_romaneio_salvo(cliente, motorista, veiculo_principal, reboque, notas):
    """Cria um romaneio com status 'Salvo'"""
    logger.info("=== Criando romaneio com status 'Salvo' ===")
    
    # Preparar dados do formulário
    form_data = {
        'cliente': cliente.pk,
        'motorista': motorista.pk,
        'veiculo_principal': veiculo_principal.pk,
        'reboque_1': reboque.pk,
        'reboque_2': None,
        'data_romaneio': datetime.now().date(),
        'origem_cidade': 'SAO PAULO',
        'origem_estado': 'SP',
        'destino_cidade': 'RIO DE JANEIRO',
        'destino_estado': 'RJ',
        'data_saida': datetime.now().date(),
        'data_chegada_prevista': (datetime.now() + timedelta(days=2)).date(),
        'notas_fiscais': [nota.pk for nota in notas[:2]],  # Apenas 2 notas inicialmente
        'status': 'Salvo'
    }
    
    # Criar formulário
    form = RomaneioViagemForm(data=form_data)
    
    if not form.is_valid():
        logger.error(f"Erro ao validar formulário: {form.errors}")
        return None
    
    # Criar romaneio usando serviço (sem emitir)
    romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
        form_data=form,
        emitir=False,  # Criar como 'Salvo'
        tipo='normal'
    )
    
    if not sucesso:
        logger.error(f"Erro ao criar romaneio: {mensagem}")
        return None
    
    logger.info(f"[OK] Romaneio criado: {romaneio.codigo}, Status: {romaneio.status}")
    logger.info(f"  - Notas vinculadas: {romaneio.notas_fiscais.count()}")
    logger.info(f"  - Peso total: {romaneio.peso_total}")
    logger.info(f"  - Valor total: {romaneio.valor_total}")
    
    return romaneio

def testar_edicao_romaneio(romaneio, cliente, notas):
    """Testa a edição de um romaneio"""
    logger.info("=== Testando edição de romaneio ===")
    
    # Preparar dados de edição
    form_data = {
        'cliente': cliente.pk,
        'motorista': romaneio.motorista.pk,
        'veiculo_principal': romaneio.veiculo_principal.pk,
        'reboque_1': romaneio.reboque_1.pk if romaneio.reboque_1 else None,
        'reboque_2': None,
        'data_romaneio': romaneio.data_emissao.date() if romaneio.data_emissao else datetime.now().date(),
        'origem_cidade': 'CAMPINAS',  # Mudança
        'origem_estado': 'SP',
        'destino_cidade': 'BELO HORIZONTE',  # Mudança
        'destino_estado': 'MG',  # Mudança
        'data_saida': (datetime.now() + timedelta(days=1)).date(),  # Mudança
        'data_chegada_prevista': (datetime.now() + timedelta(days=3)).date(),  # Mudança
        'notas_fiscais': [nota.pk for nota in notas],  # Adicionar todas as notas (3)
        'status': romaneio.status
    }
    
    # Criar formulário com instância
    form = RomaneioViagemForm(data=form_data, instance=romaneio)
    
    if not form.is_valid():
        logger.error(f"Erro ao validar formulário de edição: {form.errors}")
        return False, romaneio
    
    # Editar romaneio (sem emitir ainda)
    romaneio_editado, sucesso, mensagem = RomaneioService.editar_romaneio(
        romaneio=romaneio,
        form_data=form,
        emitir=False,
        salvar=True
    )
    
    if not sucesso:
        logger.error(f"Erro ao editar romaneio: {mensagem}")
        return False, romaneio
    
    # Verificar mudanças
    romaneio.refresh_from_db()
    verificacoes = {
        'origem_cidade': romaneio.origem_cidade == 'CAMPINAS',
        'destino_cidade': romaneio.destino_cidade == 'BELO HORIZONTE',
        'destino_estado': romaneio.destino_estado == 'MG',
        'notas_count': romaneio.notas_fiscais.count() == 3,
        'totais_atualizados': romaneio.peso_total > 0 and romaneio.valor_total > 0
    }
    
    todas_verificacoes_ok = all(verificacoes.values())
    
    logger.info(f"[OK] Edicao realizada: {mensagem}")
    logger.info(f"  - Origem: {romaneio.origem_cidade}/{romaneio.origem_estado}")
    logger.info(f"  - Destino: {romaneio.destino_cidade}/{romaneio.destino_estado}")
    logger.info(f"  - Notas vinculadas: {romaneio.notas_fiscais.count()}")
    logger.info(f"  - Peso total: {romaneio.peso_total}")
    logger.info(f"  - Valor total: {romaneio.valor_total}")
    logger.info(f"  - Verificações: {verificacoes}")
    
    return todas_verificacoes_ok, romaneio

def testar_emissao_romaneio(romaneio, cliente):
    """Testa a emissão de um romaneio"""
    logger.info("=== Testando emissão de romaneio ===")
    
    status_antes = romaneio.status
    notas_status_antes = {nota.pk: nota.status for nota in romaneio.notas_fiscais.all()}
    
    # Preparar dados para emissão
    form_data = {
        'cliente': cliente.pk,
        'motorista': romaneio.motorista.pk,
        'veiculo_principal': romaneio.veiculo_principal.pk,
        'reboque_1': romaneio.reboque_1.pk if romaneio.reboque_1 else None,
        'reboque_2': None,
        'data_romaneio': romaneio.data_emissao.date() if romaneio.data_emissao else datetime.now().date(),
        'origem_cidade': romaneio.origem_cidade,
        'origem_estado': romaneio.origem_estado,
        'destino_cidade': romaneio.destino_cidade,
        'destino_estado': romaneio.destino_estado,
        'data_saida': romaneio.data_saida,
        'data_chegada_prevista': romaneio.data_chegada_prevista,
        'notas_fiscais': [nota.pk for nota in romaneio.notas_fiscais.all()],
        'status': romaneio.status
    }
    
    # Criar formulário com instância
    form = RomaneioViagemForm(data=form_data, instance=romaneio)
    
    if not form.is_valid():
        logger.error(f"Erro ao validar formulário para emissão: {form.errors}")
        return False
    
    # Emitir romaneio
    romaneio_emitido, sucesso, mensagem = RomaneioService.editar_romaneio(
        romaneio=romaneio,
        form_data=form,
        emitir=True,  # Emitir
        salvar=False
    )
    
    if not sucesso:
        logger.error(f"Erro ao emitir romaneio: {mensagem}")
        return False
    
    # Verificar mudanças
    romaneio.refresh_from_db()
    verificacoes = {
        'status_emitido': romaneio.status == 'Emitido',
        'data_emissao_preenchida': romaneio.data_emissao is not None,
        'notas_marcadas_enviadas': all(
            nota.status == 'Enviada' 
            for nota in romaneio.notas_fiscais.all()
        )
    }
    
    todas_verificacoes_ok = all(verificacoes.values())
    
    logger.info(f"[OK] Emissao realizada: {mensagem}")
    logger.info(f"  - Status antes: {status_antes} → Status depois: {romaneio.status}")
    logger.info(f"  - Data de emissão: {romaneio.data_emissao}")
    logger.info(f"  - Notas marcadas como 'Enviada': {verificacoes['notas_marcadas_enviadas']}")
    logger.info(f"  - Verificações: {verificacoes}")
    
    return todas_verificacoes_ok

def testar_impressao_romaneio(romaneio, usuario):
    """Testa a impressão/geração de PDF do romaneio emitido"""
    logger.info("=== Testando impressão de romaneio emitido ===")
    
    if romaneio.status != 'Emitido':
        logger.warning("Romaneio não está emitido, pulando teste de impressão")
        return False
    
    # Criar cliente de teste
    client = Client()
    
    # Fazer login
    login_sucesso = client.login(username=usuario.username, password='admin123')
    if not login_sucesso:
        logger.error("Erro ao fazer login")
        return False
    
    # Testar rota de impressão
    try:
        url = reverse('notas:imprimir_romaneio_novo', args=[romaneio.pk])
        response = client.get(url)
        
        verificacoes = {
            'status_200': response.status_code == 200,
            'content_type_html': 'text/html' in response.get('Content-Type', ''),
            'romaneio_no_context': hasattr(response, 'context_data') and 'romaneio' in (response.context_data if hasattr(response, 'context_data') else {})
        }
        
        todas_verificacoes_ok = all(verificacoes.values())
        
        logger.info(f"[OK] Teste de impressao realizado")
        logger.info(f"  - Status HTTP: {response.status_code}")
        logger.info(f"  - Content-Type: {response.get('Content-Type', 'N/A')}")
        logger.info(f"  - Verificações: {verificacoes}")
        
        return todas_verificacoes_ok
        
    except Exception as e:
        logger.error(f"Erro ao testar impressão: {str(e)}", exc_info=True)
        return False

def main():
    """Executa todos os testes"""
    try:
        print("Iniciando teste 8...")
        logger.info("=" * 80)
        logger.info("TESTE 8: EDITAR ROMANEIO E EMITIR")
        logger.info("=" * 80)
    except Exception as e:
        print(f"Erro ao inicializar logging: {e}")
        return False
    
    resultados = {
        'criar_dados': False,
        'criar_romaneio': False,
        'editar_romaneio': False,
        'emitir_romaneio': False,
        'impressao_romaneio': False
    }
    
    try:
        # 1. Criar dados de teste
        usuario, cliente, motorista, veiculo_principal, reboque, notas = criar_dados_teste()
        resultados['criar_dados'] = True
        
        # 2. Criar romaneio com status 'Salvo'
        romaneio = criar_romaneio_salvo(cliente, motorista, veiculo_principal, reboque, notas)
        if romaneio:
            resultados['criar_romaneio'] = True
            
            # 3. Editar romaneio
            sucesso_edicao, romaneio = testar_edicao_romaneio(romaneio, cliente, notas)
            resultados['editar_romaneio'] = sucesso_edicao
            
            # 4. Emitir romaneio
            if sucesso_edicao:
                resultados['emitir_romaneio'] = testar_emissao_romaneio(romaneio, cliente)
                
                # 5. Testar impressão
                if resultados['emitir_romaneio']:
                    resultados['impressao_romaneio'] = testar_impressao_romaneio(romaneio, usuario)
        else:
            logger.error("Falha ao criar romaneio, abortando testes")
        
    except Exception as e:
        logger.error(f"Erro durante execução dos testes: {str(e)}", exc_info=True)
    
    # Resumo
    logger.info("=" * 80)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 80)
    
    total_testes = len(resultados)
    testes_ok = sum(1 for v in resultados.values() if v)
    
    for teste, resultado in resultados.items():
        status = "[OK] PASSOU" if resultado else "[ERRO] FALHOU"
        logger.info(f"  {teste.upper()}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"TOTAL: {testes_ok}/{total_testes} testes passaram")
    logger.info("=" * 80)
    
    return testes_ok == total_testes

if __name__ == '__main__':
    try:
        print("Executando teste 8...")
        sucesso = main()
        print(f"Teste concluido. Sucesso: {sucesso}")
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"ERRO CRITICO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

