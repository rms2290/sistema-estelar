from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max 
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
import locale
from decimal import Decimal

# Importe todos os seus modelos
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, TabelaSeguro 

# Importe todos os seus formulários
from .forms import (
    NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm, RomaneioViagemForm,
    NotaFiscalSearchForm, ClienteSearchForm, MotoristaSearchForm, HistoricoConsultaForm,
    VeiculoSearchForm, RomaneioSearchForm, MercadoriaDepositoSearchForm, TabelaSeguroForm # Adicionado o novo formulário
)

def formatar_valor_brasileiro(valor, tipo='numero'):
    """
    Formata um valor decimal como número brasileiro (1.250,00)
    """
    if valor is None:
        return ''
    
    try:
        # Configurar locale para português brasileiro
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        # Fallback se o locale não estiver disponível
        pass
    
    try:
        # Converter para float e formatar
        float_value = float(valor)
        if float_value == 0:
            return '0' if tipo == 'numero' else 'R$ 0,00'
        
        # Formatar com separador de milhares e vírgula decimal
        if tipo == 'numero':
            formatted = f"{float_value:,.0f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:  # moeda
            formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            formatted = f"R$ {formatted}"
        
        return formatted
    except (ValueError, TypeError):
        return str(valor)

def formatar_peso_brasileiro(valor):
    """
    Formata um valor de peso como número brasileiro com unidade kg (1.250,00 kg)
    """
    if valor is None:
        return ''
    
    peso_formatado = formatar_valor_brasileiro(valor, 'numero')
    return f"{peso_formatado} kg"

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

def get_next_romaneio_generico_codigo():
    """Gera o próximo código sequencial de romaneio genérico no formato ROM-GEN-AAAA-MM-NNNN, começando de 100."""
    ano = timezone.now().year
    mes = timezone.now().month
    
    last_romaneio = RomaneioViagem.objects.filter(
        data_emissao__year=ano,
        data_emissao__month=mes,
        codigo__startswith='ROM-GEN'
    ).order_by('-codigo').first()

    next_sequence = 100  # Começa do 100
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 5 and parts[0] == 'ROM' and parts[1] == 'GEN' and int(parts[2]) == ano and int(parts[3]) == mes:
                next_sequence = int(parts[4]) + 1
        except (ValueError, IndexError):
            pass

    return f"ROM-GEN-{ano:04d}-{mes:02d}-{next_sequence:04d}"

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

@login_required
def excluir_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Verificar se o usuário é administrador
    if not request.user.is_admin:
        messages.error(request, 'Apenas administradores podem excluir clientes cadastrados.')
        return redirect('notas:listar_clientes')
    
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

def toggle_status_cliente(request, pk):
    """Ativa ou desativa um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        # Alternar o status
        if cliente.status == 'Ativo':
            cliente.status = 'Inativo'
            messages.success(request, f'Cliente {cliente.razao_social} foi desativado com sucesso!')
        else:
            cliente.status = 'Ativo'
            messages.success(request, f'Cliente {cliente.razao_social} foi ativado com sucesso!')
        
        cliente.save()
        return redirect('notas:detalhes_cliente', pk=cliente.pk)
    
    return redirect('notas:detalhes_cliente', pk=cliente.pk)

# --------------------------------------------------------------------------------------
# Views para Nota Fiscal
# --------------------------------------------------------------------------------------


def adicionar_nota_fiscal(request):
    if request.method == 'POST':
        form = NotaFiscalForm(request.POST)
        if form.is_valid():
            nota_fiscal = form.save(commit=False)
            nota_fiscal.status = 'Depósito' 
            nota_fiscal.save()
            messages.success(request, f'Nota Fiscal {nota_fiscal.nota} adicionada com sucesso!')

            if 'salvar_e_adicionar' in request.POST:
                # Retorna para a mesma página com formulário limpo
                form = NotaFiscalForm()
                return render(request, 'notas/adicionar_nota.html', {
                    'form': form,
                    'focus_nota': True  # Flag para focar no campo nota
                })
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


def adicionar_motorista(request):
    if request.method == 'POST':
        form = MotoristaForm(request.POST)
        if form.is_valid():
            motorista = form.save()
            messages.success(request, 'Motorista adicionado com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao adicionar o motorista. Verifique os campos.')
    else:
        form = MotoristaForm()
    
    context = {
        'form': form,
        'historico_consultas': None,  # Não há histórico para motoristas novos
    }
    return render(request, 'notas/adicionar_motorista.html', context)

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
            
            # Atualizar o campo numero_consulta do motorista com o número da última consulta
            motorista.numero_consulta = historico.numero_consulta
            motorista.save()
            
            messages.success(request, 'Consulta de risco registrada com sucesso!')
            return redirect('notas:editar_motorista', pk=motorista.pk)
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta. Verifique os campos.')
            return redirect('notas:editar_motorista', pk=motorista.pk)
    return redirect('notas:editar_motorista', pk=motorista.pk)

def registrar_consulta_motorista(request, pk):
    """Nova view para registrar consultas diretamente na tela de pesquisa de motoristas"""
    motorista = get_object_or_404(Motorista, pk=pk)
    
    if request.method == 'POST':
        form = HistoricoConsultaForm(request.POST)
        if form.is_valid():
            historico = form.save(commit=False)
            historico.motorista = motorista
            historico.save()
            
            # Atualizar o campo numero_consulta do motorista com o número da última consulta
            motorista.numero_consulta = historico.numero_consulta
            motorista.save()
            
            messages.success(request, 'Consulta registrada com sucesso!')
            return redirect('notas:listar_motoristas')
        else:
            messages.error(request, 'Houve um erro ao registrar a consulta. Verifique os campos.')
    else:
        form = HistoricoConsultaForm()
    
    # Buscar histórico das últimas 5 consultas
    historico_consultas = HistoricoConsulta.objects.filter(motorista=motorista).order_by('-data_consulta')[:5]
    
    context = {
        'motorista': motorista,
        'form': form,
        'historico_consultas': historico_consultas,
    }
    return render(request, 'notas/registrar_consulta_motorista.html', context) 

@login_required
def excluir_motorista(request, pk):
    motorista = get_object_or_404(Motorista, pk=pk)
    
    # Verificar se o usuário é administrador
    if not request.user.is_admin:
        messages.error(request, 'Apenas administradores podem excluir motoristas cadastrados.')
        return redirect('notas:listar_motoristas')
    
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

@login_required
def excluir_veiculo(request, pk):
    veiculo = get_object_or_404(Veiculo, pk=pk)
    
    # Verificar se o usuário é administrador
    if not is_admin(request.user):
        messages.error(request, 'Apenas administradores podem excluir veículos cadastrados.')
        return redirect('notas:listar_veiculos')
    
    if request.method == 'POST':
        try:
            # Verificar se o veículo está sendo usado em romaneios
            romaneios_principal = veiculo.romaneios_veiculo_principal.all()
            romaneios_reboque1 = veiculo.romaneios_reboque_1.all()
            romaneios_reboque2 = veiculo.romaneios_reboque_2.all()
            
            total_romaneios = romaneios_principal.count() + romaneios_reboque1.count() + romaneios_reboque2.count()
            
            if total_romaneios > 0:
                # Desvincular o veículo dos romaneios
                for romaneio in romaneios_principal:
                    romaneio.veiculo_principal = None
                    romaneio.save()
                for romaneio in romaneios_reboque1:
                    romaneio.reboque_1 = None
                    romaneio.save()
                for romaneio in romaneios_reboque2:
                    romaneio.reboque_2 = None
                    romaneio.save()
                messages.warning(request, f'Veículo desvinculado de {total_romaneios} romaneio(s) antes da exclusão.')
            
            veiculo.delete()
            messages.success(request, 'Unidade de Veículo excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir o veículo: {str(e)}')
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


def adicionar_romaneio(request):
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        # Configurar o queryset das notas fiscais baseado no cliente selecionado
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
                romaneio.status = 'Salvo'

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
                return redirect('notas:visualizar_romaneio_paisagem', pk=romaneio.pk)
            else: # Salvo
                # Redirecionar para detalhes (para poder continuar editando) ou para listar
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk) # Sugiro detalhes para salvo
        else:
            # Se o formulário não for válido, reconfigurar o queryset para manter as seleções
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
            
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio. Verifique os campos.')
    else:
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_codigo()

    context = {
        'form': form,
        'provisional_codigo': provisional_codigo,
    }
    return render(request, 'notas/adicionar_romaneio.html', context)

def adicionar_romaneio_generico(request):
    if request.method == 'POST':
        form = RomaneioViagemForm(request.POST)
        
        # Configurar o queryset das notas fiscais baseado no cliente selecionado
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
            
            romaneio.codigo = get_next_romaneio_generico_codigo()
            romaneio.data_emissao = form.cleaned_data['data_romaneio']
            
            if 'emitir' in request.POST:
                romaneio.status = 'Emitido'
            else: # Clicou em 'salvar' ou outro botão
                romaneio.status = 'Salvo'

            romaneio.save()
            form.save_m2m() # Salva a relação ManyToMany

            # Atualizar o status das notas fiscais associadas
            for nota_fiscal in romaneio.notas_fiscais.all():
                if romaneio.status == 'Emitido':
                    nota_fiscal.status = 'Enviada'
                else:
                    nota_fiscal.status = 'Depósito'
                nota_fiscal.save()

            messages.success(request, f'Romaneio Genérico {romaneio.codigo} ({romaneio.status}) salvo com sucesso!')
            
            # >>> MUDANÇA AQUI: Redirecionar para a tela de visualização se Emitido <<<
            if romaneio.status == 'Emitido':
                return redirect('notas:visualizar_romaneio_paisagem', pk=romaneio.pk)
            else: # Salvo
                # Redirecionar para detalhes (para poder continuar editando) ou para listar
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk) # Sugiro detalhes para salvo
        else:
            # Se o formulário não for válido, reconfigurar o queryset para manter as seleções
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
            
            messages.error(request, 'Houve um erro ao emitir/salvar o romaneio genérico. Verifique os campos.')
    else:
        form = RomaneioViagemForm()
        provisional_codigo = get_next_romaneio_generico_codigo()

    context = {
        'form': form,
        'provisional_codigo': provisional_codigo,
    }
    return render(request, 'notas/adicionar_romaneio_generico.html', context)

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
                romaneio.status = 'Salvo'
            
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
                return redirect('notas:visualizar_romaneio_paisagem', pk=romaneio.pk)
            else: # Rascunho
                return redirect('notas:detalhes_romaneio', pk=romaneio.pk) # Volta para os detalhes do romaneio
        else:
            # Se o formulário não for válido, reconfigurar o queryset para manter as seleções
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
            
            messages.error(request, 'Houve um erro ao atualizar o romaneio. Verifique os campos.')
    else: # GET request para edição
        form = RomaneioViagemForm(instance=romaneio)

    context = {
        'form': form,
        'romaneio': romaneio,
        'provisional_codigo': romaneio.codigo,
    }
    return render(request, 'notas/editar_romaneio.html', context)

@login_required
def excluir_romaneio(request, pk):
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Verificar se o romaneio foi emitido
    if romaneio.status == 'Emitido':
        # Se foi emitido, apenas administradores podem excluir
        if not request.user.is_admin:
            messages.error(request, 'Apenas administradores podem excluir romaneios que já foram emitidos.')
            return redirect('notas:listar_romaneios')
    
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
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
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
            'quantidade': formatar_valor_brasileiro(nota.quantidade, 'numero'), 
            'peso': formatar_peso_brasileiro(nota.peso), 
            'valor': formatar_valor_brasileiro(nota.valor, 'moeda'), 
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
            'quantidade': formatar_valor_brasileiro(nota.quantidade, 'numero'), 
            'peso': formatar_peso_brasileiro(nota.peso), 
            'valor': formatar_valor_brasileiro(nota.valor, 'moeda'), 
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
    
@login_required
def load_notas_fiscais_para_romaneio(request, cliente_id):
    romaneio_id = request.GET.get('romaneio_id') # Pode ser None para adicionar novo romaneio
    
    print(f"DEBUG: load_notas_fiscais_para_romaneio chamada. cliente_id={cliente_id}, romaneio_id={romaneio_id}")
    print(f"DEBUG: Método da requisição: {request.method}")
    print(f"DEBUG: URL da requisição: {request.path}")
    print(f"DEBUG: Parâmetros GET: {request.GET}")

    notas_fiscais = NotaFiscal.objects.none()
    selected_notas_ids = []

    if cliente_id:
        # Notas do cliente com status 'Depósito'
        notas_deposito = NotaFiscal.objects.filter(cliente_id=cliente_id, status='Depósito')
        print(f"DEBUG: Encontradas {notas_deposito.count()} notas em depósito para cliente {cliente_id}")
        
        # Debug: listar algumas notas encontradas
        for nota in notas_deposito[:3]:  # Primeiras 3 notas
            print(f"DEBUG: Nota encontrada - ID: {nota.id}, Número: {nota.nota}, Cliente: {nota.cliente.razao_social}")

        # Se for um romaneio existente, incluir as notas já vinculadas a ele
        if romaneio_id:
            try:
                romaneio_existente = RomaneioViagem.objects.get(pk=romaneio_id)
                notas_vinculadas = romaneio_existente.notas_fiscais.all()
                selected_notas_ids = list(notas_vinculadas.values_list('pk', flat=True))
                print(f"DEBUG: Encontradas {notas_vinculadas.count()} notas vinculadas ao romaneio {romaneio_id}")
                
                # Combine as notas em depósito com as já vinculadas (evitando duplicatas)
                notas_fiscais = (notas_deposito | notas_vinculadas).distinct().order_by('data', 'nota')
            except RomaneioViagem.DoesNotExist:
                print(f"DEBUG: Romaneio {romaneio_id} não encontrado")
                pass # Romaneio não encontrado, apenas notas em depósito
        else:
            # Se for um novo romaneio, apenas notas em depósito
            notas_fiscais = notas_deposito.order_by('data', 'nota')
            print(f"DEBUG: Usando apenas notas em depósito para novo romaneio")
            
    print(f"DEBUG: Total de notas fiscais retornadas: {notas_fiscais.count()}")
    
    # Renderiza o template parcial com as notas e as IDs das selecionadas
    context = {
        'notas_fiscais': notas_fiscais,
        'selected_notas_ids': selected_notas_ids, # Passa as IDs das notas já selecionadas
    }
    print(f"DEBUG: Contexto para template: {context}")
    
    html = render(request, 'notas/_notas_fiscais_checkboxes.html', context).content.decode('utf-8')
    
    print(f"DEBUG: HTML gerado com {len(html)} caracteres")
    print(f"DEBUG: Primeiros 200 caracteres do HTML: {html[:200]}")
    
    return JsonResponse({'html': html})

# --------------------------------------------------------------------------------------
# Detalhes Views (já implementadas)
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
# Views de Autenticação
# --------------------------------------------------------------------------------------
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, CadastroUsuarioForm, AlterarSenhaForm
from .models import Usuario # Adicionado import para o modelo Usuario

def login_view(request):
    if request.user.is_authenticated:
        return redirect('notas:dashboard')
    
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
                return redirect('notas:dashboard')
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
                return redirect('notas:dashboard')
    else:
        form = AlterarSenhaForm()
    
    return render(request, 'notas/auth/alterar_senha.html', {'form': form})

@login_required
def perfil_usuario(request):
    return render(request, 'notas/auth/perfil.html')

# Decorators para verificar permissões
def is_admin(user):
    return user.is_authenticated and user.tipo_usuario == 'admin'

def is_funcionario(user):
    return user.is_authenticated and user.tipo_usuario in ['admin', 'funcionario']

def is_cliente(user):
    return user.is_authenticated and user.tipo_usuario in ['admin', 'funcionario', 'cliente']

# View para clientes verem apenas suas notas fiscais
@login_required
@user_passes_test(is_cliente)
def minhas_notas_fiscais(request):
    # Obter parâmetro de filtro
    status_filter = request.GET.get('status', 'deposito')  # Padrão agora é 'deposito'
    
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        # Cliente vê apenas suas notas
        notas_fiscais = NotaFiscal.objects.filter(cliente=request.user.cliente)
    else:
        # Admin e funcionários veem todas as notas
        notas_fiscais = NotaFiscal.objects.all()
    
    # Aplicar filtro por status
    if status_filter == 'deposito':
        notas_fiscais = notas_fiscais.filter(status='Depósito')
    elif status_filter == 'enviada':
        notas_fiscais = notas_fiscais.filter(status='Enviada')
    
    # Ordenar por data mais recente
    notas_fiscais = notas_fiscais.order_by('-data')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_fiscais if nota.peso)
    total_valor = sum(nota.valor for nota in notas_fiscais if nota.valor)
    
    return render(request, 'notas/auth/minhas_notas.html', {
        'notas_fiscais': notas_fiscais,
        'status_filter': status_filter,
        'total_peso': total_peso,
        'total_valor': total_valor
    })

@login_required
@user_passes_test(is_cliente)
def imprimir_nota_fiscal(request, pk):
    nota = get_object_or_404(NotaFiscal, pk=pk)
    
    # Verificar se o usuário tem permissão para ver esta nota
    if request.user.tipo_usuario == 'cliente' and request.user.cliente != nota.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta nota fiscal.')
        return redirect('notas:minhas_notas_fiscais')
    
    return render(request, 'notas/auth/imprimir_nota_fiscal.html', {
        'nota': nota
    })

@login_required
@user_passes_test(is_cliente)
def imprimir_relatorio_deposito(request):
    # Obter apenas notas em depósito do cliente
    if request.user.tipo_usuario == 'cliente' and request.user.cliente:
        notas_fiscais = NotaFiscal.objects.filter(
            cliente=request.user.cliente,
            status='Depósito'
        ).order_by('data')
    else:
        # Admin e funcionários veem todas as notas em depósito
        notas_fiscais = NotaFiscal.objects.filter(status='Depósito').order_by('data')

    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_fiscais)
    total_valor = sum(nota.valor for nota in notas_fiscais)

    return render(request, 'notas/auth/imprimir_relatorio_deposito.html', {
        'notas_fiscais': notas_fiscais,
        'total_peso': total_peso,
        'total_valor': total_valor,
        'cliente': request.user.cliente if request.user.cliente else None
    })

@login_required
def imprimir_romaneio_novo(request, pk):
    """View para imprimir romaneio usando o novo template baseado no relatório de mercadorias"""
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Obter notas fiscais vinculadas ao romaneio
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('data')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_romaneadas)
    total_valor = sum(nota.valor for nota in notas_romaneadas)
    
    return render(request, 'notas/visualizar_romaneio_para_impressao.html', {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'total_peso': total_peso,
        'total_valor': total_valor
    })

@login_required
@user_passes_test(is_cliente)
def meus_romaneios(request):
    if request.user.tipo_usuario.upper() == 'CLIENTE' and request.user.cliente:
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

# --------------------------------------------------------------------------------------
# Views para Tabela de Seguros
# --------------------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def listar_tabela_seguros(request):
    """Lista todos os registros da tabela de seguros"""
    tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    # Se não existem registros, criar automaticamente para todos os estados
    if not tabela_seguros.exists():
        for estado_uf, estado_nome in TabelaSeguro.ESTADOS_BRASIL:
            TabelaSeguro.objects.create(
                estado=estado_uf,
                percentual_seguro=0.00
            )
        tabela_seguros = TabelaSeguro.objects.all().order_by('estado')
    
    context = {
        'tabela_seguros': tabela_seguros,
    }
    return render(request, 'notas/listar_tabela_seguros.html', context)

@login_required
@user_passes_test(is_admin)
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

@login_required
@user_passes_test(is_admin)
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
                
                # Adicionar mensagem de sucesso
                messages.success(request, f'Percentual de seguro para {tabela_seguro.get_estado_display()} atualizado para {percentual_float}%')
                
                return JsonResponse({
                    'success': True,
                    'message': f'Percentual atualizado para {percentual_float}%',
                    'percentual': percentual_float
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Percentual deve estar entre 0% e 100%'
                })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Valor inválido para percentual'
            })
    
    return JsonResponse({'success': False, 'message': 'Método não permitido'})

@login_required
@user_passes_test(is_admin)
def totalizador_por_estado(request):
    """
    View para totalizador por estado com filtros de data
    """
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Inicializar variáveis
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    if data_inicial and data_final:
        try:
            # Converter strings para objetos datetime
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
            
            # Buscar romaneios emitidos no período
            romaneios_periodo = RomaneioViagem.objects.filter(
                data_emissao__date__range=[data_inicial_obj, data_final_obj],
                status='Emitido'
            ).select_related('cliente').prefetch_related('notas_fiscais')
            
            # Buscar todos os percentuais de seguro de uma vez
            tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
            
            # Agrupar por estado do cliente e calcular totais
            # Usar um dicionário para agrupar os dados por estado
            estados_agrupados = {}
            
            for romaneio in romaneios_periodo:
                estado_cliente = romaneio.cliente.estado
                if not estado_cliente:  # Ignorar estados vazios
                    continue
                
                # Inicializar dados do estado se não existir
                if estado_cliente not in estados_agrupados:
                    estados_agrupados[estado_cliente] = {
                        'estado': estado_cliente,
                        'nome_estado': dict(TabelaSeguro.ESTADOS_BRASIL).get(estado_cliente, estado_cliente),
                        'total_valor': Decimal('0.0'),
                        'quantidade_romaneios': 0,
                        'romaneios_ids': set()
                    }
                
                # Adicionar valores das notas fiscais do romaneio
                for nota in romaneio.notas_fiscais.all():
                    estados_agrupados[estado_cliente]['total_valor'] += nota.valor
                
                # Contar romaneios únicos (usar set para evitar duplicatas)
                estados_agrupados[estado_cliente]['romaneios_ids'].add(romaneio.id)
            
            # Processar dados agrupados
            for estado, dados in estados_agrupados.items():
                total_valor_estado = dados['total_valor']
                quantidade_romaneios = len(dados['romaneios_ids'])
                
                # Buscar percentual de seguro para o estado
                percentual_seguro = tabelas_seguro.get(estado, Decimal('0.0'))
                
                # Calcular valor do seguro
                valor_seguro_estado = total_valor_estado * (percentual_seguro / Decimal('100.0'))
                
                if total_valor_estado > 0:  # Só incluir estados com valores
                    resultados.append({
                        'estado': estado,
                        'nome_estado': dados['nome_estado'],
                        'total_valor': total_valor_estado,
                        'percentual_seguro': percentual_seguro,
                        'valor_seguro': valor_seguro_estado,
                        'quantidade_romaneios': quantidade_romaneios
                    })
                    
                    total_geral += total_valor_estado
                    total_seguro_geral += valor_seguro_estado
            
            # Ordenar por valor total (maior primeiro)
            resultados.sort(key=lambda x: x['total_valor'], reverse=True)
            
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
    
    context = {
        'data_inicial': data_inicial,
        'data_final': data_final,
        'resultados': resultados,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
        'tem_resultados': len(resultados) > 0
    }
    
    return render(request, 'notas/totalizador_por_estado.html', context)


@login_required
@user_passes_test(is_admin)
def totalizador_por_estado_pdf(request):
    """
    Gera relatório PDF para Totalizador por Estado
    """
    from .utils.relatorios import gerar_relatorio_pdf_totalizador_estado, gerar_resposta_pdf
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Obter parâmetros
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    
    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_estado')
    
    try:
        # Converter strings para objetos datetime
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
        
        # Buscar romaneios emitidos no período
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        # Buscar todos os percentuais de seguro de uma vez
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        
        # Agrupar por estado do cliente e calcular totais
        estados_agrupados = {}
        
        for romaneio in romaneios_periodo:
            estado_cliente = romaneio.cliente.estado
            if not estado_cliente:
                continue
            
            if estado_cliente not in estados_agrupados:
                estados_agrupados[estado_cliente] = {
                    'estado': estado_cliente,
                    'nome_estado': dict(TabelaSeguro.ESTADOS_BRASIL).get(estado_cliente, estado_cliente),
                    'total_valor': Decimal('0.0'),
                    'quantidade_romaneios': 0,
                    'romaneios_ids': set()
                }
            
            for nota in romaneio.notas_fiscais.all():
                estados_agrupados[estado_cliente]['total_valor'] += nota.valor
            
            estados_agrupados[estado_cliente]['romaneios_ids'].add(romaneio.id)
        
        # Processar dados agrupados
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')
        
        for estado, dados in estados_agrupados.items():
            total_valor_estado = dados['total_valor']
            quantidade_romaneios = len(dados['romaneios_ids'])
            
            percentual_seguro = tabelas_seguro.get(estado, Decimal('0.0'))
            valor_seguro_estado = total_valor_estado * (percentual_seguro / Decimal('100.0'))
            
            if total_valor_estado > 0:
                resultados.append({
                    'estado': estado,
                    'nome_estado': dados['nome_estado'],
                    'total_valor': total_valor_estado,
                    'percentual_seguro': percentual_seguro,
                    'valor_seguro': valor_seguro_estado,
                    'quantidade_romaneios': quantidade_romaneios
                })
                
                total_geral += total_valor_estado
                total_seguro_geral += valor_seguro_estado
        
        # Ordenar por valor total
        resultados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Gerar PDF
        pdf_content = gerar_relatorio_pdf_totalizador_estado(
            resultados, data_inicial_obj, data_final_obj, total_geral, total_seguro_geral
        )
        
        # Nome do arquivo
        nome_arquivo = f"totalizador_por_estado_{data_inicial}_{data_final}.pdf"
        
        return gerar_resposta_pdf(pdf_content, nome_arquivo)
        
    except ValueError:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_estado')


@login_required
@user_passes_test(is_admin)
def totalizador_por_estado_excel(request):
    """
    Gera relatório Excel para Totalizador por Estado
    """
    from .utils.relatorios import gerar_relatorio_excel_totalizador_estado, gerar_resposta_excel
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Obter parâmetros
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    
    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_estado')
    
    try:
        # Converter strings para objetos datetime
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
        
        # Buscar romaneios emitidos no período
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        # Buscar todos os percentuais de seguro de uma vez
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        
        # Agrupar por estado do cliente e calcular totais
        estados_agrupados = {}
        
        for romaneio in romaneios_periodo:
            estado_cliente = romaneio.cliente.estado
            if not estado_cliente:
                continue
            
            if estado_cliente not in estados_agrupados:
                estados_agrupados[estado_cliente] = {
                    'estado': estado_cliente,
                    'nome_estado': dict(TabelaSeguro.ESTADOS_BRASIL).get(estado_cliente, estado_cliente),
                    'total_valor': Decimal('0.0'),
                    'quantidade_romaneios': 0,
                    'romaneios_ids': set()
                }
            
            for nota in romaneio.notas_fiscais.all():
                estados_agrupados[estado_cliente]['total_valor'] += nota.valor
            
            estados_agrupados[estado_cliente]['romaneios_ids'].add(romaneio.id)
        
        # Processar dados agrupados
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')
        
        for estado, dados in estados_agrupados.items():
            total_valor_estado = dados['total_valor']
            quantidade_romaneios = len(dados['romaneios_ids'])
            
            percentual_seguro = tabelas_seguro.get(estado, Decimal('0.0'))
            valor_seguro_estado = total_valor_estado * (percentual_seguro / Decimal('100.0'))
            
            if total_valor_estado > 0:
                resultados.append({
                    'estado': estado,
                    'nome_estado': dados['nome_estado'],
                    'total_valor': total_valor_estado,
                    'percentual_seguro': percentual_seguro,
                    'valor_seguro': valor_seguro_estado,
                    'quantidade_romaneios': quantidade_romaneios
                })
                
                total_geral += total_valor_estado
                total_seguro_geral += valor_seguro_estado
        
        # Ordenar por valor total
        resultados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Gerar Excel
        excel_content = gerar_relatorio_excel_totalizador_estado(
            resultados, data_inicial_obj, data_final_obj, total_geral, total_seguro_geral
        )
        
        # Nome do arquivo
        nome_arquivo = f"totalizador_por_estado_{data_inicial}_{data_final}.xlsx"
        
        return gerar_resposta_excel(excel_content, nome_arquivo)
        
    except ValueError:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_estado')


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente(request):
    """
    View para totalizador por cliente com filtros de data
    """
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Inicializar variáveis
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    resultados = []
    resumo_estados = []
    lista_hierarquica = []
    total_geral = Decimal('0.0')
    total_seguro_geral = Decimal('0.0')
    
    if data_inicial and data_final:
        try:
            # Converter strings para objetos datetime
            data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
            data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
            
            # Buscar romaneios emitidos no período
            romaneios_periodo = RomaneioViagem.objects.filter(
                data_emissao__date__range=[data_inicial_obj, data_final_obj],
                status='Emitido'
            ).select_related('cliente').prefetch_related('notas_fiscais')
            
            # Buscar todos os percentuais de seguro de uma vez
            tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
            
            # Agrupar por cliente e calcular totais
            clientes_agrupados = {}
            
            for romaneio in romaneios_periodo:
                cliente = romaneio.cliente
                if not cliente:
                    continue
                
                # Inicializar dados do cliente se não existir
                if cliente.id not in clientes_agrupados:
                    clientes_agrupados[cliente.id] = {
                        'cliente': cliente,
                        'total_valor': Decimal('0.0'),
                        'quantidade_romaneios': 0,
                        'romaneios_ids': set(),
                        'estados_envolvidos': set()
                    }
                
                # Adicionar valores das notas fiscais do romaneio
                for nota in romaneio.notas_fiscais.all():
                    clientes_agrupados[cliente.id]['total_valor'] += nota.valor
                
                # Contar romaneios únicos (usar set para evitar duplicatas)
                clientes_agrupados[cliente.id]['romaneios_ids'].add(romaneio.id)
                
                # Coletar estados envolvidos
                if cliente.estado:
                    clientes_agrupados[cliente.id]['estados_envolvidos'].add(cliente.estado)
            
            # Processar dados agrupados
            for cliente_id, dados in clientes_agrupados.items():
                total_valor_cliente = dados['total_valor']
                quantidade_romaneios = len(dados['romaneios_ids'])
                cliente = dados['cliente']
                
                # Calcular seguro baseado no estado do cliente
                percentual_seguro = Decimal('0.0')
                if cliente.estado:
                    percentual_seguro = tabelas_seguro.get(cliente.estado, Decimal('0.0'))
                
                valor_seguro_cliente = total_valor_cliente * (percentual_seguro / Decimal('100.0'))
                
                if total_valor_cliente > 0:  # Só incluir clientes com valores
                    # Obter nome do estado
                    nome_estado = ''
                    if cliente.estado:
                        nome_estado = dict(TabelaSeguro.ESTADOS_BRASIL).get(cliente.estado, cliente.estado)
                    
                    resultados.append({
                        'cliente': cliente,
                        'total_valor': total_valor_cliente,
                        'percentual_seguro': percentual_seguro,
                        'valor_seguro': valor_seguro_cliente,
                        'quantidade_romaneios': quantidade_romaneios,
                        'estado': cliente.estado or 'N/A',
                        'nome_estado': nome_estado,
                        'estados_envolvidos': list(dados['estados_envolvidos'])
                    })
                    
                    total_geral += total_valor_cliente
                    total_seguro_geral += valor_seguro_cliente
            
            # Ordenar por valor total (maior primeiro)
            resultados.sort(key=lambda x: x['total_valor'], reverse=True)
            
            # Criar estrutura hierárquica agrupada por estado
            estados_agrupados = {}
            for resultado in resultados:
                estado = resultado['estado']
                if estado not in estados_agrupados:
                    estados_agrupados[estado] = {
                        'estado': estado,
                        'nome_estado': resultado['nome_estado'],
                        'clientes': [],
                        'quantidade_clientes': 0,
                        'quantidade_romaneios': 0,
                        'total_valor': Decimal('0.0'),
                        'total_seguro': Decimal('0.0')
                    }
                
                # Adicionar cliente ao estado
                estados_agrupados[estado]['clientes'].append(resultado)
                estados_agrupados[estado]['quantidade_clientes'] += 1
                estados_agrupados[estado]['quantidade_romaneios'] += resultado['quantidade_romaneios']
                estados_agrupados[estado]['total_valor'] += resultado['total_valor']
                estados_agrupados[estado]['total_seguro'] += resultado['valor_seguro']
            
            # Converter para lista e ordenar por valor total
            resumo_estados = list(estados_agrupados.values())
            resumo_estados.sort(key=lambda x: x['total_valor'], reverse=True)
            
            # Criar lista hierárquica para exibição
            lista_hierarquica = []
            for estado_info in resumo_estados:
                # Adicionar cabeçalho do estado
                lista_hierarquica.append({
                    'tipo': 'estado',
                    'estado': estado_info['estado'],
                    'nome_estado': estado_info['nome_estado'],
                    'quantidade_clientes': estado_info['quantidade_clientes'],
                    'quantidade_romaneios': estado_info['quantidade_romaneios'],
                    'total_valor': estado_info['total_valor'],
                    'total_seguro': estado_info['total_seguro']
                })
                
                # Adicionar clientes do estado
                for cliente in estado_info['clientes']:
                    lista_hierarquica.append({
                        'tipo': 'cliente',
                        'cliente': cliente['cliente'],
                        'estado': cliente['estado'],
                        'nome_estado': cliente['nome_estado'],
                        'quantidade_romaneios': cliente['quantidade_romaneios'],
                        'total_valor': cliente['total_valor'],
                        'percentual_seguro': cliente['percentual_seguro'],
                        'valor_seguro': cliente['valor_seguro']
                    })
                
                # Adicionar linha de total do estado
                lista_hierarquica.append({
                    'tipo': 'total_estado',
                    'estado': estado_info['estado'],
                    'nome_estado': estado_info['nome_estado'],
                    'quantidade_clientes': estado_info['quantidade_clientes'],
                    'quantidade_romaneios': estado_info['quantidade_romaneios'],
                    'total_valor': estado_info['total_valor'],
                    'total_seguro': estado_info['total_seguro']
                })
            
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
            resumo_estados = []
            lista_hierarquica = []
    
    context = {
        'data_inicial': data_inicial,
        'data_final': data_final,
        'resultados': resultados,
        'resumo_estados': resumo_estados,
        'lista_hierarquica': lista_hierarquica,
        'total_geral': total_geral,
        'total_seguro_geral': total_seguro_geral,
        'tem_resultados': len(resultados) > 0
    }
    
    return render(request, 'notas/totalizador_por_cliente.html', context)


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente_pdf(request):
    """
    Gera relatório PDF para Totalizador por Cliente
    """
    from .utils.relatorios import gerar_relatorio_pdf_totalizador_cliente, gerar_resposta_pdf
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Obter parâmetros
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    
    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_cliente')
    
    try:
        # Converter strings para objetos datetime
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
        
        # Buscar romaneios emitidos no período
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        # Buscar todos os percentuais de seguro de uma vez
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        
        # Agrupar por cliente e calcular totais
        clientes_agrupados = {}
        
        for romaneio in romaneios_periodo:
            cliente = romaneio.cliente
            if not cliente:
                continue
            
            if cliente.id not in clientes_agrupados:
                clientes_agrupados[cliente.id] = {
                    'cliente': cliente,
                    'total_valor': Decimal('0.0'),
                    'quantidade_romaneios': 0,
                    'romaneios_ids': set(),
                    'estados_envolvidos': set()
                }
            
            for nota in romaneio.notas_fiscais.all():
                clientes_agrupados[cliente.id]['total_valor'] += nota.valor
            
            clientes_agrupados[cliente.id]['romaneios_ids'].add(romaneio.id)
            
            if cliente.estado:
                clientes_agrupados[cliente.id]['estados_envolvidos'].add(cliente.estado)
        
        # Processar dados agrupados
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')
        
        for cliente_id, dados in clientes_agrupados.items():
            total_valor_cliente = dados['total_valor']
            quantidade_romaneios = len(dados['romaneios_ids'])
            cliente = dados['cliente']
            
            percentual_seguro = Decimal('0.0')
            if cliente.estado:
                percentual_seguro = tabelas_seguro.get(cliente.estado, Decimal('0.0'))
            
            valor_seguro_cliente = total_valor_cliente * (percentual_seguro / Decimal('100.0'))
            
            if total_valor_cliente > 0:
                resultados.append({
                    'cliente': cliente,
                    'total_valor': total_valor_cliente,
                    'percentual_seguro': percentual_seguro,
                    'valor_seguro': valor_seguro_cliente,
                    'quantidade_romaneios': quantidade_romaneios,
                    'estados_envolvidos': list(dados['estados_envolvidos'])
                })
                
                total_geral += total_valor_cliente
                total_seguro_geral += valor_seguro_cliente
        
        # Ordenar por valor total
        resultados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Criar estrutura hierárquica agrupada por estado
        estados_agrupados = {}
        for resultado in resultados:
            cliente = resultado['cliente']
            estado = cliente.estado or 'N/A'
            
            # Obter nome do estado
            nome_estado = ''
            if cliente.estado:
                nome_estado = dict(TabelaSeguro.ESTADOS_BRASIL).get(cliente.estado, cliente.estado)
            
            if estado not in estados_agrupados:
                estados_agrupados[estado] = {
                    'estado': estado,
                    'nome_estado': nome_estado,
                    'clientes': [],
                    'quantidade_clientes': 0,
                    'quantidade_romaneios': 0,
                    'total_valor': Decimal('0.0'),
                    'total_seguro': Decimal('0.0')
                }
            
            # Adicionar cliente ao estado
            estados_agrupados[estado]['clientes'].append(resultado)
            estados_agrupados[estado]['quantidade_clientes'] += 1
            estados_agrupados[estado]['quantidade_romaneios'] += resultado['quantidade_romaneios']
            estados_agrupados[estado]['total_valor'] += resultado['total_valor']
            estados_agrupados[estado]['total_seguro'] += resultado['valor_seguro']
        
        # Converter para lista e ordenar por valor total
        resumo_estados = list(estados_agrupados.values())
        resumo_estados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Criar lista hierárquica para exibição
        lista_hierarquica = []
        for estado_info in resumo_estados:
            # Adicionar cabeçalho do estado
            lista_hierarquica.append({
                'tipo': 'estado',
                'estado': estado_info['estado'],
                'nome_estado': estado_info['nome_estado'],
                'quantidade_clientes': estado_info['quantidade_clientes'],
                'quantidade_romaneios': estado_info['quantidade_romaneios'],
                'total_valor': estado_info['total_valor'],
                'total_seguro': estado_info['total_seguro']
            })
            
            # Adicionar clientes do estado
            for cliente in estado_info['clientes']:
                lista_hierarquica.append({
                    'tipo': 'cliente',
                    'cliente': cliente['cliente'],
                    'estado': cliente['cliente'].estado or 'N/A',
                    'nome_estado': estado_info['nome_estado'],
                    'quantidade_romaneios': cliente['quantidade_romaneios'],
                    'total_valor': cliente['total_valor'],
                    'percentual_seguro': cliente['percentual_seguro'],
                    'valor_seguro': cliente['valor_seguro']
                })
            
            # Adicionar linha de total do estado
            lista_hierarquica.append({
                'tipo': 'total_estado',
                'estado': estado_info['estado'],
                'nome_estado': estado_info['nome_estado'],
                'quantidade_clientes': estado_info['quantidade_clientes'],
                'quantidade_romaneios': estado_info['quantidade_romaneios'],
                'total_valor': estado_info['total_valor'],
                'total_seguro': estado_info['total_seguro']
            })
        
        # Gerar PDF
        pdf_content = gerar_relatorio_pdf_totalizador_cliente(
            lista_hierarquica, data_inicial_obj, data_final_obj, total_geral, total_seguro_geral
        )
        
        # Nome do arquivo
        nome_arquivo = f"totalizador_por_cliente_{data_inicial}_{data_final}.pdf"
        
        return gerar_resposta_pdf(pdf_content, nome_arquivo)
        
    except ValueError:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_cliente')


@login_required
@user_passes_test(is_admin)
def totalizador_por_cliente_excel(request):
    """
    Gera relatório Excel para Totalizador por Cliente
    """
    from .utils.relatorios import gerar_relatorio_excel_totalizador_cliente, gerar_resposta_excel
    from django.db.models import Sum, Q
    from datetime import datetime
    
    # Obter parâmetros
    data_inicial = request.GET.get('data_inicial', '')
    data_final = request.GET.get('data_final', '')
    
    if not data_inicial or not data_final:
        messages.error(request, 'É necessário informar as datas inicial e final.')
        return redirect('notas:totalizador_por_cliente')
    
    try:
        # Converter strings para objetos datetime
        data_inicial_obj = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        data_final_obj = datetime.strptime(data_final, '%Y-%m-%d').date()
        
        # Buscar romaneios emitidos no período
        romaneios_periodo = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicial_obj, data_final_obj],
            status='Emitido'
        ).select_related('cliente').prefetch_related('notas_fiscais')
        
        # Buscar todos os percentuais de seguro de uma vez
        tabelas_seguro = {ts.estado: ts.percentual_seguro for ts in TabelaSeguro.objects.all()}
        
        # Agrupar por cliente e calcular totais
        clientes_agrupados = {}
        
        for romaneio in romaneios_periodo:
            cliente = romaneio.cliente
            if not cliente:
                continue
            
            if cliente.id not in clientes_agrupados:
                clientes_agrupados[cliente.id] = {
                    'cliente': cliente,
                    'total_valor': Decimal('0.0'),
                    'quantidade_romaneios': 0,
                    'romaneios_ids': set(),
                    'estados_envolvidos': set()
                }
            
            for nota in romaneio.notas_fiscais.all():
                clientes_agrupados[cliente.id]['total_valor'] += nota.valor
            
            clientes_agrupados[cliente.id]['romaneios_ids'].add(romaneio.id)
            
            if cliente.estado:
                clientes_agrupados[cliente.id]['estados_envolvidos'].add(cliente.estado)
        
        # Processar dados agrupados
        resultados = []
        total_geral = Decimal('0.0')
        total_seguro_geral = Decimal('0.0')
        
        for cliente_id, dados in clientes_agrupados.items():
            total_valor_cliente = dados['total_valor']
            quantidade_romaneios = len(dados['romaneios_ids'])
            cliente = dados['cliente']
            
            percentual_seguro = Decimal('0.0')
            if cliente.estado:
                percentual_seguro = tabelas_seguro.get(cliente.estado, Decimal('0.0'))
            
            valor_seguro_cliente = total_valor_cliente * (percentual_seguro / Decimal('100.0'))
            
            if total_valor_cliente > 0:
                resultados.append({
                    'cliente': cliente,
                    'total_valor': total_valor_cliente,
                    'percentual_seguro': percentual_seguro,
                    'valor_seguro': valor_seguro_cliente,
                    'quantidade_romaneios': quantidade_romaneios,
                    'estados_envolvidos': list(dados['estados_envolvidos'])
                })
                
                total_geral += total_valor_cliente
                total_seguro_geral += valor_seguro_cliente
        
        # Ordenar por valor total
        resultados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Criar estrutura hierárquica agrupada por estado
        estados_agrupados = {}
        for resultado in resultados:
            cliente = resultado['cliente']
            estado = cliente.estado or 'N/A'
            
            # Obter nome do estado
            nome_estado = ''
            if cliente.estado:
                nome_estado = dict(TabelaSeguro.ESTADOS_BRASIL).get(cliente.estado, cliente.estado)
            
            if estado not in estados_agrupados:
                estados_agrupados[estado] = {
                    'estado': estado,
                    'nome_estado': nome_estado,
                    'clientes': [],
                    'quantidade_clientes': 0,
                    'quantidade_romaneios': 0,
                    'total_valor': Decimal('0.0'),
                    'total_seguro': Decimal('0.0')
                }
            
            # Adicionar cliente ao estado
            estados_agrupados[estado]['clientes'].append(resultado)
            estados_agrupados[estado]['quantidade_clientes'] += 1
            estados_agrupados[estado]['quantidade_romaneios'] += resultado['quantidade_romaneios']
            estados_agrupados[estado]['total_valor'] += resultado['total_valor']
            estados_agrupados[estado]['total_seguro'] += resultado['valor_seguro']
        
        # Converter para lista e ordenar por valor total
        resumo_estados = list(estados_agrupados.values())
        resumo_estados.sort(key=lambda x: x['total_valor'], reverse=True)
        
        # Criar lista hierárquica para exibição
        lista_hierarquica = []
        for estado_info in resumo_estados:
            # Adicionar cabeçalho do estado
            lista_hierarquica.append({
                'tipo': 'estado',
                'estado': estado_info['estado'],
                'nome_estado': estado_info['nome_estado'],
                'quantidade_clientes': estado_info['quantidade_clientes'],
                'quantidade_romaneios': estado_info['quantidade_romaneios'],
                'total_valor': estado_info['total_valor'],
                'total_seguro': estado_info['total_seguro']
            })
            
            # Adicionar clientes do estado
            for cliente in estado_info['clientes']:
                lista_hierarquica.append({
                    'tipo': 'cliente',
                    'cliente': cliente['cliente'],
                    'estado': cliente['cliente'].estado or 'N/A',
                    'nome_estado': estado_info['nome_estado'],
                    'quantidade_romaneios': cliente['quantidade_romaneios'],
                    'total_valor': cliente['total_valor'],
                    'percentual_seguro': cliente['percentual_seguro'],
                    'valor_seguro': cliente['valor_seguro']
                })
            
            # Adicionar linha de total do estado
            lista_hierarquica.append({
                'tipo': 'total_estado',
                'estado': estado_info['estado'],
                'nome_estado': estado_info['nome_estado'],
                'quantidade_clientes': estado_info['quantidade_clientes'],
                'quantidade_romaneios': estado_info['quantidade_romaneios'],
                'total_valor': estado_info['total_valor'],
                'total_seguro': estado_info['total_seguro']
            })
        
        # Gerar Excel
        excel_content = gerar_relatorio_excel_totalizador_cliente(
            lista_hierarquica, data_inicial_obj, data_final_obj, total_geral, total_seguro_geral
        )
        
        # Nome do arquivo
        nome_arquivo = f"totalizador_por_cliente_{data_inicial}_{data_final}.xlsx"
        
        return gerar_resposta_excel(excel_content, nome_arquivo)
        
    except ValueError:
        messages.error(request, 'Formato de data inválido. Use YYYY-MM-DD.')
        return redirect('notas:totalizador_por_cliente')


@login_required
@user_passes_test(is_admin)
def fechamento_frete(request):
    """View para o relatório de fechamento de frete."""
    return render(request, 'notas/relatorios/fechamento_frete.html')

@login_required
@user_passes_test(is_admin)
def cobranca_mensal(request):
    """View para o relatório de cobrança mensal."""
    return render(request, 'notas/relatorios/cobranca_mensal.html')

@login_required
@user_passes_test(is_admin)
def cobranca_carregamento(request):
    """View para o relatório de cobrança de carregamento."""
    return render(request, 'notas/relatorios/cobranca_carregamento.html')

@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    context = {
        'title': 'Dashboard - Agência Estelar',
        'user': request.user,
    }
    return render(request, 'notas/dashboard.html', context)

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
        veiculo_principal = search_form.cleaned_data.get('veiculo_principal')
        status = search_form.cleaned_data.get('status')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if codigo:
            queryset = queryset.filter(codigo__icontains=codigo)
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if motorista:
            queryset = queryset.filter(motorista=motorista)
        if veiculo_principal:
            queryset = queryset.filter(veiculo_principal=veiculo_principal)
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
def pesquisar_mercadorias_deposito(request):
    """Pesquisa mercadorias em depósito"""
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

# --------------------------------------------------------------------------------------
# NOVA VIEW PARA FILTRAR VEÍCULOS BASEADO NO TIPO DE COMPOSIÇÃO
# --------------------------------------------------------------------------------------
def filtrar_veiculos_por_composicao(request):
    """View para filtrar veículos baseado no tipo de composição selecionado"""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        tipo_composicao = request.GET.get('tipo_composicao')
        
        if tipo_composicao:
            # Definir filtros baseados no tipo de composição
            if tipo_composicao in ['Carro']:
                veiculos = Veiculo.objects.filter(tipo_unidade='Carro').order_by('placa')
            elif tipo_composicao in ['Van']:
                veiculos = Veiculo.objects.filter(tipo_unidade='Van').order_by('placa')
            elif tipo_composicao in ['Caminhão']:
                veiculos = Veiculo.objects.filter(tipo_unidade='Caminhão').order_by('placa')
            elif tipo_composicao in ['Carreta', 'Bitrem']:
                veiculos = Veiculo.objects.filter(tipo_unidade='Cavalo').order_by('placa')
            else:
                veiculos = Veiculo.objects.all().order_by('placa')
            
            # Preparar dados para JSON
            veiculos_data = []
            for veiculo in veiculos:
                veiculos_data.append({
                    'id': veiculo.id,
                    'placa': veiculo.placa,
                    'tipo_unidade': veiculo.tipo_unidade,
                    'text': f"{veiculo.placa} - {veiculo.tipo_unidade}"
                })
            
            from django.http import JsonResponse
            return JsonResponse({'veiculos': veiculos_data})
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'Invalid request'}, status=400)

# --------------------------------------------------------------------------------------
# NOVA VIEW: Procurar Mercadorias no Depósito (Tela Vazia)
# --------------------------------------------------------------------------------------
@login_required
def procurar_mercadorias_deposito(request):
    """Tela vazia para procurar mercadorias no depósito - para futuros aprimoramentos"""
    return render(request, 'notas/procurar_mercadorias_deposito.html')
