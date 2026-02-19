"""
Modelo Usuario - autenticação e autorização.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser

from .mixins import UpperCaseMixin, UsuarioManager
from .cliente import Cliente


class Usuario(UpperCaseMixin, AbstractUser):
    """
    Modelo de usuário customizado do sistema.

    Estende o AbstractUser do Django para adicionar funcionalidades
    específicas do sistema, incluindo tipos de usuário e relacionamento
    com clientes.
    """
    TIPO_USUARIO_CHOICES = [
        ('admin', 'Administrador'),
        ('funcionario', 'Funcionário'),
        ('cliente', 'Cliente'),
    ]

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='funcionario',
        verbose_name="Tipo de Usuário"
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cliente Vinculado"
    )

    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    ultimo_acesso = models.DateTimeField(null=True, blank=True, verbose_name="Último Acesso")

    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    USERNAME_FIELD = 'username'
    is_authenticated = True
    is_anonymous = False

    objects = UsuarioManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_tipo_usuario_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_admin(self):
        return self.tipo_usuario == 'admin'

    @property
    def is_funcionario(self):
        return self.tipo_usuario == 'funcionario'

    @property
    def is_cliente(self):
        return self.tipo_usuario == 'cliente'

    def can_access_all(self):
        """Verifica se o usuário tem acesso total ao sistema (apenas admin)."""
        return self.is_admin

    def can_access_funcionalidades(self):
        return self.is_admin or self.is_funcionario

    def can_access_client_data(self):
        return self.is_admin or self.is_funcionario or self.is_cliente
