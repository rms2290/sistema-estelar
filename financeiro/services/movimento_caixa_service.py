"""
Serviço de movimento de caixa: CRUD e atualização de acumulado do funcionário.
"""
import logging
from decimal import Decimal

from financeiro.models import AcumuladoFuncionario, MovimentoCaixa, PeriodoMovimentoCaixa

logger = logging.getLogger(__name__)


class MovimentoCaixaService:
    """Lógica de negócio dos movimentos de caixa."""

    CATEGORIAS_ENTRADA = [c[0] for c in MovimentoCaixa.CATEGORIA_ENTRADA_CHOICES]
    CATEGORIAS_SAIDA = [c[0] for c in MovimentoCaixa.CATEGORIA_SAIDA_CHOICES]

    MSG_SEM_PERIODO = (
        'É necessário iniciar um período antes de criar movimentos. Clique em "Iniciar Período".'
    )

    @classmethod
    def _atualizar_acumulado_ao_criar(cls, funcionario_id, valor):
        """Reduz o acumulado do funcionário pelo valor (acerto = pagamento)."""
        acumulado = AcumuladoFuncionario.objects.filter(
            funcionario_id=funcionario_id
        ).order_by('-semana_inicio').first()
        if acumulado:
            acumulado.valor_acumulado = max(
                Decimal('0.00'),
                acumulado.valor_acumulado - valor,
            )
            acumulado.save()

    @classmethod
    def _atualizar_acumulado_ao_editar(cls, funcionario_id, valor_anterior, valor_novo):
        """Ajusta o acumulado pela diferença (valor_novo - valor_anterior)."""
        diferenca = valor_novo - valor_anterior
        if diferenca == 0:
            return
        acumulado = AcumuladoFuncionario.objects.filter(
            funcionario_id=funcionario_id
        ).order_by('-semana_inicio').first()
        if acumulado:
            acumulado.valor_acumulado = max(
                Decimal('0.00'),
                acumulado.valor_acumulado - diferenca,
            )
            acumulado.save()

    @classmethod
    def _reverter_acumulado_ao_excluir(cls, funcionario_id, valor):
        """Devolve o valor ao acumulado do funcionário."""
        acumulado = AcumuladoFuncionario.objects.filter(
            funcionario_id=funcionario_id
        ).order_by('-semana_inicio').first()
        if acumulado:
            acumulado.valor_acumulado += valor
            acumulado.save()

    @classmethod
    def validar_dados_movimento(cls, data, tipo, valor, categoria=None):
        """
        Valida dados para criação/edição de movimento.

        Returns:
            tuple: (True, None) se válido ou (False, mensagem_erro).
        """
        if not data or not tipo or valor is None or valor <= 0:
            return False, 'Dados inválidos'
        if tipo == 'Entrada' and categoria and categoria not in cls.CATEGORIAS_ENTRADA:
            return False, 'Categoria inválida para entrada'
        if tipo == 'Saida' and categoria and categoria not in cls.CATEGORIAS_SAIDA:
            return False, 'Categoria inválida para saída'
        return True, None

    @classmethod
    def criar_movimento(
        cls,
        data,
        tipo,
        valor,
        descricao,
        categoria,
        funcionario_id,
        cliente_id,
        acerto_diario_id,
        usuario,
    ):
        """
        Cria um movimento de caixa no período ativo.
        Se for AcertoFuncionario, atualiza o acumulado do funcionário.

        Returns:
            tuple: (movimento, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        periodo_ativo = PeriodoMovimentoCaixa.objects.filter(
            status='Aberto'
        ).order_by('-criado_em').first()
        if not periodo_ativo:
            return None, cls.MSG_SEM_PERIODO

        ok, err = cls.validar_dados_movimento(data, tipo, valor, categoria)
        if not ok:
            return None, err

        movimento = MovimentoCaixa.objects.create(
            data=data,
            tipo=tipo,
            valor=valor,
            descricao=descricao or '',
            categoria=categoria or None,
            funcionario_id=funcionario_id,
            cliente_id=cliente_id,
            acerto_diario_id=acerto_diario_id,
            periodo=periodo_ativo,
            usuario_criacao=usuario,
        )

        if tipo == 'AcertoFuncionario' and funcionario_id:
            try:
                cls._atualizar_acumulado_ao_criar(funcionario_id, valor)
            except Exception as e:
                logger.warning('Erro ao atualizar acumulado ao criar movimento: %s', e)

        return movimento, None

    @classmethod
    def editar_movimento(
        cls,
        movimento,
        data,
        tipo,
        valor,
        descricao,
        categoria,
        funcionario_id,
        cliente_id,
    ):
        """
        Atualiza um movimento. Se for AcertoFuncionario, ajusta o acumulado.

        Returns:
            tuple: (movimento, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        ok, err = cls.validar_dados_movimento(data, tipo, valor, categoria)
        if not ok:
            return None, err

        if tipo == 'AcertoFuncionario' and funcionario_id:
            valor_anterior = movimento.valor
            try:
                cls._atualizar_acumulado_ao_editar(
                    funcionario_id, valor_anterior, valor
                )
            except Exception as e:
                logger.warning('Erro ao atualizar acumulado ao editar movimento: %s', e)

        movimento.data = data
        movimento.tipo = tipo
        movimento.valor = valor
        movimento.descricao = descricao or ''
        movimento.categoria = categoria or None
        movimento.funcionario_id = funcionario_id
        movimento.cliente_id = cliente_id
        movimento.save()
        return movimento, None

    @classmethod
    def excluir_movimento(cls, movimento):
        """
        Exclui um movimento. Se for AcertoFuncionario, reverte o acumulado.

        Returns:
            tuple: (True, None) em sucesso ou (None, mensagem_erro) em falha.
        """
        if movimento.tipo == 'AcertoFuncionario' and movimento.funcionario_id:
            try:
                cls._reverter_acumulado_ao_excluir(
                    movimento.funcionario_id,
                    movimento.valor,
                )
            except Exception as e:
                logger.warning('Erro ao reverter acumulado ao excluir movimento: %s', e)
        movimento.delete()
        return True, None

    @classmethod
    def obter_acumulado_funcionario(cls, funcionario_id):
        """
        Retorna o valor acumulado mais recente do funcionário.

        Returns:
            Decimal: valor acumulado ou Decimal('0.00') se não houver registro.
        """
        acumulado = AcumuladoFuncionario.objects.filter(
            funcionario_id=funcionario_id
        ).order_by('-semana_inicio').first()
        return acumulado.valor_acumulado if acumulado else Decimal('0.00')
