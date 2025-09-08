#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import Usuario, Cliente

def create_admin_user():
    # Verificar se já existe um usuário admin
    if Usuario.objects.filter(username='admin').exists():
        print("Usuário 'admin' já existe!")
        return
    
    # Criar usuário administrador
    admin_user = Usuario(
        username='admin',
        email='admin@estelar.com',
        first_name='Administrador',
        last_name='Sistema',
        tipo_usuario='admin',
        is_active=True,
        is_staff=True
    )
    admin_user.set_password('admin123')
    admin_user.save()
    
    print("Usuário administrador criado com sucesso!")
    print("Username: admin")
    print("Senha: admin123")

def create_test_users():
    # Criar um funcionário de teste
    if not Usuario.objects.filter(username='funcionario').exists():
        funcionario = Usuario(
            username='funcionario',
            email='funcionario@estelar.com',
            first_name='João',
            last_name='Silva',
            tipo_usuario='funcionario',
            is_active=True
        )
        funcionario.set_password('func123')
        funcionario.save()
        print("Usuário funcionário criado: funcionario/func123")
    
    # Criar um cliente de teste (se existir um cliente)
    if not Usuario.objects.filter(username='cliente').exists():
        # Buscar o primeiro cliente ativo
        cliente_obj = Cliente.objects.filter(status='Ativo').first()
        if cliente_obj:
            cliente_user = Usuario(
                username='cliente',
                email='cliente@empresa.com',
                first_name='Maria',
                last_name='Santos',
                tipo_usuario='cliente',
                cliente=cliente_obj,
                is_active=True
            )
            cliente_user.set_password('cliente123')
            cliente_user.save()
            print(f"Usuário cliente criado: cliente/cliente123 (vinculado a {cliente_obj.razao_social})")
        else:
            print("Nenhum cliente ativo encontrado para criar usuário cliente de teste")

if __name__ == '__main__':
    create_admin_user()
    create_test_users() 