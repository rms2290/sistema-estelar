from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max 
from django.contrib import messages
from django.utils import timezone 

from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem 

from .forms import (
    NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm, RomaneioViagemForm,
    NotaFiscalSearchForm, ClienteSearchForm, MotoristaSearchForm,
)

# --------------------------------------------------------------------------------------
# Funções Auxiliares
# --------------------------------------------------------------------------------------
def get_next_romaneio_codigo():
    """Gera o próximo código sequencial de romaneio no formato ROM-AAAA-MM-NNNN."""
    ano = timezone.now().year
    mes = timezone.now().month
    
    # Encontra o último romaneio do mês e ano atual para determinar o próximo número sequencial
    last_romaneio = RomaneioViagem.objects.filter(
        data_emissao__year=ano,
        data_emissao__month=mes
    ).order_by('-codigo').first() # Ordena por código para pegar o maior

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            # Extrai o número sequencial do código (ex: ROM-2023-07-0001 -> 0001)
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 4 and parts[0] == 'ROM' and int(parts[1]) == ano and int(parts[2]) == mes:
                next_sequence = int(parts[3]) + 1
        except (ValueError, IndexError):
            # Fallback se o formato for inválido
            pass

    return f"ROM-{ano:04d}-{mes:02d}-{next_sequence:04d}"

# --------------------------------------------------------------------------------------
# Views para Cliente
# --------------------------------------------------------------------------------------
def adicionar_cliente(request):
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

def listar_clientes(request):
    search_form = ClienteSearchForm(request.GET)
    clientes = Cliente.objects.all().order_by('razao_social') # Começa com todos
    mostrou_resultados = False # Assume que não mostrou resultados ainda

    if search_form.is_valid():
        razao_social = search_form.cleaned_data.get('razao_social')
        cnpj = search_form.cleaned_data.get('cnpj')
        status = search_form.cleaned_data.get('status')

        if razao_social:
            clientes = clientes.filter(razao_social__icontains=razao_social)
        if cnpj:
            clientes = clientes.filter(cnpj__icontains=cnpj)
        if status:
            clientes = clientes.filter(status=status)
        
        mostrou_resultados = True # Indica que a busca foi feita

    context = {
        'clientes': clientes,
        'search_form': search_form,
        'mostrou_resultados': mostrou_resultados,
    }
    return render(request, 'notas/listar_clientes.html', context)

def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('notas:listar_clientes')
        else:
            messages.error(request, 'Houve um erro ao atualizar o cliente. Verifique os campos.')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'notas/editar_cliente.html', {'form': form, 'cliente': cliente})

def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        try:
            cliente.delete()
            messages.success(request, 'Cliente excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o cliente: {e}')
        return redirect('notas:listar_clientes')
    return render(request, 'notas/excluir_cliente.html', {'cliente': cliente})

# --------------------------------------------------------------------------------------
# Views para Nota Fiscal
# --------------------------------------------------------------------------------------
def listar_notas_fiscais(request):
    # Instancia o formulário de busca
    search_form = NotaFiscalSearchForm(request.GET)
    
    # Começa com um queryset vazio
    notas_fiscais = NotaFiscal.objects.none()
    
    # Se o formulário de busca for válido (ou seja, se houver parâmetros GET)
    if search_form.is_valid():
        # Pega os dados limpos do formulário
        numero_nota = search_form.cleaned_data.get('nota')
        cliente_obj = search_form.cleaned_data.get('cliente') # Já é o objeto Cliente ou None
        data_emissao = search_form.cleaned_data.get('data')

        # Começa com todas as notas fiscais
        queryset = NotaFiscal.objects.all()

        # Aplica os filtros condicionalmente
        if numero_nota:
            queryset = queryset.filter(nota__icontains=numero_nota)
        
        if cliente_obj:
            queryset = queryset.filter(cliente=cliente_obj)
        
        if data_emissao:
            queryset = queryset.filter(data=data_emissao)
        
        # Atribui o queryset filtrado
        notas_fiscais = queryset.order_by('-data', '-nota')
    
    context = {
        'search_form': search_form,
        'notas_fiscais': notas_fiscais,
        'mostrou_resultados': bool(notas_fiscais) or search_form.is_valid(),
    }
    return render(request, 'notas/listar_notas.html', context)

def adicionar_nota_fiscal(request):
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            # Status é definido pelo sistema, não pelo usuário
            nota_fiscal = form.save(commit=False)
            nota_fiscal.status = 'Depósito' 
            nota_fiscal.save()
            messages.success(request, 'Nota fiscal adicionada com sucesso!')
            return redirect('notas:listar_notas_fiscais')
        else:
            messages.error(request, 'Houve um erro ao adicionar a nota fiscal. Verifique os campos.') # <<< LINHA COMPLETA AQUI
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
        # Ao excluir nota, desassociar de romaneios e reverter status
        for romaneio in nota.romaneios_vinculados.all(): # <<< USAR related_name correto
            romaneio.notas_fiscais.remove(nota) # Remover da relação ManyToMany
            # Lógica opcional: se o romaneio ficar sem notas, mudar seu status ou excluí-lo
        
        nota.delete()
        messages.success(request, 'Nota fiscal excluída com sucesso!')
        return redirect('notas:listar_notas_fiscais')
    return render(request, 'notas/excluir_nota.html', {'nota': nota})

# --------------------------------------------------------------------------------------
# Views Motorista
# --------------------------------------------------------------------------------------
def listar_motoristas(request):
    search_form = MotoristaSearchForm(request.GET) # Usando o search form
    motoristas = Motorista.objects.none() # Começa vazio

    if request.GET and search_form.is_valid():
        nome = search_form.cleaned_data.get('nome')
        cpf = search_form.cleaned_data.get('cpf')

        queryset = Motorista.objects.all()
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        
        motoristas = queryset.order_by('nome')

    context = {
        'motoristas': motoristas,
        'search_form': search_form,
        'mostrou_resultados': bool(motoristas) or search_form.is_valid(),
    }
    return render(request, 'notas/listar_motoristas.html', context)

def adicionar_motorista(request):
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

def editar_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        form = MotoristaForm(request.POST, instance=motorista)
        if form.is_valid():
            form.save()
            messages.success(request, 'Motorista atualizado com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao atualizar o motorista. Verifique os campos.')
    else:
        form = MotoristaForm(instance=motorista)
    return render(request, 'notas/editar_motorista.html', {'form': form})

def excluir_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        try:
            motorista.delete()
            messages.success(request, 'Motorista excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o motorista: {e}')
        return redirect('notas:listar_motoristas')
    return render(request, 'notas/confirmar_exclusao_motorista.html', {'motorista': motorista})

# --------------------------------------------------------------------------------------
# Views Veiculo (Unidades Individuais)
# --------------------------------------------------------------------------------------
def listar_veiculos(request):
    # Usa o formulário de busca de veículo
    search_form = VeiculoSearchForm(request.GET)
    veiculos = Veiculo.objects.all().order_by('placa') # Começa com todos

    mostrou_resultados = False

    if search_form.is_valid():
        placa = search_form.cleaned_data.get('placa')
        chassi = search_form.cleaned_data.get('chassi')
        proprietario_nome = search_form.cleaned_data.get('proprietario_nome')
        tipo_unidade = search_form.cleaned_data.get('tipo_unidade')

        if placa:
            veiculos = veiculos.filter(placa__icontains=placa)
        if chassi:
            veiculos = veiculos.filter(chassi__icontains=chassi)
        if proprietario_nome:
            veiculos = veiculos.filter(proprietario_nome_razao_social__icontains=proprietario_nome)
        if tipo_unidade:
            veiculos = veiculos.filter(tipo_unidade=tipo_unidade)
        
        mostrou_resultados = True

    context = {
        'veiculos': veiculos,
        'search_form': search_form,
        'mostrou_resultados': mostrou_resultados,
    }
    return render(request, 'notas/listar_veiculos.html', context)

def adicionar_veiculo(request): # Esta view é para adicionar UMA UNIDADE de Veículo
    if request.method == 'POST':
        form = VeiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidade de Veículo cadastrada com sucesso!')
            return redirect('notas:listar_veiculos') # Redireciona para a pesquisa de unidades
        else:
            messages.error(request, 'Houve um erro ao cadastrar a unidade de veículo. Verifique os campos.')
    else:
        form = VeiculoForm()
    
    context = {
        'form': form,
    }
    return render(request, 'notas/adicionar_veiculo.html', context)

def editar_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        form = VeiculoForm(request.POST, instance=veiculo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidade de Veículo atualizada com sucesso!')
            return redirect('notas:listar_veiculos')
        else:
            messages.error(request, 'Houve um erro ao atualizar a unidade de veículo. Verifique os campos.')
    else:
        form = VeiculoForm(instance=veiculo)
    return render(request, 'notas/editar_veiculo.html', {'form': form})

def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        try:
            # Ao excluir veículo, desassociar de romaneios (se estiver associado)
            for romaneio in veiculo.romaneios_veiculo.all(): # related_name de RomaneioViagem
                romaneio.veiculo = None # Desvincula o veículo do romaneio
                romaneio.save() # Salva a alteração no romaneio
            veiculo.delete()
            messages.success(request, 'Unidade de Veículo excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o veículo: {e}')
        return redirect('notas:listar_veiculos')
    return render(request, 'notas/confirmar_exclusao_veiculo.html', {'veiculo': veiculo})

# --------------------------------------------------------------------------------------
# Views Romaneio
# --------------------------------------------------------------------------------------
def listar_romaneios(request):
    romaneios = RomaneioViagem.objects.all().order_by('-data_emissao', '-codigo')
    return render(request, 'notas/listar_romaneios.html', {'romaneios': romaneios})

# Função auxiliar para gerar o próximo código sequencial do romaneio
def get_next_romaneio_codigo():
    """Gera o próximo código sequencial de romaneio no formato ROM-AAAA-MM-NNNN."""
    ano = timezone.now().year
    mes = timezone.now().month
    
    last_romaneio = RomaneioViagem.objects.filter(
        data_emissao__year=ano,
        data_emissao__month=mes
    ).order_by('-codigo').first() # Ordena por código para pegar o maior

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 4 and parts[0] == 'ROM' and int(parts[1]) == ano and int(parts[2]) == mes:
                next_sequence = int(parts[3]) + 1
        except (ValueError, IndexError):
            pass

    return f"ROM-{ano:04d}-{mes:02d}-{next_sequence:04d}"

def adicionar_romaneio(request):
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        # Lógica de filtragem de notas no POST
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj, status='Depósito' # Notas no status Depósito para o cliente
                ).order_by('nota')
            except Cliente.DoesNotExist:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            romaneio = form.save(commit=False)
            
            romaneio.codigo = get_next_romaneio_codigo()
            romaneio.data_emissao = form.cleaned_data['data_romaneio']
            
            if 'emitir' in request.POST:
                romaneio.status = 'Emitido'
            else:
                romaneio.status = 'Rascunho'

            romaneio.save()
            form.save_m2m() # Salva a relação ManyToMany

            # Atualizar o status das notas fiscais
            for nota_fiscal in romaneio.notas_fiscais.all():
                if romaneio.status == 'Emitido':
                    nota_fiscal.status = 'Enviada'
                else:
                    nota_fiscal.status = 'Depósito'
                nota_fiscal.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) salvo com sucesso!')
            return redirect('notas:listar_romaneios')
        else:
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio. Verifique os campos.')
    else: # GET request
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_codigo()
        
        # Garante que os querysets dos campos Select estejam populados
        form.fields['veiculo'].queryset = Veiculo.objects.all().order_by('placa')
        form.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        form.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')

    context = {
        'form': form,
        'provisional_codigo': provisional_codigo,
    }
    return render(request, 'notas/adicionar_romaneio.html', context)


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
                # Inclui notas que já estão neste romaneio OU notas 'Depósito' do mesmo cliente
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj
                ).filter(
                    Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
                ).order_by('nota')
            except Cliente.DoesNotExist:
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()
        else:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.none()

        if form.is_valid():
            # Pegue as notas fiscais antes de salvar o formulário para comparar depois
            notas_antes_salvar = set(romaneio.notas_fiscais.all())
            
            # AQUI: Atribui a data do formulário ao campo do modelo
            romaneio.data_emissao = form.cleaned_data['data_romaneio']
            
            if 'emitir' in request.POST:
                romaneio.status = 'Emitido'
            elif 'salvar' in request.POST:
                romaneio.status = 'Rascunho'
            
            form.save() # Salva o romaneio e as relações ManyToMany AUTOMATICAMENTE
            
            notas_depois_salvar = set(romaneio.notas_fiscais.all())

            # Lógica para atualizar o status das notas fiscais
            for nota_fiscal_removida in (notas_antes_salvar - notas_depois_salvar):
                if not nota_fiscal_removida.romaneios_vinculados.exists(): # Verifica se não está em NENHUM outro romaneio
                    nota_fiscal_removida.status = 'Depósito'
                    nota_fiscal_removida.save()
            
            for nota_fiscal_atualizada in notas_depois_salvar:
                if romaneio.status == 'Emitido':
                    nota_fiscal_atualizada.status = 'Enviada'
                else: # Se o romaneio está em Rascunho
                    nota_fiscal_atualizada.status = 'Depósito'
                nota_fiscal_atualizada.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) atualizado com sucesso!')
            return redirect('notas:listar_romaneios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o romaneio. Verifique os campos.')
    else: # GET request para edição
        form = RomaneioViagemForm(instance=romaneio)
        
        form.fields['veiculo'].queryset = Veiculo.objects.all().order_by('placa')
        form.fields['motorista'].queryset = Motorista.objects.all().order_by('nome')
        form.fields['cliente'].queryset = Cliente.objects.filter(status='Ativo').order_by('razao_social')

        # Preenche o campo de data_romaneio com o valor de data_emissao do modelo
        if romaneio.data_emissao:
            form.fields['data_romaneio'].initial = romaneio.data_emissao.date()

        if romaneio.cliente:
            form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                cliente=romaneio.cliente
            ).filter(
                Q(romaneios_vinculados=romaneio) | Q(status='Depósito')
            ).order_by('nota')

    context = {
        'form': form,
        'romaneio': romaneio,
        'provisional_codigo': romaneio.codigo,
    }
    return render(request, 'notas/editar_romaneio.html', context)

def excluir_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    if request.method == 'POST':
        for nota_fiscal in romaneio.notas_fiscais.all():
            nota_fiscal.status = 'Depósito'
            nota_fiscal.save()
        
        romaneio.delete()
        messages.success(request, 'Romaneio excluído com sucesso! Notas fiscais associadas retornaram ao status Depósito.')
        return redirect('notas:listar_romaneios')
    return render(request, 'notas/confirmar_exclusao_romaneio.html', {'romaneio': romaneio})

# --------------------------------------------------------------------------------------
# Nova View para carregar notas fiscais via AJAX
# --------------------------------------------------------------------------------------
def load_notas_fiscais(request):
    cliente_id = request.GET.get('cliente_id')
    notas = NotaFiscal.objects.filter(
        cliente_id=cliente_id,
        status='Depósito'
    ).order_by('nota')

    data = [{'id': nota.id, 'nota': f"{nota.nota} ({nota.mercadoria} - {nota.valor})"} for nota in notas]
    return JsonResponse(data, safe=False)

# Nova View para carregar notas fiscais via AJAX (para edição)
def load_notas_fiscais_edicao(request):
    cliente_id = request.GET.get('cliente_id')
    romaneio_id = request.GET.get('romaneio_id')

    if cliente_id:
        notas_query = NotaFiscal.objects.filter(cliente_id=cliente_id)
        
        if romaneio_id:
            notas_query = notas_query.filter(
                Q(status='Depósito') | Q(romaneios_vinculados__pk=romaneio_id)
            )
        else:
            notas_query = notas_query.filter(status='Depósito')

        notas = notas_query.order_by('nota')
    else:
        notas = NotaFiscal.objects.none()

    data = [{'id': nota.id, 'nota': f"{nota.nota} ({nota.mercadoria} - {nota.valor})"} for nota in notas]
    return JsonResponse(data, safe=False)