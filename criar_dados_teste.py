#!/usr/bin/env python
"""
Script para criar dados de teste no sistema Estelar
Cria: 10 clientes, 10 motoristas, 10 veículos e 100 notas fiscais
"""
import os
import sys
import django
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Cliente, Motorista, Veiculo, NotaFiscal, RomaneioViagem

def criar_clientes():
    """Cria 10 clientes de teste"""
    print("Criando 10 clientes...")
    
    clientes_dados = [
        {"razao_social": "JOÃO SILVA LTDA", "cnpj": "12.345.678/0001-90", "endereco": "Rua A, 123", "telefone": "(11) 99999-0001"},
        {"razao_social": "MARIA SANTOS LTDA", "cnpj": "23.456.789/0001-91", "endereco": "Rua B, 456", "telefone": "(11) 99999-0002"},
        {"razao_social": "PEDRO OLIVEIRA LTDA", "cnpj": "34.567.890/0001-92", "endereco": "Rua C, 789", "telefone": "(11) 99999-0003"},
        {"razao_social": "ANA COSTA LTDA", "cnpj": "45.678.901/0001-93", "endereco": "Rua D, 321", "telefone": "(11) 99999-0004"},
        {"razao_social": "CARLOS LIMA LTDA", "cnpj": "56.789.012/0001-94", "endereco": "Rua E, 654", "telefone": "(11) 99999-0005"},
        {"razao_social": "FERNANDA ROCHA LTDA", "cnpj": "67.890.123/0001-95", "endereco": "Rua F, 987", "telefone": "(11) 99999-0006"},
        {"razao_social": "ROBERTO ALVES LTDA", "cnpj": "78.901.234/0001-96", "endereco": "Rua G, 147", "telefone": "(11) 99999-0007"},
        {"razao_social": "JULIANA PEREIRA LTDA", "cnpj": "89.012.345/0001-97", "endereco": "Rua H, 258", "telefone": "(11) 99999-0008"},
        {"razao_social": "MARCOS FERREIRA LTDA", "cnpj": "90.123.456/0001-98", "endereco": "Rua I, 369", "telefone": "(11) 99999-0009"},
        {"razao_social": "PATRICIA SOUZA LTDA", "cnpj": "01.234.567/0001-99", "endereco": "Rua J, 741", "telefone": "(11) 99999-0010"},
    ]
    
    clientes_criados = []
    for dados in clientes_dados:
        cliente, created = Cliente.objects.get_or_create(
            cnpj=dados["cnpj"],
            defaults=dados
        )
        if created:
            clientes_criados.append(cliente)
            print(f"  ✓ Cliente criado: {cliente.razao_social}")
        else:
            print(f"  - Cliente já existe: {cliente.razao_social}")
    
    return clientes_criados

def criar_motoristas():
    """Cria 10 motoristas de teste"""
    print("\nCriando 10 motoristas...")
    
    motoristas_dados = [
        {"nome": "Antonio Silva", "cpf": "111.111.111-11", "cnh": "12345678901", "telefone": "(11) 88888-0001"},
        {"nome": "Bruno Santos", "cpf": "222.222.222-22", "cnh": "12345678902", "telefone": "(11) 88888-0002"},
        {"nome": "Carlos Oliveira", "cpf": "333.333.333-33", "cnh": "12345678903", "telefone": "(11) 88888-0003"},
        {"nome": "Diego Costa", "cpf": "444.444.444-44", "cnh": "12345678904", "telefone": "(11) 88888-0004"},
        {"nome": "Eduardo Lima", "cpf": "555.555.555-55", "cnh": "12345678905", "telefone": "(11) 88888-0005"},
        {"nome": "Felipe Rocha", "cpf": "666.666.666-66", "cnh": "12345678906", "telefone": "(11) 88888-0006"},
        {"nome": "Gabriel Alves", "cpf": "777.777.777-77", "cnh": "12345678907", "telefone": "(11) 88888-0007"},
        {"nome": "Henrique Pereira", "cpf": "888.888.888-88", "cnh": "12345678908", "telefone": "(11) 88888-0008"},
        {"nome": "Igor Ferreira", "cpf": "999.999.999-99", "cnh": "12345678909", "telefone": "(11) 88888-0009"},
        {"nome": "João Souza", "cpf": "000.000.000-00", "cnh": "12345678910", "telefone": "(11) 88888-0010"},
    ]
    
    motoristas_criados = []
    for dados in motoristas_dados:
        motorista, created = Motorista.objects.get_or_create(
            cpf=dados["cpf"],
            defaults=dados
        )
        if created:
            motoristas_criados.append(motorista)
            print(f"  ✓ Motorista criado: {motorista.nome}")
        else:
            print(f"  - Motorista já existe: {motorista.nome}")
    
    return motoristas_criados

def criar_veiculos():
    """Cria 10 veículos de teste"""
    print("\nCriando 10 veículos...")
    
    tipos_veiculo = ['Caminhão', 'Van', 'Pickup', 'Carreta', 'Bitruck']
    marcas = ['Volvo', 'Scania', 'Mercedes', 'Iveco', 'Ford', 'Chevrolet']
    
    veiculos_dados = [
        {"placa": "ABC1234", "modelo": "FH 460", "marca": "Volvo", "tipo_unidade": "Caminhão"},
        {"placa": "DEF5678", "modelo": "R 450", "marca": "Scania", "tipo_unidade": "Caminhão"},
        {"placa": "GHI9012", "modelo": "Actros 2651", "marca": "Mercedes", "tipo_unidade": "Caminhão"},
        {"placa": "JKL3456", "modelo": "Tector", "marca": "Iveco", "tipo_unidade": "Caminhão"},
        {"placa": "MNO7890", "modelo": "Cargo 2428", "marca": "Ford", "tipo_unidade": "Caminhão"},
        {"placa": "PQR1357", "modelo": "Master", "marca": "Iveco", "tipo_unidade": "Van"},
        {"placa": "STU2468", "modelo": "Sprinter", "marca": "Mercedes", "tipo_unidade": "Van"},
        {"placa": "VWX3691", "modelo": "Ranger", "marca": "Ford", "tipo_unidade": "Carro"},
        {"placa": "YZA4825", "modelo": "S10", "marca": "Chevrolet", "tipo_unidade": "Carro"},
        {"placa": "BCD5936", "modelo": "Carreta 3 eixos", "marca": "Volvo", "tipo_unidade": "Reboque"},
    ]
    
    veiculos_criados = []
    for dados in veiculos_dados:
        veiculo, created = Veiculo.objects.get_or_create(
            placa=dados["placa"],
            defaults=dados
        )
        if created:
            veiculos_criados.append(veiculo)
            print(f"  ✓ Veículo criado: {veiculo.placa} - {veiculo.marca} {veiculo.modelo}")
        else:
            print(f"  - Veículo já existe: {veiculo.placa}")
    
    return veiculos_criados

def criar_notas_fiscais(clientes, motoristas, veiculos):
    """Cria 100 notas fiscais (70 para o primeiro cliente)"""
    print("\nCriando 100 notas fiscais...")
    
    # 70 notas para o primeiro cliente
    cliente_principal = clientes[0]
    outros_clientes = clientes[1:]
    
    notas_criadas = 0
    
    # Criar 70 notas para o cliente principal
    print(f"  Criando 70 notas para {cliente_principal.razao_social}...")
    for i in range(70):
        data_emissao = datetime.now() - timedelta(days=random.randint(1, 365))
        
        nota = NotaFiscal.objects.create(
            nota=str(1000 + i),
            cliente=cliente_principal,
            data=data_emissao.date(),
            fornecedor=f"FORNECEDOR {i+1} LTDA",
            mercadoria=f"MERCADORIA {i+1}",
            quantidade=Decimal(str(random.uniform(1.0, 100.0))).quantize(Decimal('0.01')),
            peso=Decimal(str(random.uniform(100.0, 10000.0))).quantize(Decimal('0.1')),
            valor=Decimal(str(random.uniform(100.00, 5000.00))).quantize(Decimal('0.01'))
        )
        notas_criadas += 1
        
        if (i + 1) % 10 == 0:
            print(f"    {i + 1}/70 notas criadas...")
    
    # Criar 30 notas para os outros clientes
    print("  Criando 30 notas para outros clientes...")
    for i in range(30):
        data_emissao = datetime.now() - timedelta(days=random.randint(1, 365))
        
        nota = NotaFiscal.objects.create(
            nota=str(2000 + i),
            cliente=random.choice(outros_clientes),
            data=data_emissao.date(),
            fornecedor=f"FORNECEDOR {i+71} LTDA",
            mercadoria=f"MERCADORIA {i+71}",
            quantidade=Decimal(str(random.uniform(1.0, 100.0))).quantize(Decimal('0.01')),
            peso=Decimal(str(random.uniform(100.0, 10000.0))).quantize(Decimal('0.1')),
            valor=Decimal(str(random.uniform(100.00, 5000.00))).quantize(Decimal('0.01'))
        )
        notas_criadas += 1
        
        if (i + 1) % 10 == 0:
            print(f"    {i + 1}/30 notas criadas...")
    
    print(f"  ✓ Total de {notas_criadas} notas fiscais criadas!")
    return notas_criadas

def main():
    """Função principal"""
    print("=== CRIANDO DADOS DE TESTE PARA O SISTEMA ESTELAR ===\n")
    
    try:
        # Criar clientes
        clientes = criar_clientes()
        
        # Criar motoristas
        motoristas = criar_motoristas()
        
        # Criar veículos
        veiculos = criar_veiculos()
        
        # Criar notas fiscais
        notas_criadas = criar_notas_fiscais(clientes, motoristas, veiculos)
        
        print(f"\n=== RESUMO ===")
        print(f"✓ {len(clientes)} clientes")
        print(f"✓ {len(motoristas)} motoristas")
        print(f"✓ {len(veiculos)} veículos")
        print(f"✓ {notas_criadas} notas fiscais")
        print(f"  - 70 notas para {clientes[0].razao_social}")
        print(f"  - 30 notas distribuídas entre outros clientes")
        
        print(f"\n🎉 Dados de teste criados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro ao criar dados de teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
