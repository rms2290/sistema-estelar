"""
Views AJAX/API para requisições assíncronas
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db.models import Q

from ..models import NotaFiscal, Cliente, RomaneioViagem, Veiculo, OcorrenciaNotaFiscal, FotoOcorrencia
from ..decorators import admin_required


@login_required
def load_notas_fiscais(request):
    """Carrega notas fiscais via AJAX baseado no cliente selecionado"""
    cliente_id = request.GET.get('cliente_id')
    
    if cliente_id:
        notas = NotaFiscal.objects.filter(
            cliente_id=cliente_id,
            status='Depósito'
        ).order_by('nota')
        
        notas_data = [{
            'id': nota.id,
            'nota': nota.nota,
            'valor': str(nota.valor),
            'peso': str(nota.peso),
        } for nota in notas]
        
        return JsonResponse({'notas': notas_data})
    
    return JsonResponse({'notas': []})


@login_required
def load_notas_fiscais_edicao(request):
    """Carrega notas fiscais para edição de romaneio via AJAX"""
    cliente_id = request.GET.get('cliente_id')
    romaneio_id = request.GET.get('romaneio_id')
    
    if not cliente_id:
        return JsonResponse([], safe=False)
    
    try:
        notas = NotaFiscal.objects.filter(cliente_id=cliente_id)
        
        # Se há um romaneio, incluir notas já vinculadas e notas em depósito
        if romaneio_id:
            try:
                romaneio = RomaneioViagem.objects.get(pk=romaneio_id)
                notas = notas.filter(
                    Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
                )
            except RomaneioViagem.DoesNotExist:
                notas = notas.filter(status='Depósito')
        else:
            notas = notas.filter(status='Depósito')
        
        notas = notas.order_by('nota')
        
        # Formato esperado pelo JavaScript: array direto com campos completos
        notas_data = []
        for nota in notas:
            notas_data.append({
                'id': nota.id,
                'nota_numero': nota.nota,
                'fornecedor': nota.fornecedor or '',
                'mercadoria': nota.mercadoria or '',
                'quantidade': str(nota.quantidade) if nota.quantidade else '0',
                'peso': str(nota.peso) if nota.peso else '0',
                'valor': str(nota.valor) if nota.valor else '0',
                'data_emissao': nota.data.strftime('%d/%m/%Y') if nota.data else '',
            })
        
        return JsonResponse(notas_data, safe=False)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao carregar notas fiscais para edição: {str(e)}', exc_info=True)
        return JsonResponse({'error': 'Erro ao carregar notas fiscais'}, status=500)


@login_required
def load_notas_fiscais_para_romaneio(request, cliente_id):
    """Carrega notas fiscais disponíveis para um romaneio"""
    notas = NotaFiscal.objects.filter(
        cliente_id=cliente_id,
        status='Depósito'
    ).order_by('nota')
    
    notas_data = [{
        'id': nota.id,
        'nota': nota.nota,
        'valor': str(nota.valor),
        'peso': str(nota.peso),
    } for nota in notas]
    
    return JsonResponse({'notas': notas_data})


@login_required
def validar_credenciais_admin_ajax(request):
    """Valida credenciais de administrador via AJAX"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            username = data.get('username', '')
            password = data.get('password', '')
            
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_admin:
                return JsonResponse({'valid': True})
            else:
                return JsonResponse({'valid': False, 'message': 'Credenciais inválidas'})
        except json.JSONDecodeError:
            return JsonResponse({'valid': False, 'message': 'Erro ao processar requisição'})
    
    return JsonResponse({'valid': False, 'message': 'Método não permitido'})


@login_required
def filtrar_veiculos_por_composicao(request):
    """Filtra veículos por composição via AJAX"""
    composicao = request.GET.get('composicao', '')
    
    if composicao:
        veiculos = Veiculo.objects.filter(composicao=composicao).order_by('placa')
        
        veiculos_data = [{
            'id': veiculo.id,
            'placa': veiculo.placa,
            'tipo_unidade': veiculo.tipo_unidade,
        } for veiculo in veiculos]
        
        return JsonResponse({'veiculos': veiculos_data})
    
    return JsonResponse({'veiculos': []})


@login_required
def carregar_romaneios_cliente(request, cliente_id):
    """Carrega romaneios de um cliente via AJAX"""
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    romaneios = RomaneioViagem.objects.filter(cliente=cliente).order_by('-data_emissao')[:10]
    
    romaneios_data = [{
        'id': romaneio.id,
        'codigo': romaneio.codigo,
        'data_emissao': romaneio.data_emissao.strftime('%d/%m/%Y'),
        'valor_total': str(romaneio.valor_total),
    } for romaneio in romaneios]
    
    return JsonResponse({'romaneios': romaneios_data})


@login_required
def salvar_ocorrencia_nota_fiscal(request, nota_id):
    """Salva uma ocorrência de nota fiscal via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'}, status=405)
    
    try:
        nota = get_object_or_404(NotaFiscal, pk=nota_id)
        
        # Validar acesso: apenas administradores e funcionários podem registrar ocorrências
        if request.user.is_cliente:
            return JsonResponse({'success': False, 'message': 'Acesso negado. Apenas administradores e funcionários podem registrar ocorrências.'}, status=403)
        
        observacoes = request.POST.get('observacoes', '').strip()
        fotos = request.FILES.getlist('fotos')  # getlist para múltiplos arquivos
        
        if not observacoes and not fotos:
            return JsonResponse({'success': False, 'message': 'Por favor, preencha as observações ou anexe pelo menos uma foto.'})
        
        # Criar ocorrência
        ocorrencia = OcorrenciaNotaFiscal.objects.create(
            nota_fiscal=nota,
            observacoes=observacoes or 'Sem observações',
            usuario_criacao=request.user if request.user.is_authenticated else None
        )
        
        # Criar fotos associadas
        fotos_criadas = []
        for foto in fotos:
            foto_obj = FotoOcorrencia.objects.create(
                ocorrencia=ocorrencia,
                foto=foto
            )
            fotos_criadas.append({
                'id': foto_obj.id,
                'url': foto_obj.foto.url
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Ocorrência registrada com sucesso! {len(fotos_criadas)} foto(s) anexada(s).',
            'ocorrencia': {
                'id': ocorrencia.id,
                'observacoes': ocorrencia.observacoes,
                'fotos': fotos_criadas,
                'data_criacao': ocorrencia.data_criacao.strftime('%d/%m/%Y %H:%M'),
                'usuario': ocorrencia.usuario_criacao.username if ocorrencia.usuario_criacao else 'Sistema',
            }
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Erro ao salvar ocorrência: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'message': f'Erro ao salvar ocorrência: {str(e)}'}, status=500)

