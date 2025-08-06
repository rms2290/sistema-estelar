from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    context = {
        'title': 'Dashboard - Agência Estelar',
        'user': request.user,
    }
    return render(request, 'notas/dashboard.html', context) 