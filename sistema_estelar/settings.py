from pathlib import Path
import os
from decouple import config
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY é OBRIGATÓRIA - deve estar no arquivo .env
# Para desenvolvimento, gere uma nova chave: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
try:
    SECRET_KEY = config('SECRET_KEY')
except Exception as e:
    raise ImproperlyConfigured(
        f"SECRET_KEY não encontrada! Crie um arquivo .env na raiz do projeto com SECRET_KEY=...\n"
        f"Para gerar uma chave: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"\n"
        f"Erro: {e}"
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# ALLOWED_HOSTS - Lista de hosts permitidos
# Em desenvolvimento: localhost,127.0.0.1
# Em produção: seus domínios reais
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'notas',
    'financeiro',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    # API REST (Fase 6)
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'api',
]

# Configuração do modelo de usuário customizado
AUTH_USER_MODEL = 'notas.Usuario'

# Ordem de migrações: admin depende de notas.0016_usuario (evita erro em testes)
MIGRATION_MODULES = {
    'admin': 'sistema_estelar.admin_migrations',
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Middleware de autenticação: URLs que não redirecionam para login
PUBLIC_URL_PREFIXES = [
    '/notas/login/',
    '/admin/',
    '/static/',
    '/media/',
]
API_URL_PREFIX = '/api/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir arquivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'notas.middleware.AuthenticationMiddleware',  # Nosso middleware customizado
]

# Debug Toolbar removido
# if DEBUG:
#     INSTALLED_APPS.append('debug_toolbar')
#     MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
#     INTERNAL_IPS = ['127.0.0.1']

ROOT_URLCONF = 'sistema_estelar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'financeiro' / 'templates', BASE_DIR / 'templates'],
        'APP_DIRS': True, # <--- E ESTA LINHA!
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_estelar.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True  # Habilita localização (formato de datas, números, etc.)

USE_TZ = True

# Formato de data padrão para o Brasil
DATE_INPUT_FORMATS = [
    '%d/%m/%Y',  # DD/MM/YYYY
    '%Y-%m-%d',  # YYYY-MM-DD (formato ISO para inputs HTML5)
    '%d/%m/%y',  # DD/MM/YY
]

DATE_FORMAT = 'd/m/Y'  # Formato de exibição padrão

DATETIME_FORMAT = 'd/m/Y H:i'  # Formato de data/hora padrão


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Configuração do WhiteNoise para servir arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configurações de mídia (upload de arquivos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de Segurança

# Configurações CSRF
CSRF_COOKIE_SECURE = False  # True em produção com HTTPS
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']

# Configurações de Sessão
SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações de Sessão
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Configurações de Log (Fase 5 – formato: timestamp, nível, logger, mensagem)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} [{name}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'notas': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'financeiro': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
}

# API REST (Fase 6) – Django REST Framework e documentação OpenAPI
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema Estelar API',
    'DESCRIPTION': 'API REST para integração com o Sistema Estelar (notas, clientes, romaneios).',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Criar diretório de logs se não existir
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Configurações de Autenticação
LOGIN_REDIRECT_URL = 'notas:dashboard'
LOGIN_URL = 'notas:login'
LOGOUT_REDIRECT_URL = 'notas:login'