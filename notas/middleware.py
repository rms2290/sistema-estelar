from django.conf import settings
from django.shortcuts import redirect

class AuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # API REST: não redirecionar; DRF responde com 401/403
        api_prefix = getattr(settings, 'API_URL_PREFIX', '/api/')
        if request.path.startswith(api_prefix):
            return self.get_response(request)

        # URLs que não precisam de autenticação (web)
        public_prefixes = getattr(settings, 'PUBLIC_URL_PREFIXES', [
            '/notas/login/', '/admin/', '/static/', '/media/',
        ])
        is_public = any(request.path.startswith(url) for url in public_prefixes)

        # Se não é pública e o usuário não está autenticado, redirecionar para login
        if not is_public and not request.user.is_authenticated:
            return redirect('notas:login')
        
        response = self.get_response(request)
        return response 