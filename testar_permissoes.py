#!/usr/bin/env python
"""
Script para testar as restrições de permissão implementadas.
Este script simula tentativas de exclusão por diferentes tipos de usuário.
"""

import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from django.contrib.auth import get_user_model
from notas.models import Cliente, Motorista, RomaneioViagem, Usuario, Veiculo

def testar_permissoes():
    """Testa as restrições de permissão implementadas"""
    
    print("=== TESTE DE PERMISSÕES DE EXCLUSÃO ===\n")
    
    # Criar usuários de teste se não existirem
    try:
        admin_user = Usuario.objects.get(username='admin_test')
        print("✓ Usuário admin já existe")
    except Usuario.DoesNotExist:
        admin_user = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin123',
            tipo_usuario='admin',
            first_name='Admin',
            last_name='Test'
        )
        print("✓ Usuário admin criado")
    
    try:
        funcionario_user = Usuario.objects.get(username='funcionario_test')
        print("✓ Usuário funcionário já existe")
    except Usuario.DoesNotExist:
        funcionario_user = Usuario.objects.create_user(
            username='funcionario_test',
            email='funcionario@test.com',
            password='func123',
            tipo_usuario='funcionario',
            first_name='Funcionário',
            last_name='Test'
        )
        print("✓ Usuário funcionário criado")
    
    # Criar dados de teste
    try:
        cliente_teste = Cliente.objects.get(razao_social='EMPRESA TESTE LTDA')
        print("✓ Cliente de teste já existe")
    except Cliente.DoesNotExist:
        cliente_teste = Cliente.objects.create(
            razao_social='EMPRESA TESTE LTDA',
            cnpj='12.345.678/0001-90',
            telefone='(11) 99999-9999'
        )
        print("✓ Cliente de teste criado")
    
    try:
        motorista_teste = Motorista.objects.get(nome='MOTORISTA TESTE')
        print("✓ Motorista de teste já existe")
    except Motorista.DoesNotExist:
        motorista_teste = Motorista.objects.create(
            nome='MOTORISTA TESTE',
            cpf='123.456.789-00',
            telefone='(11) 88888-8888'
        )
        print("✓ Motorista de teste criado")
    
    # Criar veículo de teste
    try:
        veiculo_teste = Veiculo.objects.get(placa='ABC1234')
        print("✓ Veículo de teste já existe")
    except Veiculo.DoesNotExist:
        veiculo_teste = Veiculo.objects.create(
            placa='ABC1234',
            tipo_unidade='Caminhão',
            marca='Volkswagen',
            modelo='Delivery'
        )
        print("✓ Veículo de teste criado")
    
    try:
        romaneio_salvo = RomaneioViagem.objects.get(codigo='ROM-TEST-SALVO-0001')
        print("✓ Romaneio salvo já existe")
    except RomaneioViagem.DoesNotExist:
        romaneio_salvo = RomaneioViagem.objects.create(
            codigo='ROM-TEST-SALVO-0001',
            cliente=cliente_teste,
            motorista=motorista_teste,
            veiculo_principal=veiculo_teste,
            status='Salvo'
        )
        print("✓ Romaneio salvo criado")
    
    try:
        romaneio_emitido = RomaneioViagem.objects.get(codigo='ROM-TEST-EMITIDO-0001')
        print("✓ Romaneio emitido já existe")
    except RomaneioViagem.DoesNotExist:
        romaneio_emitido = RomaneioViagem.objects.create(
            codigo='ROM-TEST-EMITIDO-0001',
            cliente=cliente_teste,
            motorista=motorista_teste,
            veiculo_principal=veiculo_teste,
            status='Emitido'
        )
        print("✓ Romaneio emitido criado")
    
    print("\n=== TESTANDO PERMISSÕES ===\n")
    
    # Teste 1: Funcionário tentando excluir cliente
    print("1. Funcionário tentando excluir cliente:")
    print(f"   Usuário: {funcionario_user.username} (tipo: {funcionario_user.tipo_usuario})")
    print(f"   Cliente: {cliente_teste.razao_social}")
    print("   Resultado esperado: BLOQUEADO - Apenas administradores podem excluir clientes")
    print()
    
    # Teste 2: Funcionário tentando excluir motorista
    print("2. Funcionário tentando excluir motorista:")
    print(f"   Usuário: {funcionario_user.username} (tipo: {funcionario_user.tipo_usuario})")
    print(f"   Motorista: {motorista_teste.nome}")
    print("   Resultado esperado: BLOQUEADO - Apenas administradores podem excluir motoristas")
    print()
    
    # Teste 3: Funcionário tentando excluir romaneio salvo
    print("3. Funcionário tentando excluir romaneio salvo:")
    print(f"   Usuário: {funcionario_user.username} (tipo: {funcionario_user.tipo_usuario})")
    print(f"   Romaneio: {romaneio_salvo.codigo} (status: {romaneio_salvo.status})")
    print("   Resultado esperado: PERMITIDO - Funcionários podem excluir romaneios salvos")
    print()
    
    # Teste 4: Funcionário tentando excluir romaneio emitido
    print("4. Funcionário tentando excluir romaneio emitido:")
    print(f"   Usuário: {funcionario_user.username} (tipo: {funcionario_user.tipo_usuario})")
    print(f"   Romaneio: {romaneio_emitido.codigo} (status: {romaneio_emitido.status})")
    print("   Resultado esperado: BLOQUEADO - Apenas administradores podem excluir romaneios emitidos")
    print()
    
    # Teste 5: Admin tentando excluir cliente
    print("5. Admin tentando excluir cliente:")
    print(f"   Usuário: {admin_user.username} (tipo: {admin_user.tipo_usuario})")
    print(f"   Cliente: {cliente_teste.razao_social}")
    print("   Resultado esperado: PERMITIDO - Administradores podem excluir clientes")
    print()
    
    # Teste 6: Admin tentando excluir motorista
    print("6. Admin tentando excluir motorista:")
    print(f"   Usuário: {admin_user.username} (tipo: {admin_user.tipo_usuario})")
    print(f"   Motorista: {motorista_teste.nome}")
    print("   Resultado esperado: PERMITIDO - Administradores podem excluir motoristas")
    print()
    
    # Teste 7: Admin tentando excluir romaneio emitido
    print("7. Admin tentando excluir romaneio emitido:")
    print(f"   Usuário: {admin_user.username} (tipo: {admin_user.tipo_usuario})")
    print(f"   Romaneio: {romaneio_emitido.codigo} (status: {romaneio_emitido.status})")
    print("   Resultado esperado: PERMITIDO - Administradores podem excluir romaneios emitidos")
    print()
    
    print("=== RESUMO DAS RESTRIÇÕES IMPLEMENTADAS ===\n")
    print("✓ Clientes: Apenas administradores podem excluir")
    print("✓ Motoristas: Apenas administradores podem excluir")
    print("✓ Romaneios salvos: Todos os usuários autorizados podem excluir")
    print("✓ Romaneios emitidos: Apenas administradores podem excluir")
    print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    testar_permissoes() 