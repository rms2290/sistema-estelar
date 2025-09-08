from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que não precisam de autenticação
        public_urls = [
            '/notas/login/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Verificar se a URL atual é pública
        is_public = any(request.path.startswith(url) for url in public_urls)
        
        # Se não é pública e o usuário não está autenticado, redirecionar para login
        if not is_public and not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login para acessar esta página.')
            return redirect('notas:login')
        
        response = self.get_response(request)
        return response 