"""
Serviço de acerto diário: regras para salvar acerto e criar movimentos de caixa.
"""
from decimal import Decimal

from financeiro.models import (
    AcertoDiarioCarregamento,
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
                MovimentoCaixa.objects.create(
                    data=acerto.data,
                    tipo='Entrada',
                    valor=descarga.valor,
                    descricao=f"Descarga: {descarga.descricao or 'Descarga'}",
                    categoria='RecebimentoDescarga',
                    acerto_diario=acerto,
                    periodo=periodo_ativo,
                    usuario_criacao=usuario,
                )
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

        return acerto, None
