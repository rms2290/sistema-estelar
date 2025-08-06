from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from ..models import RomaneioViagem, NotaFiscal, Cliente, Motorista, Veiculo
from ..forms import RomaneioViagemForm, RomaneioSearchForm
from ..utils.formatters import formatar_valor_brasileiro, formatar_peso_brasileiro

def get_next_romaneio_codigo():
    """Gera o próximo código sequencial de romaneio começando do número 1."""
    last_romaneio = RomaneioViagem.objects.all().order_by('-codigo').first()

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            # Tenta extrair o número do código atual
            next_sequence = int(last_romaneio.codigo) + 1
        except (ValueError, TypeError):
            # Se não conseguir converter, começa do 1
            next_sequence = 1

    return str(next_sequence)

@login_required
def listar_romaneios(request):
    """Lista todos os romaneios com filtros de busca"""
    search_form = RomaneioSearchForm(request.GET)
    romaneios = RomaneioViagem.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        queryset = RomaneioViagem.objects.all()
        codigo = search_form.cleaned_data.get('codigo')
        cliente = search_form.cleaned_data.get('cliente')
        motorista = search_form.cleaned_data.get('motorista')
        veiculo = search_form.cleaned_data.get('veiculo')
        status = search_form.cleaned_data.get('status')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if codigo:
            queryset = queryset.filter(codigo__icontains=codigo)
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if motorista:
            queryset = queryset.filter(motorista=motorista)
        if veiculo:
            queryset = queryset.filter(veiculo=veiculo)
        if status:
            queryset = queryset.filter(status=status)
        if data_inicio:
            queryset = queryset.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_emissao__date__lte=data_fim)
        
        romaneios = queryset.order_by('-data_emissao', '-codigo')
    
    context = {
        'romaneios': romaneios,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_romaneios.html', context)

@login_required
def adicionar_romaneio(request):
    """Adiciona um novo romaneio"""
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        if form.is_valid():
            romaneio = form.save(commit=False)
            romaneio.codigo = get_next_romaneio_codigo()
            romaneio.status = 'Emitido'
            romaneio.save()
            form.save_m2m()  # Salvar relacionamentos many-to-many
            
            # Atualizar status das notas fiscais
            for nota in romaneio.notas_fiscais.all():
                nota.status = 'Enviada'
                nota.save()
            
            messages.success(request, 'Romaneio criado com sucesso!')
            return redirect('notas:visualizar_romaneio_para_impressao', pk=romaneio.pk)
        else:
            messages.error(request, 'Houve um erro ao criar o romaneio. Verifique os campos.')
    else:
        form = RomaneioViagemForm()
    
    # Gerar código provisório para exibição no template
    provisional_codigo = get_next_romaneio_codigo()
    
    return render(request, 'notas/adicionar_romaneio.html', {
        'form': form,
        'provisional_codigo': provisional_codigo
    })

@login_required
def editar_romaneio(request, pk):
    """Edita um romaneio existente"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST, instance=romaneio)
        if form.is_valid():
            romaneio = form.save()
            messages.success(request, 'Romaneio atualizado com sucesso!')
            return redirect('notas:listar_romaneios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o romaneio.')
    else:
        form = RomaneioViagemForm(instance=romaneio)
    
    return render(request, 'notas/editar_romaneio.html', {'form': form, 'romaneio': romaneio})

@login_required
def excluir_romaneio(request, pk):
    """Exclui um romaneio"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    if request.method == 'POST':
        romaneio.delete()
        messages.success(request, 'Romaneio excluído com sucesso!')
        return redirect('notas:listar_romaneios')
    
    return render(request, 'notas/confirmar_exclusao_romaneio.html', {'romaneio': romaneio})

@login_required
def detalhes_romaneio(request, pk):
    """Mostra os detalhes de um romaneio"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_romaneadas)
    total_valor = sum(nota.valor for nota in notas_romaneadas)
    
    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/detalhes_romaneio.html', context)

@login_required
def visualizar_romaneio_para_impressao(request, pk):
    """Visualiza romaneio para impressão"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_romaneadas)
    total_valor = sum(nota.valor for nota in notas_romaneadas)
    
    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/visualizar_romaneio_para_impressao.html', context)

@login_required
def visualizar_romaneio_paisagem(request, pk):
    """Visualiza romaneio em formato paisagem"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_romaneadas)
    total_valor = sum(nota.valor for nota in notas_romaneadas)
    
    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/romaneio_impressao_paisagem.html', context)

@login_required
def load_notas_fiscais_para_romaneio(request, cliente_id):
    """Carrega notas fiscais para romaneio via AJAX"""
    from django.template.loader import render_to_string
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        notas_fiscais = NotaFiscal.objects.filter(
            cliente=cliente,
            status='Depósito'
        ).order_by('nota')
        
        html = render_to_string('notas/_notas_fiscais_checkboxes.html', {
            'notas_fiscais': notas_fiscais,
            'selected_notas_ids': []
        })
        
        return JsonResponse({
            'html': html,
            'success': True
        })
    except Cliente.DoesNotExist:
        return JsonResponse({
            'html': '<p>Cliente não encontrado.</p>',
            'success': False
        }) 