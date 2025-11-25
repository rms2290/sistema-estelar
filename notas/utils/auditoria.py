"""
Utilitários para registrar logs de auditoria no sistema
"""
import json
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import models
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
                # Remover limite para garantir que todos os relacionamentos sejam salvos
                dados[field_name] = [obj.pk for obj in related_objects]
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
        observacoes=descricao,  # Usar observacoes ao invés de descricao
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


def restaurar_registro(modelo, objeto_id, usuario=None, request=None):
    """
    Restaura um registro excluído usando os dados do log de auditoria
    
    Parâmetros:
    - modelo: Nome do modelo (ex: 'NotaFiscal', 'Cliente')
    - objeto_id: ID do objeto a ser restaurado
    - usuario: Usuário que está restaurando (opcional)
    - request: Request para registrar na auditoria (opcional)
    
    Retorna:
    - Instância do modelo restaurado ou None se não foi possível restaurar
    """
    from ..models import (
        NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem,
        HistoricoConsulta, TabelaSeguro, AgendaEntrega, CobrancaCarregamento
    )
    
    # Mapear nomes de modelos para classes
    MODELOS_DISPONIVEIS = {
        'NotaFiscal': NotaFiscal,
        'Notafiscal': NotaFiscal,  # Variante
        'Cliente': Cliente,
        'Motorista': Motorista,
        'Veiculo': Veiculo,
        'Veículo': Veiculo,  # Variante
        'RomaneioViagem': RomaneioViagem,
        'Romaneioviagem': RomaneioViagem,  # Variante (com 'i' minúsculo)
        'Romaneio': RomaneioViagem,  # Variante
        'HistoricoConsulta': HistoricoConsulta,
        'TabelaSeguro': TabelaSeguro,
        'AgendaEntrega': AgendaEntrega,
        'CobrancaCarregamento': CobrancaCarregamento,
    }
    
    # Normalizar nome do modelo - tentar diferentes variações
    modelo_lower = modelo.lower()
    
    # Mapear variações comuns para o nome correto
    variacoes_modelos = {
        'romaneioviagem': 'RomaneioViagem',
        'romaneio': 'RomaneioViagem',
        'notafiscal': 'NotaFiscal',
        'nota_fiscal': 'NotaFiscal',
        'veiculo': 'Veiculo',
        'veículo': 'Veiculo',
        'historicoconsulta': 'HistoricoConsulta',
        'historico_consulta': 'HistoricoConsulta',
        'tabelaseguro': 'TabelaSeguro',
        'tabela_seguro': 'TabelaSeguro',
        'agendaentrega': 'AgendaEntrega',
        'agenda_entrega': 'AgendaEntrega',
        'cobrancacarregamento': 'CobrancaCarregamento',
        'cobranca_carregamento': 'CobrancaCarregamento',
    }
    
    # Tentar encontrar o modelo correto
    modelo_normalizado = variacoes_modelos.get(modelo_lower)
    if not modelo_normalizado:
        # Tentar title() primeiro
        modelo_normalizado = modelo.title()
        if modelo_normalizado not in MODELOS_DISPONIVEIS:
            # Tentar encontrar por similaridade (case-insensitive)
            for key in MODELOS_DISPONIVEIS.keys():
                if key.lower() == modelo_lower:
                    modelo_normalizado = key
                    break
            else:
                raise ValueError(f"Modelo '{modelo}' não suportado para restauração")
    
    ModeloClasse = MODELOS_DISPONIVEIS[modelo_normalizado]
    
    # Buscar log de exclusão - usar busca case-insensitive e flexível
    # Primeiro tentar com o modelo normalizado
    log_exclusao = AuditoriaLog.objects.filter(
        modelo__iexact=modelo_normalizado,
        objeto_id=objeto_id,
        acao='DELETE'
    ).order_by('-data_hora').first()
    
    # Se não encontrou, tentar buscar por qualquer variação do nome do modelo
    if not log_exclusao:
        # Buscar por qualquer variação case-insensitive do modelo
        log_exclusao = AuditoriaLog.objects.filter(
            modelo__iexact=modelo_lower,
            objeto_id=objeto_id,
            acao='DELETE'
        ).order_by('-data_hora').first()
    
    # Se ainda não encontrou, buscar qualquer log DELETE para este objeto_id
    if not log_exclusao:
        log_exclusao = AuditoriaLog.objects.filter(
            objeto_id=objeto_id,
            acao='DELETE'
        ).order_by('-data_hora').first()
        
        if log_exclusao:
            # Usar o modelo do log encontrado e tentar normalizar
            modelo_do_log = log_exclusao.modelo
            modelo_do_log_lower = modelo_do_log.lower()
            modelo_correto = variacoes_modelos.get(modelo_do_log_lower)
            if modelo_correto and modelo_correto in MODELOS_DISPONIVEIS:
                modelo_normalizado = modelo_correto
                ModeloClasse = MODELOS_DISPONIVEIS[modelo_normalizado]
    
    if not log_exclusao:
        raise ValueError(f"Log de exclusão não encontrado para {modelo} #{objeto_id}. Verifique se o registro foi excluído com o sistema de auditoria ativo.")
    
    if not log_exclusao.dados_anteriores:
        raise ValueError(f"Dados anteriores não disponíveis no log de exclusão")
    
    # Verificar se o objeto já existe pelo ID (não foi realmente excluído)
    try:
        objeto_existente = ModeloClasse.objects.get(pk=objeto_id)
        # Se já existe, não precisa restaurar
        return objeto_existente
    except ModeloClasse.DoesNotExist:
        pass
    
    # Restaurar o objeto usando os dados do log
    dados = log_exclusao.dados_anteriores.copy()
    
    # Remover campos que não devem ser definidos diretamente
    campos_remover = ['id', 'pk', 'criado_em', 'atualizado_em', 'data_hora']
    dados_limpos = {k: v for k, v in dados.items() if k not in campos_remover}
    
    # Verificar e tratar campos únicos que podem já existir
    # Para RomaneioViagem, verificar se o código já existe
    if modelo_normalizado == 'RomaneioViagem' and 'codigo' in dados_limpos:
        codigo_original = dados_limpos.get('codigo')
        if codigo_original and ModeloClasse.objects.filter(codigo=codigo_original).exists():
            # Código já existe, remover para que seja gerado um novo automaticamente
            dados_limpos.pop('codigo')
    
    # Verificar outros campos únicos que podem causar problemas
    # Verificar campos unique no modelo
    for field in ModeloClasse._meta.fields:
        if field.unique and field.name in dados_limpos and field.name != 'id':
            valor = dados_limpos[field.name]
            if valor and ModeloClasse.objects.filter(**{field.name: valor}).exists():
                # Campo único já existe, remover para evitar conflito
                # O sistema pode gerar um novo valor ou o usuário precisará ajustar manualmente
                dados_limpos.pop(field.name)
    
    # Separar campos ManyToMany ANTES de processar outros campos
    dados_manytomany = {}
    for field in ModeloClasse._meta.many_to_many:
        if field.name in dados_limpos:
            ids_relacionados = dados_limpos.pop(field.name)
            if isinstance(ids_relacionados, list):
                dados_manytomany[field.name] = ids_relacionados
            elif isinstance(ids_relacionados, str) and ids_relacionados.startswith('[') and ids_relacionados.endswith(']'):
                # Tentar parsear se estiver como string
                try:
                    import ast
                    ids_relacionados = ast.literal_eval(ids_relacionados)
                    if isinstance(ids_relacionados, list):
                        dados_manytomany[field.name] = ids_relacionados
                except:
                    pass
    
    # Tratar campos especiais
    for field in ModeloClasse._meta.fields:
        if field.name not in dados_limpos:
            continue
            
        # Tratar ForeignKey
        if isinstance(field, models.ForeignKey):
            valor = dados_limpos[field.name]
            if isinstance(valor, dict) and 'id' in valor:
                dados_limpos[field.name + '_id'] = valor['id']
                del dados_limpos[field.name]
            elif isinstance(valor, int):
                dados_limpos[field.name + '_id'] = valor
                del dados_limpos[field.name]
        
        # Tratar campos de data
        elif isinstance(field, (models.DateField, models.DateTimeField)):
            valor = dados_limpos[field.name]
            if isinstance(valor, str):
                try:
                    from datetime import datetime
                    # Tentar parsear a data usando fromisoformat (Python 3.7+)
                    if 'T' in valor or ' ' in valor:
                        # DateTime
                        try:
                            # Tentar formato ISO primeiro
                            parsed = datetime.fromisoformat(valor.replace('Z', '+00:00'))
                        except:
                            # Tentar outros formatos comuns
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                                try:
                                    parsed = datetime.strptime(valor, fmt)
                                    break
                                except:
                                    continue
                            else:
                                raise ValueError("Formato de data não reconhecido")
                        
                        if isinstance(field, models.DateTimeField):
                            dados_limpos[field.name] = parsed
                        else:
                            dados_limpos[field.name] = parsed.date()
                    else:
                        # Date apenas
                        try:
                            parsed = datetime.fromisoformat(valor)
                        except:
                            # Tentar formato de data simples
                            try:
                                parsed = datetime.strptime(valor, '%Y-%m-%d')
                            except:
                                raise ValueError("Formato de data não reconhecido")
                        dados_limpos[field.name] = parsed.date() if isinstance(field, models.DateField) else parsed
                except Exception as e:
                    # Se não conseguir converter, usar None se permitido
                    if field.null or field.blank:
                        dados_limpos[field.name] = None
                    else:
                        # Se campo obrigatório, tentar usar data atual
                        from django.utils import timezone
                        if isinstance(field, models.DateTimeField):
                            dados_limpos[field.name] = timezone.now()
                        else:
                            dados_limpos[field.name] = timezone.now().date()
        
        # Tratar Decimal
        elif isinstance(field, models.DecimalField):
            valor = dados_limpos[field.name]
            if isinstance(valor, (int, float)):
                from decimal import Decimal
                dados_limpos[field.name] = Decimal(str(valor))
    
    # Verificar constraints UNIQUE antes de criar para evitar violação
    objeto_existente_unique = None
    try:
        # Verificar constraints únicas do modelo
        for constraint in ModeloClasse._meta.constraints:
            if isinstance(constraint, models.UniqueConstraint):
                # Construir filtro com os campos da constraint
                filtro_unique = {}
                todos_campos_presentes = True
                for campo_constraint in constraint.fields:
                    # Verificar se o campo está nos dados limpos
                    # Para ForeignKey, a constraint usa o nome do campo (ex: 'cliente'),
                    # mas nos dados limpos temos _id (ex: 'cliente_id')
                    valor_campo = None
                    
                    # Tentar primeiro com o nome exato da constraint
                    if campo_constraint in dados_limpos:
                        valor_campo = dados_limpos[campo_constraint]
                    # Se não encontrou, tentar com _id (para ForeignKey)
                    elif campo_constraint + '_id' in dados_limpos:
                        valor_campo = dados_limpos[campo_constraint + '_id']
                    # Verificar se é um campo ForeignKey e tentar obter o ID do objeto relacionado
                    else:
                        # Verificar se há um campo ForeignKey com esse nome
                        try:
                            field_obj = ModeloClasse._meta.get_field(campo_constraint)
                            if isinstance(field_obj, models.ForeignKey):
                                # Tentar buscar pelo campo relacionado
                                campo_id = campo_constraint + '_id'
                                if campo_id in dados_limpos:
                                    valor_campo = dados_limpos[campo_id]
                        except:
                            pass
                    
                    if valor_campo is not None:
                        # Usar o nome do campo original da constraint para o filtro ORM
                        # O Django aceita tanto 'cliente' quanto 'cliente_id' no filtro
                        filtro_unique[campo_constraint] = valor_campo
                    else:
                        todos_campos_presentes = False
                        break
                
                # Se todos os campos da constraint estão presentes, verificar se já existe
                if todos_campos_presentes and filtro_unique:
                    try:
                        objeto_existente_unique = ModeloClasse.objects.get(**filtro_unique)
                        # Se encontrou, usar esse objeto ao invés de criar um novo
                        # Restaurar ManyToMany se necessário
                        if dados_manytomany:
                            for field_name, ids_relacionados in dados_manytomany.items():
                                if isinstance(ids_relacionados, list) and ids_relacionados:
                                    ids_validos = []
                                    for id_val in ids_relacionados:
                                        if id_val is not None:
                                            try:
                                                related_model = ModeloClasse._meta.get_field(field_name).related_model
                                                if related_model.objects.filter(pk=id_val).exists():
                                                    ids_validos.append(id_val)
                                            except:
                                                ids_validos.append(id_val)
                                    if ids_validos:
                                        getattr(objeto_existente_unique, field_name).set(ids_validos)
                        
                        # Registrar a restauração na auditoria
                        if usuario and request:
                            registrar_restauracao(
                                usuario=usuario,
                                instancia=objeto_existente_unique,
                                request=request
                            )
                        
                        return objeto_existente_unique
                    except ModeloClasse.DoesNotExist:
                        pass
                    except ModeloClasse.MultipleObjectsReturned:
                        # Se houver múltiplos, pegar o primeiro
                        objeto_existente_unique = ModeloClasse.objects.filter(**filtro_unique).first()
                        if objeto_existente_unique:
                            if dados_manytomany:
                                for field_name, ids_relacionados in dados_manytomany.items():
                                    if isinstance(ids_relacionados, list) and ids_relacionados:
                                        ids_validos = [id_val for id_val in ids_relacionados if id_val is not None]
                                        if ids_validos:
                                            getattr(objeto_existente_unique, field_name).set(ids_validos)
                            if usuario and request:
                                registrar_restauracao(
                                    usuario=usuario,
                                    instancia=objeto_existente_unique,
                                    request=request
                                )
                            return objeto_existente_unique
                    break  # Se encontrou uma constraint e verificou, não precisa verificar outras
    except Exception as e:
        # Se houver erro ao verificar constraints, continuar e tentar criar
        # Mas vamos usar get_or_create para evitar violação de constraint
        pass
    
    # Criar o objeto (sem ManyToMany)
    # Usar get_or_create para evitar violação de constraint se a verificação anterior falhou
    try:
        # Tentar criar normalmente primeiro
        objeto_restaurado = ModeloClasse.objects.create(**dados_limpos)
    except Exception as create_error:
        # Se falhar por constraint UNIQUE, tentar buscar o objeto existente
        error_str = str(create_error)
        if 'UNIQUE constraint' in error_str or 'unique' in error_str.lower():
            # Tentar buscar usando os campos principais
            try:
                # Para NotaFiscal, usar os campos da constraint
                if modelo_normalizado == 'NotaFiscal':
                    filtro_fallback = {}
                    if 'nota' in dados_limpos:
                        filtro_fallback['nota'] = dados_limpos['nota']
                    # Para ForeignKey, usar o nome do campo sem _id no filtro ORM
                    if 'cliente_id' in dados_limpos:
                        filtro_fallback['cliente'] = dados_limpos['cliente_id']  # Usar 'cliente' no filtro
                    elif 'cliente' in dados_limpos:
                        filtro_fallback['cliente'] = dados_limpos['cliente']
                    if 'mercadoria' in dados_limpos:
                        filtro_fallback['mercadoria'] = dados_limpos['mercadoria']
                    if 'quantidade' in dados_limpos:
                        filtro_fallback['quantidade'] = dados_limpos['quantidade']
                    if 'peso' in dados_limpos:
                        filtro_fallback['peso'] = dados_limpos['peso']
                    
                    if filtro_fallback:
                        objeto_restaurado = ModeloClasse.objects.filter(**filtro_fallback).first()
                        if objeto_restaurado:
                            # Restaurar ManyToMany
                            if dados_manytomany:
                                for field_name, ids_relacionados in dados_manytomany.items():
                                    if isinstance(ids_relacionados, list) and ids_relacionados:
                                        ids_validos = [id_val for id_val in ids_relacionados if id_val is not None]
                                        if ids_validos:
                                            getattr(objeto_restaurado, field_name).set(ids_validos)
                            
                            # Registrar restauração
                            if usuario and request:
                                registrar_restauracao(
                                    usuario=usuario,
                                    instancia=objeto_restaurado,
                                    request=request
                                )
                            
                            return objeto_restaurado
                
                # Se não encontrou, relançar o erro original
                raise create_error
            except:
                raise create_error
        else:
            raise create_error
        
        # Restaurar relacionamentos ManyToMany após criar o objeto
        for field_name, ids_relacionados in dados_manytomany.items():
            if isinstance(ids_relacionados, list) and ids_relacionados:
                # Filtrar IDs válidos e verificar se existem
                ids_validos = []
                try:
                    # Obter o modelo relacionado
                    related_field = ModeloClasse._meta.get_field(field_name)
                    related_model = related_field.related_model
                    
                    for id_val in ids_relacionados:
                        if id_val is not None:
                            # Verificar se o objeto relacionado existe
                            try:
                                if related_model.objects.filter(pk=id_val).exists():
                                    ids_validos.append(id_val)
                            except Exception as e:
                                # Se houver erro, tentar mesmo assim (pode ser problema de tipo)
                                try:
                                    ids_validos.append(int(id_val))
                                except:
                                    pass
                    
                    # Restaurar os relacionamentos ManyToMany
                    if ids_validos:
                        try:
                            getattr(objeto_restaurado, field_name).set(ids_validos)
                        except Exception as e:
                            # Se falhar, tentar adicionar um por um
                            manytomany_field = getattr(objeto_restaurado, field_name)
                            manytomany_field.clear()
                            for id_val in ids_validos:
                                try:
                                    related_obj = related_model.objects.get(pk=id_val)
                                    manytomany_field.add(related_obj)
                                except related_model.DoesNotExist:
                                    pass
                                except Exception as e2:
                                    # Log do erro mas continua
                                    pass
                except Exception as e:
                    # Se houver erro ao obter o campo, tentar método alternativo
                    try:
                        # Tentar usar o nome do campo diretamente
                        manytomany_manager = getattr(objeto_restaurado, field_name)
                        manytomany_manager.set(ids_relacionados)
                    except:
                        pass
        
        # Registrar a restauração na auditoria
        if usuario and request:
            registrar_restauracao(
                usuario=usuario,
                instancia=objeto_restaurado,
                request=request
            )
        
        return objeto_restaurado
        
    except Exception as e:
        raise Exception(f"Erro ao restaurar {modelo_normalizado} #{objeto_id}: {str(e)}")

