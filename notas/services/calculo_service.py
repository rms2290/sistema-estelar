"""
Serviço para cálculos financeiros e de valores
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
from ..models import RomaneioViagem, NotaFiscal, TabelaSeguro


class CalculoService:
    """Serviço para cálculos financeiros"""
    
    @staticmethod
    def calcular_seguro_por_estado(valor_total, estado):
        """
        Calcula o valor do seguro baseado no estado e tabela de seguros
        
        Args:
            valor_total: Valor total a ser segurado
            estado: Sigla do estado (ex: 'SP', 'RJ')
        
        Returns:
            dict: {'percentual': Decimal, 'valor_seguro': Decimal}
        """
        try:
            tabela_seguro = TabelaSeguro.objects.get(estado=estado)
            percentual = Decimal(str(tabela_seguro.percentual_seguro))
            valor_seguro = valor_total * (percentual / Decimal('100.0'))
            
            return {
                'percentual': percentual,
                'valor_seguro': valor_seguro
            }
        except TabelaSeguro.DoesNotExist:
            return {
                'percentual': Decimal('0.0'),
                'valor_seguro': Decimal('0.0')
            }
    
    @staticmethod
    def calcular_totais_por_periodo(data_inicio, data_fim, status='Emitido'):
        """
        Calcula totais de romaneios emitidos em um período
        
        Args:
            data_inicio: Data inicial
            data_fim: Data final
            status: Status dos romaneios (padrão: 'Emitido')
        
        Returns:
            dict: {'total_romaneios': int, 'total_valor': Decimal, 'total_peso': float}
        """
        romaneios = RomaneioViagem.objects.filter(
            data_emissao__date__range=[data_inicio, data_fim],
            status=status
        ).prefetch_related('notas_fiscais')
        
        total_romaneios = romaneios.count()
        total_valor = Decimal('0.0')
        total_peso = 0.0
        
        for romaneio in romaneios:
            for nota in romaneio.notas_fiscais.all():
                total_valor += nota.valor
                total_peso += nota.peso
        
        return {
            'total_romaneios': total_romaneios,
            'total_valor': total_valor,
            'total_peso': total_peso
        }
    
    @staticmethod
    def calcular_totais_por_cliente(cliente_id, data_inicio=None, data_fim=None):
        """
        Calcula totais de romaneios de um cliente
        
        Args:
            cliente_id: ID do cliente
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)
        
        Returns:
            dict: {'total_romaneios': int, 'total_valor': Decimal, 'total_peso': float}
        """
        romaneios = RomaneioViagem.objects.filter(cliente_id=cliente_id)
        
        if data_inicio:
            romaneios = romaneios.filter(data_emissao__date__gte=data_inicio)
        if data_fim:
            romaneios = romaneios.filter(data_emissao__date__lte=data_fim)
        
        romaneios = romaneios.prefetch_related('notas_fiscais')
        
        total_romaneios = romaneios.count()
        total_valor = Decimal('0.0')
        total_peso = 0.0
        
        for romaneio in romaneios:
            for nota in romaneio.notas_fiscais.all():
                total_valor += nota.valor
                total_peso += nota.peso
        
        return {
            'total_romaneios': total_romaneios,
            'total_valor': total_valor,
            'total_peso': total_peso
        }
    
    @staticmethod
    def formatar_valor_brasileiro(valor):
        """
        Formata um valor decimal no formato brasileiro
        
        Args:
            valor: Decimal ou float
        
        Returns:
            str: Valor formatado (ex: "R$ 1.234,56")
        """
        from ..views.base import formatar_valor_brasileiro as formatar
        return formatar(valor, tipo='moeda')
    
    @staticmethod
    def formatar_peso_brasileiro(peso):
        """
        Formata um peso no formato brasileiro
        
        Args:
            peso: float
        
        Returns:
            str: Peso formatado (ex: "1.234,56 kg")
        """
        from ..views.base import formatar_peso_brasileiro as formatar
        return formatar(peso)


