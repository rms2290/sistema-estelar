"""
Configurações OTIMIZADAS para produção na Locaweb - Baixo consumo de memória
"""
import os
from django.core.exceptions import ImproperlyConfigured
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
# PostgreSQL é recomendado para produção (já está no requirements_production.txt)
# Para usar SQLite (não recomendado), descomente as linhas abaixo e comente PostgreSQL

USE_POSTGRESQL = os.environ.get('USE_POSTGRESQL', 'True').lower() == 'true'

if USE_POSTGRESQL:
    # Configuração PostgreSQL (RECOMENDADO PARA PRODUÇÃO)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'sistema_estelar'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,  # 10 minutos
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
    
    # Validar que variáveis obrigatórias estão configuradas
    if not os.environ.get('DB_NAME'):
        raise ImproperlyConfigured(
            "DB_NAME não encontrada nas variáveis de ambiente! "
            "Configure DB_NAME, DB_USER, DB_PASSWORD, DB_HOST e DB_PORT para usar PostgreSQL."
        )
else:
    # Configuração SQLite (APENAS PARA DESENVOLVIMENTO/TESTE)
    # ⚠️ NÃO RECOMENDADO PARA PRODUÇÃO - Use apenas em emergências
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
# SECRET_KEY é OBRIGATÓRIA em produção - deve estar nas variáveis de ambiente
if 'SECRET_KEY' not in os.environ:
    raise ImproperlyConfigured(
        "SECRET_KEY não encontrada nas variáveis de ambiente! "
        "Configure SECRET_KEY antes de executar em produção."
    )
SECRET_KEY = os.environ['SECRET_KEY']
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configurações de sessão e segurança HTTPS
# Estas configurações devem ser True quando HTTPS estiver configurado
USE_HTTPS = os.environ.get('USE_HTTPS', 'False').lower() == 'true'

if USE_HTTPS:
    # Redirecionar HTTP para HTTPS
    SECURE_SSL_REDIRECT = True
    # Cookies seguros apenas em HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HTTP Strict Transport Security (HSTS)
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Outras configurações de segurança
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Desabilitado para HTTP (habilitar quando tiver HTTPS)
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

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

# Logging produção: timestamp, nível, logger, mensagem (sem debug; erros e ações críticas)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} [{name}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'notas': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'financeiro': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'level': 'WARNING',
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
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
