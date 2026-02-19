"""
Serializers da API v1 – expõem modelos como JSON.
"""
from rest_framework import serializers

from notas.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer para o recurso Cliente (listagem e detalhe)."""

    class Meta:
        model = Cliente
        fields = [
            'id',
            'razao_social',
            'nome_fantasia',
            'cnpj',
            'inscricao_estadual',
            'endereco',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'estado',
            'cep',
            'telefone',
            'email',
            'status',
        ]
        read_only_fields = fields
