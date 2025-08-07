from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from ..models import Motorista, HistoricoConsulta
from ..forms import MotoristaForm, MotoristaSearchForm, HistoricoConsultaForm

@login_required
def listar_motoristas(request):
    """Lista todos os motoristas com filtros de busca"""
    search_form = MotoristaSearchForm(request.GET)
    motoristas = Motorista.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = Motorista.objects.all()
        nome = search_form.cleaned_data.get('nome')
        cpf = search_form.cleaned_data.get('cpf')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        
        motoristas = queryset.order_by('nome')

    context = {
        'motoristas': motoristas,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_motoristas.html', context)

@login_required
def adicionar_motorista(request):
    """Adiciona um novo motorista"""
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao adicionar o motorista. Verifique os campos.')
    else:
        form = MotoristaForm()
    
    return render(request, 'notas/adicionar_motorista.html', {'form': form})

@login_required
def editar_motorista(request, pk):
    """Edita um motorista existente"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao atualizar o motorista.')
    else:
        form = MotoristaForm(instance=motorista)
    
    return render(request, 'notas/editar_motorista.html', {'form': form, 'motorista': motorista})

@login_required
def excluir_motorista(request, pk):
    """Exclui um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        motorista.delete()
        messages.success(request, 'Motorista excluído com sucesso!')
        return redirect('notas:listar_motoristas')
    
    return render(request, 'notas/confirmar_exclusao_motorista.html', {'motorista': motorista})

@login_required
def detalhes_motorista(request, pk):
    """Mostra os detalhes de um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    historico_consultas = motorista.historico_consultas.all().order_by('-data_consulta')
    
    context = {
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/detalhes_motorista.html', context)

@login_required
def adicionar_historico_consulta(request, pk):
    """Adiciona histórico de consulta para um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.motorista = motorista
            consulta.save()
            
            # Atualizar número da consulta no motorista
            motorista.numero_consulta = consulta.numero_consulta
            motorista.save()
            
            messages.success(request, 'Histórico de consulta adicionado com sucesso!')
            return redirect('notas:detalhes_motorista', pk=pk)
        else:
            messages.error(request, 'Houve um erro ao adicionar o histórico de consulta.')
    else:
        form = HistoricoConsultaForm()
    
    context = {
        'form': form,
        'motorista': motorista,
    }
    return render(request, 'notas/adicionar_historico_consulta.html', context)

@login_required
def registrar_consulta_motorista(request, pk):
    """Registra uma nova consulta para um motorista"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.motorista = motorista
            consulta.save()
            
            # Atualizar número da consulta no motorista
            motorista.numero_consulta = consulta.numero_consulta
            motorista.save()
            
            messages.success(request, 'Consulta registrada com sucesso!')
            return redirect('notas:detalhes_motorista', pk=pk)
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta.')
    else:
        form = HistoricoConsultaForm()
    
    context = {
        'form': form,
        'motorista': motorista,
    }
    return render(request, 'notas/registrar_consulta_motorista.html', context) 