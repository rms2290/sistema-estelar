from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from ..models import NotaFiscal
from ..forms import NotaFiscalForm, NotaFiscalSearchForm

@login_required
def listar_notas_fiscais(request):
    """Lista todas as notas fiscais com filtros de busca"""
    search_form = NotaFiscalSearchForm(request.GET)
    notas_fiscais = NotaFiscal.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = NotaFiscal.objects.all()
        nota = search_form.cleaned_data.get('nota')
        cliente = search_form.cleaned_data.get('cliente')
        data = search_form.cleaned_data.get('data')
        
        if nota:
            queryset = queryset.filter(nota__icontains=nota)
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if data:
            queryset = queryset.filter(data=data)
        
        notas_fiscais = queryset.order_by('-data', '-nota')
    
    context = {
        'notas_fiscais': notas_fiscais,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_notas.html', context)

@login_required
def adicionar_nota_fiscal(request):
    """Adiciona uma nova nota fiscal"""
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota fiscal adicionada com sucesso!')
            
            # Verificar se deve continuar adicionando mais notas
            if 'salvar_e_adicionar' in request.POST:
                # Criar novo formulário limpo com data de hoje
                new_form = NotaFiscalForm()
                return render(request, 'notas/adicionar_nota.html', {
                    'form': new_form,
                    'focus_nota': True  # Flag para focar no campo nota
                })
            else:
                return redirect('notas:listar_notas_fiscais')
        else:
            messages.error(request, 'Houve um erro ao adicionar a nota fiscal. Verifique os campos.')
    else:
        form = NotaFiscalForm()
    
    return render(request, 'notas/adicionar_nota.html', {'form': form})

@login_required
def editar_nota_fiscal(request, pk):
    """Edita uma nota fiscal existente"""
    nota_fiscal = get_object_or_404(NotaFiscal, pk=pk)
    
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota_fiscal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota fiscal atualizada com sucesso!')
            return redirect('notas:listar_notas_fiscais')
        else:
            messages.error(request, 'Houve um erro ao atualizar a nota fiscal.')
    else:
        form = NotaFiscalForm(instance=nota_fiscal)
    
    return render(request, 'notas/editar_nota.html', {'form': form, 'nota_fiscal': nota_fiscal})

@login_required
def excluir_nota_fiscal(request, pk):
    """Exclui uma nota fiscal"""
    nota_fiscal = get_object_or_404(NotaFiscal, pk=pk)
    
    if request.method == 'POST':
        nota_fiscal.delete()
        messages.success(request, 'Nota fiscal excluída com sucesso!')
        return redirect('notas:listar_notas_fiscais')
    
    return render(request, 'notas/excluir_nota.html', {'nota_fiscal': nota_fiscal})

@login_required
def detalhes_nota_fiscal(request, pk):
    """Mostra os detalhes de uma nota fiscal"""
    nota_fiscal = get_object_or_404(NotaFiscal, pk=pk)
    return render(request, 'notas/detalhes_nota_fiscal.html', {'nota_fiscal': nota_fiscal})

@login_required
def load_notas_fiscais(request):
    """Carrega notas fiscais via AJAX"""
    cliente_id = request.GET.get('cliente_id')
    if cliente_id:
        notas = NotaFiscal.objects.filter(cliente_id=cliente_id, status='Depósito')
        return JsonResponse({'notas': list(notas.values())})
    return JsonResponse({'notas': []})

@login_required
def load_notas_fiscais_edicao(request):
    """Carrega notas fiscais para edição via AJAX"""
    romaneio_id = request.GET.get('romaneio_id')
    if romaneio_id:
        from ..models import RomaneioViagem
        romaneio = get_object_or_404(RomaneioViagem, pk=romaneio_id)
        notas_vinculadas = romaneio.notas_fiscais.all()
        notas_disponiveis = NotaFiscal.objects.filter(
            cliente=romaneio.cliente,
            status='Depósito'
        ).exclude(id__in=notas_vinculadas.values_list('id', flat=True))
        
        return JsonResponse({
            'notas_vinculadas': list(notas_vinculadas.values()),
            'notas_disponiveis': list(notas_disponiveis.values())
        })
    return JsonResponse({'notas_vinculadas': [], 'notas_disponiveis': []})

@login_required
def pesquisar_mercadorias_deposito(request):
    """Pesquisa mercadorias em depósito"""
    from ..models import NotaFiscal
    from ..forms import MercadoriaDepositoSearchForm
    from django.contrib import messages
    
    search_form = MercadoriaDepositoSearchForm(request.GET)
    search_performed = bool(request.GET)

    # Inicializar com queryset vazio
    notas_fiscais = NotaFiscal.objects.none()
    total_peso = 0
    total_valor = 0
    
    if search_performed and search_form.is_valid():
        # Buscar notas em depósito apenas quando há pesquisa válida
        queryset = NotaFiscal.objects.filter(status='Depósito')
        
        cliente = search_form.cleaned_data.get('cliente')
        mercadoria = search_form.cleaned_data.get('mercadoria')
        fornecedor = search_form.cleaned_data.get('fornecedor')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if mercadoria:
            queryset = queryset.filter(mercadoria__icontains=mercadoria)
        if fornecedor:
            queryset = queryset.filter(fornecedor__icontains=fornecedor)
        if data_inicio:
            queryset = queryset.filter(data__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data__lte=data_fim)
        
        notas_fiscais = queryset.order_by('data', 'nota')
        
        # Calcular totais apenas quando há resultados
        total_peso = sum(nota.peso for nota in notas_fiscais)
        total_valor = sum(nota.valor for nota in notas_fiscais)
    elif search_performed:
        # Se o formulário não for válido, mostrar mensagem de erro
        messages.warning(request, f'Erro na validação do formulário: {search_form.errors}.')
    
    context = {
        'mercadorias': notas_fiscais,
        'search_form': search_form,
        'search_performed': search_performed,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/pesquisar_mercadorias_deposito.html', context) 