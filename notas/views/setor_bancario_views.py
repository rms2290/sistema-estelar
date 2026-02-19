"""
Views de setores bancários (apenas administradores).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from financeiro.models import SetorBancario
from ..forms import SetorBancarioForm
from ..decorators import admin_required


@admin_required
def listar_setores_bancarios(request):
    """Lista todos os setores bancários cadastrados"""
    setores = SetorBancario.objects.all().order_by('setor')
    
    if not setores.exists():
        SetorBancario.objects.create(
            setor='Carregamento',
            nome_responsavel='',
            banco='',
            agencia='',
            conta_corrente='',
            chave_pix='',
            tipo_chave_pix='Telefone',
            ativo=True
        )
        SetorBancario.objects.create(
            setor='Armazenagem',
            nome_responsavel='',
            banco='',
            agencia='',
            conta_corrente='',
            chave_pix='',
            tipo_chave_pix='CNPJ',
            ativo=True
        )
        setores = SetorBancario.objects.all().order_by('setor')
    
    context = {'setores': setores}
    return render(request, 'notas/listar_setores_bancarios.html', context)


@admin_required
def editar_setor_bancario(request, pk):
    """Edita um setor bancário específico"""
    setor = get_object_or_404(SetorBancario, pk=pk)
    
    if request.method == 'POST':
        form = SetorBancarioForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dados bancários do setor {setor.get_setor_display()} atualizados com sucesso!')
            return redirect('notas:listar_setores_bancarios')
        else:
            messages.error(request, 'Houve um erro ao atualizar os dados. Verifique os campos.')
    else:
        form = SetorBancarioForm(instance=setor)
    
    context = {
        'form': form,
        'setor': setor,
    }
    return render(request, 'notas/editar_setor_bancario.html', context)
