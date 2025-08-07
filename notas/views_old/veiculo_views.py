from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import Veiculo
from ..forms import VeiculoForm, VeiculoSearchForm

@login_required
def listar_veiculos(request):
    """Lista todos os veículos com filtros de busca"""
    search_form = VeiculoSearchForm(request.GET)
    veiculos = Veiculo.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = Veiculo.objects.all()
        placa = search_form.cleaned_data.get('placa')
        chassi = search_form.cleaned_data.get('chassi')
        proprietario_nome = search_form.cleaned_data.get('proprietario_nome')
        tipo_unidade = search_form.cleaned_data.get('tipo_unidade')
        
        if placa:
            queryset = queryset.filter(placa__icontains=placa)
        if chassi:
            queryset = queryset.filter(chassi__icontains=chassi)
        if proprietario_nome:
            queryset = queryset.filter(proprietario_nome_razao_social__icontains=proprietario_nome)
        if tipo_unidade:
            queryset = queryset.filter(tipo_unidade=tipo_unidade)
        
        veiculos = queryset.order_by('placa')
    
    context = {
        'veiculos': veiculos,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_veiculos.html', context)

@login_required
def adicionar_veiculo(request):
    """Adiciona um novo veículo"""
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
            return redirect('notas:listar_veiculos')
        else:
            messages.error(request, 'Houve um erro ao adicionar o veículo. Verifique os campos.')
    else:
        form = VeiculoForm()
    
    return render(request, 'notas/adicionar_veiculo.html', {'form': form})

@login_required
def editar_veiculo(request, pk):
    """Edita um veículo existente"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    if request.method == 'POST':
        form = VeiculoForm(request.POST, instance=veiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
            return redirect('notas:listar_veiculos')
        else:
            messages.error(request, 'Houve um erro ao atualizar o veículo.')
    else:
        form = VeiculoForm(instance=veiculo)
    
    return render(request, 'notas/editar_veiculo.html', {'form': form, 'veiculo': veiculo})

@login_required
def excluir_veiculo(request, pk):
    """Exclui um veículo"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    if request.method == 'POST':
        veiculo.delete()
        messages.success(request, 'Veículo excluído com sucesso!')
        return redirect('notas:listar_veiculos')
    
    return render(request, 'notas/confirmar_exclusao_veiculo.html', {'veiculo': veiculo})

@login_required
def detalhes_veiculo(request, pk):
    """Mostra os detalhes de um veículo"""
    veiculo = get_object_or_404(Veiculo, pk=pk)
    return render(request, 'notas/detalhes_veiculo.html', {'veiculo': veiculo}) 