"""
Respostas JSON padronizadas para APIs internas (AJAX/API).

Contrato:
---------
Sucesso:
  {
    "success": true,
    "data": { ... }   (opcional; payload principal)
    "message": "..."  (opcional)
    ...               (campos extras permitidos para compatibilidade)
  }

Erro:
  {
    "success": false,
    "code": "..."     (opcional; código de erro)
    "message": "..."
    "details": { ... } (opcional; dados adicionais do erro)
  }

Uso:
----
  from sistema_estelar.api_utils import json_success, json_error

  return json_success(data={'id': 1}, message='Criado com sucesso')
  return json_error('Dados inválidos', code='VALIDATION_ERROR', status=400)
"""
from django.http import JsonResponse


def json_success(data=None, message=None, status=200, **kwargs):
    """
    Retorna JsonResponse de sucesso padronizado.

    Args:
        data: Objeto (dict/list) com o payload principal. Será incluído em response["data"].
        message: Mensagem opcional.
        status: Código HTTP (default 200).
        **kwargs: Campos extras mesclados na raiz (ex.: movimento_id=1 para compatibilidade).

    Returns:
        JsonResponse com success=true.
    """
    payload = {'success': True}
    if data is not None:
        payload['data'] = data
    if message is not None:
        payload['message'] = message
    payload.update(kwargs)
    return JsonResponse(payload, status=status)


def json_error(message, code=None, details=None, status=400):
    """
    Retorna JsonResponse de erro padronizado.

    Args:
        message: Mensagem de erro (obrigatória).
        code: Código de erro opcional (ex.: 'VALIDATION_ERROR', 'NOT_FOUND').
        details: Dict com detalhes adicionais opcional.
        status: Código HTTP (default 400).

    Returns:
        JsonResponse com success=false.
    """
    payload = {'success': False, 'message': message}
    if code is not None:
        payload['code'] = code
    if details is not None:
        payload['details'] = details
    return JsonResponse(payload, status=status)


def json_exception_handler(view_func):
    """
    Decorator que captura exceções não tratadas em views que retornam JSON
    e responde com json_error no formato padronizado.
    """
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Exceção em view JSON')
            return json_error(
                message=str(e),
                code='INTERNAL_ERROR',
                status=500,
            )
    return wrapper
