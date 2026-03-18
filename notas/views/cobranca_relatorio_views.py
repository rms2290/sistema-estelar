"""
Views de relatórios de cobrança (cobrança mensal e listagem de cobrança de carregamento).
"""
from django.shortcuts import render
from django.contrib import messages

from ..models import Cliente, CobrancaCarregamento
from ..decorators import admin_required
from ..utils.date_utils import parse_date_iso


@admin_required
def cobranca_mensal(request):
    """View para cobrança mensal"""
    messages.info(request, 'Funcionalidade de cobrança mensal em desenvolvimento')
    return render(request, 'notas/relatorios/cobranca_mensal.html')


@admin_required
def cobranca_carregamento(request):
    """View para listar cobranças de carregamento. Abre sem dados; exibe resultados ao selecionar filtro por status (Pendente/Baixado)."""
    status_filtro = request.GET.get('status')
    if status_filtro not in ('Pendente', 'Baixado'):
        cobrancas = CobrancaCarregamento.objects.none()
    else:
        cobrancas = CobrancaCarregamento.objects.filter(status=status_filtro).select_related('cliente').prefetch_related('romaneios')
        cliente_id = request.GET.get('cliente')
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        if cliente_id:
            cobrancas = cobrancas.filter(cliente_id=cliente_id)
        data_inicio_obj = parse_date_iso(data_inicio) if data_inicio else None
        if data_inicio_obj:
            cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio_obj)
        data_fim_obj = parse_date_iso(data_fim) if data_fim else None
        if data_fim_obj:
            cobrancas = cobrancas.filter(criado_em__date__lte=data_fim_obj)

    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    context = {
        'cobrancas': cobrancas,
        'clientes': clientes,
        'status_filtro': status_filtro,
    }
    return render(request, 'notas/relatorios/cobranca_carregamento.html', context)
