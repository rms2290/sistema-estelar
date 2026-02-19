"""
Views API para Fechamento de Frete
"""
import logging
from sistema_estelar.api_utils import json_success, json_error
from django.db.models import Sum, Q
from datetime import datetime
from ..models import RomaneioViagem, Cliente
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso

logger = logging.getLogger(__name__)


@admin_required
def carregar_dados_romaneios(request):
    """
    API para carregar dados de múltiplos romaneios
    
    Parâmetros GET:
        - romaneios_ids: Lista de IDs de romaneios separados por vírgula
    
    Retorna:
        - motorista: Dados do motorista (primeiro romaneio)
        - data: Data (primeiro romaneio)
        - clientes: Lista de clientes com seus dados consolidados
        - romaneios: Lista de romaneios com detalhes
    """
    romaneios_ids = request.GET.get('romaneios_ids', '')
    
    if not romaneios_ids:
        return json_error('Nenhum romaneio selecionado', status=400)
    
    try:
        ids_list = [int(id.strip()) for id in romaneios_ids.split(',') if id.strip()]
        
        if not ids_list:
            return json_error('IDs inválidos', status=400)
        
        romaneios = RomaneioViagem.objects.filter(
            pk__in=ids_list,
            status='Emitido'
        ).select_related('motorista', 'cliente').prefetch_related('notas_fiscais')
        
        if not romaneios.exists():
            return json_error('Nenhum romaneio encontrado', status=404)
        
        # Dados gerais (do primeiro romaneio)
        primeiro_romaneio = romaneios.first()
        motorista_data = {
            'id': primeiro_romaneio.motorista.pk,
            'nome': primeiro_romaneio.motorista.nome
        }
        
        data_emissao = primeiro_romaneio.data_emissao.date() if primeiro_romaneio.data_emissao else None
        
        # Agrupar por cliente
        clientes_data = {}
        romaneios_data = []
        
        for romaneio in romaneios:
            cliente_id = romaneio.cliente.pk
            cliente_nome = romaneio.cliente.razao_social
            
            # Dados do romaneio
            romaneio_info = {
                'id': romaneio.pk,
                'codigo': romaneio.codigo,
                'cliente_id': cliente_id,
                'cliente_nome': cliente_nome,
                'peso_total': float(romaneio.peso_total or 0),
                'valor_total': float(romaneio.valor_total or 0),
                'data_emissao': romaneio.data_emissao.date().strftime('%d/%m/%Y') if romaneio.data_emissao else None
            }
            romaneios_data.append(romaneio_info)
            
            # Agrupar por cliente (inicialmente por ID)
            if cliente_id not in clientes_data:
                clientes_data[cliente_id] = {
                    'cliente_id': cliente_id,
                    'cliente_nome': cliente_nome,
                    'romaneios': [],
                    'peso_total': 0,
                    'valor_total': 0,
                    'quantidade_romaneios': 0
                }
            
            clientes_data[cliente_id]['romaneios'].append(romaneio_info)
            clientes_data[cliente_id]['peso_total'] += romaneio_info['peso_total']
            clientes_data[cliente_id]['valor_total'] += romaneio_info['valor_total']
            clientes_data[cliente_id]['quantidade_romaneios'] += 1
        
        # Converter para lista
        clientes_list = []
        for cliente_id, dados in clientes_data.items():
            clientes_list.append({
                'cliente_id': dados['cliente_id'],
                'cliente_nome': dados['cliente_nome'],
                'peso_total': dados['peso_total'],
                'valor_total': dados['valor_total'],
                'quantidade_romaneios': dados['quantidade_romaneios'],
                'romaneios': dados['romaneios']
            })
        
        # Totais gerais
        totais = {
            'peso_total': sum(c['peso_total'] for c in clientes_list),
            'valor_total': sum(c['valor_total'] for c in clientes_list),
            'quantidade_clientes': len(clientes_list),
            'quantidade_romaneios': len(romaneios_data)
        }
        
        return json_success(
            motorista=motorista_data,
            data=data_emissao.strftime('%Y-%m-%d') if data_emissao else None,
            clientes=clientes_list,
            romaneios=romaneios_data,
            totais=totais,
        )
        
    except Exception as e:
        logger.error('Erro ao carregar dados dos romaneios: %s', str(e), exc_info=True)
        return json_error('Erro ao processar', status=500)


@admin_required
def carregar_mais_romaneios(request):
    """
    API para carregar mais romaneios (scroll infinito)
    
    Parâmetros GET:
        - offset: Número de romaneios já carregados
        - limit: Quantidade de romaneios para carregar (padrão: 10)
    
    Retorna:
        - romaneios: Lista de romaneios
        - has_more: Se há mais romaneios para carregar
    """
    try:
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))
        
        romaneios = RomaneioViagem.objects.filter(
            status='Emitido'
        ).select_related('cliente', 'motorista').order_by('-data_emissao', '-id')[offset:offset + limit]
        
        romaneios_data = []
        for romaneio in romaneios:
            romaneios_data.append({
                'id': romaneio.pk,
                'codigo': romaneio.codigo,
                'cliente_nome': romaneio.cliente.razao_social,
                'cliente_id': romaneio.cliente.pk,
                'data_emissao': romaneio.data_emissao.date().strftime('%d/%m/%Y') if romaneio.data_emissao else None,
                'data': romaneio.data_emissao.date().strftime('%Y-%m-%d') if romaneio.data_emissao else None,
                'motorista_nome': romaneio.motorista.nome if romaneio.motorista else '',
                'motorista_id': romaneio.motorista.pk if romaneio.motorista else None,
                'peso_total': float(romaneio.peso_total or 0),
                'valor_total': float(romaneio.valor_total or 0),
            })
        
        # Verificar se há mais romaneios
        total_romaneios = RomaneioViagem.objects.filter(status='Emitido').count()
        has_more = (offset + limit) < total_romaneios
        
        return json_success(
            romaneios=romaneios_data,
            has_more=has_more,
            offset=offset + len(romaneios_data),
        )
        
    except Exception as e:
        logger.error('Erro ao carregar mais romaneios: %s', str(e), exc_info=True)
        return json_error('Erro ao processar', status=500)


@admin_required
def buscar_clientes_ativos(request):
    """
    API para buscar clientes ativos (para modal de seleção)
    
    Parâmetros GET:
        - busca: Termo de busca (opcional)
    
    Retorna:
        - clientes: Lista de clientes ativos
    """
    try:
        busca = request.GET.get('busca', '').strip()
        
        clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
        
        if busca:
            clientes = clientes.filter(
                Q(razao_social__icontains=busca) |
                Q(nome_fantasia__icontains=busca) |
                Q(cnpj__icontains=busca)
            )
        
        clientes_data = []
        for cliente in clientes[:100]:  # Limitar a 100 resultados
            clientes_data.append({
                'id': cliente.pk,
                'razao_social': cliente.razao_social,
                'nome_fantasia': cliente.nome_fantasia or '',
                'cnpj': cliente.cnpj or '',
                'cidade': cliente.cidade or '',
                'estado': cliente.estado or '',
            })
        
        return json_success(
            clientes=clientes_data,
            total=len(clientes_data),
        )
        
    except Exception as e:
        logger.error('Erro ao buscar clientes: %s', str(e), exc_info=True)
        return json_error('Erro ao processar', status=500)


@admin_required
def buscar_romaneios_filtrados(request):
    """
    API para buscar romaneios com filtros (para modal de seleção)
    
    Parâmetros GET:
        - data_inicio: Data inicial (opcional)
        - data_fim: Data final (opcional)
        - cliente_id: ID do cliente (opcional)
        - motorista_id: ID do motorista (opcional)
        - busca: Termo de busca (código do romaneio) (opcional)
        - offset: Offset para paginação (opcional)
        - limit: Limite de resultados (padrão: 50)
    
    Retorna:
        - romaneios: Lista de romaneios
        - total: Total de romaneios encontrados
        - has_more: Se há mais romaneios
    """
    try:
        data_inicio = request.GET.get('data_inicio', '')
        data_fim = request.GET.get('data_fim', '')
        cliente_id = request.GET.get('cliente_id', '')
        motorista_id = request.GET.get('motorista_id', '')
        busca = request.GET.get('busca', '').strip()
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 50))
        
        romaneios = RomaneioViagem.objects.filter(status='Emitido').select_related(
            'cliente', 'motorista'
        )
        
        # Aplicar filtros
        data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
        if data_inicio_obj:
            romaneios = romaneios.filter(data_emissao__date__gte=data_inicio_obj)
        
        data_fim_obj = parse_date_iso(data_fim) if data_fim else None
        if data_fim_obj:
            romaneios = romaneios.filter(data_emissao__date__lte=data_fim_obj)
        
        if cliente_id:
            try:
                romaneios = romaneios.filter(cliente_id=int(cliente_id))
            except ValueError:
                pass
        
        if motorista_id:
            try:
                romaneios = romaneios.filter(motorista_id=int(motorista_id))
            except ValueError:
                pass
        
        if busca:
            romaneios = romaneios.filter(codigo__icontains=busca)
        
        # Contar total antes de aplicar offset/limit
        total = romaneios.count()
        
        # Ordenar e aplicar paginação
        romaneios = romaneios.order_by('-data_emissao', '-id')[offset:offset + limit]
        
        romaneios_data = []
        for romaneio in romaneios:
            romaneios_data.append({
                'id': romaneio.pk,
                'codigo': romaneio.codigo,
                'cliente_id': romaneio.cliente.pk,
                'cliente_nome': romaneio.cliente.razao_social,
                'motorista_id': romaneio.motorista.pk if romaneio.motorista else None,
                'motorista_nome': romaneio.motorista.nome if romaneio.motorista else '',
                'data_emissao': romaneio.data_emissao.date().strftime('%d/%m/%Y') if romaneio.data_emissao else None,
                'data': romaneio.data_emissao.date().strftime('%Y-%m-%d') if romaneio.data_emissao else None,
                'peso_total': float(romaneio.peso_total or 0),
                'valor_total': float(romaneio.valor_total or 0),
            })
        
        has_more = (offset + limit) < total
        
        return json_success(
            romaneios=romaneios_data,
            total=total,
            has_more=has_more,
            offset=offset + len(romaneios_data),
        )
        
    except Exception as e:
        logger.error('Erro ao buscar romaneios: %s', str(e), exc_info=True)
        return json_error('Erro ao processar', status=500)
