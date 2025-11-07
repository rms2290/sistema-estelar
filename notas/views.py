from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max, Sum 
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
import locale
from decimal import Decimal
from datetime import datetime, date, timedelta

# Importe todos os seus modelos
from .models import NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem, HistoricoConsulta, TabelaSeguro, AgendaEntrega, DespesaCarregamento, CobrancaCarregamento

# Importe todos os seus formulários
from .forms import (
    NotaFiscalForm, ClienteForm, MotoristaForm, VeiculoForm, RomaneioViagemForm,
    NotaFiscalSearchForm, ClienteSearchForm, MotoristaSearchForm, HistoricoConsultaForm,
    VeiculoSearchForm, RomaneioSearchForm, MercadoriaDepositoSearchForm, TabelaSeguroForm,
    AgendaEntregaForm, MercadoriaDepositoSearchForm # Adicionados os novos formulários
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
    """Gera o próximo código sequencial de romaneio no formato ROM-NNN (sequencial sem resetar)."""
    # Buscar todos os romaneios (exceto genéricos ROM-100-XXX)
    romaneios = RomaneioViagem.objects.exclude(
        codigo__startswith="ROM-100-"
    ).exclude(
        codigo__isnull=True
    ).exclude(
        codigo=""
    )
    
    max_sequence = 0
    
    # Extrair números de todos os formatos possíveis
    for romaneio in romaneios:
        if not romaneio.codigo:
            continue
            
        try:
            parts = romaneio.codigo.split('-')
            
            # Formato ROM-XXX (formato simples)
            if len(parts) == 2 and parts[0] == 'ROM':
                num = int(parts[1])
                max_sequence = max(max_sequence, num)
            
            # Formato ROM-YYYY-MM-XXXX (formato com data)
            elif len(parts) == 4 and parts[0] == 'ROM':
                num = int(parts[3])
                max_sequence = max(max_sequence, num)
            
            # Formato ROM-YYYY-MM-XXXX (caso tenha menos partes mas ainda seja numérico)
            elif len(parts) >= 2 and parts[0] == 'ROM':
                # Tentar extrair o último número
                for part in reversed(parts[1:]):
                    if part.isdigit():
                        num = int(part)
                        max_sequence = max(max_sequence, num)
                        break
                        
        except (ValueError, IndexError):
            continue
    
    # Próximo número sequencial (nunca reseta)
    next_sequence = max_sequence + 1
    
    return f"ROM-{next_sequence:03d}"

def get_next_romaneio_generico_codigo():
    """Gera o próximo código sequencial de romaneio genérico no formato ROM-100-NNN (sequencial sem resetar)."""
    # Buscar todos os romaneios genéricos
    romaneios_genericos = RomaneioViagem.objects.filter(
        codigo__startswith="ROM-100-"
    ).exclude(
        codigo__isnull=True
    ).exclude(
        codigo=""
    )
    
    max_sequence = 0
    
    # Extrair números de todos os romaneios genéricos
    for romaneio in romaneios_genericos:
        if not romaneio.codigo:
            continue
            
        try:
            parts = romaneio.codigo.split('-')
            
            # Formato ROM-100-XXX
            if len(parts) == 3 and parts[0] == 'ROM' and parts[1] == '100':
                num = int(parts[2])
                max_sequence = max(max_sequence, num)
                
        except (ValueError, IndexError):
            continue
    
    # Próximo número sequencial (nunca reseta)
    next_sequence = max_sequence + 1
    
    return f"ROM-100-{next_sequence:03d}"

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
        print(f"DEBUG POST: Dados recebidos: {request.POST}")
        print(f"DEBUG POST: notas_fiscais no POST: {request.POST.getlist('notas_fiscais')}")
        
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

        print(f"DEBUG POST: Form válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG POST: Erros do form: {form.errors}")
        
        if form.is_valid():
            print(f"DEBUG POST: Form válido! Notas selecionadas: {form.cleaned_data.get('notas_fiscais', [])}")
            romaneio = form.save(commit=False)
            
            # Tentar salvar com código único (proteção contra concorrência)
            max_tentativas = 5
            for tentativa in range(max_tentativas):
                try:
                    romaneio.codigo = get_next_romaneio_codigo()
                    romaneio.data_emissao = form.cleaned_data['data_romaneio']
                    
                    if 'emitir' in request.POST:
                        romaneio.status = 'Emitido'
                    else: # Clicou em 'salvar' ou outro botão
                        romaneio.status = 'Salvo'

                    romaneio.save()
                    print(f"DEBUG POST: Romaneio salvo com ID {romaneio.id}")
                    form.save_m2m() # Salva a relação ManyToMany
                    print(f"DEBUG POST: Relações ManyToMany salvas. Notas vinculadas: {romaneio.notas_fiscais.count()}")
                    break  # Sucesso, sair do loop
                except IntegrityError as e:
                    if 'codigo' in str(e) and tentativa < max_tentativas - 1:
                        # Código duplicado, tentar novamente
                        continue
                    else:
                        # Outro erro ou esgotaram as tentativas
                        raise e

            # Atualizar o status das notas fiscais associadas
            for nota_fiscal in romaneio.notas_fiscais.all():
                # Se a nota está vinculada a qualquer romaneio, deve ter status "Enviada"
                # Verificar se há outros romaneios emitidos além do atual
                outros_romaneios_emitidos = nota_fiscal.romaneios_vinculados.exclude(pk=romaneio.pk).filter(status='Emitido')
                if outros_romaneios_emitidos.exists() or romaneio.status == 'Emitido':
                    # Se está vinculada a romaneios emitidos, manter como Enviada
                    nota_fiscal.status = 'Enviada'
                elif nota_fiscal.romaneios.exists():
                    # Se está vinculada a qualquer romaneio (mesmo que não emitido), colocar como Enviada
                    nota_fiscal.status = 'Enviada'
                else:
                    # Se não está vinculada a nenhum romaneio, colocar como Depósito
                    nota_fiscal.status = 'Depósito'
                nota_fiscal.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) salvo com sucesso!')
            
            # Redirecionar sempre para detalhes do romaneio (impressão apenas via botão)
            return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
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
            # Definir provisional_codigo mesmo em caso de erro
            provisional_codigo = get_next_romaneio_codigo()
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
            
            # Tentar salvar com código único (proteção contra concorrência)
            max_tentativas = 5
            for tentativa in range(max_tentativas):
                try:
                    romaneio.codigo = get_next_romaneio_generico_codigo()
                    romaneio.data_emissao = form.cleaned_data['data_romaneio']
                    
                    if 'emitir' in request.POST:
                        romaneio.status = 'Emitido'
                    else: # Clicou em 'salvar' ou outro botão
                        romaneio.status = 'Salvo'

                    romaneio.save()
                    form.save_m2m() # Salva a relação ManyToMany
                    break  # Sucesso, sair do loop
                except IntegrityError as e:
                    if 'codigo' in str(e) and tentativa < max_tentativas - 1:
                        # Código duplicado, tentar novamente
                        continue
                    else:
                        # Outro erro ou esgotaram as tentativas
                        raise e

            # Atualizar o status das notas fiscais associadas
            for nota_fiscal in romaneio.notas_fiscais.all():
                # Se a nota está vinculada a qualquer romaneio, deve ter status "Enviada"
                # Verificar se há outros romaneios emitidos além do atual
                outros_romaneios_emitidos = nota_fiscal.romaneios_vinculados.exclude(pk=romaneio.pk).filter(status='Emitido')
                if outros_romaneios_emitidos.exists() or romaneio.status == 'Emitido':
                    # Se está vinculada a romaneios emitidos, manter como Enviada
                    nota_fiscal.status = 'Enviada'
                elif nota_fiscal.romaneios.exists():
                    # Se está vinculada a qualquer romaneio (mesmo que não emitido), colocar como Enviada
                    nota_fiscal.status = 'Enviada'
                else:
                    # Se não está vinculada a nenhum romaneio, colocar como Depósito
                    nota_fiscal.status = 'Depósito'
                nota_fiscal.save()

            messages.success(request, f'Romaneio Genérico {romaneio.codigo} ({romaneio.status}) salvo com sucesso!')
            
            # Redirecionar sempre para detalhes do romaneio (impressão apenas via botão)
            return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
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
            # Definir provisional_codigo mesmo em caso de erro
            provisional_codigo = get_next_romaneio_generico_codigo()
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
                # Verificar se a nota ainda está vinculada a outros romaneios
                if not nota_fiscal_removida.romaneios.exists():
                    # Se não está vinculada a nenhum romaneio, colocar de volta para Depósito
                    nota_fiscal_removida.status = 'Depósito'
                    nota_fiscal_removida.save()
                else:
                    # Se ainda está vinculada a outros romaneios, manter como Enviada
                    nota_fiscal_removida.status = 'Enviada'
                    nota_fiscal_removida.save()
            
            for nota_fiscal_atualizada in notas_depois_salvar:
                # Se a nota está vinculada a qualquer romaneio, deve ter status "Enviada"
                if nota_fiscal_atualizada.romaneios.exists():
                    # Se está vinculada a qualquer romaneio, colocar como Enviada
                    nota_fiscal_atualizada.status = 'Enviada'
                else:
                    # Se não está vinculada a nenhum romaneio, colocar como Depósito
                    nota_fiscal_atualizada.status = 'Depósito'
                nota_fiscal_atualizada.save()

            messages.success(request, f'Romaneio {romaneio.codigo} ({romaneio.status}) atualizado com sucesso!')
            
            # Redirecionar sempre para detalhes do romaneio (impressão apenas via botão)
            return redirect('notas:detalhes_romaneio', pk=romaneio.pk)
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
        # Antes de excluir o romaneio, verificar se as notas estão vinculadas a outros romaneios emitidos
        for nota_fiscal in romaneio.notas_fiscais.all():
            # Verificar se a nota está vinculada a outros romaneios emitidos
            outros_romaneios_emitidos = nota_fiscal.romaneios_vinculados.exclude(pk=romaneio.pk).filter(status='Emitido')
            if not outros_romaneios_emitidos.exists():
                # Se não há outros romaneios emitidos, colocar de volta para Depósito
                nota_fiscal.status = 'Depósito'
                nota_fiscal.save()
        
        romaneio.delete()
        messages.success(request, 'Romaneio excluído com sucesso! Notas fiscais associadas foram atualizadas conforme necessário.')
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
                notas_fiscais = romaneio_existente.notas_fiscais.all()
                selected_notas_ids = list(notas_fiscais.values_list('pk', flat=True))
                print(f"DEBUG: Encontradas {notas_fiscais.count()} notas vinculadas ao romaneio {romaneio_id}")
                
                # Combine as notas em depósito com as já vinculadas (evitando duplicatas)
                notas_fiscais = (notas_deposito | notas_fiscais).distinct().order_by('nota')
            except RomaneioViagem.DoesNotExist:
                print(f"DEBUG: Romaneio {romaneio_id} não encontrado")
                pass # Romaneio não encontrado, apenas notas em depósito
        else:
            # Se for um novo romaneio, apenas notas em depósito
            notas_fiscais = notas_deposito.order_by('nota')
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
    
    error_message = None
    
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
                error_message = 'Nome de usuário ou senha inválidos.'
    else:
        form = LoginForm()
    
    return render(request, 'notas/auth/login.html', {'form': form, 'error_message': error_message})

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
    
    # Verificar se o usuário é cliente e tem cliente associado
    if request.user.tipo_usuario.upper() == 'CLIENTE' and request.user.cliente:
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
    # Se status_filter for vazio ou outro valor, mostrar todas as notas do cliente
    
    # Ordenar por data crescente
    notas_fiscais = notas_fiscais.order_by('data')
    
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
    if request.user.tipo_usuario.upper() == 'CLIENTE' and request.user.cliente != nota.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta nota fiscal.')
        return redirect('notas:minhas_notas_fiscais')
    
    return render(request, 'notas/auth/imprimir_nota_fiscal.html', {
        'nota': nota
    })

@login_required
@user_passes_test(is_cliente)
def imprimir_relatorio_deposito(request):
    # Obter apenas notas em depósito do cliente
    if request.user.tipo_usuario.upper() == 'CLIENTE' and request.user.cliente:
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
    
    # Dividir notas em grupos de 20 para multipágina
    notas_list = list(notas_romaneadas)
    notas_paginas = []
    for i in range(0, len(notas_list), 20):
        pagina = notas_list[i:i + 20]
        notas_paginas.append(pagina)
    
    # Adicionar parâmetro de versão para forçar reload
    import time
    version = int(time.time())
    
    return render(request, 'notas/visualizar_romaneio_para_impressao.html', {
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'notas_paginas': notas_paginas,
        'total_peso': total_peso,
        'total_valor': total_valor,
        'version': version
    })

@login_required
def gerar_romaneio_pdf(request, pk):
    """View para gerar PDF do romaneio"""
    from django.http import HttpResponse
    from django.template.loader import get_template
    from django.conf import settings
    import os
    
    romaneio = get_object_or_404(RomaneioViagem, pk=pk)
    
    # Obter notas fiscais vinculadas ao romaneio
    notas_romaneadas = romaneio.notas_fiscais.all().order_by('data')
    
    # Calcular totais
    total_peso = sum(nota.peso for nota in notas_romaneadas)
    total_valor = sum(nota.valor for nota in notas_romaneadas)
    
    # Renderizar template
    template = get_template('notas/visualizar_romaneio_para_impressao.html')
    html = template.render({
        'romaneio': romaneio,
        'notas_romaneadas': notas_romaneadas,
        'total_peso': total_peso,
        'total_valor': total_valor
    })
    
    # Configurar resposta para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="romaneio_{romaneio.codigo}.pdf"'
    
    # Tentar usar weasyprint se disponível
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        font_config = FontConfiguration()
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
            .no-print {
                display: none !important;
            }
            .print-button {
                display: none !important;
            }
        ''', font_config=font_config)
        
        HTML(string=html).write_pdf(response, stylesheets=[css], font_config=font_config)
        
    except ImportError:
        # Fallback: retornar HTML para impressão
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="romaneio_{romaneio.codigo}.html"'
        messages.warning(request, 'Biblioteca WeasyPrint não encontrada. Instale com: pip install weasyprint')
    
    return response

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
    """Lista todas as cobranças de carregamento"""
    cobrancas = CobrancaCarregamento.objects.all().prefetch_related('romaneios', 'cliente')
    
    # Filtros
    cliente_id = request.GET.get('cliente')
    status_cobranca = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # Por padrão, mostrar apenas cobranças pendentes
    # Se o usuário selecionar explicitamente um status, usar o selecionado
    if status_cobranca:
        cobrancas = cobrancas.filter(status=status_cobranca)
    else:
        # Se não houver filtro de status, mostrar apenas pendentes
        cobrancas = cobrancas.filter(status='Pendente')
    
    if cliente_id:
        cobrancas = cobrancas.filter(cliente_id=cliente_id)
    
    if data_inicio:
        cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio)
    
    if data_fim:
        cobrancas = cobrancas.filter(criado_em__date__lte=data_fim)
    
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    
    context = {
        'cobrancas': cobrancas,
        'clientes': clientes,
    }
    return render(request, 'notas/relatorios/cobranca_carregamento.html', context)


@login_required
@user_passes_test(is_admin)
def criar_cobranca_carregamento(request):
    """Cria uma nova cobrança de carregamento"""
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente')
            romaneios_ids = request.POST.getlist('romaneios')
            valor_carregamento = request.POST.get('valor_carregamento', '0') or '0'
            valor_cte_manifesto = request.POST.get('valor_cte_manifesto', '0') or '0'
            data_vencimento = request.POST.get('data_vencimento') or None
            observacoes = request.POST.get('observacoes', '')
            
            if not cliente_id or not romaneios_ids:
                messages.error(request, 'Cliente e pelo menos um romaneio são obrigatórios!')
                return redirect('notas:criar_cobranca_carregamento')
            
            cliente = Cliente.objects.get(pk=cliente_id)
            
            cobranca = CobrancaCarregamento.objects.create(
                cliente=cliente,
                valor_carregamento=valor_carregamento,
                valor_cte_manifesto=valor_cte_manifesto,
                data_vencimento=data_vencimento,
                observacoes=observacoes
            )
            
            # Associar romaneios
            for romaneio_id in romaneios_ids:
                romaneio = RomaneioViagem.objects.get(pk=romaneio_id)
                cobranca.romaneios.add(romaneio)
            
            messages.success(request, 'Cobrança criada com sucesso!')
            return redirect('notas:cobranca_carregamento')
            
        except Exception as e:
            messages.error(request, f'Erro ao criar cobrança: {str(e)}')
    
    # GET - Mostrar formulário
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    cliente_id = request.GET.get('cliente')
    romaneios = None
    
    if cliente_id:
        # Buscar todos os romaneios emitidos do cliente (pode ter múltiplos CNPJs)
        romaneios = RomaneioViagem.objects.filter(
            cliente_id=cliente_id,
            status='Emitido'
        ).order_by('-data_emissao')
    
    context = {
        'clientes': clientes,
        'romaneios': romaneios,
        'cliente_selecionado_id': cliente_id,
    }
    return render(request, 'notas/criar_cobranca_carregamento.html', context)


@login_required
@user_passes_test(is_admin)
def editar_cobranca_carregamento(request, cobranca_id):
    """Edita uma cobrança de carregamento"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        try:
            romaneios_ids = request.POST.getlist('romaneios')
            cobranca.valor_carregamento = request.POST.get('valor_carregamento', '0') or '0'
            cobranca.valor_cte_manifesto = request.POST.get('valor_cte_manifesto', '0') or '0'
            cobranca.data_vencimento = request.POST.get('data_vencimento') or None
            cobranca.observacoes = request.POST.get('observacoes', '')
            cobranca.save()
            
            # Atualizar romaneios
            cobranca.romaneios.clear()
            for romaneio_id in romaneios_ids:
                romaneio = RomaneioViagem.objects.get(pk=romaneio_id)
                cobranca.romaneios.add(romaneio)
            
            messages.success(request, 'Cobrança atualizada com sucesso!')
            return redirect('notas:cobranca_carregamento')
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar cobrança: {str(e)}')
    
    # GET - Mostrar formulário
    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    romaneios_cliente = RomaneioViagem.objects.filter(
        cliente=cobranca.cliente,
        status='Emitido'
    ).order_by('-data_emissao')
    
    context = {
        'cobranca': cobranca,
        'clientes': clientes,
        'romaneios': romaneios_cliente,
        'romaneios_selecionados': list(cobranca.romaneios.values_list('id', flat=True)),
    }
    return render(request, 'notas/editar_cobranca_carregamento.html', context)


@login_required
@user_passes_test(is_admin)
def baixar_cobranca_carregamento(request, cobranca_id):
    """Baixa uma cobrança (marca como paga)"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        cobranca.status = 'Baixado'
        cobranca.data_baixa = timezone.now().date()
        cobranca.save()
        messages.success(request, 'Cobrança baixada com sucesso!')
        return redirect('notas:cobranca_carregamento')
    
    return render(request, 'notas/confirmar_baixa_cobranca.html', {'cobranca': cobranca})


@login_required
@user_passes_test(is_admin)
def excluir_cobranca_carregamento(request, cobranca_id):
    """Exclui uma cobrança"""
    cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id)
    
    if request.method == 'POST':
        cobranca.delete()
        messages.success(request, 'Cobrança excluída com sucesso!')
        return redirect('notas:cobranca_carregamento')
    
    return render(request, 'notas/confirmar_exclusao_cobranca.html', {'cobranca': cobranca})


@login_required
@user_passes_test(is_admin)
def gerar_relatorio_consolidado_cobranca_pdf(request):
    """Gera relatório PDF consolidado com cobranças pendentes do cliente selecionado"""
    from django.http import HttpResponse
    from .utils.relatorios import gerar_relatorio_pdf_consolidado_cobranca
    
    # Buscar cobranças pendentes do cliente selecionado (se houver)
    cliente_id = request.GET.get('cliente')
    
    cobrancas_pendentes = CobrancaCarregamento.objects.filter(
        status='Pendente'
    )
    
    # Filtrar por cliente se selecionado
    if cliente_id:
        cobrancas_pendentes = cobrancas_pendentes.filter(cliente_id=cliente_id)
        cliente = get_object_or_404(Cliente, pk=cliente_id)
        nome_arquivo = f"relatorio_consolidado_{cliente.razao_social.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    else:
        # Se não houver cliente selecionado, mostrar mensagem
        from django.contrib import messages
        messages.warning(request, 'Por favor, selecione um cliente nos filtros para gerar o relatório consolidado.')
        return redirect('notas:cobranca_carregamento')
    
    cobrancas_pendentes = cobrancas_pendentes.select_related('cliente').prefetch_related(
        'romaneios__motorista',
        'romaneios__veiculo_principal',
        'romaneios__reboque_1',
        'romaneios__reboque_2'
    ).order_by('criado_em')
    
    # Verificar se há cobranças pendentes
    if not cobrancas_pendentes.exists():
        from django.contrib import messages
        messages.info(request, f'O cliente {cliente.razao_social} não possui cobranças pendentes.')
        return redirect('notas:cobranca_carregamento')
    
    # Gerar PDF
    pdf_content = gerar_relatorio_pdf_consolidado_cobranca(cobrancas_pendentes, cliente_selecionado=cliente if cliente_id else None)
    
    # Criar resposta com inline para visualização no navegador
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    response.write(pdf_content)
    return response


@login_required
@user_passes_test(is_cliente)
def minhas_cobrancas_carregamento(request):
    """Lista as cobranças de carregamento do cliente logado"""
    # Verificar se o usuário é cliente e tem cliente associado
    if request.user.tipo_usuario.upper() != 'CLIENTE' or not request.user.cliente:
        messages.error(request, 'Acesso negado. Esta área é exclusiva para clientes.')
        return redirect('notas:dashboard')
    
    # Buscar cobranças apenas do cliente logado
    cobrancas = CobrancaCarregamento.objects.filter(
        cliente=request.user.cliente
    ).prefetch_related('romaneios', 'cliente').order_by('-criado_em')
    
    # Filtros
    status_cobranca = request.GET.get('status')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    if status_cobranca:
        cobrancas = cobrancas.filter(status=status_cobranca)
    
    if data_inicio:
        cobrancas = cobrancas.filter(criado_em__date__gte=data_inicio)
    
    if data_fim:
        cobrancas = cobrancas.filter(criado_em__date__lte=data_fim)
    
    context = {
        'cobrancas': cobrancas,
    }
    return render(request, 'notas/auth/minhas_cobrancas_carregamento.html', context)


@login_required
@user_passes_test(is_cliente)
def gerar_relatorio_cobranca_carregamento_pdf_cliente(request, cobranca_id):
    """Gera relatório PDF para uma cobrança de carregamento - Versão Cliente"""
    from django.http import HttpResponse
    from .utils.relatorios import gerar_relatorio_pdf_cobranca_carregamento
    
    cobranca = get_object_or_404(
        CobrancaCarregamento.objects.select_related('cliente').prefetch_related(
            'romaneios__motorista',
            'romaneios__veiculo_principal',
            'romaneios__reboque_1',
            'romaneios__reboque_2'
        ),
        pk=cobranca_id
    )
    
    # Verificar se o cliente logado tem permissão para ver esta cobrança
    if request.user.tipo_usuario.upper() == 'CLIENTE' and cobranca.cliente != request.user.cliente:
        messages.error(request, 'Você não tem permissão para acessar esta cobrança.')
        return redirect('notas:minhas_cobrancas_carregamento')
    
    # Gerar PDF
    pdf_content = gerar_relatorio_pdf_cobranca_carregamento(cobranca)
    
    # Nome do arquivo
    nome_arquivo = f"cobranca_carregamento_{cobranca.id}_{cobranca.cliente.razao_social.replace(' ', '_')}.pdf"
    
    # Criar resposta com inline para visualização no navegador
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    response.write(pdf_content)
    return response


@login_required
@user_passes_test(is_admin)
def gerar_relatorio_cobranca_carregamento_pdf(request, cobranca_id):
    """Gera relatório PDF para uma cobrança de carregamento - Versão Admin"""
    from django.http import HttpResponse
    from .utils.relatorios import gerar_relatorio_pdf_cobranca_carregamento
    
    cobranca = get_object_or_404(
        CobrancaCarregamento.objects.select_related('cliente').prefetch_related(
            'romaneios__motorista',
            'romaneios__veiculo_principal',
            'romaneios__reboque_1',
            'romaneios__reboque_2'
        ),
        pk=cobranca_id
    )
    
    # Gerar PDF
    pdf_content = gerar_relatorio_pdf_cobranca_carregamento(cobranca)
    
    # Nome do arquivo
    nome_arquivo = f"cobranca_carregamento_{cobranca.id}_{cobranca.cliente.razao_social.replace(' ', '_')}.pdf"
    
    # Criar resposta com inline para visualização no navegador
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_arquivo}"'
    response.write(pdf_content)
    return response


@login_required
@user_passes_test(is_admin)
def carregar_romaneios_cliente(request, cliente_id):
    """Carrega romaneios emitidos de um cliente via AJAX"""
    try:
        romaneios = RomaneioViagem.objects.filter(
            cliente_id=cliente_id,
            status='Emitido'
        ).order_by('-data_emissao')
        
        romaneios_data = []
        for romaneio in romaneios:
            romaneios_data.append({
                'id': romaneio.id,
                'codigo': romaneio.codigo,
                'data_emissao': romaneio.data_emissao.strftime('%d/%m/%Y'),
                'cliente': romaneio.cliente.razao_social,
            })
        
        return JsonResponse({'romaneios': romaneios_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def gerenciar_despesas_romaneio(request, romaneio_id):
    """Gerencia as despesas de um romaneio específico"""
    romaneio = get_object_or_404(RomaneioViagem, pk=romaneio_id)
    despesas = romaneio.despesas.all()
    
    if request.method == 'POST':
        # Processar múltiplas despesas
        despesas_criadas = 0
        erros = []
        
        # Verificar se é um formulário de múltiplas despesas
        tipos = request.POST.getlist('tipo_despesa[]')
        valores = request.POST.getlist('valor[]')
        datas_vencimento = request.POST.getlist('data_vencimento[]')
        observacoes_list = request.POST.getlist('observacoes[]')
        
        if tipos:
            # Processar múltiplas despesas
            for i, tipo in enumerate(tipos):
                if tipo and i < len(valores) and valores[i]:
                    try:
                        valor = valores[i]
                        data_vencimento = datas_vencimento[i] if i < len(datas_vencimento) else ''
                        observacoes = observacoes_list[i] if i < len(observacoes_list) else ''
                        
                        DespesaCarregamento.objects.create(
                            romaneio=romaneio,
                            tipo_despesa=tipo,
                            valor=valor,
                            data_vencimento=data_vencimento or None,
                            observacoes=observacoes
                        )
                        despesas_criadas += 1
                    except Exception as e:
                        erros.append(f'Erro ao adicionar {tipo}: {str(e)}')
            
            if despesas_criadas > 0:
                if despesas_criadas == 1:
                    messages.success(request, f'{despesas_criadas} despesa adicionada com sucesso!')
                else:
                    messages.success(request, f'{despesas_criadas} despesas adicionadas com sucesso!')
            
            if erros:
                for erro in erros:
                    messages.error(request, erro)
        else:
            # Compatibilidade com formulário antigo (uma despesa)
            tipo = request.POST.get('tipo_despesa')
            valor = request.POST.get('valor')
            data_vencimento = request.POST.get('data_vencimento')
            observacoes = request.POST.get('observacoes')
            
            if tipo and valor:
                try:
                    DespesaCarregamento.objects.create(
                        romaneio=romaneio,
                        tipo_despesa=tipo,
                        valor=valor,
                        data_vencimento=data_vencimento or None,
                        observacoes=observacoes
                    )
                    messages.success(request, 'Despesa adicionada com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao adicionar despesa: {str(e)}')
        
        return redirect('notas:gerenciar_despesas_romaneio', romaneio_id=romaneio_id)
    
    total_pendente = despesas.filter(status='Pendente').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    total_baixado = despesas.filter(status='Baixado').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Calcular totais por tipo de despesa
    total_carregamento = despesas.filter(tipo_despesa='Carregamento').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Unificar CTE e Manifesto em CTE/Manifesto
    total_cte_manifesto = (
        despesas.filter(tipo_despesa='CTE').aggregate(total=Sum('valor'))['total'] or 0
    ) + (
        despesas.filter(tipo_despesa='Manifesto').aggregate(total=Sum('valor'))['total'] or 0
    ) + (
        despesas.filter(tipo_despesa='CTE/Manifesto').aggregate(total=Sum('valor'))['total'] or 0
    )
    
    context = {
        'romaneio': romaneio,
        'despesas': despesas,
        'total_pendente': total_pendente,
        'total_baixado': total_baixado,
        'total_carregamento': total_carregamento,
        'total_cte_manifesto': total_cte_manifesto,
    }
    return render(request, 'notas/gerenciar_despesas_romaneio.html', context)


@login_required
@user_passes_test(is_admin)
def baixar_despesa(request, despesa_id):
    """Baixa uma despesa (marca como paga)"""
    despesa = get_object_or_404(DespesaCarregamento, pk=despesa_id)
    
    if request.method == 'POST':
        despesa.status = 'Baixado'
        despesa.data_baixa = timezone.now().date()
        despesa.save()
        messages.success(request, 'Despesa baixada com sucesso!')
        return redirect('notas:gerenciar_despesas_romaneio', romaneio_id=despesa.romaneio.id)
    
    return render(request, 'notas/confirmar_baixa_despesa.html', {'despesa': despesa})


@login_required
@user_passes_test(is_admin)
def editar_despesa(request, despesa_id):
    """Edita uma despesa"""
    despesa = get_object_or_404(DespesaCarregamento, pk=despesa_id)
    
    if request.method == 'POST':
        try:
            despesa.tipo_despesa = request.POST.get('tipo_despesa')
            despesa.valor = request.POST.get('valor')
            despesa.data_vencimento = request.POST.get('data_vencimento') or None
            despesa.observacoes = request.POST.get('observacoes')
            despesa.save()
            messages.success(request, 'Despesa atualizada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
        return redirect('notas:gerenciar_despesas_romaneio', romaneio_id=despesa.romaneio.id)
    
    return render(request, 'notas/editar_despesa.html', {'despesa': despesa})


@login_required
@user_passes_test(is_admin)
def excluir_despesa(request, despesa_id):
    """Exclui uma despesa"""
    despesa = get_object_or_404(DespesaCarregamento, pk=despesa_id)
    romaneio_id = despesa.romaneio.id
    
    if request.method == 'POST':
        despesa.delete()
        messages.success(request, 'Despesa excluída com sucesso!')
        return redirect('notas:gerenciar_despesas_romaneio', romaneio_id=romaneio_id)
    
    return render(request, 'notas/confirmar_exclusao_despesa.html', {'despesa': despesa})

@login_required
def dashboard(request):
    """Dashboard principal do sistema"""
    # Se o usuário for um cliente, redirecionar para o dashboard específico do cliente
    if hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'cliente':
        return dashboard_cliente(request)
    
    # Se o usuário for um funcionário, redirecionar para o dashboard específico do funcionário
    if hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'funcionario':
        return dashboard_funcionario(request)
    
    # Verificar se o usuário tem o atributo is_cliente (método alternativo)
    if hasattr(request.user, 'is_cliente') and request.user.is_cliente:
        return dashboard_cliente(request)
    
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Estatísticas básicas para o dashboard
    total_notas = NotaFiscal.objects.count()
    total_clientes = Cliente.objects.count()
    total_motoristas = Motorista.objects.count()
    total_veiculos = Veiculo.objects.count()
    total_romaneios = RomaneioViagem.objects.count()
    
    # Notas por status
    notas_deposito = NotaFiscal.objects.filter(status='Depósito').count()
    notas_enviadas = NotaFiscal.objects.filter(status='Enviada').count()
    
    # Valores financeiros
    valor_total_deposito = NotaFiscal.objects.filter(status='Depósito').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    valor_total_enviadas = NotaFiscal.objects.filter(status='Enviada').aggregate(
        total=Sum('valor')
    )['total'] or 0
    
    # Atividade recente (últimos 7 dias)
    data_limite = datetime.now() - timedelta(days=7)
    notas_recentes = NotaFiscal.objects.filter(
        data__gte=data_limite.date()
    ).order_by('-data')[:5]
    
    romaneios_recentes = RomaneioViagem.objects.filter(
        data_emissao__gte=data_limite
    ).order_by('-data_emissao')[:5]
    
    # Top clientes por valor em depósito
    top_clientes_deposito = Cliente.objects.annotate(
        valor_deposito=Sum('notas_fiscais__valor', filter=Q(notas_fiscais__status='Depósito'))
    ).filter(valor_deposito__gt=0).order_by('-valor_deposito')[:5]
    
    # Dados da agenda de entregas
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    now = datetime.now()
    proximas_entregas = AgendaEntrega.objects.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('data_entrega')[:5]
    
    entregas_hoje = AgendaEntrega.objects.filter(
        data_entrega=hoje,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('cliente__razao_social')
    
    # Entregas agendadas para o dashboard (apenas status 'Agendada')
    entregas_agendadas = AgendaEntrega.objects.filter(
        status='Agendada'
    ).select_related('cliente').order_by('data_entrega')[:10]
    
    total_agendadas = AgendaEntrega.objects.filter(status='Agendada').count()
    total_em_andamento = AgendaEntrega.objects.filter(status='Em Andamento').count()
    
    context = {
        'title': 'Dashboard - Agência Estelar',
        'user': request.user,
        
        # Estatísticas gerais
        'total_notas': total_notas,
        'total_clientes': total_clientes,
        'total_motoristas': total_motoristas,
        'total_veiculos': total_veiculos,
        'total_romaneios': total_romaneios,
        
        # Estatísticas por status
        'notas_deposito': notas_deposito,
        'notas_enviadas': notas_enviadas,
        
        # Valores financeiros
        'valor_total_deposito': valor_total_deposito,
        'valor_total_enviadas': valor_total_enviadas,
        
        # Atividade recente
        'notas_recentes': notas_recentes,
        'romaneios_recentes': romaneios_recentes,
        
        # Top clientes
        'top_clientes_deposito': top_clientes_deposito,
        
        # Dados da agenda
        'proximas_entregas': proximas_entregas,
        'entregas_hoje': entregas_hoje,
        'entregas_agendadas': entregas_agendadas,
        'total_agendadas': total_agendadas,
        'total_em_andamento': total_em_andamento,
        'hoje': hoje,
        'now': now,
    }
    return render(request, 'notas/dashboard.html', context)

@login_required
def dashboard_cliente(request):
    """Dashboard específico para clientes"""
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Verificar se o usuário é um cliente
    if not (hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'cliente'):
        return redirect('notas:dashboard')
    
    # Obter o cliente vinculado ao usuário
    cliente = request.user.cliente
    if not cliente:
        messages.error(request, 'Cliente não encontrado. Entre em contato com o administrador.')
        return redirect('notas:login')
    
    # Estatísticas do cliente
    total_notas_cliente = NotaFiscal.objects.filter(cliente=cliente).count()
    notas_deposito_cliente = NotaFiscal.objects.filter(cliente=cliente, status='Depósito').count()
    notas_enviadas_cliente = NotaFiscal.objects.filter(cliente=cliente, status='Enviada').count()
    
    # Valores financeiros do cliente
    valor_total_deposito_cliente = NotaFiscal.objects.filter(
        cliente=cliente, status='Depósito'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    valor_total_enviadas_cliente = NotaFiscal.objects.filter(
        cliente=cliente, status='Enviada'
    ).aggregate(total=Sum('valor'))['total'] or 0
    
    # Últimas notas do cliente (últimos 30 dias)
    data_limite = datetime.now() - timedelta(days=30)
    ultimas_notas = NotaFiscal.objects.filter(
        cliente=cliente,
        data__gte=data_limite.date()
    ).order_by('-data')[:10]
    
    # Romaneios do cliente (últimos 30 dias)
    romaneios_cliente = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite
    ).order_by('-data_emissao')[:10]
    
    # Estatísticas de carregamentos (últimos 6 meses)
    data_limite_6_meses = datetime.now() - timedelta(days=180)
    carregamentos_6_meses = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite_6_meses
    ).count()
    
    # Carregamentos por mês (últimos 6 meses)
    carregamentos_por_mes = []
    for i in range(6):
        data_inicio = datetime.now() - timedelta(days=30*i + 30)
        data_fim = datetime.now() - timedelta(days=30*i)
        mes = data_inicio.strftime('%m/%Y')
        
        quantidade = RomaneioViagem.objects.filter(
            cliente=cliente,
            data_emissao__gte=data_inicio,
            data_emissao__lt=data_fim
        ).count()
        
        carregamentos_por_mes.append({
            'mes': mes,
            'quantidade': quantidade
        })
    
    carregamentos_por_mes.reverse()  # Ordenar do mais antigo para o mais recente
    
    # Valor total dos carregamentos (últimos 6 meses)
    valor_total_carregamentos = RomaneioViagem.objects.filter(
        cliente=cliente,
        data_emissao__gte=data_limite_6_meses
    ).aggregate(total=Sum('valor_total'))['total'] or 0
    
    context = {
        'title': f'Dashboard - {cliente.razao_social}',
        'user': request.user,
        'cliente': cliente,
        
        # Estatísticas do cliente
        'total_notas_cliente': total_notas_cliente,
        'notas_deposito_cliente': notas_deposito_cliente,
        'notas_enviadas_cliente': notas_enviadas_cliente,
        
        # Valores financeiros do cliente
        'valor_total_deposito_cliente': valor_total_deposito_cliente,
        'valor_total_enviadas_cliente': valor_total_enviadas_cliente,
        
        # Atividade recente do cliente
        'ultimas_notas': ultimas_notas,
        'romaneios_cliente': romaneios_cliente,
        
        # Estatísticas de carregamentos
        'carregamentos_6_meses': carregamentos_6_meses,
        'carregamentos_por_mes': carregamentos_por_mes,
        'valor_total_carregamentos': valor_total_carregamentos,
    }
    return render(request, 'notas/dashboard_cliente.html', context)

@login_required
def dashboard_funcionario(request):
    """Dashboard específico para funcionários"""
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Verificar se o usuário é um funcionário
    if not (hasattr(request.user, 'tipo_usuario') and request.user.tipo_usuario == 'funcionario'):
        return redirect('notas:dashboard')
    
    # Estatísticas básicas para funcionários
    total_notas = NotaFiscal.objects.count()
    total_clientes = Cliente.objects.count()
    total_motoristas = Motorista.objects.count()
    total_veiculos = Veiculo.objects.count()
    total_romaneios = RomaneioViagem.objects.count()
    
    # Notas por status
    notas_deposito = NotaFiscal.objects.filter(status='Depósito').count()
    notas_enviadas = NotaFiscal.objects.filter(status='Enviada').count()
    
    # Valores financeiros
    valor_total_notas = NotaFiscal.objects.aggregate(total=Sum('valor'))['total'] or 0
    valor_total_romaneios = RomaneioViagem.objects.aggregate(total=Sum('valor_total'))['total'] or 0
    
    # Atividade recente (últimas 5 notas fiscais)
    notas_recentes = NotaFiscal.objects.select_related('cliente').order_by('-data')[:5]
    
    # Romaneios recentes (últimos 5)
    romaneios_recentes = RomaneioViagem.objects.select_related('cliente', 'motorista').order_by('-data_emissao')[:5]
    
    context = {
        'title': 'Dashboard - Funcionário',
        'user': request.user,
        
        # Estatísticas básicas
        'total_notas': total_notas,
        'total_clientes': total_clientes,
        'total_motoristas': total_motoristas,
        'total_veiculos': total_veiculos,
        'total_romaneios': total_romaneios,
        
        # Notas por status
        'notas_deposito': notas_deposito,
        'notas_enviadas': notas_enviadas,
        
        # Valores financeiros
        'valor_total_notas': valor_total_notas,
        'valor_total_romaneios': valor_total_romaneios,
        
        # Atividade recente
        'notas_recentes': notas_recentes,
        'romaneios_recentes': romaneios_recentes,
    }
    return render(request, 'notas/dashboard_funcionario.html', context)

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
        local = search_form.cleaned_data.get('local')
        
        if nota:
            queryset = queryset.filter(nota__icontains=nota)
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if data:
            queryset = queryset.filter(data=data)
        if local:
            queryset = queryset.filter(local=local)
        
        notas_fiscais = queryset.order_by('nota')
    
    context = {
        'notas_fiscais': notas_fiscais,
        'search_form': search_form,
        'search_performed': search_performed,
    }
    return render(request, 'notas/listar_notas.html', context)

@login_required
def buscar_mercadorias_deposito(request):
    """Busca mercadorias no depósito com foco na localização"""
    search_form = MercadoriaDepositoSearchForm(request.GET)
    mercadorias = NotaFiscal.objects.none()
    search_performed = bool(request.GET)
    
    
    # Contagem por galpão
    contagem_galpoes = {}
    galpoes_com_mercadorias = set()  # Para destacar galpões com mercadorias do cliente pesquisado
    galpoes_info = []  # Lista com informações dos galpões
    
    for choice in NotaFiscal.LOCAL_CHOICES:
        codigo = choice[0]
        nome = choice[1]
        contagem = NotaFiscal.objects.filter(local=codigo, status='Depósito').count()
        contagem_galpoes[nome] = contagem
        galpoes_info.append({
            'codigo': codigo,
            'nome': nome,
            'quantidade': contagem
        })

    if search_performed and search_form.is_valid():
        # Na tela de busca por localização, sempre filtrar apenas status "Depósito"
        queryset = NotaFiscal.objects.filter(status='Depósito')
        cliente = search_form.cleaned_data.get('cliente')
        mercadoria = search_form.cleaned_data.get('mercadoria')
        nota = search_form.cleaned_data.get('nota')
        local = search_form.cleaned_data.get('local')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if cliente:
            queryset = queryset.filter(cliente=cliente)
        if mercadoria:
            queryset = queryset.filter(mercadoria__icontains=mercadoria)
        if nota:
            queryset = queryset.filter(nota__icontains=nota)
        if data_inicio:
            queryset = queryset.filter(data__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data__lte=data_fim)
        
        # Se foi filtrado por galpão específico, agrupar por cliente
        if local:
            queryset = queryset.filter(local=local)
            from django.db.models import Sum, Count
            mercadorias = queryset.values('cliente__razao_social', 'cliente__id').annotate(
                valor_total=Sum('valor'),
                peso_total=Sum('peso'),
                quantidade_total=Sum('quantidade'),
                total_notas=Count('id')
            ).order_by('cliente__razao_social')
        # Se foi filtrado por cliente (sem galpão específico), agrupar por galpão
        elif cliente:
            from django.db.models import Sum, Count
            mercadorias = queryset.values('local', 'cliente__razao_social', 'cliente__id').annotate(
                valor_total=Sum('valor'),
                peso_total=Sum('peso'),
                quantidade_total=Sum('quantidade'),
                total_notas=Count('id')
            ).order_by('local', 'cliente__razao_social')
        else:
            # Busca geral, mostrar lista normal
            mercadorias = queryset.order_by('local', 'cliente__razao_social', 'mercadoria')
        
        # Identificar galpões com mercadorias do cliente pesquisado (apenas status "Depósito")
        if cliente:
            galpoes_com_mercadorias = set()
            # Se foi filtrado por galpão específico ou cliente, mercadorias é um queryset de dicionários
            if local or cliente:
                # Para galpão específico ou cliente, usar o queryset original para identificar galpões
                cliente_mercadorias = NotaFiscal.objects.filter(cliente=cliente, status='Depósito')
                for mercadoria in cliente_mercadorias:
                    if mercadoria.local:
                        galpoes_com_mercadorias.add(mercadoria.local)
            else:
                # Para busca geral, mercadorias são objetos
                for mercadoria in mercadorias:
                    if mercadoria.local and mercadoria.status == 'Depósito':
                        galpoes_com_mercadorias.add(mercadoria.local)
    
    context = {
        'mercadorias': mercadorias,
        'search_form': search_form,
        'search_performed': search_performed,
        'contagem_galpoes': contagem_galpoes,
        'galpoes_com_mercadorias': list(galpoes_com_mercadorias),
        'galpoes_info': galpoes_info,
    }
    return render(request, 'notas/buscar_mercadorias_deposito.html', context)

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
        rg = search_form.cleaned_data.get('rg')

        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        if rg:
            queryset = queryset.filter(rg__icontains=rg)
        
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
        tipo_romaneio = search_form.cleaned_data.get('tipo_romaneio')
        cliente = search_form.cleaned_data.get('cliente')
        motorista = search_form.cleaned_data.get('motorista')
        veiculo_principal = search_form.cleaned_data.get('veiculo_principal')
        status = search_form.cleaned_data.get('status')
        data_inicio = search_form.cleaned_data.get('data_inicio')
        data_fim = search_form.cleaned_data.get('data_fim')
        
        if codigo:
            queryset = queryset.filter(codigo__icontains=codigo)
        if tipo_romaneio:
            if tipo_romaneio == 'normal':
                # Romaneios normais: formato ROM-XXX (excluindo genéricos)
                queryset = queryset.filter(codigo__startswith='ROM-').exclude(codigo__startswith='ROM-100-')
            elif tipo_romaneio == 'generico':
                # Romaneios genéricos: formato ROM-100-XXX
                queryset = queryset.filter(codigo__startswith='ROM-100-')
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
        
        notas_fiscais = queryset.order_by('nota')
        
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

@login_required
def imprimir_relatorio_mercadorias_deposito(request):
    """Imprime relatório de mercadorias no depósito"""
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
        
        notas_fiscais = queryset.order_by('nota')
        
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
        'filtros_aplicados': {
            'cliente': search_form.cleaned_data.get('cliente') if search_form.is_valid() else None,
            'mercadoria': search_form.cleaned_data.get('mercadoria') if search_form.is_valid() else None,
            'fornecedor': search_form.cleaned_data.get('fornecedor') if search_form.is_valid() else None,
            'data_inicio': search_form.cleaned_data.get('data_inicio') if search_form.is_valid() else None,
            'data_fim': search_form.cleaned_data.get('data_fim') if search_form.is_valid() else None,
        }
    }
    return render(request, 'notas/imprimir_relatorio_mercadorias_deposito.html', context)

# --------------------------------------------------------------------------------------
# NOVA VIEW PARA FILTRAR VEÍCULOS BASEADO NO TIPO DE COMPOSIÇÃO
# --------------------------------------------------------------------------------------
@login_required
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

# --------------------------------------------------------------------------------------
# Views para Agenda de Entregas
# --------------------------------------------------------------------------------------
@login_required
@user_passes_test(is_admin)
def listar_agenda_entregas(request):
    """Lista todas as entregas agendadas"""
    from datetime import date, timedelta
    
    # Filtros
    status_filter = request.GET.get('status', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    
    # Query base
    entregas = AgendaEntrega.objects.select_related('cliente', 'usuario_criacao').all()
    
    # Aplicar filtros
    if status_filter:
        entregas = entregas.filter(status=status_filter)
    
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            entregas = entregas.filter(data_entrega__gte=data_inicio_obj)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            entregas = entregas.filter(data_entrega__lte=data_fim_obj)
        except ValueError:
            pass
    
    # Ordenar por data de entrega
    entregas = entregas.order_by('data_entrega', 'cliente__razao_social')
    
    # Estatísticas
    total_entregas = entregas.count()
    entregas_agendadas = entregas.filter(status='Agendada').count()
    entregas_entregues = entregas.filter(status='Entregue').count()
    entregas_canceladas = entregas.filter(status='Cancelada').count()
    
    # Próximas entregas (próximos 7 dias)
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    proximas_entregas = entregas.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).order_by('data_entrega')[:10]
    
    context = {
        'title': 'Agenda de Entregas',
        'entregas': entregas,
        'proximas_entregas': proximas_entregas,
        'total_entregas': total_entregas,
        'entregas_agendadas': entregas_agendadas,
        'entregas_entregues': entregas_entregues,
        'entregas_canceladas': entregas_canceladas,
        'status_filter': status_filter,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'status_choices': AgendaEntrega.STATUS_ENTREGA_CHOICES,
    }
    
    return render(request, 'notas/agenda/listar_agenda_entregas.html', context)

@login_required
@user_passes_test(is_admin)
def adicionar_agenda_entrega(request):
    """Adiciona uma nova entrega à agenda"""
    if request.method == 'POST':
        form = AgendaEntregaForm(request.POST)
        if form.is_valid():
            agenda_entrega = form.save(commit=False)
            agenda_entrega.usuario_criacao = request.user
            agenda_entrega.save()
            messages.success(request, 'Entrega agendada com sucesso!')
            return redirect('notas:listar_agenda_entregas')
    else:
        form = AgendaEntregaForm()
    
    context = {
        'title': 'Agendar Nova Entrega',
        'form': form,
    }
    
    return render(request, 'notas/agenda/adicionar_agenda_entrega.html', context)

@login_required
@user_passes_test(is_admin)
def editar_agenda_entrega(request, pk):
    """Edita uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        form = AgendaEntregaForm(request.POST, instance=agenda_entrega)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrega atualizada com sucesso!')
            return redirect('notas:listar_agenda_entregas')
    else:
        form = AgendaEntregaForm(instance=agenda_entrega)
    
    context = {
        'title': f'Editar Entrega - {agenda_entrega.cliente.razao_social}',
        'form': form,
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/editar_agenda_entrega.html', context)

@login_required
@user_passes_test(is_admin)
def excluir_agenda_entrega(request, pk):
    """Exclui uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        try:
            cliente_nome = agenda_entrega.cliente.razao_social
            data_entrega = agenda_entrega.data_entrega.strftime('%d/%m/%Y')
            agenda_entrega.delete()
            messages.success(request, f'Entrega para {cliente_nome} em {data_entrega} excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Não foi possível excluir a entrega: {e}')
        return redirect('notas:listar_agenda_entregas')
    
    context = {
        'title': 'Confirmar Exclusão',
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/confirmar_exclusao_agenda_entrega.html', context)

@login_required
@user_passes_test(is_admin)
def detalhes_agenda_entrega(request, pk):
    """Mostra os detalhes de uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    context = {
        'title': f'Detalhes da Entrega - {agenda_entrega.cliente.razao_social}',
        'agenda_entrega': agenda_entrega,
    }
    
    return render(request, 'notas/agenda/detalhes_agenda_entrega.html', context)

@login_required
@user_passes_test(is_admin)
def alterar_status_agenda(request, pk):
    """Altera o status de uma entrega agendada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    
    if request.method == 'POST':
        novo_status = request.POST.get('status')
        if novo_status in [choice[0] for choice in AgendaEntrega.STATUS_ENTREGA_CHOICES]:
            agenda_entrega.status = novo_status
            agenda_entrega.save()
            messages.success(request, f'Status alterado para {agenda_entrega.get_status_display()}!')
            return redirect('notas:listar_agenda_entregas')
        else:
            messages.error(request, 'Status inválido!')
    
    context = {
        'title': f'Alterar Status - {agenda_entrega.cliente.razao_social}',
        'agenda_entrega': agenda_entrega,
        'status_choices': AgendaEntrega.STATUS_ENTREGA_CHOICES,
    }
    
    return render(request, 'notas/agenda/alterar_status_agenda.html', context)

@login_required
@user_passes_test(is_admin)
def marcar_em_andamento(request, pk):
    """Marca uma entrega como em andamento"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    agenda_entrega.status = 'Em Andamento'
    agenda_entrega.save()
    messages.success(request, 'Entrega marcada como Em Andamento!')
    return redirect('notas:listar_agenda_entregas')

@login_required
@user_passes_test(is_admin)
def marcar_concluida(request, pk):
    """Marca uma entrega como concluída"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    agenda_entrega.status = 'Concluída'
    agenda_entrega.save()
    messages.success(request, 'Entrega marcada como Concluída!')
    return redirect('notas:listar_agenda_entregas')

@login_required
@user_passes_test(is_admin)
def marcar_entregue(request, pk):
    """Marca uma entrega como entregue"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    agenda_entrega.status = 'Entregue'
    agenda_entrega.save()
    
    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('Content-Type') == 'application/json' or request.method == 'POST':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'message': 'Entrega marcada como Entregue!'
        })
    
    # Se for uma requisição normal, redirecionar
    messages.success(request, 'Entrega marcada como Entregue!')
    return redirect('notas:listar_agenda_entregas')

@login_required
@user_passes_test(is_admin)
def marcar_cancelada(request, pk):
    """Marca uma entrega como cancelada"""
    agenda_entrega = get_object_or_404(AgendaEntrega, pk=pk)
    agenda_entrega.status = 'Cancelada'
    agenda_entrega.save()
    messages.success(request, 'Entrega marcada como Cancelada!')
    return redirect('notas:listar_agenda_entregas')

@login_required
@user_passes_test(is_admin)
def widget_agenda_entregas(request):
    """Widget de agenda de entregas para o dashboard"""
    from datetime import date, timedelta
    
    # Próximas entregas (próximos 7 dias)
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    
    proximas_entregas = AgendaEntrega.objects.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('data_entrega')[:5]
    
    # Entregas de hoje
    entregas_hoje = AgendaEntrega.objects.filter(
        data_entrega=hoje,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('cliente__razao_social')
    
    # Estatísticas rápidas
    total_agendadas = AgendaEntrega.objects.filter(status='Agendada').count()
    total_em_andamento = AgendaEntrega.objects.filter(status='Em Andamento').count()
    
    context = {
        'proximas_entregas': proximas_entregas,
        'entregas_hoje': entregas_hoje,
        'total_agendadas': total_agendadas,
        'total_em_andamento': total_em_andamento,
        'hoje': hoje,
    }
    
    return render(request, 'notas/widgets/widget_agenda_entregas.html', context)

@login_required
@user_passes_test(is_admin)
def test_widget_agenda(request):
    """View de teste para o widget de agenda"""
    from datetime import date, timedelta
    
    # Próximas entregas (próximos 7 dias)
    hoje = date.today()
    proxima_semana = hoje + timedelta(days=7)
    
    proximas_entregas = AgendaEntrega.objects.filter(
        data_entrega__gte=hoje,
        data_entrega__lte=proxima_semana,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('data_entrega')[:5]
    
    # Entregas de hoje
    entregas_hoje = AgendaEntrega.objects.filter(
        data_entrega=hoje,
        status__in=['Agendada', 'Em Andamento']
    ).select_related('cliente').order_by('cliente__razao_social')
    
    # Estatísticas rápidas
    total_agendadas = AgendaEntrega.objects.filter(status='Agendada').count()
    total_em_andamento = AgendaEntrega.objects.filter(status='Em Andamento').count()
    
    context = {
        'title': 'Teste Widget Agenda',
        'proximas_entregas': proximas_entregas,
        'entregas_hoje': entregas_hoje,
        'total_agendadas': total_agendadas,
        'total_em_andamento': total_em_andamento,
        'hoje': hoje,
    }
    
    return render(request, 'notas/test_widget_agenda.html', context)


# =============================================================================
