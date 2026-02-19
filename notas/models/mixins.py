"""
Mixins e utilitários compartilhados pelos modelos.
"""
from django.contrib.auth.models import BaseUserManager


class UpperCaseMixin:
    """
    Mixin que converte automaticamente campos de texto para maiúsculas.

    Aplica-se a todos os campos CharField do modelo, exceto aqueles
    especificados na lista de exclusão (emails, senhas, CPF/CNPJ, etc.).

    Uso:
        class MeuModelo(UpperCaseMixin, models.Model):
            nome = models.CharField(max_length=100)
            # 'nome' será automaticamente convertido para maiúsculas

    Campos Excluídos da Conversão:
        - email, password, username
        - cpf, cnpj, cnh, chassi, renavam, placa, cep
        - telefone, rntrc, numero_consulta
        - tipo_usuario, status, rg
    """
    def save(self, *args, **kwargs):
        for field in self._meta.fields:
            if hasattr(field, 'max_length') and hasattr(self, field.name):
                value = getattr(self, field.name)
                if value and isinstance(value, str):
                    exclude_fields = [
                        'email', 'password', 'username', 'cpf', 'cnpj',
                        'cnh', 'chassi', 'renavam', 'placa', 'cep',
                        'telefone', 'rntrc', 'numero_consulta', 'tipo_usuario',
                        'status', 'rg', 'tipo', 'categoria', 'tipo_pagamento', 'tipo_cliente'
                    ]
                    if field.name not in exclude_fields:
                        setattr(self, field.name, value.upper())
        super().save(*args, **kwargs)


class UsuarioManager(BaseUserManager):
    """
    Gerenciador customizado para o modelo Usuario.

    Fornece métodos para criar usuários normais e superusuários,
    seguindo as melhores práticas do Django.
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('O nome de usuário é obrigatório')
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('tipo_usuario', 'admin')
        return self.create_user(username, email, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username=username)
