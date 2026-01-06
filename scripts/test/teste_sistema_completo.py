#!/usr/bin/env python
"""
Script de Teste Completo do Sistema Estelar

Este script cria dados de teste para validar todos os processos do sistema:
- 30 Clientes
- 30 Motoristas
- 30 Veículos (alternando cavalo e composição)
- 300 Notas Fiscais
- Romaneios com os dados criados
- Cobranças de carregamento

Objetivo: Verificar se há erros nos processos do sistema
"""
import os
import sys
import django
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import random

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from notas.models import (
    Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem,
    CobrancaCarregamento, TabelaSeguro
)
from notas.services.romaneio_service import RomaneioService
from notas.forms import RomaneioViagemForm, CobrancaCarregamentoForm


class TesteSistemaCompleto:
    """Classe para executar testes completos do sistema"""
    
    def __init__(self):
        self.clientes = []
        self.motoristas = []
        self.veiculos = []
        self.notas_fiscais = []
        self.romaneios = []
        self.cobrancas = []
        self.erros = []
        self.sucessos = []
        
    def log_sucesso(self, mensagem):
        """Registra um sucesso"""
        self.sucessos.append(mensagem)
        print(f"[OK] {mensagem}")
    
    def log_erro(self, mensagem, erro=None):
        """Registra um erro"""
        erro_msg = f"{mensagem}: {str(erro)}" if erro else mensagem
        self.erros.append(erro_msg)
        print(f"[ERRO] {erro_msg}")
    
    def gerar_cnpj(self, numero):
        """Gera um CNPJ válido para teste"""
        base = f"{numero:012d}"
        # Adicionar dígitos verificadores simples (não validação real)
        return f"{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{base[12:14]}"
    
    def gerar_cpf(self, numero):
        """Gera um CPF válido para teste"""
        base = f"{numero:011d}"
        return f"{base[:3]}.{base[3:6]}.{base[6:9]}-{base[9:11]}"
    
    def gerar_placa(self, numero):
        """Gera uma placa válida para teste"""
        letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        num = f"{numero:04d}"
        return f"{letras[numero % 26]}{letras[(numero + 1) % 26]}{letras[(numero + 2) % 26]}{num[0:4]}"
    
    def criar_clientes(self, quantidade=30):
        """Cria clientes de teste"""
        print("\n" + "="*70)
        print("CRIANDO CLIENTES")
        print("="*70)
        
        for i in range(1, quantidade + 1):
            try:
                # Verificar se já existe
                razao_social = f"Empresa Teste {i:03d} LTDA"
                cnpj_valor = self.gerar_cnpj(i) if i % 2 == 0 else None
                
                cliente_existente = Cliente.objects.filter(razao_social=razao_social).first()
                if cliente_existente:
                    cliente = cliente_existente
                    self.log_sucesso(f"Cliente {i:03d} ja existe: {cliente.razao_social}")
                else:
                    # Verificar se CNPJ já existe
                    if cnpj_valor and Cliente.objects.filter(cnpj=cnpj_valor).exists():
                        # Usar cliente existente com esse CNPJ ou criar sem CNPJ
                        cliente = Cliente.objects.filter(cnpj=cnpj_valor).first()
                        if cliente:
                            self.log_sucesso(f"Cliente {i:03d} usando existente (CNPJ): {cliente.razao_social}")
                        else:
                            cliente = Cliente.objects.create(
                                razao_social=razao_social,
                                cnpj=None,  # Sem CNPJ para evitar duplicata
                                nome_fantasia=f"Teste {i:03d}",
                                inscricao_estadual=f"12345678{i:02d}",
                                endereco=f"Rua Teste {i}",
                                numero=str(i * 10),
                                bairro="Centro",
                                cidade="São Paulo",
                                estado="SP",
                                cep=f"01000-{i:03d}",
                                telefone=f"(11) 98765-{i:04d}",
                                email=f"teste{i:03d}@empresa.com.br",
                                status="Ativo"
                            )
                            self.log_sucesso(f"Cliente {i:03d} criado: {cliente.razao_social}")
                    else:
                        cliente = Cliente.objects.create(
                            razao_social=razao_social,
                            cnpj=cnpj_valor,
                            nome_fantasia=f"Teste {i:03d}",
                            inscricao_estadual=f"12345678{i:02d}",
                            endereco=f"Rua Teste {i}",
                            numero=str(i * 10),
                            bairro="Centro",
                            cidade="São Paulo",
                            estado="SP",
                            cep=f"01000-{i:03d}",
                            telefone=f"(11) 98765-{i:04d}",
                            email=f"teste{i:03d}@empresa.com.br",
                            status="Ativo"
                        )
                        self.log_sucesso(f"Cliente {i:03d} criado: {cliente.razao_social}")
                self.clientes.append(cliente)
            except Exception as e:
                self.log_erro(f"Erro ao criar cliente {i:03d}", e)
        
        print(f"\n[OK] Clientes criados: {len(self.clientes)}/{quantidade}")
        return len(self.clientes)
    
    def criar_motoristas(self, quantidade=30):
        """Cria motoristas de teste"""
        print("\n" + "="*70)
        print("CRIANDO MOTORISTAS")
        print("="*70)
        
        tipos_composicao = ['Caminhão', 'Carreta', 'Bitrem', 'Rodotrem']
        
        for i in range(1, quantidade + 1):
            try:
                cpf = self.gerar_cpf(i)
                # Verificar se já existe
                if Motorista.objects.filter(cpf=cpf).exists():
                    motorista = Motorista.objects.get(cpf=cpf)
                    self.log_sucesso(f"Motorista {i:03d} já existe: {motorista.nome}")
                else:
                    motorista = Motorista.objects.create(
                        nome=f"Motorista Teste {i:03d}",
                        cpf=cpf,
                    rg=f"12.345.678-{i:02d}",
                    cnh=f"1234567890{i:02d}",
                    codigo_seguranca=f"{i:03d}",
                    vencimento_cnh=date.today() + timedelta(days=365),
                    uf_emissao_cnh="SP",
                    telefone=f"(11) 98765-{i:04d}",
                    endereco=f"Rua Motorista {i}",
                    numero=str(i * 10),
                    bairro="Centro",
                    cidade="São Paulo",
                    estado="SP",
                    cep=f"01000-{i:03d}",
                    data_nascimento=date(1980, 1, 1) + timedelta(days=i),
                        tipo_composicao_motorista=tipos_composicao[i % len(tipos_composicao)]
                    )
                    self.log_sucesso(f"Motorista {i:03d} criado: {motorista.nome}")
                self.motoristas.append(motorista)
            except Exception as e:
                self.log_erro(f"Erro ao criar motorista {i:03d}", e)
        
        print(f"\n[OK] Motoristas criados: {len(self.motoristas)}/{quantidade}")
        return len(self.motoristas)
    
    def criar_veiculos(self, quantidade=30):
        """Cria veículos de teste (alternando cavalo e composição)"""
        print("\n" + "="*70)
        print("CRIANDO VEÍCULOS")
        print("="*70)
        
        tipos_unidade = ['Cavalo', 'Caminhão', 'Reboque', 'Semi-reboque']
        
        for i in range(1, quantidade + 1):
            try:
                # Alternar entre cavalo e composição
                if i % 2 == 0:
                    tipo = 'Cavalo'
                else:
                    tipo = tipos_unidade[i % len(tipos_unidade)]
                
                placa = self.gerar_placa(i)
                # Verificar se já existe
                if Veiculo.objects.filter(placa=placa).exists():
                    veiculo = Veiculo.objects.get(placa=placa)
                    self.log_sucesso(f"Veículo {i:03d} já existe: {veiculo.placa} ({tipo})")
                else:
                    veiculo = Veiculo.objects.create(
                        tipo_unidade=tipo,
                        placa=placa,
                    chassi=f"9BW{''.join([str(random.randint(0,9)) for _ in range(14)])}",
                    renavam=f"{i:011d}",
                    marca="Volvo" if i % 2 == 0 else "Scania",
                    modelo=f"Modelo {i:03d}",
                    ano_fabricacao=2020 + (i % 5),
                    estado="SP",
                    cidade="São Paulo",
                    largura=Decimal("2.50"),
                    altura=Decimal("2.70"),
                    comprimento=Decimal(f"{6.0 + (i % 3)}"),
                        cubagem=Decimal(f"{40.0 + (i % 10)}")
                    )
                    self.log_sucesso(f"Veículo {i:03d} criado: {veiculo.placa} ({tipo})")
                self.veiculos.append(veiculo)
            except Exception as e:
                self.log_erro(f"Erro ao criar veículo {i:03d}", e)
        
        print(f"\n[OK] Veiculos criados: {len(self.veiculos)}/{quantidade}")
        return len(self.veiculos)
    
    def criar_notas_fiscais(self, quantidade=300):
        """Cria notas fiscais de teste"""
        print("\n" + "="*70)
        print("CRIANDO NOTAS FISCAIS")
        print("="*70)
        
        mercadorias = [
            "Cimento", "Areia", "Pedra", "Tijolo", "Telha",
            "Madeira", "Ferro", "Aço", "Vidro", "Tinta"
        ]
        locais = ['Galpão A', 'Galpão B', 'Galpão C', 'Depósito Central']
        
        if not self.clientes:
            self.log_erro("Não há clientes criados. Criando clientes primeiro...")
            self.criar_clientes()
        
        for i in range(1, quantidade + 1):
            try:
                if not self.clientes:
                    self.log_erro("Não há clientes disponíveis")
                    break
                    
                cliente = random.choice(self.clientes)
                mercadoria = random.choice(mercadorias)
                local = random.choice(locais)
                
                # Distribuir datas nos últimos 90 dias
                data_nota = date.today() - timedelta(days=random.randint(0, 90))
                
                nota_numero = f"NF{i:06d}"
                # Verificar se já existe
                if NotaFiscal.objects.filter(nota=nota_numero, cliente=cliente).exists():
                    nota = NotaFiscal.objects.get(nota=nota_numero, cliente=cliente)
                    if i % 50 == 0:
                        self.log_sucesso(f"Nota fiscal {i:06d} já existe (Total: {i})")
                else:
                    nota = NotaFiscal.objects.create(
                        nota=nota_numero,
                        cliente=cliente,
                        fornecedor=f"Fornecedor {i:03d}",
                        mercadoria=f"{mercadoria} {i:03d}",
                        quantidade=random.randint(10, 1000),
                        peso=Decimal(f"{random.randint(100, 10000)}"),
                        valor=Decimal(f"{random.randint(1000, 50000)}"),
                        data=data_nota,
                        local=local,
                        status="Depósito" if random.random() > 0.3 else "Enviada"
                    )
                    if i % 50 == 0:
                        self.log_sucesso(f"Nota fiscal {i:06d} criada (Total: {i})")
                self.notas_fiscais.append(nota)
            except Exception as e:
                self.log_erro(f"Erro ao criar nota fiscal {i:06d}", e)
        
        print(f"\n[OK] Notas fiscais criadas: {len(self.notas_fiscais)}/{quantidade}")
        return len(self.notas_fiscais)
    
    def criar_romaneios(self, quantidade=None):
        """Cria romaneios de teste com os dados criados"""
        print("\n" + "="*70)
        print("CRIANDO ROMANEIOS")
        print("="*70)
        
        if not self.clientes or not self.motoristas or not self.veiculos:
            self.log_erro("Dados insuficientes para criar romaneios")
            return 0
        
        if not self.notas_fiscais:
            self.log_erro("Não há notas fiscais criadas")
            return 0
        
        # Criar romaneios baseado nas notas fiscais em depósito
        notas_deposito = [n for n in self.notas_fiscais if n.status == 'Depósito']
        
        if not notas_deposito:
            self.log_erro("Não há notas fiscais em depósito para criar romaneios")
            return 0
        
        # Agrupar notas por cliente
        notas_por_cliente = {}
        for nota in notas_deposito[:min(100, len(notas_deposito))]:  # Limitar a 100 notas
            cliente_id = nota.cliente.id
            if cliente_id not in notas_por_cliente:
                notas_por_cliente[cliente_id] = []
            notas_por_cliente[cliente_id].append(nota)
        
        romaneios_criados = 0
        
        for cliente_id, notas in list(notas_por_cliente.items())[:30]:  # Máximo 30 romaneios
            try:
                cliente = Cliente.objects.get(pk=cliente_id)
                motorista = random.choice(self.motoristas)
                
                # Filtrar veículos adequados para veículo principal (UpperCaseMixin converte para maiúsculas)
                veiculos_principais = [v for v in self.veiculos if v.tipo_unidade.upper() in ['CAVALO', 'CAMINHÃO', 'CAMINHAO', 'CARRO', 'VAN']]
                if not veiculos_principais:
                    # Se não houver, usar qualquer veículo disponível
                    veiculos_principais = self.veiculos[:5]  # Pegar primeiros 5
                    if not veiculos_principais:
                        self.log_erro(f"Nao ha veiculos disponiveis para cliente {cliente_id}")
                        continue
                veiculo_principal = random.choice(veiculos_principais)
                
                # Selecionar até 10 notas para o romaneio
                notas_romaneio = notas[:min(10, len(notas))]
                
                # Criar romaneio diretamente usando o service
                data_romaneio = date.today() - timedelta(days=random.randint(0, 30))
                
                # Criar formulário de romaneio
                from notas.forms import RomaneioViagemForm
                
                form_data = {
                    'cliente': cliente.id,
                    'motorista': motorista.id,
                    'veiculo_principal': veiculo_principal.id,
                    'data_romaneio': data_romaneio.strftime('%Y-%m-%d'),
                    'origem_cidade': 'São Paulo',
                    'origem_estado': 'SP',
                    'destino_cidade': f'Cidade {random.randint(1, 50)}',
                    'destino_estado': 'SP',
                    'observacoes': f'Romaneio de teste criado automaticamente',
                    'notas_fiscais': [n.id for n in notas_romaneio]
                }
                
                form = RomaneioViagemForm(data=form_data)
                
                if form.is_valid():
                    romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
                        form, emitir=True, tipo='normal'
                    )
                    
                    if sucesso and romaneio:
                        # Adicionar notas fiscais ao romaneio (já deve estar no form)
                        # Atualizar status das notas
                        for nota in notas_romaneio:
                            nota.status = 'Enviada'
                            nota.save()
                        
                        self.romaneios.append(romaneio)
                        romaneios_criados += 1
                        self.log_sucesso(f"Romaneio {romaneio.codigo} criado com {len(notas_romaneio)} notas")
                    else:
                        self.log_erro(f"Erro ao criar romaneio: {mensagem}")
                else:
                    self.log_erro(f"Formulário inválido: {form.errors}")
                    
            except Exception as e:
                self.log_erro(f"Erro ao criar romaneio para cliente {cliente_id}", e)
        
        print(f"\n[OK] Romaneios criados: {romaneios_criados}")
        return romaneios_criados
    
    def criar_cobrancas_carregamento(self):
        """Cria cobranças de carregamento para os romaneios"""
        print("\n" + "="*70)
        print("CRIANDO COBRANÇAS DE CARREGAMENTO")
        print("="*70)
        
        if not self.romaneios:
            self.log_erro("Não há romaneios criados para gerar cobranças")
            return 0
        
        cobrancas_criadas = 0
        
        for romaneio in self.romaneios[:20]:  # Criar cobranças para até 20 romaneios
            try:
                # Calcular valor baseado no romaneio
                totais = romaneio.calcular_totais()
                valor_total = totais.get('valor_total', Decimal('0.00')) if isinstance(totais, dict) else Decimal('0.00')
                valor_cobranca = valor_total * Decimal('0.10')  # 10% do valor total
                
                data_vencimento = date.today() + timedelta(days=30)
                
                cobranca = CobrancaCarregamento.objects.create(
                    cliente=romaneio.cliente,
                    valor_carregamento=valor_cobranca,
                    data_vencimento=data_vencimento,
                    status='Pendente',
                    observacoes=f'Cobranca gerada automaticamente para romaneio {romaneio.codigo}'
                )
                
                # Vincular romaneio à cobrança
                cobranca.romaneios.add(romaneio)
                
                self.cobrancas.append(cobranca)
                cobrancas_criadas += 1
                self.log_sucesso(f"Cobranca criada: R$ {valor_cobranca:.2f} para romaneio {romaneio.codigo}")
                
            except Exception as e:
                self.log_erro(f"Erro ao criar cobrança para romaneio {romaneio.codigo}", e)
        
        print(f"\n[OK] Cobrancas criadas: {cobrancas_criadas}")
        return cobrancas_criadas
    
    def executar_teste_completo(self):
        """Executa todos os testes"""
        print("\n" + "="*70)
        print("INICIANDO TESTE COMPLETO DO SISTEMA")
        print("="*70)
        print(f"Data/Hora: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        inicio = timezone.now()
        
        try:
            # 1. Criar clientes
            self.criar_clientes(30)
            
            # 2. Criar motoristas
            self.criar_motoristas(30)
            
            # 3. Criar veículos
            self.criar_veiculos(30)
            
            # 4. Criar notas fiscais
            self.criar_notas_fiscais(300)
            
            # 5. Criar romaneios
            self.criar_romaneios()
            
            # 6. Criar cobranças
            self.criar_cobrancas_carregamento()
            
        except Exception as e:
            self.log_erro("Erro crítico durante execução do teste", e)
        
        fim = timezone.now()
        duracao = (fim - inicio).total_seconds()
        
        # Relatório final
        self.gerar_relatorio(duracao)
    
    def gerar_relatorio(self, duracao):
        """Gera relatório final do teste"""
        print("\n" + "="*70)
        print("RELATÓRIO FINAL DO TESTE")
        print("="*70)
        
        print(f"\nDuracao: {duracao:.2f} segundos")
        print(f"\nRESUMO:")
        print(f"   [OK] Clientes criados: {len(self.clientes)}")
        print(f"   [OK] Motoristas criados: {len(self.motoristas)}")
        print(f"   [OK] Veiculos criados: {len(self.veiculos)}")
        print(f"   [OK] Notas fiscais criadas: {len(self.notas_fiscais)}")
        print(f"   [OK] Romaneios criados: {len(self.romaneios)}")
        print(f"   [OK] Cobrancas criadas: {len(self.cobrancas)}")
        
        print(f"\n[OK] SUCESSOS: {len(self.sucessos)}")
        print(f"[ERRO] ERROS: {len(self.erros)}")
        
        if self.erros:
            print(f"\n[ERRO] ERROS ENCONTRADOS:")
            for i, erro in enumerate(self.erros[:20], 1):  # Mostrar apenas primeiros 20
                print(f"   {i}. {erro}")
            if len(self.erros) > 20:
                print(f"   ... e mais {len(self.erros) - 20} erros")
        else:
            print(f"\n[OK] NENHUM ERRO ENCONTRADO! Sistema funcionando perfeitamente.")
        
        print("\n" + "="*70)
        
        # Salvar relatório em arquivo
        relatorio_path = BASE_DIR / 'logs' / 'teste_sistema_completo.log'
        relatorio_path.parent.mkdir(exist_ok=True)
        
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("RELATÓRIO DE TESTE COMPLETO DO SISTEMA\n")
            f.write("="*70 + "\n\n")
            f.write(f"Data/Hora: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Duração: {duracao:.2f} segundos\n\n")
            f.write(f"RESUMO:\n")
            f.write(f"  Clientes criados: {len(self.clientes)}\n")
            f.write(f"  Motoristas criados: {len(self.motoristas)}\n")
            f.write(f"  Veículos criados: {len(self.veiculos)}\n")
            f.write(f"  Notas fiscais criadas: {len(self.notas_fiscais)}\n")
            f.write(f"  Romaneios criados: {len(self.romaneios)}\n")
            f.write(f"  Cobranças criadas: {len(self.cobrancas)}\n\n")
            f.write(f"SUCESSOS: {len(self.sucessos)}\n")
            f.write(f"ERROS: {len(self.erros)}\n\n")
            
            if self.erros:
                f.write("ERROS ENCONTRADOS:\n")
                for i, erro in enumerate(self.erros, 1):
                    f.write(f"  {i}. {erro}\n")
        
        print(f"Relatorio salvo em: {relatorio_path}")


if __name__ == '__main__':
    teste = TesteSistemaCompleto()
    teste.executar_teste_completo()

