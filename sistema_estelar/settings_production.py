"""
Configurações OTIMIZADAS para produção na Locaweb - Baixo consumo de memória
"""
import os
from .settings import *

# Configurações de segurança para produção
DEBUG = False
ALLOWED_HOSTS = [
    'agenciaestelar.online', 
    'www.agenciaestelar.online', 
    '191.252.113.245',
    '191.115.102.155',
    'vps61227.publiccloud.com.br', 
    'www.vps61227.publiccloud.com.br', 
    'vps61227OO', 
    'localhost', 
    '127.0.0.1'
]

# Configurações de banco de dados para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'CONN_MAX_AGE': 60,
    }
}
# Configurações de arquivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configurações de segurança
SECRET_KEY = os.environ.get('SECRET_KEY', 'sua-chave-secreta-aqui')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações de sessão
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# OTIMIZAÇÃO: Cache em arquivo em vez de memória
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Limitar entradas no cache
            'CULL_FREQUENCY': 3,  # Limpar cache mais frequentemente
        }
    }
}

# OTIMIZAÇÃO: Configurações de logging mais eficientes
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'root': {
        'level': 'ERROR',
        'handlers': ['file'],
    },
}

# Configurações de email (ajuste conforme necessário)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.locaweb.com.br'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Configurações de timezone
TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True

# Configurações de idioma
LANGUAGE_CODE = 'pt-br'
USE_I18N = True
USE_L10N = True

# OTIMIZAÇÃO: Configurações adicionais para economizar memória
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# OTIMIZAÇÃO: Desabilitar funcionalidades desnecessárias
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = '.'
DECIMAL_SEPARATOR = ','

# OTIMIZAÇÃO: Configurações de arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# OTIMIZAÇÃO: Configurações de sessão
SESSION_COOKIE_AGE = 1800  # 30 minutos (reduzido de 1 hora)
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
