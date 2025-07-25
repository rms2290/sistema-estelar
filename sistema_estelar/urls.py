# projeto_notas/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('notas/', include('notas.urls')), # Inclua as URLs do app 'notas'
]