"""
Views de auditoria e logs (apenas administradores).
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator

from ..models import AuditoriaLog, Usuario
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso


@admin_required
def listar_logs_auditoria(request):
    """Lista todos os logs de auditoria"""
    logs = AuditoriaLog.objects.all().select_related('usuario')
    
    modelo_filtro = request.GET.get('modelo', '')
    acao_filtro = request.GET.get('acao', '')
    usuario_filtro = request.GET.get('usuario', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    if modelo_filtro:
        logs = logs.filter(modelo__icontains=modelo_filtro)
    if acao_filtro:
        logs = logs.filter(acao=acao_filtro)
    if usuario_filtro:
        logs = logs.filter(usuario__username__icontains=usuario_filtro)
    data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
    if data_inicio_obj:
        logs = logs.filter(data_hora__date__gte=data_inicio_obj)
    data_fim_obj = parse_date_iso(data_fim) if data_fim else None
    if data_fim_obj:
        logs = logs.filter(data_hora__date__lte=data_fim_obj)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_logs = AuditoriaLog.objects.count()
    acoes_count = AuditoriaLog.objects.values_list('acao', flat=True).distinct()
    modelos_count = AuditoriaLog.objects.values_list('modelo', flat=True).distinct()
    usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'page_obj': page_obj,
        'modelo_filtro': modelo_filtro,
        'acao_filtro': acao_filtro,
        'usuario_filtro': usuario_filtro,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'acoes': AuditoriaLog.ACAO_CHOICES,
        'ACTION_CHOICES': AuditoriaLog.ACAO_CHOICES,
        'total_logs': total_logs,
        'acoes_count': acoes_count,
        'modelos_count': modelos_count,
        'usuarios': usuarios,
        'acao_atual': acao_filtro,
        'modelo_atual': modelo_filtro,
        'usuario_atual': usuario_filtro,
        'data_inicio_atual': data_inicio,
        'data_fim_atual': data_fim,
    }
    return render(request, 'notas/auditoria/listar_logs.html', context)


@admin_required
def detalhes_log_auditoria(request, pk):
    """Exibe os detalhes de um log de auditoria específico"""
    log = get_object_or_404(AuditoriaLog, pk=pk)
    context = {'log': log}
    return render(request, 'notas/auditoria/detalhes_log.html', context)


@admin_required
def listar_registros_excluidos(request):
    """Lista todos os registros que foram excluídos (soft delete)"""
    logs_exclusao = AuditoriaLog.objects.filter(acao='DELETE').select_related('usuario')
    
    modelos_excluidos = {}
    for log in logs_exclusao:
        if log.modelo not in modelos_excluidos:
            modelos_excluidos[log.modelo] = []
        modelos_excluidos[log.modelo].append(log)
    
    context = {'modelos_excluidos': modelos_excluidos}
    return render(request, 'notas/auditoria/registros_excluidos.html', context)


@admin_required
def restaurar_registro(request, modelo, pk):
    """Restaura um registro excluído usando os dados do log de auditoria"""
    from ..utils.auditoria import restaurar_registro as restaurar
    
    try:
        objeto_restaurado = restaurar(modelo, pk, usuario=request.user, request=request)
        
        if objeto_restaurado:
            messages.success(request, f'{modelo} #{objeto_restaurado.pk} restaurado com sucesso!')
        else:
            messages.error(request, f'Não foi possível restaurar {modelo} #{pk}. Log de exclusão não encontrado ou dados inválidos.')
    except Exception as e:
        messages.error(request, f'Erro ao restaurar registro: {str(e)}')
    
    return redirect('notas:listar_registros_excluidos')
