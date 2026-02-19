"""
Utilitários para tratamento de exceções específicas.

Use handle_model_exception() em views que redirecionam após sucesso e desejam
tratamento padronizado (log + message + redirect) em caso de IntegrityError,
ValidationError ou DoesNotExist. Ex.: em views de criação/edição que fazem
redirect('...:listar') após save, envolva o save em try/except e retorne
handle_model_exception(request, e, 'Cliente', 'criar', redirect_url) quando
a função retornar um HttpResponse.
"""
import logging
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def handle_model_exception(request, exception, model_name: str, action: str, redirect_url: str):
    """
    Trata exceções específicas de modelos Django de forma padronizada.
    
    Args:
        request: HttpRequest object
        exception: Exceção capturada
        model_name: Nome do modelo (ex: 'Cliente', 'NotaFiscal')
        action: Ação que estava sendo executada (ex: 'criar', 'editar', 'excluir')
        redirect_url: URL para redirecionar em caso de erro
    
    Returns:
        HttpResponse: Resposta de redirecionamento ou None
    """
    if isinstance(exception, IntegrityError):
        logger.error(
            f'Erro de integridade ao {action} {model_name}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'action': action,
                'model': model_name,
                'error': str(exception)
            },
            exc_info=True
        )
        messages.error(
            request,
            f'Erro ao {action} {model_name}. '
            'Verifique se não há dados duplicados ou conflitos.'
        )
        return redirect(redirect_url)
    
    elif isinstance(exception, ValidationError):
        logger.warning(
            f'Erro de validação ao {action} {model_name}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'action': action,
                'model': model_name,
                'errors': exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
            }
        )
        messages.error(
            request,
            f'Dados inválidos ao {action} {model_name}. '
            'Verifique os campos e tente novamente.'
        )
        return redirect(redirect_url)
    
    elif hasattr(exception, 'DoesNotExist'):
        logger.warning(
            f'{model_name} não encontrado ao {action}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'action': action,
                'model': model_name
            }
        )
        messages.error(request, f'{model_name} não encontrado.')
        return redirect(redirect_url)
    
    else:
        # Exceção genérica - logar com detalhes completos
        logger.error(
            f'Erro inesperado ao {action} {model_name}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'action': action,
                'model': model_name,
                'error_type': type(exception).__name__,
                'error': str(exception)
            },
            exc_info=True
        )
        messages.error(
            request,
            f'Erro inesperado ao {action} {model_name}. '
            'Tente novamente ou entre em contato com o suporte.'
        )
        return redirect(redirect_url)


def handle_get_object_exception(request, model_class, pk, redirect_url: str):
    """
    Trata exceções ao buscar um objeto específico.
    
    Args:
        request: HttpRequest object
        model_class: Classe do modelo Django
        pk: Primary key do objeto
        redirect_url: URL para redirecionar em caso de erro
    
    Returns:
        Objeto do modelo ou HttpResponse de redirecionamento
    """
    try:
        return model_class.objects.get(pk=pk)
    except model_class.DoesNotExist:
        logger.warning(
            f'{model_class.__name__} não encontrado',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'model': model_class.__name__,
                'pk': pk
            }
        )
        messages.error(request, f'{model_class.__name__} não encontrado.')
        return redirect(redirect_url)
    except Exception as e:
        logger.error(
            f'Erro ao buscar {model_class.__name__}',
            extra={
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'model': model_class.__name__,
                'pk': pk,
                'error': str(e)
            },
            exc_info=True
        )
        messages.error(request, f'Erro ao buscar {model_class.__name__}.')
        return redirect(redirect_url)


