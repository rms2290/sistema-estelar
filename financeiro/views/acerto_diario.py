"""
Views de acerto diário: listar, salvar, carregamento/distribuição, valor Estelar.
"""
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from sistema_estelar.api_utils import json_success, json_error
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from notas.decorators import admin_required
from notas.models import Cliente, CobrancaCarregamento
from financeiro.models import (
    AcertoDiarioCarregamento,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    FuncionarioFluxoCaixa,
    MovimentoCaixa,
)

from django.db import transaction

logger = logging.getLogger(__name__)


@login_required
@admin_required
def listar_acertos_diarios(request):
    """Lista todos os acertos diários com opção de pesquisa"""
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')
    if data_inicio:
        try:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            acertos = acertos.filter(data__gte=data_inicio_obj)
        except Exception as e:
            logger.warning('Filtro data_inicio inválido em listar_acertos_diarios: %s', e)
    if data_fim:
        try:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            acertos = acertos.filter(data__lte=data_fim_obj)
        except Exception as e:
            logger.warning('Filtro data_fim inválido em listar_acertos_diarios: %s', e)
    context = {'acertos': acertos, 'data_inicio': data_inicio, 'data_fim': data_fim}
    return render(request, 'financeiro/fluxo_caixa/listar_acertos_diarios.html', context)


@login_required
@admin_required
def acerto_diario_carregamento(request):
    """Tela principal de acerto diário de carregamento"""
    if request.GET.get('ajax') == '1' and request.GET.get('acerto_id'):
        acerto_id = request.GET.get('acerto_id')
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            carregamentos = list(CarregamentoCliente.objects.filter(
                acerto_diario=acerto
            ).select_related('cliente'))
            carregamentos.sort(key=lambda x: (
                0 if x.cliente else 1,
                x.cliente.razao_social if x.cliente else '',
                x.descricao or ''
            ))
            distribuicoes = DistribuicaoFuncionario.objects.filter(
                acerto_diario=acerto
            ).select_related('funcionario').order_by('funcionario__nome')
            diferenca = abs(acerto.total_carregamentos - acerto.total_distribuido)
            html = render_to_string('financeiro/fluxo_caixa/detalhes_acerto_diario.html', {
                'acerto': acerto,
                'carregamentos': carregamentos,
                'distribuicoes': distribuicoes,
                'diferenca': diferenca,
            }, request=request)
            return json_success(html=mark_safe(html))
        except AcertoDiarioCarregamento.DoesNotExist:
            return json_error('Acerto não encontrado', status=404)

    # "Adicionar" na lista: permite escolher a data (hoje ou retroativa); cria acerto se não existir e abre edição
    data_acerto_param = request.GET.get('data_acerto')
    if data_acerto_param:
        try:
            data_acerto_obj = datetime.strptime(data_acerto_param, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            data_acerto_obj = timezone.now().date()
        acerto_data, _ = AcertoDiarioCarregamento.objects.get_or_create(
            data=data_acerto_obj,
            defaults={
                'valor_estelar': Decimal('0.00'),
                'observacoes': '',
                'usuario_criacao': request.user,
            },
        )
        return redirect(reverse('financeiro:acerto_diario_carregamento') + '?acerto_id=' + str(acerto_data.pk))
    # Compatibilidade: acerto_hoje=1 continua abrindo o acerto de hoje (sem modal)
    if request.GET.get('acerto_hoje') == '1':
        data_hoje_obj = timezone.now().date()
        acerto_hoje, _ = AcertoDiarioCarregamento.objects.get_or_create(
            data=data_hoje_obj,
            defaults={
                'valor_estelar': Decimal('0.00'),
                'observacoes': '',
                'usuario_criacao': request.user,
            },
        )
        return redirect(reverse('financeiro:acerto_diario_carregamento') + '?acerto_id=' + str(acerto_hoje.pk))

    mostrar_formulario = bool(request.GET.get('acerto_id'))
    acerto_id = request.GET.get('acerto_id')

    if not mostrar_formulario:
        data_inicio = request.GET.get('data_inicio', '')
        data_fim = request.GET.get('data_fim', '')
        acertos = AcertoDiarioCarregamento.objects.all().order_by('-data')
        if data_inicio:
            try:
                acertos = acertos.filter(data__gte=datetime.strptime(data_inicio, '%Y-%m-%d').date())
            except Exception as e:
                logger.warning('Filtro data_inicio inválido em acerto_diario_carregamento: %s', e)
        if data_fim:
            try:
                acertos = acertos.filter(data__lte=datetime.strptime(data_fim, '%Y-%m-%d').date())
            except Exception as e:
                logger.warning('Filtro data_fim inválido em acerto_diario_carregamento: %s', e)
        return render(request, 'financeiro/fluxo_caixa/acerto_diario_carregamento.html', {
            'acertos': acertos,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'mostrar_lista': True,
        })

    if acerto_id:
        try:
            acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
            data_obj = acerto.data
        except AcertoDiarioCarregamento.DoesNotExist:
            acerto = None
            data_obj = timezone.now().date()
    else:
        acerto = None
        data_obj = timezone.now().date()

    if acerto:
        carregamentos = list(CarregamentoCliente.objects.filter(
            acerto_diario_id=acerto.pk
        ).select_related('cliente'))
        carregamentos.sort(key=lambda x: (
            0 if x.cliente else 1,
            x.cliente.razao_social if x.cliente else '',
            x.descricao or ''
        ))
        distribuicoes = list(DistribuicaoFuncionario.objects.filter(
            acerto_diario_id=acerto.pk
        ).select_related('funcionario').order_by('funcionario__nome'))
    else:
        carregamentos = []
        distribuicoes = []

    clientes = Cliente.objects.filter(status='Ativo').order_by('razao_social')
    funcionarios = FuncionarioFluxoCaixa.objects.filter(ativo=True).order_by('nome')
    abrir_modal_carregamento = request.GET.get('abrir_modal_carregamento') == '1'
    context = {
        'acerto': acerto,
        'data_selecionada': acerto.data if acerto else (data_obj if data_obj else None),
        'carregamentos': carregamentos,
        'distribuicoes': distribuicoes,
        'clientes': clientes,
        'funcionarios': funcionarios,
        'mostrar_formulario': True,
        'abrir_modal_carregamento': abrir_modal_carregamento,
    }
    return render(request, 'financeiro/fluxo_caixa/acerto_diario_carregamento.html', context)


@login_required
@admin_required
def salvar_acerto_diario(request):
    """Salva o acerto diário e cria movimentos de caixa automaticamente.
    Se acerto_id for enviado, usa esse acerto (evita ambiguidade por data)."""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        data = request.POST.get('data', '').strip()
        observacoes = request.POST.get('observacoes', '')
        acerto_id = request.POST.get('acerto_id', '').strip()
        from financeiro.services import AcertoDiarioService
        acerto, erro = AcertoDiarioService.salvar_acerto_e_criar_movimentos(
            data=data,
            observacoes=observacoes,
            usuario=request.user,
            acerto_id=acerto_id or None,
        )
        if erro:
            return json_error(erro)
        return json_success(
            message='Acerto salvo com sucesso! Movimentos de caixa criados automaticamente.',
            acerto_id=acerto.pk,
        )
    except Exception as e:
        logger.error(f'Erro ao salvar acerto diário: {str(e)}', exc_info=True)
        return json_error(f'Erro ao salvar acerto: {str(e)}')


@login_required
@admin_required
def adicionar_carregamento_cliente_ajax(request):
    """Adiciona um carregamento de cliente ou descarga via AJAX. Aceita acerto_id ou data_acerto (YYYY-MM-DD)."""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id', '').strip()
        data_acerto_str = request.POST.get('data_acerto', '').strip()
        cliente_id = request.POST.get('cliente_id', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        valor = Decimal(request.POST.get('valor', '0.00'))
        observacoes = request.POST.get('observacoes', '')

        if acerto_id:
            acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        elif data_acerto_str:
            try:
                data_acerto = datetime.strptime(data_acerto_str, '%Y-%m-%d').date()
            except ValueError:
                return json_error('Data do acerto inválida')
            acerto, _ = AcertoDiarioCarregamento.objects.get_or_create(
                data=data_acerto,
                defaults={
                    'valor_estelar': Decimal('0.00'),
                    'observacoes': '',
                    'usuario_criacao': request.user,
                },
            )
        else:
            return json_error('Informe acerto_id ou data_acerto')
        if valor <= 0:
            return json_error('Valor deve ser maior que zero')
        if not cliente_id and not descricao:
            return json_error('Informe um cliente ou a descrição da descarga')
        if cliente_id and descricao:
            return json_error('Informe apenas cliente OU descrição, não ambos')
        cliente = None
        if cliente_id:
            cliente = get_object_or_404(Cliente, pk=cliente_id)
        tipo_pagamento = request.POST.get('tipo_pagamento', 'Dinheiro') if not cliente else None

        # Descargas e carregamentos: sempre criar novo registro (mesmo cliente pode ter vários no mesmo dia, ex.: 2 veículos).
        if cliente is None:
            carregamento = CarregamentoCliente.objects.create(
                acerto_diario=acerto,
                cliente=None,
                descricao=descricao,
                valor=valor,
                observacoes=observacoes,
                tipo_pagamento=tipo_pagamento,
                cobranca_carregamento=None,
            )
        else:
            carregamento = CarregamentoCliente.objects.create(
                acerto_diario=acerto,
                cliente=cliente,
                descricao='',
                valor=valor,
                observacoes=observacoes,
                tipo_pagamento=None,
                cobranca_carregamento=None,
            )
        return json_success(
            message='Registro adicionado com sucesso!',
            carregamento_id=carregamento.pk,
            nome_display=carregamento.nome_display,
            tipo=carregamento.tipo,
            valor=str(carregamento.valor),
        )
    except Exception as e:
        return json_error(f'Erro ao adicionar registro: {str(e)}')


@login_required
@admin_required
def remover_carregamento_cliente_ajax(request, pk):
    """Remove um carregamento de cliente via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        carregamento = get_object_or_404(CarregamentoCliente, pk=pk)
        carregamento.delete()
        return json_success(message='Carregamento removido com sucesso!')
    except Exception as e:
        return json_error(f'Erro ao remover carregamento: {str(e)}')


@login_required
@admin_required
def adicionar_distribuicao_funcionario_ajax(request):
    """Adiciona uma distribuição para funcionário via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id')
        funcionario_id = request.POST.get('funcionario_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        funcionario = get_object_or_404(FuncionarioFluxoCaixa, pk=funcionario_id)
        if valor <= 0:
            return json_error('Valor deve ser maior que zero')
        distribuicao, created = DistribuicaoFuncionario.objects.get_or_create(
            acerto_diario=acerto,
            funcionario=funcionario,
            defaults={'valor': valor}
        )
        if not created:
            distribuicao.valor = valor
            distribuicao.save()
        return json_success(
            message='Distribuição adicionada com sucesso!',
            distribuicao_id=distribuicao.pk,
            funcionario_nome=funcionario.nome,
            valor=str(distribuicao.valor),
        )
    except Exception as e:
        return json_error(f'Erro ao adicionar distribuição: {str(e)}')


@login_required
@admin_required
def remover_distribuicao_funcionario_ajax(request, pk):
    """Remove uma distribuição de funcionário via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        distribuicao = get_object_or_404(DistribuicaoFuncionario, pk=pk)
        distribuicao.delete()
        return json_success(message='Distribuição removida com sucesso!')
    except Exception as e:
        return json_error(f'Erro ao remover distribuição: {str(e)}')


@login_required
@admin_required
def salvar_valor_estelar_ajax(request):
    """Salva o valor Estelar via AJAX"""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        acerto_id = request.POST.get('acerto_id')
        valor = Decimal(request.POST.get('valor', '0.00'))
        acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)
        if valor < 0:
            return json_error('Valor não pode ser negativo')
        acerto.valor_estelar = valor
        acerto.save()
        return json_success(message='Valor Estelar salvo com sucesso!', valor=str(valor))
    except Exception as e:
        return json_error(f'Erro ao salvar valor Estelar: {str(e)}')


@login_required
@admin_required
def listar_cobrancas_pendentes_ajax(request):
    """Lista cobranças pendentes para adicionar ao acerto diário (GET)."""
    try:
        cobrancas = CobrancaCarregamento.objects.filter(
            status='Pendente'
        ).select_related('cliente').order_by('-criado_em')[:50]
        data_acerto = request.GET.get('data_acerto', '')
        if data_acerto:
            try:
                data_obj = datetime.strptime(data_acerto, '%Y-%m-%d').date()
                acerto = AcertoDiarioCarregamento.objects.filter(data=data_obj).first()
                if acerto:
                    ja_no_acerto = set(
                        CarregamentoCliente.objects.filter(
                            acerto_diario=acerto
                        ).exclude(cobranca_carregamento__isnull=True).values_list('cobranca_carregamento_id', flat=True)
                    )
                    cobrancas = [c for c in cobrancas if c.pk not in ja_no_acerto]
            except ValueError:
                pass
        lista = [
            {
                'id': c.pk,
                'cliente': c.cliente.razao_social,
                'valor_carregamento': str(c.valor_carregamento or '0.00'),
                'valor_distribuicao_trabalhadores': str(c.valor_distribuicao_trabalhadores) if c.valor_distribuicao_trabalhadores is not None else '',
                'margem': str(c.margem_carregamento),
            }
            for c in cobrancas
        ]
        return json_success(cobrancas=lista)
    except Exception as e:
        return json_error(f'Erro ao listar cobranças: {str(e)}')


@login_required
@admin_required
def adicionar_cobranca_ao_acerto_ajax(request):
    """Adiciona uma cobrança ao acerto do dia (POST: cobranca_id, data_acerto, opcional: distribuicoes JSON)."""
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)
    try:
        import json as _json
        cobranca_id = request.POST.get('cobranca_id', '').strip()
        data_acerto_str = request.POST.get('data_acerto', '').strip()
        if not cobranca_id or not data_acerto_str:
            return json_error('Informe cobranca_id e data_acerto')
        cobranca = get_object_or_404(CobrancaCarregamento, pk=cobranca_id, status='Pendente')
        data_obj = datetime.strptime(data_acerto_str, '%Y-%m-%d').date()
        acerto, _ = AcertoDiarioCarregamento.objects.get_or_create(
            data=data_obj,
            defaults={
                'valor_estelar': Decimal('0.00'),
                'observacoes': '',
                'usuario_criacao': request.user,
            },
        )
        if CarregamentoCliente.objects.filter(acerto_diario=acerto, cobranca_carregamento=cobranca).exists():
            return json_error('Esta cobrança já foi adicionada ao acerto deste dia.')
        valor = cobranca.valor_carregamento or Decimal('0.00')
        if valor <= 0:
            return json_error('Cobrança sem valor de carregamento.')
        carregamento = CarregamentoCliente.objects.create(
            acerto_diario=acerto,
            cliente=cobranca.cliente,
            valor=valor,
            descricao='',
            observacoes=f'Cobrança #{cobranca.pk}',
            cobranca_carregamento=cobranca,
        )
        # Opcional: distribuições entre trabalhadores (JSON: [{"funcionario_id": 1, "valor": "100.00"}, ...])
        distribuicoes_raw = request.POST.get('distribuicoes', '').strip()
        if distribuicoes_raw:
            try:
                itens = _json.loads(distribuicoes_raw)
                valores_por_funcionario = {}
                for item in itens:
                    fid = item.get('funcionario_id')
                    v = Decimal(str(item.get('valor', 0)))
                    if fid and v > 0:
                        fid = int(fid)
                        valores_por_funcionario[fid] = valores_por_funcionario.get(fid, Decimal('0')) + v
                for fid, v in valores_por_funcionario.items():
                    funcionario = FuncionarioFluxoCaixa.objects.filter(pk=fid).first()
                    if funcionario:
                        dist, created = DistribuicaoFuncionario.objects.get_or_create(
                            acerto_diario=acerto,
                            funcionario=funcionario,
                            defaults={'valor': v},
                        )
                        if not created:
                            dist.valor += v
                            dist.save()
            except (ValueError, TypeError) as e:
                logger.warning('distribuicoes inválido em adicionar_cobranca_ao_acerto_ajax: %s', e)
        return json_success(
            message='Cobrança adicionada ao acerto!',
            carregamento_id=carregamento.pk,
            valor=str(carregamento.valor),
            valor_distribuicao=str(cobranca.valor_distribuicao_trabalhadores or ''),
            margem=str(cobranca.margem_carregamento),
        )
    except ValueError:
        return json_error('Data inválida')
    except Exception as e:
        logger.exception('Erro ao adicionar cobrança ao acerto')
        return json_error(f'Erro: {str(e)}')


@login_required
@admin_required
def excluir_acerto_diario(request):
    """
    Exclui um acerto diário:
    - remove MovimentoCaixa associado (FK do MovimentoCaixa para acerto usa SET_NULL)
    - deleta o próprio AcertoDiarioCarregamento (CASCADE remove CarregamentoCliente/DistribuicaoFuncionario)
    """
    if request.method != 'POST':
        return json_error('Método não permitido', status=405)

    acerto_id = request.POST.get('acerto_id', '').strip()
    if not acerto_id:
        return json_error('acerto_id é obrigatório')

    acerto = get_object_or_404(AcertoDiarioCarregamento, pk=acerto_id)

    try:
        with transaction.atomic():
            acerto_data = acerto.data
            MovimentoCaixa.objects.filter(acerto_diario=acerto).delete()
            acerto.delete()

            # Recalcula os acumulados da semana para refletir a exclusão.
            from financeiro.services import AcertoDiarioService
            AcertoDiarioService._recalcular_acumulado_funcionarios_semana(acerto_data)
        return json_success(message='Acerto excluído com sucesso!')
    except Exception as e:
        logger.exception('Erro ao excluir acerto diário: %s', e)
        return json_error(f'Erro ao excluir acerto: {str(e)}')
