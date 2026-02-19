"""
URLs da API v1 – recursos sob /api/v1/.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import ClienteViewSet

router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')

urlpatterns = [
    path('token/', obtain_auth_token, name='api-token'),
    path('', include(router.urls)),
]
