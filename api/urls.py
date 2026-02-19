"""
URLs da API – namespace /api/ com v1 e documentação OpenAPI.
"""
from django.urls import path, include
from rest_framework.permissions import AllowAny
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Documentação acessível sem autenticação
schema_view = SpectacularAPIView.as_view(permission_classes=[AllowAny])
swagger_view = SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny])
redoc_view = SpectacularRedocView.as_view(url_name='schema', permission_classes=[AllowAny])

urlpatterns = [
    path('v1/', include('api.v1.urls')),
    path('schema/', schema_view, name='schema'),
    path('schema/swagger-ui/', swagger_view, name='swagger-ui'),
    path('schema/redoc/', redoc_view, name='redoc'),
]
