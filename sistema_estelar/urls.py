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
    path('notas/', include('notas.urls')), # Inclua as URLs do app 'notas'
]

# Debug Toolbar URLs (apenas em desenvolvimento)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]