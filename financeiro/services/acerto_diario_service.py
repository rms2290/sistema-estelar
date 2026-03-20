"""
Serviço de acerto diário: regras para salvar acerto e criar movimentos de caixa.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum

from financeiro.models import (
    AcertoDiarioCarregamento,
    AcumuladoFuncionario,
    CarregamentoCliente,
    DistribuicaoFuncionario,
    MovimentoCaixa,
    PeriodoMovimentoCaixa,
)


class AcertoDiarioService:
    """Lógica de negócio do acerto diário de carregamento."""

    MSG_SEM_PERIODO = (
        'É necessário iniciar um período antes de salvar o acerto. '
        'Clique em "Iniciar Período" na página de gerenciamento.'
    )

    @classmethod
    def _recalcular_acumulado_funcionarios_semana(cls, data_referencia):
        """
        Recalcula AcumuladoFuncionario para a semana do `data_referencia`.

        Regra:
        - valor_acumulado = soma das DistribuicaoFuncionario da semana (por funcionário)
        - se existir AcumuladoFuncionario com status=Depositado, não altera o valor
        """
        # Semana de segunda (0) a domingo (6)
        semana_inicio = data_referencia - timedelta(days=data_referencia.weekday())
        semana_fim = semana_inicio + timedelta(days=6)

        acertos_semana = AcertoDiarioCarregamento.objects.filter(
            data__gte=semana_inicio,
            data__lte=semana_fim,
        )

        totals = dict(
            DistribuicaoFuncionario.objects.filter(
                acerto_diario__in=acertos_semana
            )
            .values('funcionario_id')
            .annotate(total=Sum('valor'))
            .values_list('funcionario_id', 'total')
        )

        totals = {fid: (t or Decimal('0.00')) for fid, t in totals.items()}

        # Atualiza acumulados existentes (apenas Pendente)
        acumulados_existentes = AcumuladoFuncionario.objects.filter(
            semana_inicio=semana_inicio,
            semana_fim=semana_fim,
        )
        for acc in acumulados_existentes:
            if acc.status != 'Pendente':
                continue
            acc.valor_acumulado = totals.get(acc.funcionario_id, Decimal('0.00'))
            acc.save(update_fields=['valor_acumulado'])

        # Cria acumulados que existam na semana mas não existam na tabela
        for funcionario_id, total in totals.items():
            if total <= 0:
                continue
            acc, created = AcumuladoFuncionario.objects.get_or_create(
                funcionario_id=funcionario_id,
                semana_inicio=semana_inicio,
                semana_fim=semana_fim,
                defaults={'valor_acumulado': total, 'status': 'Pendente'},
            )
            if not created and acc.status == 'Pendente':
                if acc.valor_acumulado != total:
                    acc.valor_acumulado = total
                    acc.save(update_fields=['valor_acumulado'])

    @classmethod
    def salvar_acerto_e_criar_movimentos(cls, data, observacoes, usuario, acerto_id=None):
        """
        Salva ou atualiza o acerto diário e cria os movimentos de caixa correspondentes.

        Se acerto_id for informado, usa esse acerto (garante que estamos atualizando o mesmo
        acerto que o usuário está editando). Caso contrário, usa get_or_create por data.

        Regras:
        - Carregamentos (com cliente): Saída
        - Descargas em dinheiro: Entrada (RecebimentoDescarga)
        - Descargas em depósito: Saída (Outros)
        - Valor Estelar: Entrada (RecebimentoCarregamento)
        - Distribuições para funcionários: AcertoFuncionario (entrada)

        Returns:
            tuple: (acerto, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        if acerto_id:
            try:
                acerto = AcertoDiarioCarregamento.objects.get(pk=acerto_id)
                acerto.observacoes = observacoes
                acerto.save()
            except (ValueError, AcertoDiarioCarregamento.DoesNotExist):
                acerto = None
            if not acerto:
                return None, 'Acerto não encontrado.'
        else:
            if not data:
                return None, 'Informe a data do acerto.'
            acerto, created = AcertoDiarioCarregamento.objects.get_or_create(
                data=data,
                defaults={
                    'valor_estelar': Decimal('0.00'),
                    'observacoes': observacoes,
                    'usuario_criacao': usuario,
                },
            )
            if not created:
                acerto.observacoes = observacoes
                acerto.save()

        periodo_ativo = PeriodoMovimentoCaixa.objects.filter(
            status='Aberto'
        ).order_by('-criado_em').first()
        if not periodo_ativo:
            return None, cls.MSG_SEM_PERIODO

        MovimentoCaixa.objects.filter(acerto_diario=acerto).delete()

        for carregamento in CarregamentoCliente.objects.filter(
            acerto_diario=acerto,
            cliente__isnull=False,
        ):
            MovimentoCaixa.objects.create(
                data=acerto.data,
                tipo='Saida',
                valor=carregamento.valor,
                descricao=f"Carregamento: {carregamento.cliente.razao_social}",
                categoria='Outros',
                cliente=carregamento.cliente,
                acerto_diario=acerto,
                periodo=periodo_ativo,
                usuario_criacao=usuario,
            )

        for descarga in CarregamentoCliente.objects.filter(
            acerto_diario=acerto,
            cliente__isnull=True,
        ):
            tipo_pagamento = (descarga.tipo_pagamento or 'Dinheiro').upper()
            if tipo_pagamento in ('DINHEIRO',):
                # Regra do seu modelo: descarga em dinheiro já entra na divisão
                # (Empresa/Funcionários) via valor_estelar + DistribuicaoFuncionario.
                # Para evitar contabilização duplicada, não criamos MovimentoCaixa
                # como RecebimentoDescarga.
                continue
            elif tipo_pagamento in ('DEPOSITO', 'DEPÓSITO'):
                MovimentoCaixa.objects.create(
                    data=acerto.data,
                    tipo='Saida',
                    valor=descarga.valor,
                    descricao=f"Descarga (Depósito): {descarga.descricao or 'Descarga'}",
                    categoria='Outros',
                    acerto_diario=acerto,
                    periodo=periodo_ativo,
                    usuario_criacao=usuario,
                )

        if acerto.valor_estelar and acerto.valor_estelar > 0:
            MovimentoCaixa.objects.create(
                data=acerto.data,
                tipo='Entrada',
                valor=acerto.valor_estelar,
                descricao="Valor Estelar",
                categoria='RecebimentoCarregamento',
                acerto_diario=acerto,
                periodo=periodo_ativo,
                usuario_criacao=usuario,
            )

        for distribuicao in DistribuicaoFuncionario.objects.filter(acerto_diario=acerto):
            MovimentoCaixa.objects.create(
                data=acerto.data,
                tipo='AcertoFuncionario',
                valor=distribuicao.valor,
                descricao=f"Acerto Funcionário: {distribuicao.funcionario.nome}",
                categoria=None,
                funcionario=distribuicao.funcionario,
                acerto_diario=acerto,
                periodo=periodo_ativo,
                usuario_criacao=usuario,
            )

        # Gera/atualiza "contas a pagar" (valores derivados do acerto diário)
        cls._recalcular_acumulado_funcionarios_semana(acerto.data)

        return acerto, None
