#!/usr/bin/env python
"""
Script para verificar os dados formatados dos clientes, motoristas e veículos
"""
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Cliente, Motorista, Veiculo


def verificar_clientes():
    """Verifica e mostra os dados dos clientes"""
    print("=" * 60)
    print("DADOS DOS CLIENTES")
    print("=" * 60)
    
    clientes = Cliente.objects.all().order_by('razao_social')
    
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return
    
    for cliente in clientes:
        print(f"\nCliente: {cliente.razao_social}")
        print(f"  CNPJ: {cliente.cnpj or 'Não informado'}")
        print(f"  Telefone: {cliente.telefone or 'Não informado'}")
        print(f"  CEP: {cliente.cep or 'Não informado'}")
        print(f"  Email: {cliente.email or 'Não informado'}")
        print(f"  Status: {cliente.status}")


def verificar_motoristas():
    """Verifica e mostra os dados dos motoristas"""
    print("\n" + "=" * 60)
    print("DADOS DOS MOTORISTAS")
    print("=" * 60)
    
    motoristas = Motorista.objects.all().order_by('nome')
    
    if not motoristas:
        print("Nenhum motorista cadastrado.")
        return
    
    for motorista in motoristas:
        print(f"\nMotorista: {motorista.nome}")
        print(f"  CPF: {motorista.cpf or 'Não informado'}")
        print(f"  Telefone: {motorista.telefone or 'Não informado'}")
        print(f"  CEP: {motorista.cep or 'Não informado'}")
        print(f"  CNH: {motorista.cnh or 'Não informado'}")


def verificar_veiculos():
    """Verifica e mostra os dados dos veículos"""
    print("\n" + "=" * 60)
    print("DADOS DOS VEÍCULOS")
    print("=" * 60)
    
    veiculos = Veiculo.objects.all().order_by('placa')
    
    if not veiculos:
        print("Nenhum veículo cadastrado.")
        return
    
    for veiculo in veiculos:
        print(f"\nVeículo: {veiculo.placa}")
        print(f"  Tipo: {veiculo.get_tipo_unidade_display()}")
        print(f"  CPF/CNPJ do Proprietário: {veiculo.proprietario_cpf_cnpj or 'Não informado'}")
        print(f"  Telefone do Proprietário: {veiculo.proprietario_telefone or 'Não informado'}")
        print(f"  CEP do Proprietário: {veiculo.proprietario_cep or 'Não informado'}")


def main():
    """Função principal"""
    print("RELATÓRIO DE DADOS FORMATADOS")
    print("Sistema Estelar")
    print("=" * 60)
    
    verificar_clientes()
    verificar_motoristas()
    verificar_veiculos()
    
    print("\n" + "=" * 60)
    print("RELATÓRIO CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    main() 