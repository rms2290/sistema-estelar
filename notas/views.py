from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max
from django.contrib import messages

from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem
from .forms import NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm, RomaneioViagemForm

# Views Notas
# ... (manter as views de NotaFiscal, Cliente, Motorista, Veiculo inalteradas) ...
def listar_notas_fiscais(request):
    notas = NotaFiscal.objects.all()
    return render(request, 'notas/listar_notas.html', {'notas': notas})

def adicionar_nota_fiscal(request):
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota fiscal adicionada com sucesso!')
            return redirect('notas:listar_notas_fiscais')
    else:
        form = NotaFiscalForm()
    return render(request, 'notas/adicionar_nota.html', {'form': form})

def editar_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, 'Nota fiscal atualizada com sucesso!')
            return redirect('notas:listar_notas_fiscais')
    else:
        form = NotaFiscalForm(instance=nota)
    return render(request, 'notas/editar_nota.html', {'form': form, 'nota': nota})

def excluir_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if request.method == 'POST':
        for romaneio in nota.romaneios.all():
            romaneio.notas_fiscais.remove(nota)
        nota.delete()
        messages.success(request, 'Nota fiscal excluída com sucesso!')
        return redirect('notas:listar_notas_fiscais')
    return render(request, 'notas/excluir_nota.html', {'nota': nota})


# Views Cliente
def listar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'notas/listar_clientes.html', {'clientes': clientes})

def adicionar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente adicionado com sucesso!')
            return redirect('notas:listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'notas/adicionar_cliente.html', {'form': form})

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('notas:listar_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'notas/editar_cliente.html', {'form': form, 'cliente': cliente})

def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente excluído com sucesso!')
        return redirect('notas:listar_clientes')
    return render(request, 'notas/excluir_cliente.html', {'cliente': cliente})

# Views Motorista
def listar_motoristas(request):
    motoristas = Motorista.objects.all()
    return render(request, 'notas/listar_motoristas.html', {'motoristas': motoristas})

def adicionar_motorista(request):
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
            return redirect('notas:listar_motoristas')
    else:
        form = MotoristaForm()
    return render(request, 'notas/adicionar_motorista.html', {'form': form})

def editar_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
            return redirect('notas:listar_motoristas')
    else:
        form = MotoristaForm(instance=motorista)
    return render(request, 'notas/editar_motorista.html', {'form': form})

def excluir_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        motorista.delete()
        messages.success(request, 'Motorista excluído com sucesso!')
        return redirect('notas:listar_motoristas')
    return render(request, 'notas/confirmar_exclusao_motorista.html', {'motorista': motorista})

# Views Veiculo
def listar_veiculos(request):
    veiculos = Veiculo.objects.all()
    return render(request, 'notas/listar_veiculos.html', {'veiculos': veiculos})

def adicionar_veiculo(request):
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo adicionado com sucesso!')
            return redirect('notas:listar_veiculos')
    else:
        form = VeiculoForm()
    return render(request, 'notas/adicionar_veiculo.html', {'form': form})

def editar_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        form = VeiculoForm(request.POST, instance=veiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Veículo atualizado com sucesso!')
            return redirect('notas:listar_veiculos')
    else:
        form = VeiculoForm(instance=veiculo)
    return render(request, 'notas/editar_veiculo.html', {'form': form})

def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        veiculo.delete()
        messages.success(request, 'Veículo excluído com sucesso!')
        return redirect('notas:listar_veiculos')
    return render(request, 'notas/confirmar_exclusao_veiculo.html', {'veiculo': veiculo})

# Views Romaneio

def listar_romaneios(request):
    romaneios = RomaneioViagem.objects.all().order_by('-data_emissao')
    return render(request, 'notas/listar_romaneios.html', {'romaneios': romaneios})

def adicionar_romaneio(request):
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj, romaneios__isnull=True 
                ).order_by('nota')
            except Cliente.DoesNotExist:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            romaneio = form.save(commit=False)
            
            max_codigo = RomaneioViagem.objects.aggregate(Max('codigo'))['codigo__max']
            romaneio.codigo = (max_codigo or 0) + 1

            romaneio.save()
            form.save_m2m() # AQUI SIM, save_m2m() é necessário porque chamamos save(commit=False)

            for nota_fiscal in romaneio.notas_fiscais.all():
                nota_fiscal.status = 'Romaneada'
                nota_fiscal.save()

            messages.success(request, f'Romaneio {romaneio.codigo} emitido com sucesso!')
            return redirect('notas:listar_romaneios')
        else:
            messages.error(request, 'Houve um erro ao emitir o romaneio. Verifique os campos.')
    else:
        form = RomaneioViagemForm()
        
    return render(request, 'notas/adicionar_romaneio.html', {'form': form})

def editar_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST, instance=romaneio)
        
        cliente_id = request.POST.get('cliente')
        if not cliente_id:
            cliente_id = romaneio.cliente.pk
        
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj
                ).filter(
                    Q(romaneios=romaneio) | Q(romaneios__isnull=True)
                ).order_by('nota')
            except Cliente.DoesNotExist:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            # Pegue as notas fiscais antes de salvar o formulário para comparar depois
            # Importante: romaneio.notas_fiscais.all() no início da função
            # representa o estado ANTES do POST. Após form.save(),
            # ele refletirá o novo estado.
            notas_antes_salvar = set(romaneio.notas_fiscais.all())
            
            form.save() # Isso salva o romaneio e as relações ManyToMany AUTOMATICAMENTE

            notas_depois_salvar = set(romaneio.notas_fiscais.all())

            # Notas que foram removidas do romaneio
            for nota_fiscal_removida in (notas_antes_salvar - notas_depois_salvar):
                # Verificar se a nota não está em NENHUM outro romaneio
                if not nota_fiscal_removida.romaneios.exclude(pk=romaneio.pk).exists():
                    nota_fiscal_removida.status = 'Pendente'
                    nota_fiscal_removida.save()
            
            # Notas que foram adicionadas ou permaneceram no romaneio
            for nota_fiscal_atualizada in notas_depois_salvar:
                nota_fiscal_atualizada.status = 'Romaneada'
                nota_fiscal_atualizada.save()

            messages.success(request, f'Romaneio {romaneio.codigo} atualizado com sucesso!')
            return redirect('notas:listar_romaneios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o romaneio. Verifique os campos.')
    else: # GET request para edição
        form = RomaneioViagemForm(instance=romaneio)
        if romaneio.cliente:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                cliente=romaneio.cliente
            ).filter(
                Q(romaneios=romaneio) | Q(romaneios__isnull=True)
            ).order_by('nota')

    return render(request, 'notas/editar_romaneio.html', {'form': form, 'romaneio': romaneio})

def excluir_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    if request.method == 'POST':
        for nota_fiscal in romaneio.notas_fiscais.all():
            nota_fiscal.status = 'Pendente'
            nota_fiscal.save()
        
        romaneio.delete()
        messages.success(request, 'Romaneio excluído com sucesso! Notas fiscais associadas retornaram ao status Pendente.')
        return redirect('notas:listar_romaneios')
    return render(request, 'notas/confirmar_exclusao_romaneio.html', {'romaneio': romaneio})


# Nova View para carregar notas fiscais via AJAX
def load_notas_fiscais(request):
    cliente_id = request.GET.get('cliente_id')
    notas = NotaFiscal.objects.filter(
        cliente_id=cliente_id,
        status='Pendente' # Filtre pelo status, que agora está no modelo
    ).order_by('nota')

    data = [{'id': nota.id, 'nota': f"{nota.nota} ({nota.mercadoria} - {nota.valor})"} for nota in notas]
    return JsonResponse(data, safe=False)