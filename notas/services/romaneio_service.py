"""
=============================================================================
SERVIÇO DE ROMANEIOS
=============================================================================

Este módulo contém a lógica de negócio para operações relacionadas a
romaneios de viagem. Centraliza todas as operações complexas que envolvem
criação, edição, exclusão e cálculos de romaneios.

Responsabilidades:
------------------
1. Criação de romaneios (normal e genérico)
2. Edição de romaneios e atualização de status
3. Exclusão de romaneios com atualização de notas fiscais
4. Cálculo de totais (peso, valor, quantidade)
5. Gerenciamento de status de notas fiscais vinculadas
6. Geração de códigos únicos sequenciais

Autor: Sistema Estelar
Data: 2025
Versão: 2.0
=============================================================================
"""
from typing import Tuple, Optional, List, Dict, Any
from django.db import IntegrityError, transaction
from django.contrib import messages
from ..models import RomaneioViagem, NotaFiscal


# ============================================================================
# FUNÇÕES AUXILIARES (PRIVADAS)
# ============================================================================

def _get_next_romaneio_codigo() -> str:
    """
    Gera o próximo código sequencial de romaneio normal.
    
    Formato: ROM-NNN (ex: ROM-001, ROM-002)
    Busca o último romaneio com prefixo "ROM-" (excluindo genéricos ROM-100-)
    e incrementa o número sequencial.
    
    Returns:
        str: Código do próximo romaneio (ex: "ROM-001")
    
    Nota:
        Função privada (_) - não deve ser chamada diretamente.
        Use RomaneioService.criar_romaneio() que chama esta função internamente.
    """
    from ..models import RomaneioViagem
    prefix = "ROM-"
    last_romaneio = RomaneioViagem.objects.filter(
        codigo__startswith=prefix
    ).exclude(
        codigo__startswith="ROM-100-"
    ).order_by('-codigo').first()
    
    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 2 and parts[0] == 'ROM':
                next_sequence = int(parts[1]) + 1
        except (ValueError, IndexError):
            pass
    
    return f"ROM-{next_sequence:03d}"


def _get_next_romaneio_generico_codigo():
    """
    Gera o próximo código sequencial de romaneio genérico.
    
    Formato: ROM-100-NNN (ex: ROM-100-001, ROM-100-002)
    Busca o último romaneio genérico e incrementa o número sequencial.
    
    Returns:
        str: Código do próximo romaneio genérico (ex: "ROM-100-001")
    
    Nota:
        Função privada (_) - não deve ser chamada diretamente.
        Use RomaneioService.criar_romaneio(tipo='generico').
    """
    from ..models import RomaneioViagem
    prefix = "ROM-100-"
    last_romaneio = RomaneioViagem.objects.filter(
        codigo__startswith=prefix
    ).order_by('-codigo').first()
    
    next_sequence = 1
    if last_romaneio and last_romaneio.codigo:
        try:
            parts = last_romaneio.codigo.split('-')
            if len(parts) == 3 and parts[0] == 'ROM' and parts[1] == '100':
                next_sequence = int(parts[2]) + 1
        except (ValueError, IndexError):
            pass
    
    return f"ROM-100-{next_sequence:03d}"


# ============================================================================
# CLASSE PRINCIPAL DO SERVIÇO
# ============================================================================

class RomaneioService:
    """
    Serviço centralizado para operações de negócio relacionadas a Romaneios.
    
    Esta classe encapsula toda a lógica complexa de manipulação de romaneios,
    incluindo validações, atualizações de status, cálculos e gerenciamento
    de transações de banco de dados.
    
    Todos os métodos são estáticos (@staticmethod) para facilitar o uso
    sem necessidade de instanciar a classe.
    
    Uso:
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(
            form_data, emitir=True, tipo='normal'
        )
    
    Métodos Principais:
        - criar_romaneio(): Cria novo romaneio
        - editar_romaneio(): Edita romaneio existente
        - excluir_romaneio(): Exclui romaneio e atualiza notas
        - calcular_totais_romaneio(): Calcula totais de peso e valor
        - obter_notas_disponiveis_para_cliente(): Busca notas disponíveis
    
    Métodos Privados:
        - _atualizar_status_notas_fiscais(): Atualiza status das notas
        - _atualizar_status_nota_removida(): Atualiza nota removida
    """
    
    @staticmethod
    @transaction.atomic
    def criar_romaneio(form_data: Dict[str, Any], emitir: bool = False, tipo: str = 'normal') -> Tuple[Optional[RomaneioViagem], bool, str]:
        """
        Cria um novo romaneio com validações e atualizações de status
        
        Args:
            form_data: Dados do formulário validado
            emitir: Se True, cria como 'Emitido', senão 'Salvo'
            tipo: 'normal' ou 'generico'
        
        Returns:
            tuple: (romaneio, sucesso, mensagem_erro)
        """
        try:
            romaneio = form_data.save(commit=False)
            
            # Gerar código único
            from ..utils.constants import MAX_TENTATIVAS_CODIGO_ROMANEIO
            max_tentativas = MAX_TENTATIVAS_CODIGO_ROMANEIO
            codigo_gerado = False
            
            for tentativa in range(max_tentativas):
                try:
                    if tipo == 'generico':
                        romaneio.codigo = _get_next_romaneio_generico_codigo()
                    else:
                        romaneio.codigo = _get_next_romaneio_codigo()
                    
                    romaneio.data_emissao = form_data.cleaned_data.get('data_romaneio')
                    romaneio.status = 'Emitido' if emitir else 'Salvo'
                    
                    romaneio.save()
                    form_data.save_m2m()  # Salva a relação ManyToMany
                    codigo_gerado = True
                    break
                    
                except IntegrityError as e:
                    if 'codigo' in str(e) and tentativa < max_tentativas - 1:
                        continue
                    else:
                        raise e
            
            if not codigo_gerado:
                return None, False, "Não foi possível gerar código único para o romaneio após várias tentativas."
            
            # Atualizar status das notas fiscais associadas
            RomaneioService._atualizar_status_notas_fiscais(romaneio)
            
            tipo_str = "Genérico" if tipo == 'generico' else ""
            mensagem = f'Romaneio {tipo_str} {romaneio.codigo} ({romaneio.status}) salvo com sucesso!'
            
            return romaneio, True, mensagem
            
        except Exception as e:
            return None, False, f"Erro ao criar romaneio: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def editar_romaneio(romaneio, form_data, emitir=False, salvar=False):
        """
        Edita um romaneio existente e atualiza status das notas fiscais
        
        Args:
            romaneio: Instância do RomaneioViagem
            form_data: Dados do formulário validado
            emitir: Se True, marca como 'Emitido'
            salvar: Se True, marca como 'Salvo'
        
        Returns:
            tuple: (romaneio, sucesso, mensagem_erro)
        """
        try:
            notas_antes_salvar = set(romaneio.notas_fiscais.all())
            
            romaneio.data_emissao = form_data.cleaned_data.get('data_romaneio')
            
            if emitir:
                romaneio.status = 'Emitido'
            elif salvar:
                romaneio.status = 'Salvo'
            
            form_data.save()
            
            notas_depois_salvar = set(romaneio.notas_fiscais.all())
            
            # Atualizar notas removidas
            for nota_fiscal_removida in (notas_antes_salvar - notas_depois_salvar):
                RomaneioService._atualizar_status_nota_removida(nota_fiscal_removida, romaneio)
            
            # Atualizar notas adicionadas/modificadas
            RomaneioService._atualizar_status_notas_fiscais(romaneio)
            
            mensagem = f'Romaneio {romaneio.codigo} ({romaneio.status}) atualizado com sucesso!'
            return romaneio, True, mensagem
            
        except Exception as e:
            return None, False, f"Erro ao editar romaneio: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def excluir_romaneio(romaneio):
        """
        Exclui um romaneio e atualiza status das notas fiscais
        
        Args:
            romaneio: Instância do RomaneioViagem
        
        Returns:
            tuple: (sucesso, mensagem)
        """
        try:
            # Salvar código antes de excluir
            codigo = romaneio.codigo
            pk = romaneio.pk
            
            # Atualizar status das notas antes de excluir
            for nota_fiscal in romaneio.notas_fiscais.all():
                RomaneioService._atualizar_status_nota_removida(nota_fiscal, romaneio)
            
            romaneio.delete()
            
            return True, f'Romaneio {codigo} excluído com sucesso! Notas fiscais associadas foram atualizadas conforme necessário.'
            
        except Exception as e:
            return False, f"Erro ao excluir romaneio: {str(e)}"
    
    @staticmethod
    def _atualizar_status_notas_fiscais(romaneio):
        """
        Atualiza o status de todas as notas fiscais associadas a um romaneio.
        
        Lógica de Atualização:
        1. Se nota está em outro romaneio emitido → Status 'Enviada'
        2. Se romaneio atual está 'Emitido' → Status 'Enviada'
        3. Caso contrário → Status 'Depósito'
        
        Args:
            romaneio (RomaneioViagem): Instância do romaneio
        
        Nota:
            Método privado (_) - chamado internamente pelos métodos públicos.
            Não deve ser chamado diretamente.
        
        Exemplo:
            # Chamado automaticamente por criar_romaneio() ou editar_romaneio()
            RomaneioService._atualizar_status_notas_fiscais(romaneio)
        """
        for nota_fiscal in romaneio.notas_fiscais.all():
            outros_romaneios_emitidos = nota_fiscal.romaneios_vinculados.exclude(
                pk=romaneio.pk
            ).filter(status='Emitido')
            
            if outros_romaneios_emitidos.exists():
                nota_fiscal.status = 'Enviada'
            elif romaneio.status == 'Emitido':
                nota_fiscal.status = 'Enviada'
            else:
                nota_fiscal.status = 'Depósito'
            
            nota_fiscal.save()
    
    @staticmethod
    def _atualizar_status_nota_removida(nota_fiscal, romaneio_excluido):
        """
        Atualiza o status de uma nota fiscal quando removida de um romaneio.
        
        Lógica:
        - Se nota NÃO está em outros romaneios emitidos → Status 'Depósito'
        - Se nota está em outros romaneios emitidos → Mantém 'Enviada'
        
        Args:
            nota_fiscal (NotaFiscal): Instância da nota fiscal
            romaneio_excluido (RomaneioViagem): Romaneio que foi excluído ou
                                                do qual a nota foi removida
        
        Nota:
            Método privado (_) - chamado internamente durante edição/exclusão.
            Não deve ser chamado diretamente.
        
        Exemplo:
            # Chamado automaticamente por editar_romaneio() ou excluir_romaneio()
            RomaneioService._atualizar_status_nota_removida(nota, romaneio)
        """
        outros_romaneios_emitidos = nota_fiscal.romaneios_vinculados.exclude(
            pk=romaneio_excluido.pk
        ).filter(status='Emitido')
        
        if not outros_romaneios_emitidos.exists():
            nota_fiscal.status = 'Depósito'
            nota_fiscal.save()
    
    @staticmethod
    def calcular_totais_romaneio(romaneio):
        """
        Calcula totais de peso e valor de um romaneio
        
        Args:
            romaneio: Instância do RomaneioViagem
        
        Returns:
            dict: {'total_peso': float, 'total_valor': Decimal}
        """
        notas_romaneadas = romaneio.notas_fiscais.all()
        
        total_peso = sum(nota.peso for nota in notas_romaneadas) if notas_romaneadas else 0
        total_valor = sum(nota.valor for nota in notas_romaneadas) if notas_romaneadas else 0
        
        return {
            'total_peso': total_peso,
            'total_valor': total_valor,
            'quantidade_notas': notas_romaneadas.count()
        }
    
    @staticmethod
    def obter_notas_disponiveis_para_cliente(cliente_id):
        """
        Retorna queryset de notas fiscais disponíveis para um cliente
        
        Args:
            cliente_id: ID do cliente
        
        Returns:
            QuerySet: Notas fiscais com status 'Depósito'
        """
        from ..models import Cliente, NotaFiscal
        
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            return NotaFiscal.objects.filter(
                cliente=cliente,
                status='Depósito'
            ).order_by('nota')
        except Cliente.DoesNotExist:
            return NotaFiscal.objects.none()

