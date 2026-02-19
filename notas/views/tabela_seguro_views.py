"""
Views da tabela de seguros por estado (apenas administradores).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from sistema_estelar.api_utils import json_success, json_error
from ..models import TabelaSeguro
from ..forms import TabelaSeguroForm
from ..decorators import admin_required


@admin_required
def listar_tabela_seguros(request):
    """Lista todos os registros da tabela de seguros"""
    tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    if not tabela_seguros.exists():
        for estado_uf, estado_nome in TabelaSeguro.ESTADOS_BRASIL:
            TabelaSeguro.objects.create(
                estado=estado_uf,
                percentual_seguro=0.0,
            )
        tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    context = {
        'tabela_seguros': tabela_seguros,
    }
    return render(request, 'notas/listar_tabela_seguros.html', context)


@admin_required
def editar_tabela_seguro(request, pk):
    """Edita um registro específico da tabela de seguros"""
    tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
    
    if request.method == 'POST':
        form = TabelaSeguroForm(request.POST, instance=tabela_seguro)
        if form.is_valid():
            form.save()
            messages.success(request, f'Percentual de seguro para {tabela_seguro.get_estado_display()} atualizado com sucesso!')
            return redirect('notas:listar_tabela_seguros')
        else:
            messages.error(request, 'Houve um erro ao atualizar o percentual. Verifique os campos.')
    else:
        form = TabelaSeguroForm(instance=tabela_seguro)
    
    context = {
        'form': form,
        'tabela_seguro': tabela_seguro,
    }
    return render(request, 'notas/editar_tabela_seguro.html', context)


@admin_required
def atualizar_tabela_seguro_ajax(request, pk):
    """Atualiza um registro da tabela de seguros via AJAX"""
    if request.method == 'POST':
        tabela_seguro = get_object_or_404(TabelaSeguro, pk=pk)
        percentual = request.POST.get('percentual_seguro')
        
        try:
            percentual_float = float(percentual)
            if 0 <= percentual_float <= 100:
                tabela_seguro.percentual_seguro = percentual_float
                tabela_seguro.save()
                
                messages.success(request, f'Percentual de seguro para {tabela_seguro.get_estado_display()} atualizado para {percentual_float}%')
                
                return json_success(
                    message=f'Percentual atualizado para {percentual_float}%',
                    percentual=percentual_float,
                )
            else:
                return json_error('Percentual deve estar entre 0% e 100%', status=400)
        except ValueError:
            return json_error('Valor inválido para percentual', status=400)
    
    return json_error('Método não permitido', status=405)
