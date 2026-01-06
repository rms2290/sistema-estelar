"""
Serviço para lógica de negócio de Notas Fiscais
"""
from django.db import transaction
from ..models import NotaFiscal, Cliente


class NotaFiscalService:
    """Serviço para operações relacionadas a Notas Fiscais"""
    
    @staticmethod
    def criar_nota_fiscal(form_data):
        """
        Cria uma nova nota fiscal
        
        Args:
            form_data: Dados do formulário validado
        
        Returns:
            tuple: (nota_fiscal, sucesso, mensagem_erro)
        """
        try:
            nota_fiscal = form_data.save()
            return nota_fiscal, True, f'Nota Fiscal {nota_fiscal.nota} criada com sucesso!'
        except Exception as e:
            return None, False, f"Erro ao criar nota fiscal: {str(e)}"
    
    @staticmethod
    def atualizar_nota_fiscal(nota_fiscal, form_data):
        """
        Atualiza uma nota fiscal existente
        
        Args:
            nota_fiscal: Instância da NotaFiscal
            form_data: Dados do formulário validado
        
        Returns:
            tuple: (nota_fiscal, sucesso, mensagem_erro)
        """
        try:
            form_data.save()
            return nota_fiscal, True, f'Nota Fiscal {nota_fiscal.nota} atualizada com sucesso!'
        except Exception as e:
            return None, False, f"Erro ao atualizar nota fiscal: {str(e)}"
    
    @staticmethod
    def obter_notas_por_cliente(cliente_id, status=None):
        """
        Retorna notas fiscais de um cliente
        
        Args:
            cliente_id: ID do cliente
            status: Filtro opcional de status ('Depósito', 'Enviada', etc.)
        
        Returns:
            QuerySet: Notas fiscais do cliente
        """
        queryset = NotaFiscal.objects.filter(cliente_id=cliente_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-data', 'nota')
    
    @staticmethod
    def calcular_totais_por_cliente(cliente_id, status=None):
        """
        Calcula totais de peso e valor das notas fiscais de um cliente
        
        Args:
            cliente_id: ID do cliente
            status: Filtro opcional de status
        
        Returns:
            dict: {'total_peso': float, 'total_valor': Decimal, 'quantidade': int}
        """
        notas = NotaFiscalService.obter_notas_por_cliente(cliente_id, status)
        
        total_peso = sum(nota.peso for nota in notas)
        total_valor = sum(nota.valor for nota in notas)
        
        return {
            'total_peso': total_peso,
            'total_valor': total_valor,
            'quantidade': notas.count()
        }
    
    @staticmethod
    def verificar_disponibilidade_nota(nota_fiscal):
        """
        Verifica se uma nota fiscal está disponível para ser adicionada a um romaneio
        
        Args:
            nota_fiscal: Instância da NotaFiscal
        
        Returns:
            bool: True se disponível, False caso contrário
        """
        return nota_fiscal.status == 'Depósito'


