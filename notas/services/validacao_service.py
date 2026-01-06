"""
Serviço para validações complexas de negócio
"""
from django.core.exceptions import ValidationError
from validate_docbr import CNPJ, CPF
from ..utils.constants import TAMANHO_CNPJ, TAMANHO_CPF, TAMANHO_PLACA


class ValidacaoService:
    """Serviço para validações de negócio"""
    
    @staticmethod
    def validar_cnpj(cnpj):
        """
        Valida um CNPJ
        
        Args:
            cnpj: String com CNPJ
        
        Returns:
            tuple: (valido, mensagem_erro)
        """
        if not cnpj:
            return False, "CNPJ não informado"
        
        # Remove caracteres não numéricos
        cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_limpo) != TAMANHO_CNPJ:
            return False, f"CNPJ deve conter {TAMANHO_CNPJ} dígitos"
        
        validador = CNPJ()
        if validador.validate(cnpj_limpo):
            return True, None
        else:
            return False, "CNPJ inválido"
    
    @staticmethod
    def validar_cpf(cpf):
        """
        Valida um CPF
        
        Args:
            cpf: String com CPF
        
        Returns:
            tuple: (valido, mensagem_erro)
        """
        if not cpf:
            return False, "CPF não informado"
        
        # Remove caracteres não numéricos
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_limpo) != TAMANHO_CPF:
            return False, f"CPF deve conter {TAMANHO_CPF} dígitos"
        
        validador = CPF()
        if validador.validate(cpf_limpo):
            return True, None
        else:
            return False, "CPF inválido"
    
    @staticmethod
    def validar_placa(placa):
        """
        Valida uma placa de veículo (formato antigo ou Mercosul)
        
        Args:
            placa: String com placa
        
        Returns:
            tuple: (valido, mensagem_erro)
        """
        if not placa:
            return False, "Placa não informada"
        
        placa_limpa = placa.upper().replace('-', '').replace(' ', '')
        
        # Formato antigo: ABC1234 (3 letras + 4 números)
        # Formato Mercosul: ABC1D23 (3 letras + 1 número + 1 letra + 2 números)
        if len(placa_limpa) == TAMANHO_PLACA:
            # Verificar formato antigo
            if placa_limpa[:3].isalpha() and placa_limpa[3:].isdigit():
                return True, None
            # Verificar formato Mercosul
            elif (placa_limpa[:3].isalpha() and 
                  placa_limpa[3].isdigit() and 
                  placa_limpa[4].isalpha() and 
                  placa_limpa[5:].isdigit()):
                return True, None
        
        return False, "Placa inválida. Use formato ABC1234 ou ABC1D23"
    
    @staticmethod
    def validar_romaneio_antes_salvar(romaneio):
        """
        Valida um romaneio antes de salvar
        
        Args:
            romaneio: Instância do RomaneioViagem
        
        Returns:
            tuple: (valido, lista_mensagens_erro)
        """
        erros = []
        
        # Validar que tem pelo menos uma nota fiscal
        if not romaneio.notas_fiscais.exists():
            erros.append("Romaneio deve ter pelo menos uma nota fiscal")
        
        # Validar que tem cliente
        if not romaneio.cliente:
            erros.append("Romaneio deve ter um cliente associado")
        
        # Validar que tem motorista
        if not romaneio.motorista:
            erros.append("Romaneio deve ter um motorista associado")
        
        # Validar que tem veículo principal
        if not romaneio.veiculo_principal:
            erros.append("Romaneio deve ter um veículo principal associado")
        
        return len(erros) == 0, erros
    
    @staticmethod
    def validar_nota_fiscal_antes_salvar(nota_fiscal):
        """
        Valida uma nota fiscal antes de salvar
        
        Args:
            nota_fiscal: Instância da NotaFiscal
        
        Returns:
            tuple: (valido, lista_mensagens_erro)
        """
        erros = []
        
        # Validar que tem número da nota
        if not nota_fiscal.nota:
            erros.append("Nota fiscal deve ter um número")
        
        # Validar que tem cliente
        if not nota_fiscal.cliente:
            erros.append("Nota fiscal deve ter um cliente associado")
        
        # Validar valores positivos
        if nota_fiscal.valor and nota_fiscal.valor < 0:
            erros.append("Valor da nota fiscal não pode ser negativo")
        
        if nota_fiscal.peso and nota_fiscal.peso < 0:
            erros.append("Peso da nota fiscal não pode ser negativo")
        
        return len(erros) == 0, erros

