"""
Utilitários para registrar logs de auditoria no sistema
"""
import json
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from ..models import AuditoriaLog


def get_client_ip(request):
    """Obtém o IP do cliente da requisição"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtém o user agent da requisição"""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # Limita a 500 caracteres


def serializer_modelo_para_dict(instance):
    """Serializa um modelo para dicionário (para armazenar em JSONField)"""
    if instance is None:
        return None
    
    dados = {}
    
    try:
        # Obter campos do modelo (não incluir ManyToMany aqui)
        for field in instance._meta.fields:
            field_name = field.name
            
            # Ignorar campos sensíveis
            if field_name in ['password', 'deleted_at', 'deleted_by']:
                continue
            
            try:
                value = getattr(instance, field_name, None)
                
                # Função auxiliar para converter valor para JSON-serializável
                def convert_to_serializable(val):
                    if val is None:
                        return None
                    elif isinstance(val, (str, int, float, bool)):
                        return val
                    elif isinstance(val, Decimal):
                        return float(val)
                    elif hasattr(val, 'isoformat'):
                        return val.isoformat()
                    elif hasattr(val, 'pk'):
                        # É um objeto relacionado
                        try:
                            return {
                                'id': val.pk,
                                'repr': str(val)[:100] if hasattr(val, '__str__') else None
                            }
                        except:
                            return val.pk if val else None
                    elif isinstance(val, (list, tuple)):
                        return [convert_to_serializable(item) for item in val[:10]]
                    elif isinstance(val, dict):
                        return {k: convert_to_serializable(v) for k, v in list(val.items())[:20]}
                    else:
                        # Tentar converter para string como último recurso
                        try:
                            str_val = str(val)
                            return str_val[:200] if len(str_val) > 200 else str_val
                        except:
                            return None
                
                dados[field_name] = convert_to_serializable(value)
                        
            except Exception as e:
                # Se houver erro ao acessar o campo, pular mas registrar nome do campo
                try:
                    dados[field_name] = f'[Erro ao serializar: {str(e)[:50]}]'
                except:
                    continue
        
        # Adicionar ManyToMany como lista de IDs (se houver)
        for field in instance._meta.many_to_many:
            field_name = field.name
            try:
                related_objects = getattr(instance, field_name).all()
                dados[field_name] = [obj.pk for obj in related_objects[:20]]  # Limitar a 20 itens
            except Exception as e:
                try:
                    dados[field_name] = f'[Erro ao serializar relacionamento: {str(e)[:50]}]'
                except:
                    continue
                
    except Exception as e:
        # Se houver erro geral, retornar apenas informações básicas
        try:
            dados = {
                'id': getattr(instance, 'pk', None),
                'repr': str(instance)[:200] if hasattr(instance, '__str__') else 'Objeto',
                'model': instance._meta.model_name if hasattr(instance, '_meta') else 'Desconhecido',
                'error': f'Erro ao serializar: {str(e)[:100]}'
            }
        except:
            dados = {'error': 'Erro crítico ao serializar objeto'}
    
    # Garantir que o resultado final é JSON-serializável usando json.dumps
    import json
    try:
        json.dumps(dados)  # Testa se é serializável
        return dados
    except (TypeError, ValueError) as e:
        # Se ainda não for serializável, retornar versão simplificada
        return {
            'id': getattr(instance, 'pk', None),
            'repr': str(instance)[:200] if hasattr(instance, '__str__') else 'Objeto',
            'model': instance._meta.model_name if hasattr(instance, '_meta') else 'Desconhecido',
            'error': 'Objeto não totalmente serializável - dados simplificados'
        }


def registrar_log_auditoria(
    usuario,
    acao,
    modelo,
    objeto_id=None,
    descricao='',
    dados_anteriores=None,
    dados_novos=None,
    request=None,
    instancia_anterior=None,
    instancia_nova=None
):
    """
    Registra uma entrada no log de auditoria
    
    Parâmetros:
    - usuario: Instância do Usuario que executou a ação
    - acao: String com a ação (CREATE, UPDATE, DELETE, etc.)
    - modelo: Nome do modelo (ex: 'Cliente', 'NotaFiscal')
    - objeto_id: ID do objeto afetado
    - descricao: Descrição detalhada da ação
    - dados_anteriores: Dicionário com dados anteriores (para updates/deletes)
    - dados_novos: Dicionário com dados novos (para creates/updates)
    - request: Objeto HttpRequest (para obter IP e User Agent)
    - instancia_anterior: Instância do modelo antes da mudança (serializa automaticamente)
    - instancia_nova: Instância do modelo depois da mudança (serializa automaticamente)
    
    Nota: Se estiver em modo de impersonação (request.session tem 'admin_original_id'),
    o usuário do log será o administrador original, não o usuário impersonado.
    """
    # Verificar se está em modo de impersonação
    if request and 'admin_original_id' in request.session:
        try:
            from ..models import Usuario
            admin_original_id = request.session.get('admin_original_id')
            admin_original = Usuario.objects.get(pk=admin_original_id)
            # Usar o admin original para registrar o log
            usuario = admin_original
            # Adicionar informação de impersonação na descrição se não estiver presente
            if descricao and 'impersonação' not in descricao.lower() and 'impersonate' not in descricao.lower():
                usuario_impersonado_id = request.session.get('usuario_impersonado_id')
                if usuario_impersonado_id:
                    try:
                        usuario_impersonado = Usuario.objects.get(pk=usuario_impersonado_id)
                        descricao = f"[IMPERSONANDO {usuario_impersonado.username}] {descricao}"
                    except Usuario.DoesNotExist:
                        pass
        except Exception:
            # Se houver erro ao obter admin original, usar o usuário fornecido
            pass
    
    # Serializar instâncias se fornecidas
    if instancia_anterior and dados_anteriores is None:
        dados_anteriores = serializer_modelo_para_dict(instancia_anterior)
    
    if instancia_nova and dados_novos is None:
        dados_novos = serializer_modelo_para_dict(instancia_nova)
    
    # Obter IP e User Agent do request se fornecido
    ip_address = None
    user_agent = ''
    if request:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
    
    # Criar registro de auditoria
    log = AuditoriaLog.objects.create(
        usuario=usuario,
        acao=acao,
        modelo=modelo,
        objeto_id=objeto_id,
        descricao=descricao,
        dados_anteriores=dados_anteriores,
        dados_novos=dados_novos,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return log


def registrar_criacao(usuario, instancia, request=None, descricao=None):
    """Registra a criação de um objeto"""
    modelo_nome = instancia._meta.verbose_name.title()
    if descricao is None:
        descricao = f"{modelo_nome} '{str(instancia)}' criado"
    
    # Serializar a instância ANTES de passar para registrar_log_auditoria
    dados_novos = serializer_modelo_para_dict(instancia)
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao='CREATE',
        modelo=instancia._meta.model_name.title(),
        objeto_id=instancia.pk,
        descricao=descricao,
        dados_novos=dados_novos,  # Já serializado
        request=request
        # Não passar instancia_nova pois já serializamos
    )


def registrar_edicao(usuario, instancia_anterior, instancia_nova, request=None, descricao=None):
    """Registra a edição de um objeto"""
    modelo_nome = instancia_nova._meta.verbose_name.title()
    if descricao is None:
        descricao = f"{modelo_nome} '{str(instancia_nova)}' editado"
    
    # Serializar as instâncias ANTES de passar para registrar_log_auditoria
    dados_anteriores = serializer_modelo_para_dict(instancia_anterior)
    dados_novos = serializer_modelo_para_dict(instancia_nova)
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao='UPDATE',
        modelo=instancia_nova._meta.model_name.title(),
        objeto_id=instancia_nova.pk,
        descricao=descricao,
        dados_anteriores=dados_anteriores,  # Já serializado
        dados_novos=dados_novos,  # Já serializado
        request=request
        # Não passar instancia_anterior nem instancia_nova pois já serializamos
    )


def registrar_exclusao(usuario, instancia, request=None, descricao=None, soft_delete=False):
    """Registra a exclusão de um objeto (hard ou soft delete)"""
    modelo_nome = instancia._meta.verbose_name.title()
    acao = 'SOFT_DELETE' if soft_delete else 'DELETE'
    
    if descricao is None:
        tipo = "excluído suavemente" if soft_delete else "excluído permanentemente"
        descricao = f"{modelo_nome} '{str(instancia)}' {tipo}"
    
    # Serializar a instância ANTES de passar para registrar_log_auditoria
    dados_anteriores = serializer_modelo_para_dict(instancia)
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao=acao,
        modelo=instancia._meta.model_name.title(),
        objeto_id=instancia.pk,
        descricao=descricao,
        dados_anteriores=dados_anteriores,  # Já serializado
        request=request
        # Não passar instancia_anterior pois já serializamos
    )


def registrar_restauracao(usuario, instancia, request=None, descricao=None):
    """Registra a restauração de um objeto soft deleted"""
    modelo_nome = instancia._meta.verbose_name.title()
    if descricao is None:
        descricao = f"{modelo_nome} '{str(instancia)}' restaurado"
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao='RESTORE',
        modelo=instancia._meta.model_name.title(),
        objeto_id=instancia.pk,
        descricao=descricao,
        request=request
    )


def registrar_login(usuario, request=None, descricao=None):
    """Registra o login de um usuário"""
    if descricao is None:
        descricao = f"Usuário '{usuario.username}' fez login no sistema"
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao='LOGIN',
        modelo='Usuario',
        objeto_id=usuario.pk,
        descricao=descricao,
        request=request
    )


def registrar_logout(usuario, request=None, descricao=None):
    """Registra o logout de um usuário"""
    if descricao is None:
        descricao = f"Usuário '{usuario.username}' fez logout do sistema"
    
    return registrar_log_auditoria(
        usuario=usuario,
        acao='LOGOUT',
        modelo='Usuario',
        objeto_id=usuario.pk,
        descricao=descricao,
        request=request
    )

