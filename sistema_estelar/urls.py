# projeto_notas/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.shortcuts import redirect

def index(request):
    """Redireciona para o dashboard se autenticado, senão para o login"""
    if request.user.is_authenticated:
        return redirect('notas:dashboard')
    else:
        return redirect('notas:login')

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('notas/', include('notas.urls')),
    # Fluxo de caixa: namespace 'financeiro' registrado na raiz para {% url 'financeiro:...' %}
    path('notas/fluxo-caixa/', include('financeiro.urls')),
    # API REST (Fase 6): /api/v1/ + documentação em /api/schema/
    path('api/', include('api.urls')),
]

# Debug Toolbar URLs (apenas em desenvolvimento)
if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    # Servir arquivos de mídia em desenvolvimento
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)