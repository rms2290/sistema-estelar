"""
Serviço de período de caixa: abrir, fechar, editar, excluir e obter totais.
"""
from decimal import Decimal

from django.utils import timezone

from financeiro.models import MovimentoCaixa, PeriodoMovimentoCaixa


class PeriodoCaixaService:
    """Lógica de negócio dos períodos de movimento de caixa."""

    @classmethod
    def obter_periodo_aberto(cls):
        """Retorna o período com status Aberto mais recente, ou None."""
        return PeriodoMovimentoCaixa.objects.filter(
            status='Aberto'
        ).order_by('-criado_em').first()

    @classmethod
    def iniciar_periodo(cls, data_inicio, valor_inicial_caixa, observacoes, usuario):
        """
        Inicia um novo período se não existir outro aberto.

        Returns:
            tuple: (periodo, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        if not data_inicio:
            return None, 'Data de início é obrigatória.'
        periodo_aberto = cls.obter_periodo_aberto()
        if periodo_aberto:
            nome = (
                periodo_aberto.data_inicio.strftime('%d/%m/%Y')
                if not periodo_aberto.nome
                else periodo_aberto.nome
            )
            return None, f'Já existe um período aberto: {nome}. Feche-o antes de iniciar um novo.'
        valor = Decimal(str(valor_inicial_caixa)) if valor_inicial_caixa is not None else Decimal('0.00')
        periodo = PeriodoMovimentoCaixa.objects.create(
            nome=None,
            data_inicio=data_inicio,
            valor_inicial_caixa=valor,
            observacoes=observacoes or None,
            status='Aberto',
            usuario_criacao=usuario,
        )
        return periodo, None

    @classmethod
    def fechar_periodo(cls, periodo):
        """
        Fecha um período (chama o método do modelo).

        Returns:
            tuple: (True, None) em sucesso ou (False, mensagem_erro) em falha.
        """
        if periodo.status == 'Fechado':
            return False, 'Período já está fechado'
        periodo.fechar_periodo()
        return True, None

    @classmethod
    def editar_periodo(cls, periodo, data_inicio, valor_inicial_caixa, observacoes):
        """
        Edita período (apenas se não tiver movimentos).

        Returns:
            tuple: (periodo, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        if periodo.movimentos.exists():
            return None, 'Não é possível editar um período que já possui movimentos cadastrados.'
        if not data_inicio:
            return None, 'Data de início é obrigatória.'
        periodo.data_inicio = data_inicio
        periodo.valor_inicial_caixa = Decimal(str(valor_inicial_caixa)) if valor_inicial_caixa is not None else Decimal('0.00')
        periodo.observacoes = observacoes or None
        periodo.save()
        return periodo, None

    @classmethod
    def excluir_periodo(cls, periodo):
        """
        Exclui um período e seus movimentos.

        Returns:
            tuple: (movimentos_count, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        movimentos_count = periodo.movimentos.count()
        periodo.movimentos.all().delete()
        periodo.delete()
        return movimentos_count, None

    @classmethod
    def get_totais_periodo(cls, periodo):
        """
        Retorna totais de entradas, saídas e saldo para um período.

        Returns:
            dict: total_entradas, total_saidas, saldo (valor_inicial + entradas - saídas).
        """
        movimentos = MovimentoCaixa.objects.filter(periodo=periodo)
        total_entradas = sum(mov.valor for mov in movimentos if mov.is_entrada)
        total_saidas = sum(mov.valor for mov in movimentos if mov.is_saida)
        saldo = periodo.valor_inicial_caixa + total_entradas - total_saidas
        return {
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'saldo': saldo,
        }
