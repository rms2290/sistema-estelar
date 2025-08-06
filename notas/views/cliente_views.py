from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import Cliente
from ..forms import ClienteForm, ClienteSearchForm

@login_required
def listar_clientes(request):
    """Lista todos os clientes com filtros de busca"""
    search_form = ClienteSearchForm(request.GET)
    clientes = Cliente.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = Cliente.objects.all()
        razao_social = search_form.cleaned_data.get('razao_social')
        cnpj = search_form.cleaned_data.get('cnpj')
        status = search_form.cleaned_data.get('status')

        if razao_social:
            queryset = queryset.filter(razao_social__icontains=razao_social)
        if cnpj:
            queryset = queryset.filter(cnpj__icontains=cnpj)
        if status:
            queryset = queryset.filter(status=status)
        
        clientes = queryset.order_by('razao_social')
    
    context = {
        'clientes': clientes,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_clientes.html', context)

@login_required
def adicionar_cliente(request):
    """Adiciona um novo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente adicionado com sucesso!')
            return redirect('notas:listar_clientes')
        else:
            messages.error(request, 'Houve um erro ao adicionar o cliente. Verifique os campos.')
    else:
        form = ClienteForm()
    
    return render(request, 'notas/adicionar_cliente.html', {'form': form})

@login_required
def editar_cliente(request, pk):
    """Edita um cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('notas:listar_clientes')
        else:
            messages.error(request, 'Houve um erro ao atualizar o cliente.')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'notas/editar_cliente.html', {'form': form, 'cliente': cliente})

@login_required
def excluir_cliente(request, pk):
    """Exclui um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente excluído com sucesso!')
        return redirect('notas:listar_clientes')
    
    return render(request, 'notas/confirmar_exclusao_cliente.html', {'cliente': cliente})

@login_required
def detalhes_cliente(request, pk):
    """Mostra os detalhes de um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'notas/detalhes_cliente.html', {'cliente': cliente}) 