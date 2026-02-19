"""
Views da API v1 – ViewSets REST para recursos prioritários.
"""
from rest_framework import viewsets
from rest_framework.filters import SearchFilter

from notas.models import Cliente

from .serializers import ClienteSerializer


class ClienteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lista e detalha clientes.

    - **list**: GET /api/v1/clientes/
    - **retrieve**: GET /api/v1/clientes/{id}/
    """
    queryset = Cliente.objects.all().order_by('razao_social')
    serializer_class = ClienteSerializer
    filter_backends = [SearchFilter]
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj', 'cidade']
