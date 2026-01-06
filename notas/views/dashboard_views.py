"""
Views de Dashboard
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from datetime import datetime, date, timedelta

from ..models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, AgendaEntrega


@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    # Se o usuário for um cliente, redirecionar para o dashboard específico do cliente
    if hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'cliente':
        return dashboard_cliente(request)
    
    # Se o usuário for um funcionário, redirecionar para o dashboard específico do funcionário
    if hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'funcionario':
        return dashboard_funcionario(request)
    
    # Verificar se o usuário tem o atributo is_cliente (método alternativo)
    if hasattr(request.user, 'is_cliente') and request.user.is_cliente:
        return dashboard_cliente(request)
    
    # Estatísticas básicas para o dashboard
    total_notas = NotaFiscal.objects.count()
    total_clientes = Cliente.objects.count()
    total_motoristas = Motorista.objects.count()
    total_veiculos = Veiculo.objects.count()
    total_romaneios = RomaneioViagem.objects.count()
    
    # Notas por status
    notas_deposito = NotaFiscal.objects.filter(status='Depósito').count()
    notas_enviadas = NotaFiscal.objects.filter(status='Enviada').count()
    
    # Valores financeiros
    valor_total_deposito = NotaFiscal.objects.filter(status='Depósito').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    valor_total_enviadas = NotaFiscal.objects.filter(status='Enviada').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Atividade recente (últimos 7 dias)
    data_limite = datetime.now() - timedelta(days=7)
    notas_recentes = NotaFiscal.objects.filter(
        data__gte=data_limite.date()
    ).select_related('cliente').order_by('-data')[:5]
    
    romaneios_recentes = RomaneioViagem.objects.filter(
        data_emissao__gte=data_limite
    ).select_related(
        'cliente', 'motorista', 'veiculo_principal'
    ).prefetch_related('notas_fiscais').order_by('-data_emissao')[:5]
    
    # Top clientes por valor em depósito
    top_clientes_deposito = Cliente.objects.annotate(
        valor_deposito=Sum('notas_fiscais__valor', filter=Q(notas_fiscais__status='Depósito'))
    ).filter(valor_deposito__gt=0).order_by('-valor_deposito')[:5]
    
    # Dados da agenda de entregas
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    now = datetime.now()
    proximas_entregas = AgendaEntrega.objects.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('data_entrega')[:5]
    
    entregas_hoje = AgendaEntrega.objects.filter(
        data_entrega=hoje,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('cliente__razao_social')
    
    # Entregas agendadas para o dashboard (apenas status 'Agendada')
    entregas_agendadas = AgendaEntrega.objects.filter(
        status='Agendada'
    ).select_related('cliente').order_by('data_entrega')[:10]
    
    total_agendadas = AgendaEntrega.objects.filter(status='Agendada').count()
    total_em_andamento = AgendaEntrega.objects.filter(status='Em Andamento').count()
    
    context = {
        'title': 'Dashboard - Agência Estelar',
        'user': request.user,
        
        # Estatísticas gerais
        'total_notas': total_notas,
        'total_clientes': total_clientes,
        'total_motoristas': total_motoristas,
        'total_veiculos': total_veiculos,
        'total_romaneios': total_romaneios,
        
        # Estatísticas por status
        'notas_deposito': notas_deposito,
        'notas_enviadas': notas_enviadas,
        
        # Valores financeiros
        'valor_total_deposito': valor_total_deposito,
        'valor_total_enviadas': valor_total_enviadas,
        
        # Atividade recente
        'notas_recentes': notas_recentes,
        'romaneios_recentes': romaneios_recentes,
        
        # Top clientes
        'top_clientes_deposito': top_clientes_deposito,
        
        # Dados da agenda
        'proximas_entregas': proximas_entregas,
        'entregas_hoje': entregas_hoje,
        'entregas_agendadas': entregas_agendadas,
        'total_agendadas': total_agendadas,
        'total_em_andamento': total_em_andamento,
        'hoje': hoje,
        'now': now,
    }
    return render(request, 'notas/dashboard.html', context)


@login_required
def dashboard_cliente(request):
    """Dashboard específico para clientes"""
    # Verificar se o usuário é um cliente
    if not (hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'cliente'):
        return redirect('notas:dashboard')
    
    # Obter o cliente vinculado ao usuário
    cliente = request.user.cliente
    if not cliente:
        from django.contrib import messages
        messages.error(request, 'Cliente não encontrado. Entre em contato com o administrador.')
        return redirect('notas:login')
    
    # Estatísticas do cliente
    total_notas_cliente = NotaFiscal.objects.filter(cliente=cliente).count()
    notas_deposito_cliente = NotaFiscal.objects.filter(cliente=cliente, status='Depósito').count()
    notas_enviadas_cliente = NotaFiscal.objects.filter(cliente=cliente, status='Enviada').count()
    
    # Valores financeiros do cliente
    valor_total_deposito_cliente = NotaFiscal.objects.filter(
        cliente=cliente, status='Depósito'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    valor_total_enviadas_cliente = NotaFiscal.objects.filter(
        cliente=cliente, status='Enviada'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    # Últimas notas do cliente (últimos 30 dias)
    data_limite = datetime.now() - timedelta(days=30)
    ultimas_notas = NotaFiscal.objects.filter(
        cliente=cliente,
        data__gte=data_limite.date()
    ).select_related('cliente').order_by('-data')[:10]
    
    # Romaneios do cliente (últimos 30 dias)
    romaneios_cliente = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite
    ).select_related(
        'cliente', 'motorista', 'veiculo_principal'
    ).prefetch_related('notas_fiscais').order_by('-data_emissao')[:10]
    
    # Estatísticas de carregamentos (últimos 6 meses)
    data_limite_6_meses = datetime.now() - timedelta(days=180)
    carregamentos_6_meses = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite_6_meses
    ).count()
    
    # Carregamentos por mês (últimos 6 meses)
    carregamentos_por_mes = []
    for i in range(6):
        data_inicio = datetime.now() - timedelta(days=30*i + 30)
        data_fim = datetime.now() - timedelta(days=30*i)
        mes = data_inicio.strftime('%m/%Y')
        
        quantidade = RomaneioViagem.objects.filter(
            cliente=cliente,
            data_emissao__gte=data_inicio,
            data_emissao__lt=data_fim
        ).count()
        
        carregamentos_por_mes.append({
            'mes': mes,
            'quantidade': quantidade
        })
    
    carregamentos_por_mes.reverse()  # Ordenar do mais antigo para o mais recente
    
    # Valor total dos carregamentos (últimos 6 meses)
    valor_total_carregamentos = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite_6_meses
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    
    context = {
        'title': f'Dashboard - {cliente.razao_social}',
        'user': request.user,
        'cliente': cliente,
        
        # Estatísticas do cliente
        'total_notas_cliente': total_notas_cliente,
        'notas_deposito_cliente': notas_deposito_cliente,
        'notas_enviadas_cliente': notas_enviadas_cliente,
        
        # Valores financeiros do cliente
        'valor_total_deposito_cliente': valor_total_deposito_cliente,
        'valor_total_enviadas_cliente': valor_total_enviadas_cliente,
        
        # Atividade recente do cliente
        'ultimas_notas': ultimas_notas,
        'romaneios_cliente': romaneios_cliente,
        
        # Estatísticas de carregamentos
        'carregamentos_6_meses': carregamentos_6_meses,
        'carregamentos_por_mes': carregamentos_por_mes,
        'valor_total_carregamentos': valor_total_carregamentos,
    }
    return render(request, 'notas/dashboard_cliente.html', context)


@login_required
def dashboard_funcionario(request):
    """Dashboard específico para funcionários"""
    # Verificar se o usuário é um funcionário
    if not (hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'funcionario'):
        return redirect('notas:dashboard')
    
    # Estatísticas básicas para funcionários
    total_notas = NotaFiscal.objects.count()
    total_clientes = Cliente.objects.count()
    total_motoristas = Motorista.objects.count()
    total_veiculos = Veiculo.objects.count()
    total_romaneios = RomaneioViagem.objects.count()
    
    # Notas por status
    notas_deposito = NotaFiscal.objects.filter(status='Depósito').count()
    notas_enviadas = NotaFiscal.objects.filter(status='Enviada').count()
    
    # Valores financeiros
    valor_total_notas = NotaFiscal.objects.aggregate(total=Sum('valor'))['total'] or 0
    valor_total_romaneios = RomaneioViagem.objects.aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Atividade recente (últimas 5 notas fiscais)
    notas_recentes = NotaFiscal.objects.select_related('cliente').order_by('-data')[:5]
    
    # Romaneios recentes (últimos 5)
    romaneios_recentes = RomaneioViagem.objects.select_related('cliente', 'motorista').order_by('-data_emissao')[:5]
    
    context = {
        'title': 'Dashboard - Funcionário',
        'user': request.user,
        
        # Estatísticas básicas
        'total_notas': total_notas,
        'total_clientes': total_clientes,
        'total_motoristas': total_motoristas,
        'total_veiculos': total_veiculos,
        'total_romaneios': total_romaneios,
        
        # Estatísticas por status
        'notas_deposito': notas_deposito,
        'notas_enviadas': notas_enviadas,
        
        # Valores financeiros
        'valor_total_notas': valor_total_notas,
        'valor_total_romaneios': valor_total_romaneios,
        
        # Atividade recente
        'notas_recentes': notas_recentes,
        'romaneios_recentes': romaneios_recentes,
    }
    return render(request, 'notas/dashboard_funcionario.html', context)

