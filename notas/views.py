from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max 
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test

# Importe todos os seus modelos
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta 

# Importe todos os seus formulários
from .forms import (
    NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm, RomaneioViagemForm,
    NotaFiscalSearchForm, ClienteSearchForm, MotoristaSearchForm, HistoricoConsultaForm,
    VeiculoSearchForm, RomaneioSearchForm, MercadoriaDepositoSearchForm # Adicionado o novo formulário
)

# --------------------------------------------------------------------------------------
# Funções Auxiliares
# --------------------------------------------------------------------------------------
def get_next_romaneio_codigo():
    """Gera o próximo código sequencial de romaneio no formato ROM-AAAA-MM-NNNN."""
    ano = timezone.now().year
    mes = timezone.now().month
    
    last_romaneio = RomaneioViagem.objects.filter(
        data_emissao__year=ano,
        data_emissao__month=mes
    ).order_by('-codigo').first()

    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 4 and parts[0] == 'ROM' and int(parts[1]) == ano and int(parts[2]) == mes:
                next_sequence = int(parts[3]) + 1
        except (ValueError, IndexError):
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

def detalhes_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    context = {
        'cliente': cliente,
    }
    return render(request, 'notas/detalhes_cliente.html', context)

# --------------------------------------------------------------------------------------
# Views para Nota Fiscal
# --------------------------------------------------------------------------------------
def listar_notas_fiscais(request):
    search_form = NotaFiscalSearchForm(request.GET)
    notas_fiscais = NotaFiscal.objects.none()
    search_performed = bool(request.GET)

    if search_performed and search_form.is_valid():
        numero_nota = search_form.cleaned_data.get('nota')
        cliente_obj = search_form.cleaned_data.get('cliente')
        data_emissao = search_form.cleaned_data.get('data')

        queryset = NotaFiscal.objects.all()
        if numero_nota:
            queryset = queryset.filter(nota__icontains=numero_nota)
        if cliente_obj:
            queryset = queryset.filter(cliente=cliente_obj)
        if data_emissao:
            queryset = queryset.filter(data=data_emissao)
        
        notas_fiscais = queryset.order_by('-data', '-nota')
    
    context = {
        'search_form': search_form,
        'notas_fiscais': notas_fiscais,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_notas.html', context)

def adicionar_nota_fiscal(request):
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            nota_fiscal = form.save(commit=False)
            nota_fiscal.status = 'Depósito' 
            nota_fiscal.save()
            messages.success(request, f'Nota Fiscal {nota_fiscal.nota} adicionada com sucesso!')

            if 'salvar_e_adicionar' in request.POST:
                return redirect('notas:adicionar_nota_fiscal')
            else:
                return redirect('notas:detalhes_nota_fiscal', pk=nota_fiscal.pk)

        else:
            messages.error(request, 'Houve um erro ao adicionar a nota fiscal. Verifique os campos.')
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
            return redirect('notas:detalhes_nota_fiscal', pk=nota.pk)
        else:
            messages.error(request, 'Houve um erro ao atualizar a nota fiscal. Verifique os campos.')
    else:
        form = NotaFiscalForm(instance=nota)
    return render(request, 'notas/editar_nota.html', {'form': form, 'nota': nota})

def excluir_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    if request.method == 'POST':
        for romaneio in nota.romaneios_vinculados.all():
            romaneio.notas_fiscais.remove(nota)
        nota.delete()
        messages.success(request, 'Nota fiscal excluída com sucesso!')
        return redirect('notas:listar_notas_fiscais')
    return render(request, 'notas/excluir_nota.html', {'nota': nota})

def detalhes_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    romaneios_vinculados = nota.romaneios_vinculados.all().order_by('-data_emissao')
    context = {
        'nota': nota,
        'romaneios_vinculados': romaneios_vinculados,
    }
    return render(request, 'notas/detalhes_nota_fiscal.html', context)

# --------------------------------------------------------------------------------------
# Views Motorista
# --------------------------------------------------------------------------------------
def listar_motoristas(request):
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
    
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]

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
    
    context = {
        'form': form,
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/editar_motorista.html', context)

def adicionar_historico_consulta(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.motorista = motorista
            historico.save()
            messages.success(request, 'Consulta de risco registrada com sucesso!')
            return redirect('notas:editar_motorista', pk=motorista.pk)
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta. Verifique os campos.')
            return redirect('notas:editar_motorista', pk=motorista.pk)
    return redirect('notas:editar_motorista', pk=motorista.pk) 

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

def detalhes_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]
    context = {
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/detalhes_motorista.html', context)

# --------------------------------------------------------------------------------------
# Views Veiculo (Unidades Individuais)
# --------------------------------------------------------------------------------------
def listar_veiculos(request):
    search_form = VeiculoSearchForm(request.GET)
    
    veiculos = []  # Inicia com lista vazia
    filters_applied = False  # Variável para verificar se algum filtro foi realmente aplicado

    if search_form.is_valid():
        placa = search_form.cleaned_data.get('placa')
        chassi = search_form.cleaned_data.get('chassi')
        proprietario_nome = search_form.cleaned_data.get('proprietario_nome')
        tipo_unidade = search_form.cleaned_data.get('tipo_unidade')

        # Só executa a busca se pelo menos um filtro foi aplicado
        if placa or chassi or proprietario_nome or tipo_unidade:
            veiculos_query = Veiculo.objects.all().order_by('placa')
            
            if placa:
                veiculos_query = veiculos_query.filter(placa__icontains=placa)
                filters_applied = True
            
            if chassi:
                veiculos_query = veiculos_query.filter(chassi__icontains=chassi)
                filters_applied = True
            
            if proprietario_nome:
                veiculos_query = veiculos_query.filter(proprietario_nome_razao_social__icontains=proprietario_nome)
                filters_applied = True
            
            if tipo_unidade:
                veiculos_query = veiculos_query.filter(tipo_unidade=tipo_unidade)
                filters_applied = True
            
            veiculos = veiculos_query.order_by('placa')

    context = {
        'veiculos': veiculos,
        'search_form': search_form,
        'filters_applied': filters_applied,
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
            return redirect('notas:detalhes_veiculo', pk=veiculo.pk)
        else:
            messages.error(request, 'Houve um erro ao atualizar a unidade de veículo. Verifique os campos.')
    else:
        form = VeiculoForm(instance=veiculo)
    return render(request, 'notas/editar_veiculo.html', {'form': form, 'veiculo': veiculo})

def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    if request.method == 'POST':
        try:
            for romaneio in veiculo.romaneios_veiculo.all():
                romaneio.veiculo = None
                romaneio.save()
            veiculo.delete()
            messages.success(request, 'Unidade de Veículo excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o veículo: {e}')
        return redirect('notas:listar_veiculos')
    return render(request, 'notas/confirmar_exclusao_veiculo.html', {'veiculo': veiculo})

def detalhes_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    context = {
        'veiculo': veiculo,
    }
    return render(request, 'notas/detalhes_veiculo.html', context)

# --------------------------------------------------------------------------------------
# Views Romaneio
# --------------------------------------------------------------------------------------
def listar_romaneios(request):
    search_form = RomaneioSearchForm(request.GET)
    
    romaneios = []  # Inicia com lista vazia
    filters_applied = False  # Variável para verificar se algum filtro foi realmente aplicado

    if search_form.is_valid():
        codigo = search_form.cleaned_data.get('codigo')
        cliente = search_form.cleaned_data.get('cliente')
        motorista = search_form.cleaned_data.get('motorista')
        veiculo = search_form.cleaned_data.get('veiculo')
        status = search_form.cleaned_data.get('status')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')

        # Só executa a busca se pelo menos um filtro foi aplicado
        if codigo or cliente or motorista or veiculo or status or data_inicio or data_fim:
            romaneios_query = RomaneioViagem.objects.all().order_by('-data_emissao', '-codigo')
            
            if codigo:
                romaneios_query = romaneios_query.filter(codigo__icontains=codigo)
                filters_applied = True
            
            if cliente:
                romaneios_query = romaneios_query.filter(cliente=cliente)
                filters_applied = True
            
            if motorista:
                romaneios_query = romaneios_query.filter(motorista=motorista)
                filters_applied = True
            
            if veiculo:
                romaneios_query = romaneios_query.filter(veiculo=veiculo)
                filters_applied = True
            
            if status:
                romaneios_query = romaneios_query.filter(status=status)
                filters_applied = True
            
            if data_inicio:
                romaneios_query = romaneios_query.filter(data_emissao__gte=data_inicio)
                filters_applied = True
            
            if data_fim:
                romaneios_query = romaneios_query.filter(data_emissao__lte=data_fim)
                filters_applied = True
            
            romaneios = romaneios_query.order_by('-data_emissao', '-codigo')

    context = {
        'romaneios': romaneios,
        'search_form': search_form,
        'filters_applied': filters_applied,
    }
    return render(request, 'notas/listar_romaneios.html', context)

def adicionar_romaneio(request):
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        cliente_id = request.POST.get('cliente')
        if cliente_id:
            try:
                cliente_obj = Cliente.objects.get(pk=cliente_id)
                form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(
                    cliente=cliente_obj, status='Depósito' 
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
            else: # Clicou em 'salvar' ou outro botão
                romaneio.status = 'Rascunho'

            romaneio.save()
            form.save_m2m() # Salva a relação ManyToMany

            # Atualizar o status das notas fiscais associadas
            for nota_fiscal in romaneio.notas_fiscais.all():
                if romaneio.status == 'Emitido':
                    nota_fiscal.status = 'Enviada'
                else:
                    nota_fiscal.status = 'Depósito'
                nota_fiscal.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) salvo com sucesso!')
            
            # >>> MUDANÇA AQUI: Redirecionar para a tela de visualização se Emitido <<<
            if romaneio.status == 'Emitido':
                return redirect('notas:visualizar_romaneio_para_impressao', pk=romaneio.pk)
            else: # Rascunho
                # Redirecionar para detalhes (para poder continuar editando) ou para listar
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk) # Sugiro detalhes para rascunho
        else:
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio. Verifique os campos.')
    else:
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_codigo()
        
        # ... (querysets) ...

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
            notas_antes_salvar = set(romaneio.notas_fiscais.all())
            
            romaneio.data_emissao = form.cleaned_data['data_romaneio']
            
            # --- Lógica de Status Baseada no Botão Clicado ---
            if 'emitir' in request.POST:
                romaneio.status = 'Emitido'
            elif 'salvar' in request.POST:
                romaneio.status = 'Rascunho'
            
            form.save()
            
            notas_depois_salvar = set(romaneio.notas_fiscais.all())

            for nota_fiscal_removida in (notas_antes_salvar - notas_depois_salvar):
                if not nota_fiscal_removida.romaneios_vinculados.exclude(pk=romaneio.pk).exists():
                    nota_fiscal_removida.status = 'Depósito'
                    nota_fiscal_removida.save()
            
            for nota_fiscal_atualizada in notas_depois_salvar:
                if romaneio.status == 'Emitido':
                    nota_fiscal_atualizada.status = 'Enviada'
                else:
                    nota_fiscal_atualizada.status = 'Depósito'
                nota_fiscal_atualizada.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) atualizado com sucesso!')
            
            # >>> MUDANÇA AQUI: Redirecionar para a tela de visualização se Emitido <<<
            if romaneio.status == 'Emitido':
                return redirect('notas:visualizar_romaneio_para_impressao', pk=romaneio.pk)
            else: # Rascunho
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk) # Volta para os detalhes do romaneio
        else:
            messages.error(request, 'Houve um erro ao atualizar o romaneio. Verifique os campos.')
    else: # GET request para edição
        form = RomaneioViagemForm(instance=romaneio)
        
        # ... (querysets e data_emissao) ...

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

def detalhes_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Verificar se o usuário tem permissão para ver este romaneio
    if request.user.is_cliente and request.user.cliente:
        # Cliente só pode ver romaneios que contêm suas notas fiscais
        if not romaneio.notas_fiscais.filter(cliente=request.user.cliente).exists():
            messages.error(request, 'Você não tem permissão para acessar este romaneio.')
            return redirect('notas:meus_romaneios')
    
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota')

    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
    }
    return render(request, 'notas/detalhes_romaneio.html', context)

# --------------------------------------------------------------------------------------
# Nova View para carregar notas fiscais via AJAX
# --------------------------------------------------------------------------------------
def load_notas_fiscais(request):
    cliente_id = request.GET.get('cliente_id')
    print(f"AJAX: load_notas_fiscais (Adicionar Romaneio) chamada. cliente_id={cliente_id}")

    if not cliente_id:
        print("AJAX: cliente_id não fornecido. Retornando notas vazias.")
        return JsonResponse([], safe=False)

    try:
        cliente_obj = Cliente.objects.get(pk=cliente_id)
        
        notas = NotaFiscal.objects.filter(
            cliente=cliente_obj,
            status='Depósito'
        ).order_by('nota')
        
        print(f"AJAX: Encontradas {notas.count()} notas 'Depósito' para cliente {cliente_obj.razao_social}.")

        data = [{
            'id': nota.id,
            'nota_numero': nota.nota,
            'fornecedor': nota.fornecedor,
            'quantidade': str(nota.quantidade), 
            'peso': str(nota.peso) if nota.peso is not None else '', 
            'valor': f"{nota.valor:.2f}", 
            'mercadoria': nota.mercadoria, 
            'data_emissao': nota.data.strftime("%d/%m/%Y"), 
            'status_nf': nota.get_status_display(), 
        } for nota in notas]
        print(f"AJAX: Dados JSON sendo enviados: {data}")
        
        return JsonResponse(data, safe=False)
    except Cliente.DoesNotExist:
        print(f"AJAX: Cliente com ID {cliente_id} não encontrado.")
        return JsonResponse([], safe=False)
    except Exception as e:
        print(f"AJAX: Erro inesperado na view load_notas_fiscais: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def load_notas_fiscais_edicao(request):
    cliente_id = request.GET.get('cliente_id')
    romaneio_id = request.GET.get('romaneio_id')
    print(f"AJAX: load_notas_fiscais_edicao (Editar Romaneio) chamada. cliente_id={cliente_id}, romaneio_id={romaneio_id}")

    if not cliente_id:
        print("AJAX: cliente_id não fornecido. Retornando notas vazias.")
        return JsonResponse([], safe=False)

    try:
        cliente_obj = Cliente.objects.get(pk=cliente_id)
        
        notas_query = NotaFiscal.objects.filter(cliente=cliente_obj)
        
        if romaneio_id:
            notas_query = notas_query.filter(
                Q(status='Depósito') | Q(romaneios_vinculados__pk=romaneio_id)
            )
        else:
            notas_query = notas_query.filter(status='Depósito')

        notas = notas_query.order_by('nota')
        print(f"AJAX: Encontradas {notas.count()} notas para cliente {cliente_obj.razao_social} (para edição).")
        
        data = [{
            'id': nota.id,
            'nota_numero': nota.nota,
            'fornecedor': nota.fornecedor,
            'quantidade': str(nota.quantidade), 
            'peso': str(nota.peso) if nota.peso is not None else '', 
            'valor': f"{nota.valor:.2f}", 
            'mercadoria': nota.mercadoria, 
            'data_emissao': nota.data.strftime("%d/%m/%Y"), 
            'status_nf': nota.get_status_display(), 
        } for nota in notas]
        return JsonResponse(data, safe=False)
    except Cliente.DoesNotExist:
        print(f"AJAX: Cliente com ID {cliente_id} não encontrado (em edição).")
        return JsonResponse([], safe=False)
    except Exception as e:
        print(f"AJAX: Erro inesperado na view load_notas_fiscais_edicao: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
def load_notas_fiscais_para_romaneio(request):
    cliente_id = request.GET.get('cliente_id')
    romaneio_id = request.GET.get('romaneio_id') # Pode ser None para adicionar novo romaneio

    notas_fiscais = NotaFiscal.objects.none()
    selected_notas_ids = []

    if cliente_id:
        # Notas do cliente com status 'Depósito'
        notas_deposito = NotaFiscal.objects.filter(cliente_id=cliente_id, status='Depósito')

        # Se for um romaneio existente, incluir as notas já vinculadas a ele
        if romaneio_id:
            try:
                romaneio_existente = RomaneioViagem.objects.get(pk=romaneio_id)
                notas_vinculadas = romaneio_existente.notas_fiscais.all()
                selected_notas_ids = list(notas_vinculadas.values_list('pk', flat=True))
                
                # Combine as notas em depósito com as já vinculadas (evitando duplicatas)
                notas_fiscais = (notas_deposito | notas_vinculadas).distinct().order_by('data', 'nota')
            except RomaneioViagem.DoesNotExist:
                pass # Romaneio não encontrado, apenas notas em depósito
        else:
            # Se for um novo romaneio, apenas notas em depósito
            notas_fiscais = notas_deposito.order_by('data', 'nota')
            
    # Renderiza o template parcial com as notas e as IDs das selecionadas
    html = render(request, 'notas/_notas_fiscais_checkboxes.html', {
        'notas_fiscais': notas_fiscais,
        'selected_notas_ids': selected_notas_ids, # Passa as IDs das notas já selecionadas
    }).content.decode('utf-8')
    
    return JsonResponse({'html': html})

# --------------------------------------------------------------------------------------
# Detalhes Views (já implementadas)
# --------------------------------------------------------------------------------------
def detalhes_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]
    context = {
        'motorista': motorista,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/detalhes_motorista.html', context)

def detalhes_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    romaneios_vinculados = nota.romaneios_vinculados.all().order_by('-data_emissao')
    context = {
        'nota': nota,
        'romaneios_vinculados': romaneios_vinculados,
    }
    return render(request, 'notas/detalhes_nota_fiscal.html', context)

def detalhes_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    context = {
        'cliente': cliente,
    }
    return render(request, 'notas/detalhes_cliente.html', context)

def detalhes_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    context = {
        'veiculo': veiculo,
    }
    return render(request, 'notas/detalhes_veiculo.html', context)
# --------------------------------------------------------------------------------------
# NOVA VIEW: Pesquisar Mercadorias no Depósito por Cliente
# --------------------------------------------------------------------------------------
def pesquisar_mercadorias_deposito(request):
    search_form = MercadoriaDepositoSearchForm(request.GET)
    mercadorias = NotaFiscal.objects.none()
    search_performed = False
    total_peso = 0
    total_valor = 0

    if request.GET and search_form.is_valid():
        search_performed = True
        
        # Filtrar apenas notas com status 'Depósito'
        queryset = NotaFiscal.objects.filter(status='Depósito')
        
        # Aplicar filtros do formulário
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
        
        # Ordenar por data de emissão (mais recente primeiro) e depois por número da nota
        mercadorias = queryset.order_by('-data', 'nota')
        
        # Calcular totais
        total_peso = sum(mercadoria.peso for mercadoria in mercadorias if mercadoria.peso)
        total_valor = sum(mercadoria.valor for mercadoria in mercadorias if mercadoria.valor)
    
    context = {
        'search_form': search_form,
        'mercadorias': mercadorias,
        'search_performed': search_performed,
        'total_peso': total_peso,
        'total_valor': total_valor,
    }
    return render(request, 'notas/pesquisar_mercadorias_deposito.html', context)

# --------------------------------------------------------------------------------------
# NOVA VIEW: Visualizar Romaneio para Impressão
# --------------------------------------------------------------------------------------
def visualizar_romaneio_para_impressao(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Verificar se o usuário tem permissão para imprimir este romaneio
    if request.user.is_cliente and request.user.cliente:
        # Cliente só pode imprimir romaneios que contêm suas notas fiscais
        if not romaneio.notas_fiscais.filter(cliente=request.user.cliente).exists():
            messages.error(request, 'Você não tem permissão para imprimir este romaneio.')
            return redirect('notas:meus_romaneios')
    
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('nota') # Pegar notas associadas

    context = {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
    }
    return render(request, 'notas/visualizar_romaneio_para_impressao.html', context)

# --------------------------------------------------------------------------------------
# Views de Autenticação
# --------------------------------------------------------------------------------------
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, CadastroUsuarioForm, AlterarSenhaForm
from .models import Usuario # Adicionado import para o modelo Usuario

def login_view(request):
    if request.user.is_authenticated:
        return redirect('notas:listar_notas_fiscais')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None and user.is_active:
                login(request, user)
                # Atualizar último acesso
                user.ultimo_acesso = timezone.now()
                user.save()
                
                messages.success(request, f'Bem-vindo, {user.get_full_name()}!')
                return redirect('notas:listar_notas_fiscais')
            else:
                messages.error(request, 'Nome de usuário ou senha inválidos.')
    else:
        form = LoginForm()
    
    return render(request, 'notas/auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Você foi desconectado com sucesso.')
    return redirect('notas:login')

@login_required
def alterar_senha(request):
    if request.method == 'POST':
        form = AlterarSenhaForm(request.POST)
        if form.is_valid():
            senha_atual = form.cleaned_data['senha_atual']
            nova_senha = form.cleaned_data['nova_senha']
            
            # Verificar senha atual
            if not request.user.check_password(senha_atual):
                messages.error(request, 'Senha atual incorreta.')
            else:
                # Alterar senha
                request.user.set_password(nova_senha)
                request.user.save()
                messages.success(request, 'Senha alterada com sucesso!')
                return redirect('notas:listar_notas_fiscais')
    else:
        form = AlterarSenhaForm()
    
    return render(request, 'notas/auth/alterar_senha.html', {'form': form})

@login_required
def perfil_usuario(request):
    return render(request, 'notas/auth/perfil.html')

# Decorators para verificar permissões
def is_admin(user):
    return user.is_authenticated and user.is_admin

def is_funcionario(user):
    return user.is_authenticated and (user.is_admin or user.is_funcionario)

def is_cliente(user):
    return user.is_authenticated and (user.is_admin or user.is_funcionario or user.is_cliente)

# View para clientes verem apenas suas notas fiscais
@login_required
@user_passes_test(is_cliente)
def minhas_notas_fiscais(request):
    # Obter parâmetro de filtro
    status_filter = request.GET.get('status', '')
    
    if request.user.is_cliente and request.user.cliente:
        # Cliente vê apenas suas notas
        notas_fiscais = NotaFiscal.objects.filter(cliente=request.user.cliente)
    else:
        # Admin e funcionários veem todas as notas
        notas_fiscais = NotaFiscal.objects.all()
    
    # Aplicar filtro por status se especificado
    if status_filter:
        if status_filter == 'deposito':
            notas_fiscais = notas_fiscais.filter(status='Depósito')
        elif status_filter == 'enviada':
            notas_fiscais = notas_fiscais.filter(status='Enviada')
    
    # Ordenar por data mais recente
    notas_fiscais = notas_fiscais.order_by('-data')
    
    return render(request, 'notas/auth/minhas_notas.html', {
        'notas_fiscais': notas_fiscais,
        'status_filter': status_filter
    })

@login_required
@user_passes_test(is_cliente)
def imprimir_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    # Verificar se o usuário tem permissão para ver esta nota
    if request.user.is_cliente and request.user.cliente != nota.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta nota fiscal.')
        return redirect('notas:minhas_notas_fiscais')
    
    return render(request, 'notas/auth/imprimir_nota_fiscal.html', {
        'nota': nota
    })

@login_required
@user_passes_test(is_cliente)
def meus_romaneios(request):
    if request.user.is_cliente and request.user.cliente:
        # Cliente vê apenas romaneios de suas notas
        romaneios = RomaneioViagem.objects.filter(
            notas_fiscais__cliente=request.user.cliente
        ).distinct().order_by('-data_emissao')
    else:
        # Admin e funcionários veem todos os romaneios
        romaneios = RomaneioViagem.objects.all().order_by('-data_emissao')
    
    return render(request, 'notas/auth/meus_romaneios.html', {
        'romaneios': romaneios
    })

# View para administradores cadastrarem novos usuários
@login_required
@user_passes_test(is_admin)
def cadastrar_usuario(request):
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuário {user.username} cadastrado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao cadastrar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'notas/auth/cadastrar_usuario.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'notas/auth/listar_usuarios.html', {'usuarios': usuarios})

@login_required
@user_passes_test(is_admin)
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            # Se a senha foi alterada, hash ela
            if form.cleaned_data.get('password1'):
                usuario.set_password(form.cleaned_data['password1'])
            form.save()
            messages.success(request, f'Usuário {usuario.username} atualizado com sucesso!')
            return redirect('notas:listar_usuarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar o usuário. Verifique os campos.')
    else:
        form = CadastroUsuarioForm(instance=usuario)
    
    return render(request, 'notas/auth/editar_usuario.html', {'form': form, 'usuario': usuario})

@login_required
@user_passes_test(is_admin)
def excluir_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # Não permitir excluir o próprio usuário
    if usuario == request.user:
        messages.error(request, 'Você não pode excluir seu próprio usuário.')
        return redirect('notas:listar_usuarios')
    
    if request.method == 'POST':
        try:
            username = usuario.username
            usuario.delete()
            messages.success(request, f'Usuário {username} excluído com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o usuário: {e}')
        return redirect('notas:listar_usuarios')
    
    return render(request, 'notas/auth/confirmar_exclusao_usuario.html', {'usuario': usuario})
